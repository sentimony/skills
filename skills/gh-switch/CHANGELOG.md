# Changelog

All notable changes to the `gh-switch` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.0] - 2026-10-01

### Added
- Initial release: before project-scoped gh commands on github.com, switch to the
  already logged-in account named by GH_ACC in the project's .env/.env and report the
  switch in one line; a stdlib helper with tests on a fake gh.
