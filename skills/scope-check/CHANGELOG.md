# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.4] - 2026-10-14 - [0.0.84]

### Changed

- **Breaking:** rewritten from scratch. `/scope-check` no longer runs `scope-triage`;
  it renders a saved spec or plan to an HTML preview in the OS temp directory, prints a
  clickable `file://` link, and adds the file to the folder `README.md` index when one
  exists. `scope-triage` and `plan-crafting` call it after writing and after each edit.

## [0.0.3] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.2] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.1] - 2026-10-01 - [0.0.61]

### Added

- Experimental user-invoked entry point: `/scope-check` hands the current request to the
  `scope-triage` skill.
