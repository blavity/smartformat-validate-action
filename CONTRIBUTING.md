# Contributing

## Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setup

```bash
git clone https://github.com/blavity/smartformat-validate-action
cd smartformat-validate-action
uv sync
```

### Running tests

```bash
uv run pytest tests/ -v
```

### Linting

```bash
uv run flake8 validate.py tests/
```

### Running the validator locally

```bash
INPUT_FEED_URLS='["https://blavity.com/rss.xml"]' \
INPUT_MIN_ITEM_COUNT=5 \
INPUT_MAX_AGE_HOURS=48 \
INPUT_REQUIRE_SNF_NAMESPACE=true \
  uv run python validate.py
```

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): description`.

Scopes: `validate`, `action`, `ci`, `docs`.

## Releasing

Releases are fully automated via [release-please](https://github.com/googleapis/release-please):

1. Merge commits to `main` using Conventional Commits.
2. release-please will open or update a release PR aggregating the changes.
3. Merge the release PR — release-please creates the semver tag (`v1.x.x`) and GitHub Release automatically.
4. The `release.yml` workflow fires and moves the floating `v1` tag to the new release commit.

No manual tagging is required.
