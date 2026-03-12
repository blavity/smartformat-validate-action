"""
Tests for validate.py — SmartFormat v2.1 feed validator.

Tests use local XML fixtures (no network required) by monkey-patching
validate.fetch_feed to return fixture bytes directly.
"""

import sys
import pathlib

# Make the repo root importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import validate  # noqa: E402

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def make_fetcher(xml_bytes: bytes):
    """Return a fetch_feed replacement that always returns xml_bytes."""

    def _fetch(url):  # noqa: ANN001,ANN202
        return xml_bytes

    return _fetch


# ---------------------------------------------------------------------------
# Channel-level checks
# ---------------------------------------------------------------------------


class TestChannelRequired:
    def test_valid_feed_no_errors(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        errors, warnings = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=5,
            max_age_hours=0,
            require_snf_namespace=True,
        )
        assert errors == []

    def test_missing_channel_title(self, monkeypatch):
        xml = load_fixture("valid_feed.xml").replace(b"<title>Test Feed</title>", b"")
        monkeypatch.setattr(validate, "fetch_feed", make_fetcher(xml))
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("title" in e.lower() for e in errors)

    def test_missing_channel_link(self, monkeypatch):
        xml = load_fixture("valid_feed.xml").replace(
            b"<link>https://example.com</link>", b"", 1
        )
        monkeypatch.setattr(validate, "fetch_feed", make_fetcher(xml))
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("link" in e.lower() for e in errors)

    def test_missing_channel_description(self, monkeypatch):
        xml = load_fixture("valid_feed.xml").replace(
            b"<description>A test RSS feed</description>", b""
        )
        monkeypatch.setattr(validate, "fetch_feed", make_fetcher(xml))
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("description" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Item-level checks
# ---------------------------------------------------------------------------


class TestItemRequired:
    def test_missing_guid(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_required.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("guid" in e.lower() for e in errors)

    def test_missing_pubdate(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_required.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("pubdate" in e.lower() for e in errors)

    def test_missing_content_encoded(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_required.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("content:encoded" in e for e in errors)

    def test_missing_media_thumbnail(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_required.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("media:thumbnail" in e for e in errors)


# ---------------------------------------------------------------------------
# Item count check
# ---------------------------------------------------------------------------


class TestItemCount:
    def test_below_minimum(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=10,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("minimum" in e.lower() for e in errors)

    def test_meets_minimum(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=5,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert not any("minimum" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Namespace check
# ---------------------------------------------------------------------------


class TestNamespace:
    def test_missing_namespace_fails(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_namespace.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=True,
        )
        assert any("snf" in e.lower() for e in errors)

    def test_missing_namespace_ignored_when_disabled(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_namespace.xml"))
        )
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert not any("snf" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Freshness check (warn-only)
# ---------------------------------------------------------------------------


class TestFreshnessWarning:
    def test_stale_feed_emits_warning(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        # valid_feed.xml has lastBuildDate of 2024-01-01 — well over 48h ago
        _, warnings = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=48,
            require_snf_namespace=False,
        )
        assert any("lastBuildDate" in w for w in warnings)

    def test_freshness_check_disabled(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        _, warnings = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert not any("lastBuildDate" in w for w in warnings)


# ---------------------------------------------------------------------------
# HTTP / parse error handling
# ---------------------------------------------------------------------------


class TestFetchErrors:
    def test_http_error_produces_error(self, monkeypatch):
        import urllib.error

        def bad_fetch(url):
            raise urllib.error.HTTPError(  # type: ignore[arg-type]
                url, 404, "Not Found", None, None
            )

        monkeypatch.setattr(validate, "fetch_feed", bad_fetch)
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("404" in e for e in errors)

    def test_malformed_xml_produces_error(self, monkeypatch):
        monkeypatch.setattr(validate, "fetch_feed", make_fetcher(b"<not valid xml"))
        errors, _ = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("parse" in e.lower() or "xml" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# snf:logo warning
# ---------------------------------------------------------------------------


class TestSnfLogoWarning:
    def test_missing_snf_logo_warns(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("missing_namespace.xml"))
        )
        _, warnings = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert any("snf:logo" in w for w in warnings)

    def test_present_snf_logo_no_warning(self, monkeypatch):
        monkeypatch.setattr(
            validate, "fetch_feed", make_fetcher(load_fixture("valid_feed.xml"))
        )
        _, warnings = validate.validate_feed(
            "https://example.com/rss.xml",
            min_item_count=1,
            max_age_hours=0,
            require_snf_namespace=False,
        )
        assert not any("snf:logo" in w for w in warnings)
