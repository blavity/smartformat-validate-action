#!/usr/bin/env python3
"""
SmartFormat v2.1 RSS feed validator.

Validates one or more RSS feeds against the SmartNews SmartFormat v2.1
specification: https://publishers.smartnews.com/hc/en-us/articles/360036526213

Hard failures cause a non-zero exit code (action fails).
Warnings are surfaced in the step summary but do not fail the action.

Environment variables (set by action.yml):
  INPUT_FEED_URLS             JSON array of feed URLs
  INPUT_MIN_ITEM_COUNT        Minimum items required per feed (default: 5)
  INPUT_MAX_AGE_HOURS         Max hours since lastBuildDate before warn (default: 48)
  INPUT_REQUIRE_SNF_NAMESPACE Require snf: namespace declaration (default: true)
  GITHUB_OUTPUT               Path to GitHub Actions output file
  GITHUB_STEP_SUMMARY         Path to GitHub Actions step summary file
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ---------------------------------------------------------------------------
# Namespace URIs
# ---------------------------------------------------------------------------
NS_CONTENT = "http://purl.org/rss/1.0/modules/content/"
NS_MEDIA = "http://search.yahoo.com/mrss/"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_SNF = "http://www.smartnews.be/snf"

# Required channel-level tags (plain RSS 2.0, no namespace)
CHANNEL_REQUIRED = ["title", "link", "description"]

# Required item-level tags — (local_name, namespace_uri or None)
ITEM_REQUIRED = [
    ("title", None),
    ("link", None),
    ("guid", None),
    ("pubDate", None),
    ("encoded", NS_CONTENT),  # content:encoded
    ("thumbnail", NS_MEDIA),  # media:thumbnail
]

VALIDATOR_BASE_URL = "https://sf-validator.smartnews.com/?url="


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tag(local, ns=None):
    """Return Clark-notation tag string."""
    if ns:
        return f"{{{ns}}}{local}"
    return local


def _find_text(parent, local, ns=None):
    el = parent.find(_tag(local, ns))
    return el.text.strip() if el is not None and el.text else None


def _has_element(parent, local, ns=None):
    return parent.find(_tag(local, ns)) is not None


def fetch_feed(url):
    """Fetch a URL and return the raw bytes, or raise on HTTP error."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "smartformat-validate-action/1"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_date(date_str):
    """Parse an RFC 2822 date string; return datetime or None."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_feed(url, min_item_count, max_age_hours, require_snf_namespace):
    """
    Validate a single feed URL.

    Returns:
        errors   list[str]  — hard failures
        warnings list[str]  — non-fatal issues
    """
    errors = []
    warnings = []

    # 1. Fetch
    try:
        raw = fetch_feed(url)
    except urllib.error.HTTPError as exc:
        errors.append(f"HTTP {exc.code} fetching feed")
        return errors, warnings
    except Exception as exc:
        errors.append(f"Failed to fetch feed: {exc}")
        return errors, warnings

    # 2. Parse XML
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        errors.append(f"XML parse error: {exc}")
        return errors, warnings

    # 3. RSS 2.0 root check
    if root.tag != "rss":
        errors.append(f"Root element is <{root.tag}>, expected <rss>")
        return errors, warnings

    # 4. snf: namespace declaration
    if require_snf_namespace:
        raw_str = raw.decode("utf-8", errors="replace")
        if "http://www.smartnews.be/snf" not in raw_str:
            errors.append(
                "Missing SmartNews snf: namespace declaration "
                '(xmlns:snf="http://www.smartnews.be/snf")'
            )

    # 5. Channel
    channel = root.find("channel")
    if channel is None:
        errors.append("Missing <channel> element")
        return errors, warnings

    for field in CHANNEL_REQUIRED:
        if not _has_element(channel, field):
            errors.append(f"Channel missing required element <{field}>")

    # 6. lastBuildDate freshness (warn-only)
    if max_age_hours > 0:
        lbd_text = _find_text(channel, "lastBuildDate")
        if lbd_text:
            lbd = parse_date(lbd_text)
            if lbd:
                age = datetime.now(timezone.utc) - lbd
                if age > timedelta(hours=max_age_hours):
                    hours_old = int(age.total_seconds() / 3600)
                    warnings.append(
                        f"<lastBuildDate> is {hours_old}h old "
                        f"(threshold: {max_age_hours}h)"
                    )
            else:
                warnings.append(f"<lastBuildDate> could not be parsed: {lbd_text!r}")
        else:
            warnings.append("<lastBuildDate> is absent from <channel>")

    # 7. snf:logo (warn-only)
    if not _has_element(channel, "logo", NS_SNF):
        warnings.append(
            "Channel missing optional <snf:logo> (recommended for branding)"
        )

    # 8. Items
    items = channel.findall("item")
    if len(items) < min_item_count:
        errors.append(
            f"Feed contains {len(items)} item(s); minimum required is {min_item_count}"
        )

    # 9. Per-item required fields
    for idx, item in enumerate(items, start=1):
        item_title = _find_text(item, "title") or f"item[{idx}]"
        for local, ns in ITEM_REQUIRED:
            if not _has_element(item, local, ns):
                ns_prefix = ""
                if ns == NS_CONTENT:
                    ns_prefix = "content:"
                elif ns == NS_MEDIA:
                    ns_prefix = "media:"
                errors.append(
                    f"Item {idx} ({item_title!r}) missing <{ns_prefix}{local}>"
                )

        # description is optional per spec but recommended (warn-only)
        if not _has_element(item, "description"):
            warnings.append(
                f"Item {idx} ({item_title!r}) missing optional <description>"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Summary rendering
# ---------------------------------------------------------------------------


def build_summary(results, feed_urls):
    """Return a Markdown string for $GITHUB_STEP_SUMMARY."""
    lines = ["# SmartFormat Feed Validation\n"]

    all_passed = all(not errs for errs, _ in results.values())
    badge = "**Result: PASS**" if all_passed else "**Result: FAIL**"
    lines.append(f"{badge}\n")

    for url in feed_urls:
        errs, warns = results[url]
        status = "PASS" if not errs else "FAIL"
        icon = ":white_check_mark:" if not errs else ":x:"
        encoded_url = urllib.parse.quote(url, safe="")
        validator_link = (
            f"[Open in SmartNews Validator]({VALIDATOR_BASE_URL}{encoded_url})"
        )

        lines.append(f"## {icon} {url}\n")
        lines.append(f"Status: **{status}** | {validator_link}\n")

        if errs:
            lines.append("### Errors\n")
            for e in errs:
                lines.append(f"- {e}")
            lines.append("")

        if warns:
            lines.append("### Warnings\n")
            for w in warns:
                lines.append(f"- {w}")
            lines.append("")

        if not errs and not warns:
            lines.append("All checks passed with no warnings.\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():

    # Read inputs
    feed_urls_raw = os.environ.get("INPUT_FEED_URLS", "").strip()
    min_item_count = int(os.environ.get("INPUT_MIN_ITEM_COUNT", "5"))
    max_age_hours = int(os.environ.get("INPUT_MAX_AGE_HOURS", "48"))
    require_snf_namespace = (
        os.environ.get("INPUT_REQUIRE_SNF_NAMESPACE", "true").lower() == "true"
    )
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    github_step_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")

    # Parse feed URLs
    try:
        feed_urls = json.loads(feed_urls_raw)
        if not isinstance(feed_urls, list) or not feed_urls:
            raise ValueError("feed_urls must be a non-empty JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"::error ::Invalid feed_urls input: {exc}", file=sys.stderr)
        sys.exit(1)

    # Validate each feed
    results = {}
    for url in feed_urls:
        print(f"Validating: {url}")
        errs, warns = validate_feed(
            url, min_item_count, max_age_hours, require_snf_namespace
        )
        results[url] = (errs, warns)

        for e in errs:
            print(f"  ERROR: {e}")
        for w in warns:
            print(f"  WARN:  {w}")
        if not errs and not warns:
            print("  OK")

    # Aggregate
    feeds_passed = sum(1 for errs, _ in results.values() if not errs)
    feeds_failed = len(feed_urls) - feeds_passed
    overall = "pass" if feeds_failed == 0 else "fail"

    # Write step summary
    if github_step_summary:
        summary = build_summary(results, feed_urls)
        with open(github_step_summary, "a", encoding="utf-8") as fh:
            fh.write(summary)

    # Write outputs
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"result={overall}\n")
            fh.write(f"feeds_passed={feeds_passed}\n")
            fh.write(f"feeds_failed={feeds_failed}\n")

    if overall == "fail":
        print(
            f"\n{feeds_failed}/{len(feed_urls)} feed(s) failed SmartFormat validation.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(f"\nAll {feeds_passed}/{len(feed_urls)} feed(s) passed.")


if __name__ == "__main__":
    main()
