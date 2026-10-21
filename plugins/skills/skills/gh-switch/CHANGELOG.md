# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.4] - 2026-10-20 - [1.58.10]

### Added

- `--no-switch` mode for projects whose instructions forbid `gh auth switch`: the helper
  checks GH_ACC as before but never switches the shared active account, and prints the
  per-command `GH_TOKEN="$(gh auth token --hostname github.com --user <login>)"` prefix.
- A project with a github.com remote but no GH_ACC now gets the line
  `gh-switch: no GH_ACC in .env/.env; account unchanged, do not switch by hand` instead of
  silence, which agents read as a matching account.

### Changed

- A manual `gh auth switch` after an access error, and switching back afterwards, are
  named as trying another account; exit 4 is documented as a session-wide override only.

## [1.1.3] - 2026-10-17 - [1.58.6]

### Added

- `--gitlab` mode: in a project whose .env/.env names GL_ACC, the helper checks before
  GitLab API calls that GITLAB_TOKEN belongs to that account, with one HTTPS
  `GET /api/v4/user` to the single non-GitHub remote host, no redirects, and the token
  masked in every message; exit 7 when the token belongs to another account, and exit 5
  when the Git remotes cannot be read, so the check is never skipped silently. Without the
  flag the helper behaves as in 1.1.2 and does not read the GitLab keys.

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
