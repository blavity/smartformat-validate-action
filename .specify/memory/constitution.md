<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0
Added sections: initial ratification — adapted from blavity/do-app-action constitution
  for this Python composite GitHub Action.
Templates requiring updates: none (no .specify/templates in this repo yet)
Follow-up TODOs:
  - TODO(CI_SHA_PINS): pin GitHub Actions steps to full commit SHAs in ci.yml.
  - TODO(PR_TITLE_LINT): merge ci/add-pr-title-lint when ready.
-->

# smartformat-validate-action Constitution

## Core Principles

### I. Single-Responsibility Composite Action

This repository ships **one** GitHub Action: validate RSS feeds against the
SmartNews SmartFormat v2.1 rules in `validate.py`, invoked from root
`action.yml` as a **composite** action. Validation logic MUST live in
`validate.py` (and tests under `tests/`). Do not split into multiple actions
or add orchestration that belongs in caller workflows.

**Rationale**: Callers compose this action alongside their own CI. Scope creep
in a pinned `@v1` dependency breaks external pipelines silently.

### II. Public API Stability

Inputs and outputs declared in `action.yml` are a public contract. Removing or
renaming an existing input or output is a BREAKING CHANGE and MUST trigger a
semver MAJOR bump. Adding optional inputs with defaults is backward-compatible
(MINOR). Callers pin to `@v1`; breaking that tag silently is unacceptable.

**Rationale**: External RSS pipelines depend on stable input names and output
semantics they do not control.

### III. Idempotency & Safe Defaults

Running validation twice on the same feed URLs MUST produce the same pass/fail
outcome for unchanged feeds. Defaults (`min_item_count`, `max_age_hours`,
`require_snf_namespace`) MUST favor the least-surprising behavior for generic
adopters. Warnings MUST NOT flip to hard failures without a semver-justified
contract change.

**Rationale**: Re-runs and matrix jobs are common in GitHub Actions.

### IV. No Secret Surfaces

This action validates **public RSS feed URLs** supplied by the caller. It MUST
NOT read credentials from environment variables, files, or undeclared inputs.
Feed URLs, error details, and step output MUST NOT echo tokens or other secrets
passed incidentally by the caller environment.

**Rationale**: Composite actions run in the caller's job context; accidental
logging of adjacent secrets is a common failure mode.

### V. Test Every Behavior Unit

All non-trivial validation rules in `validate.py` MUST have pytest coverage
using fixtures under `tests/fixtures/`. CI MUST run `ruff check`, `ruff format
--check`, and `pytest` on every PR.

New validation rules MUST ship with at least one passing and one failing fixture
where applicable. "I'll add tests later" is not acceptable for new hard checks.

**Rationale**: The action has no runtime introspection; tests are the quality
gate for feed-validation logic consumed by third parties.

### VI. Conventional Commits Drive Automated Releases

All commits to `main` MUST follow Conventional Commits with scopes matching
changed components (`validate`, `action`, `ci`, `docs`). `feat:` bumps MINOR,
`fix:` bumps PATCH, `feat!:` / `BREAKING CHANGE:` bumps MAJOR. Release-please
automation MUST NOT be bypassed. Manual tagging or force-pushing version tags
is prohibited.

**Rationale**: Automated changelogs and semver accuracy depend on commit
discipline. This is a public repo — consumers read the changelog.

### VII. Minimal, Pinned Dependencies

Runtime dependencies MUST remain empty (`dependencies = []` in
`pyproject.toml`) unless a new runtime library is explicitly approved in the PR.
Dev dependencies (`pytest`, `ruff`) are managed by `uv` with a committed
`uv.lock`. Adding a runtime dependency requires explicit justification in the PR.

GitHub Actions workflow steps SHOULD be pinned to full commit SHAs alongside a
version comment (e.g. `uses: actions/checkout@<sha> # v4`). Renovate or
Dependabot manages updates.

**Rationale**: Smaller surface area for a composite action that ships as source,
not a container image.

### VIII. GitHub Token Sufficiency

CI workflows in this repository MUST operate using only the built-in
`GITHUB_TOKEN` (and no organization-specific secrets). Workflow
`permissions` MUST be least-privilege (`contents: read` for CI; release jobs
may require `contents: write` / `pull-requests: write` as already declared).

