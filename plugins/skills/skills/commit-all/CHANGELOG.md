# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.4.3] - 2026-10-27 - [1.58.14]

### Changed

- Actions after the commit go to awf `finalize`, or to `branch-finish` where awf is
  not installed.
- `argument-hint` lists the explicit path scope the body already accepts.
- Mechanics: the `-F`-before-pathspec rule joins the partial-commit item instead of
  repeating the same command in its own item; two wrapped workflow lines are reflowed.
  No behavior change.

## [1.4.2] - 2026-10-21 - [1.58.10]

### Added

- `session-only` (or the same limit in words): only the session's own paths and hunks are
  committed, a file with foreign hunks goes through the index, and a session with nothing
  left ends with "no session changes to commit" and the other changed files.
- Step 0 shows, per repository, how many files hold changes the session did not make and
  any `AGENTS.md` or `CLAUDE.md` rule that limits agent commits, offers "only this
  session's changes" as a third option, and leaves out a repository whose rules forbid
  the commit unless the user names it.
- Post-commit actions in the arguments (push, pull request, merge, squash, branch deletion,
  switching to the default branch) are committed for first and then handed to
  `branch-finish`; deploys go to the project's own commands. The skill's own git commands
  do not change.

### Changed

- Step 3 compares each session file's diff with the session's own edits and names foreign
  hunks in the plan; step 4 asks about untracked files unrelated to the session's changes,
  such as screenshots and dumps.

## [1.4.1] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.4.0] - 2026-10-10 - [1.55.0]

### Added

- `--main true|false` (`argument-hint: "[dry-run] [--main true|false]"`). `--main true`
  commits to the default branch without asking; the default `--main false` asks with two
  options, commit there or create a branch from `HEAD`.
- Step 0 offers a commit in every other repository this conversation changed that still
  has uncommitted changes, after listing each with its branch and changed-file count.
  One commit per repository; the Security Model states the wider scope explicitly.

## [1.3.0] - 2026-10-10 - [1.54.1]

### Changed

- Step 1 starts from `git diff --stat` and `git diff --staged --stat`; the full diff is
  read for code, configuration, and documentation, while large generated or data files
  get only the stat and structural signs.
- Step 4 excludes local tooling that is plainly not part of the work (`.envrc`,
  directories of generated output) without stopping, and names each excluded path.
- Step 5 counts the summary line before committing and rewrites it when longer than 72
  characters. It checks what the repository's instructions allow in commit messages and,
  when they restrict it, describes the change by category, count, and period.
- Amend is offered only when the previous commit of this session is unpushed and either
  its message has a defect or the new changes fix it; a later run with new work is always
  a new commit. The introduction now matches the Amend section.
- Mechanics: a staged rename in a partial commit needs both paths in the pathspec.
- Security Model: filenames and diff content may be confidential and reach the message
  only within the repository's rules.

## [1.2.0] - 2026-10-09 - [1.54.0]

### Added

- `argument-hint: "[dry-run]"` in the frontmatter, so the Claude Code `/` menu shows the
  documented argument. The skill instructions are unchanged.

### Changed

- `disable-model-invocation` is `false`, and the Codex display name is `commit-all`.

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.1.3] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description, and `allow_implicit_invocation: false` mirroring `disable-model-invocation`.
- `metadata.internal: false` in the frontmatter.

## [1.1.2] - 2026-09-15 - [1.39.0]

### Changed

- Step 2 resolves the repository's actual default branch through remote HEAD or
  `init.defaultBranch`, and treats `main`/`master` as a fallback rather than the rule.
  The Security Model lists the two added read-only lookups.

## [1.1.1] - 2026-09-14 - [1.34.3]

### Added
- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [1.1.0] - 2026-08-30 - [1.16.0]

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

## [1.0.1] - 2026-08-21 - [1.12.1]

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the frontmatter description to the /commit-all invocation line; the
  never-auto-trigger and own-message rules moved into the skill body.

## [1.0.0] - 2026-08-20 - [1.12.0]

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
