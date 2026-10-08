# Changelog

All notable changes to the `commit-all` skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
entries are headed by date; older ones keep the skill version they shipped in.

## 2026-10-09

### Added

- `argument-hint: "[dry-run]"` in the frontmatter, so the Claude Code `/` menu shows the
  documented argument. The skill instructions are unchanged.

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.1.3] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description, and `allow_implicit_invocation: false` mirroring `disable-model-invocation`.
- `metadata.internal: false` in the frontmatter.

## [1.1.2] - 2026-09-15

### Changed

- Step 2 resolves the repository's actual default branch through remote HEAD or
  `init.defaultBranch`, and treats `main`/`master` as a fallback rather than the rule.
  The Security Model lists the two added read-only lookups.

## [1.1.1] - 2026-09-14

### Added
- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

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
