# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.4.0] - 2026-10-12 - [1.58.4]

### Added

- `--agent antigravity` runs the Antigravity CLI (`agy`, observed with 1.3.3) as the
  reviewer, by default `gemini-3.8-flash` with effort `high`, only on the user's explicit
  request and never as a default or fallback. The runner reads the `--output-format json`
  result, records tokens with the cost as unknown, resumes the same conversation with
  `--conversation` and ends with code 24 when `agy` started a new one instead, and ends
  with code 23 when a denied tool call left no answer. The brief embeds the diff and
  forbids commands; SKILL.md and `references/cli-runtime.md` record that `agy` has no
  read-only flag, honors the user's global `permissions.allow`, and loads the reviewed
  repository's `AGENTS.md` and `GEMINI.md`.

### Changed

- The automatic-rounds rule and the Security Model limits are split into labeled bullets
  per case and per reviewer, and `references/cli-runtime.md` opens with a contents list;
  the rules themselves are unchanged.

## [1.3.2] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.3.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: step 6 keeps the exit-code actions in the body; the
  exit-code table, environment allowlist, and artifacts live in
  `references/cli-runtime.md`.

## [1.3.0] - 2026-10-10 - [1.55.0]

### Added

- `argument-hint` and invocation arguments `--agent claude-code|codex`, `--model`, and
  `--effort low|medium|high|xhigh|max`. The runner flag `--reviewer` is renamed
  `--agent`; `--reviewer` and the value `claude` stay as deprecated aliases, and an old
  `run.log` still resumes. The runner rejects an unknown effort before the run; model
  names stay unvalidated. A same-CLI reviewer runs only on an explicit `--agent` and the
  run report says it is not cross-vendor.
- `--target range BASE..HEAD | tree REV | working-tree` makes the runner compute the file
  list, standard exclusions, and fingerprint; `--followup <run-dir> --dispositions
  <file>` starts the next round with the previous findings and their dispositions, and
  `usage.json` gains `round` and `target_total`. New `references/implementation-brief.md`
  with the host's test output and a sandbox note.
- Automatic rounds: after `review-resolution` asks for another round, the next one starts
  without asking up to and including round 3 of the same target, then only with the
  user's consent and a recommendation.

### Changed

- The reviewer gets an environment allowlist (path, home, locale, proxy, its own CLI's
  authentication) instead of the host environment; `--pass-env NAME` adds more.
- `PRICES` is dated 2026-10-10 and adds `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`,
  and `gpt-5.5`; a Claude price table backs up the CLI's own cost. The runner summary is
  ASCII.

## [1.2.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.1.2] - 2026-10-05 - [1.52.0]

### Changed
- Run report token counts use thousands separators (`282,797 in (245,504 cached)`).

## [1.1.1] - 2026-10-05 - [1.51.1]

### Fixed

- Run report: multi-line format (Reviewer, Tokens, Cost, Session) instead of single-line;
  removed redundant skills line (always "none detected" for Codex, "none (disabled by policy)"
  for Claude).
- Documentation: clarify that opposite CLI is required and no same-CLI fallback is supported
  to preserve read-only isolation and prevent circular dependencies.

## [1.1.0] - 2026-10-05 - [1.51.0]

### Added

- Run report: the runner writes `usage.json` with the reviewer's model, effort, skills
  (detected from `SKILL.md` reads for Codex, disabled by policy for Claude), token counts,
  and an approximate cost (Codex from a dated price table in the runner, Claude from the
  CLI's list-price total), plus a session total across resumed runs, and prints a one-line
  summary. Step 7 shows it as a run report above the verdicts.

### Changed

- Codex runs with `--json` and its session id comes from the `thread.started` event; Claude
  runs with `--output-format json` and `review.md` holds the parsed `result`.

## [1.0.0] - 2026-10-04 - [1.49.0]

### Added

- Initial release: hand an implementation plan or a finished implementation to the
  opposite agent CLI (Codex for Claude Code, Claude Code for Codex) for an independent
  read-only review, with a self-contained brief, secret hygiene before the handoff, a
  target fingerprint, and the result passed to review-resolution.
- `scripts/cross_review.py`: stdlib runner with a `CROSS_REVIEW_DEPTH` loop guard, fixed
  read-only argv for both CLIs on run and resume, the reviewed repository forced untrusted
  for the Codex reviewer so its project `.codex/config.toml` is not loaded, private run
  directories under the system temporary directory, and distinct exit codes; tests in
  `scripts/test_cross_review.py`.
- `references/plan-brief.md` for plan mode and `references/cli-runtime.md` for host launch
  mechanics, production commands, and exit codes.
- `agents/openai.yaml` with the Codex display name and short description.
