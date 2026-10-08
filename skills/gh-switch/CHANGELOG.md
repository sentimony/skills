# Changelog

All notable changes to the `gh-switch` skill. Older entries are headed by the skill
version they shipped in, newer ones by date. This file is for maintainers and is never
loaded by agents using the skill.

## 2026-10-09

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.1] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.0] - 2026-10-01

### Added
- Initial release: before project-scoped gh commands on github.com, switch to the
  already logged-in account named by GH_ACC in the project's .env/.env and report the
  switch in one line; a stdlib helper with tests on a fake gh.
