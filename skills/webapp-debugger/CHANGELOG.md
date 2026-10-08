# Changelog

All notable changes to the `webapp-debugger` skill. Older entries are headed by the
skill version they shipped in, newer ones by date. This file is for maintainers and is
never loaded by agents using the skill.

## 2026-10-09

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.0] - 2026-10-01

### Added

- Experimental user-invoked entry point: `/webapp-debugger` hands the current request to the
  `debugging` skill.
