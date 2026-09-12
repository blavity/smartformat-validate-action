# Agent Guide — smartformat-validate-action

## Constitution check is mandatory

**Before making any change**, read the full constitution:

> `.specify/memory/constitution.md`

Every principle applies to every task. There are no exceptions scoped to
"small" or "quick" changes. If you have not read the constitution in this
session, read it now before proceeding.

---

## Repo at a glance

One **composite** GitHub Action:

```
action.yml     — public inputs/outputs contract
validate.py    — SmartFormat validation logic
tests/         — pytest + XML fixtures
```

Rules:
- `action.yml` inputs/outputs are a public API — removals and renames are
  BREAKING CHANGES (Principle II).
- Do **not** add internal fleet files (`catalog-info.yaml`, `.governance/`,
  org-specific agent bundles) — this is a **public** OSS repo (Principle IX).

## Toolchain

Python 3.11+, [uv](https://docs.astral.sh/uv/). See `CONTRIBUTING.md`.

| Command | What it does |
| --- | --- |
| `uv sync` | Install dev dependencies |
| `uv run ruff check validate.py tests/` | Lint |
| `uv run ruff format --check validate.py tests/` | Format check |
| `uv run pytest tests/ -v` | Test |

**Run all three checks before proposing a PR.**

## Commit format

```
type(scope): description
```

Valid scopes: `validate`, `action`, `ci`, `docs` (see `CONTRIBUTING.md`).

## Before opening a PR

1. Lint + format check + pytest pass locally.
2. Compliance Statement in the PR body — principles affected and how they are met.
3. If you changed `action.yml` inputs/outputs, state Principle II impact and
   semver bump type.
4. If you added a runtime Python dependency, include Principle VII justification.
5. State that changes are agent-generated when applicable.
6. Push the branch; confirm `git status` is clean.

A human maintainer must approve before merge.

## Hard stops — ask before proceeding

- Changing `action.yml` inputs or outputs
- Adding runtime Python dependencies
- Adding files that register this repo in a host org's internal catalog,
  governance bundle, or fleet inventory
- Ambiguous requirements
- Non-trivial pre-existing CI failures

## What this repo does not have

No Backstage catalog, no governance manifest sync, no org-internal CI secrets.
If a task assumes otherwise, stop — those belong in private/platform repos.