Callers MUST be able to run `uses: blavity/smartformat-validate-action@v1`
with only their feed URLs — no Blavity-internal secrets.

**Rationale**: Public, forkable action. Invisible org-only dependencies break
external adoption.

### IX. Organizational Information Confidentiality

No artifact committed to this repository — including source code,
documentation, scripts, agent instructions, specs, plans, and this
constitution — MAY reference, describe, infer, or otherwise expose:

- Internal processes, workflows, fleet tooling, or catalog systems of any host
  organization (e.g. Backstage, org-catalog assemblers, managed-repos
  inventory, internal issue/epic trackers in commit messages or user-facing
  docs).
- Organizational policies, internal URLs, or governance bundles not meant for
  public readers.
- Internal metadata files (`catalog-info.yaml`, `.governance/`, agent bundle
  sync outputs) that register this repo in a host organization's private
  fleet graph.

Guidance, examples, and documentation MUST be written generically so any
organization adopting this action needs no context about the originating
organization.

**Rationale**: This repository is public and forkable. Internal fleet
machinery belongs in private/platform repos — not in the OSS action tree.

### X. Own the Codebase

Pre-existing issues encountered during work MUST be surfaced and tracked, never
silently ignored.

- Trivial fixes (one-line ruff findings, stale comments) MAY be fixed in the
  current PR when low-risk.
- Non-trivial pre-existing issues MUST have a GitHub issue before deferral.
- Silently passing CI by ignoring unrelated findings is prohibited.

### XI. No Stranded Work

Every commit MUST be pushed; release-please PRs MUST be merged promptly after
their triggering feature lands. Merging a PR is not shipping until the
release tag and floating `v1` tag reflect the change (see `CONTRIBUTING.md`).

Agents MUST run `git status` after every commit and resolve unpushed state
before ending a session.

### XII. Documentation as Artifact

User-facing changes MUST update `README.md` and/or `CONTRIBUTING.md` in the
same PR when behavior or contributor workflow changes.

- New or changed `action.yml` inputs/outputs MUST appear in README tables and
  `action.yml` descriptions.
- Breaking changes MUST include a migration note in the PR description.
- Documentation MUST NOT reference internal systems (Principle IX).

## Security & Supply Chain

- CI permissions MUST follow least-privilege unless a broader scope is
  explicitly justified in a workflow comment.
- Dependabot MUST remain enabled for uv/Python and GitHub Actions.
- PRs from external contributors MUST pass CI before maintainer review.
- Validation failures MUST set actionable GitHub Actions outputs (`result`,
  `feeds_failed`) and non-zero exit where appropriate — silent pass on hard
  failures is prohibited.

## Agentic Development Standards

- **Scope discipline**: Confine changes to the stated task.
- **Conventional commits are mandatory** for release-please.
- **Always run local checks** before proposing a PR:
  `uv run ruff check validate.py tests/ && uv run ruff format --check validate.py tests/ && uv run pytest tests/ -v`
- **Lockfiles**: commit `uv.lock` atomically with `pyproject.toml` changes.
- **Public repo awareness**: no `.env`, tokens, internal hostnames, or fleet
  metadata files.
- **No org-specific context** in any committed artifact (Principle IX).
- **Agent directories are gitignored**: `.claude/`, `.codex/`, `.opencode/`,
  and `.specify/**` except `memory/constitution.md` MUST NOT be committed.

## Responsible Agentic Use & Pull Request Policy

- Agents MUST NOT open speculative PRs or expand scope without instruction.
- Agent PRs MUST state they are agent-generated and include a **Compliance
  Statement** listing materially affected principles.
- Every agent PR MUST receive human maintainer approval before merge.
- `action.yml` input/output changes MUST state Principle II impact and semver
  bump type.
- New runtime Python dependencies MUST include Principle VII justification.
- Agents MUST NOT force-push.

## Governance

This constitution supersedes all other development guidance. When `CONTRIBUTING.md`,
a PR comment, or an agent instruction conflicts with this document, this document
wins. Amend this constitution first to resolve genuine conflicts.

**Amendment procedure**:
1. Open a PR changing this file.
2. State version bump type (MAJOR/MINOR/PATCH) and rationale.
3. At least one maintainer MUST approve before merge.
4. Update `CONSTITUTION_VERSION` and ratification date in the same commit.

**Version**: 1.0.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-12
