# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.11] - 2026-11-07 - [0.0.101]

### Changed

- `20261101-1223`: the exit 0 "no project config" row now tells the agent that an SSH alias
  `ssh -G` did not resolve to github.com counts as not GitHub, that the helper does not
  diagnose `Include` or `Match`, and to suggest checking `ssh -G <alias>`.

## [0.0.10] - 2026-11-04 - [0.0.99]

### Changed

- `20261104-0706`: the project-to-account mapping moves to
  `~/.sentimony/skills/gh-switch/accounts.md` (a table of `<main checkout>/ | GH_ACC=<login>`
  and `... | GL_ACC=<user>` rows, exact match, worktrees map to the main checkout). The helper
  appends an unambiguous `GH_ACC` row itself under a file lock, parses the table fail-closed,
  refuses symlinks and foreign owners, and `--migrate [--yes]` imports `GH_ACC` and `GL_ACC`
  from `.env/.env` after confirmation without overwriting a differing row. `GH_ACC` and
  `GL_ACC` no longer pick an account from `.env/.env` (a leftover line only prompts the
  migration); `GITLAB_TOKEN` stays there. A GitLab remote
  without a `GL_ACC` row now stops `--gitlab` (exit 2) instead of staying silent.
- `20261101-1223`: a remote through an SSH alias (`git@github-<acc>:owner/repo.git`) is
  recognised when `ssh -G <alias>` resolves its `hostname` to github.com; the owner and
  repository come from the remote, never the alias name. Any other resolution, an `ssh`
  failure, a timeout, or a missing `ssh` leaves the remote ignored. HTTPS remotes are not
  resolved. The Security Model lists the new command. Follow-ups not in this change:
  diagnosing unsupported or ambiguous `Include`/`Match` configuration explicitly.
- `--target` documentation notes that commands without `-R`/`--repo` (`gh api repos/O/R/...`,
  `gh pr view <URL>`) are not covered, so no target-mismatch error is produced for them.

## [0.0.9] - 2026-10-27 - [0.0.95]

### Changed

- `20261024-2354`: a confirmed switch is the skill's authority. "Run the helper" now says
  not to warn that the account changed for other sessions and not to offer, suggest, or
  run a switch back, for the user or for the agent itself; the rule covers the whole
  workflow instead of only the failed-command steps. Security Model calls the shared
  switch expected and limits the report to the helper's line. A contract test in
  `test_gh_switch.py` checks both sentences.

## [0.0.8] - 2026-10-27 - [0.0.93]

### Added

- A missing GH_ACC is added to a gitignored `.env/.env` without asking when the account is
  unambiguous: the only github.com remote owner that is a logged-in account, or the one
  GH_ACC every sibling clone of the same owner names. The helper writes the
  `# used by gh-switch skill` header and the line at the top, keeps every other line
  byte for byte, and reports `gh-switch: GH_ACC=<login> added to .env/.env; ...`. Without
  such an account, under a token override, or with a tracked `.env/.env` it prints the
  no-GH_ACC line as before.

## [0.0.7] - 2026-10-21 - [0.0.89]

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

## [0.0.6] - 2026-10-17 - [0.0.85]

### Added

- `--gitlab` mode: in a project whose .env/.env names GL_ACC, the helper checks before
  GitLab API calls that GITLAB_TOKEN belongs to that account, with one HTTPS
  `GET /api/v4/user` to the single non-GitHub remote host, no redirects, and the token
  masked in every message; exit 7 when the token belongs to another account, and exit 5
  when the Git remotes cannot be read, so the check is never skipped silently. Without the
  flag the helper behaves as in 0.0.5 and does not read the GitLab keys.

## [0.0.5] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.4] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.3] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.2] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.1] - 2026-10-01 - [0.0.60]

### Added
- Initial release: before project-scoped gh commands on github.com, switch to the
  already logged-in account named by GH_ACC in the project's .env/.env and report the
  switch in one line; a stdlib helper with tests on a fake gh.
