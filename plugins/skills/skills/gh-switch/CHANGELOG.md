# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.2] - 2026-10-12 - [1.58.4]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [1.1.1] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.1] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.0] - 2026-10-01 - [1.47.0]

### Added
- Initial release: before project-scoped gh commands on github.com, switch to the
  already logged-in account named by GH_ACC in the project's .env/.env and report the
  switch in one line; a stdlib helper with tests on a fake gh.
