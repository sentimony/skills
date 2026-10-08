# Changelog

All notable changes to the `cross-review` skill. Older entries are headed by the skill
version they shipped in, newer ones by date. This file is for maintainers and is never
loaded by agents using the skill.

## 2026-10-09

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.1.2] - 2026-10-05

### Changed
- Run report token counts use thousands separators (`282,797 in (245,504 cached)`).

## [1.1.1] - 2026-10-05

### Fixed

- Run report: multi-line format (Reviewer, Tokens, Cost, Session) instead of single-line;
  removed redundant skills line (always "none detected" for Codex, "none (disabled by policy)"
  for Claude).
- Documentation: clarify that opposite CLI is required and no same-CLI fallback is supported
  to preserve read-only isolation and prevent circular dependencies.

## [1.1.0] - 2026-10-05

### Added

- Run report: the runner writes `usage.json` with the reviewer's model, effort, skills
  (detected from `SKILL.md` reads for Codex, disabled by policy for Claude), token counts,
  and an approximate cost (Codex from a dated price table in the runner, Claude from the
  CLI's list-price total), plus a session total across resumed runs, and prints a one-line
  summary. Step 7 shows it as a run report above the verdicts.

### Changed

- Codex runs with `--json` and its session id comes from the `thread.started` event; Claude
  runs with `--output-format json` and `review.md` holds the parsed `result`.

## [1.0.0] - 2026-10-04

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
