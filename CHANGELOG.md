# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- release-please-start-changelog -->

## [1.1.0](https://github.com/blavity/smartformat-validate-action/compare/v1.0.0...v1.1.0) (2026-03-12)


### Features

* initial SmartFormat v2.1 validation action ([920456d](https://github.com/blavity/smartformat-validate-action/commit/920456d8a57874f0acec6be1f0ee1eacc222542b))


### Bug Fixes

* **ci:** add .flake8 config with max-line-length=88 ([7228670](https://github.com/blavity/smartformat-validate-action/commit/7228670cd900a145598d93e8e5a45bc8bfdf5213))
* **ci:** use GITHUB_TOKEN for release-please instead of GitHub App ([ef02783](https://github.com/blavity/smartformat-validate-action/commit/ef02783494ded5928a2e062d0895acff313a932e))

## [1.0.0] - 2026-03-12

### Features

- Initial release: SmartFormat v2.1 RSS feed validation
  - Hard-fail checks for channel and item required fields
  - `media:thumbnail` enforcement per SmartFormat spec
  - `snf:` namespace validation
  - Item count threshold
  - Warn-only staleness and optional field checks
  - `$GITHUB_STEP_SUMMARY` table with SmartNews Validator links
  <!-- release-please-end-changelog -->
