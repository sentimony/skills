# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.2] - 2026-10-21 - [1.58.10]

### Changed

- The skill no longer hands the request to `debugging`. `/webapp-debugger` now drives a local
  web app through the agent-browser CLI: a private session, waits on concrete conditions,
  actions by accessibility refs, and console, page errors, network requests, and screenshots
  collected as evidence, with a Security Model. Requires `agent-browser` in PATH; it is
  installed, pinned to 0.39.0, only once the user authorizes setup.

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

## [1.0.0] - 2026-10-01 - [1.48.0]

### Added

- Experimental user-invoked entry point: `/webapp-debugger` hands the current request to the
  `debugging` skill.
