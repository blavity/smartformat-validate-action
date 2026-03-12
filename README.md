# smartformat-validate-action

GitHub Action to validate RSS feeds against the [SmartNews SmartFormat v2.1 specification](https://publishers.smartnews.com/hc/en-us/articles/360036526213).

## Usage

```yaml
- uses: blavity/smartformat-validate-action@v1
  with:
    feed_urls: '["https://example.com/rss.xml", "https://example.com/tech/rss.xml"]'
```

### Inputs

| Input                   | Required | Default | Description                                                                          |
| ----------------------- | -------- | ------- | ------------------------------------------------------------------------------------ |
| `feed_urls`             | yes      |         | JSON array of RSS feed URLs to validate                                              |
| `min_item_count`        | no       | `5`     | Minimum number of `<item>` elements required per feed                                |
| `max_age_hours`         | no       | `48`    | Max hours since `<lastBuildDate>` before a staleness warning. Set to `0` to disable. |
| `require_snf_namespace` | no       | `true`  | Require `xmlns:snf="http://www.smartnews.be/snf"` namespace declaration              |

### Outputs

| Output         | Description                                         |
| -------------- | --------------------------------------------------- |
| `result`       | `pass` or `fail`                                    |
| `feeds_passed` | Number of feeds that passed all hard checks         |
| `feeds_failed` | Number of feeds that failed one or more hard checks |

## What gets validated

### Hard failures (action exits non-zero)

**Channel level:**

- `<title>`, `<link>`, `<description>` present

**Item level (per item):**

- `<title>`, `<link>`, `<guid>`, `<pubDate>` present
- `<content:encoded>` present
- `<media:thumbnail>` present (required per SmartFormat v2.1 spec)

**Feed level:**

- Item count ≥ `min_item_count`
- `snf:` namespace declared (when `require_snf_namespace: true`)

### Warnings (surfaced in step summary, do not fail)

- `<lastBuildDate>` older than `max_age_hours`
- `<snf:logo>` absent from channel (recommended for branding)
- Item `<description>` absent (recommended per spec)

## Step summary

Each run writes a Markdown table to `$GITHUB_STEP_SUMMARY` with per-feed pass/fail status and a direct link to the [SmartNews Validator](https://sf-validator.smartnews.com/) for each URL.

## Example — post-deploy smoke test

```yaml
jobs:
  deploy:
    uses: blavity/shared-workflows/.github/workflows/kinsta-deploy.yaml@main
    # ...

  rss-smoke-test:
    needs: deploy
    uses: blavity/shared-workflows/.github/workflows/rss-smoke-test.yaml@main
    with:
      feed_urls: '["https://blavity.com/rss.xml","https://blavity.com/entertainment/rss.xml"]'
```

## Versioning

Pin to a major tag (`@v1`) for stability. See [releases](https://github.com/blavity/smartformat-validate-action/releases) for the changelog.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Trademarks

SmartNews and SmartFormat are trademarks or registered trademarks of SmartNews, Inc. Blavity, Inc. is not affiliated with, endorsed by, or sponsored by SmartNews, Inc. All other trademarks are the property of their respective owners.

## License

MIT — see [LICENSE](LICENSE).
