# Changelog

All notable changes to the `commit-all` skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-30

One-shot release: an explicit `/commit-all` is the approval, so a normal run on a
feature branch commits in the same turn.

### Changed
- Pre-existing tracked changes no longer trigger a confirmation gate: the
  session-snapshot comparison now only feeds the message's thematic groups and
  suspicious-file screening, and a missing snapshot no longer forces a question
- Step 6 shows the file list and generated message as a progress update and continues
  to the commit in the same turn; only `dry-run` stops there
- Remaining stop conditions listed explicitly: default branch, suspicious untracked
  files, and path/partial-commit arguments whose scope cannot be determined safely

## [1.0.1] - 2026-08-21

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the frontmatter description to the /commit-all invocation line; the
  never-auto-trigger and own-message rules moved into the skill body.

## [1.0.0] - 2026-08-20

### Added
- Initial release: gather the working tree into a single commit on the current branch
  with a generated English message, on explicit `/commit-all` invocation only
  (`disable-model-invocation: true`)
- Guard rails: stop and ask on `main`/`master`, preview the file list and message when
  the tree holds changes the session did not make, screen untracked files for one-off
  artifacts and secrets, never push, never `--amend` without consent, never
  `--no-verify`, never rewrite history
- `dry-run` argument that prints the planned commit without executing it
- Mechanics notes: `git commit -F -` with a heredoc, `-F` before the pathspec, path
  lists in a file or array against zsh word-splitting, partial commits that keep staged
  renames intact
