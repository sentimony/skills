# Changelog

All notable changes to the `scope-check` skill. Versions refer to `metadata.version` in
`SKILL.md`. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.1] - 2026-10-08

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.

## [1.0.0] - 2026-10-01

### Added

- Experimental user-invoked entry point: `/scope-check` hands the current request to the
  `scope-triage` skill.
