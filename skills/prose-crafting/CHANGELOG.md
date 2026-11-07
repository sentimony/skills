# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.8] - 2026-11-07 - [0.0.101]

### Changed

- The `rewrite` text-only rule now says directly that only the ambiguity notes are left out,
  while notes for dropped checkable claims and instruction-shaped text stay (`20261003-1418`).

## [0.0.7] - 2026-11-04 - [0.0.99]

### Changed

- The description no longer limits the trigger to English or Ukrainian: the method does not
  depend on the language, and the language references stay in the body (`20261030-0448`).

## [0.0.6] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.5] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.4] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.3] - 2026-10-04 - [0.0.66]

### Changed

- `references/ukrainian.md`: dashes in Ukrainian follow `dashfix` 0.0.9. The reference
  no longer forbids replacing a Ukrainian dash with a hyphen; it tells the agent not to
  flag a spaced hyphen as an error or suggest an em dash in its place.
- `SKILL.md`, `references/english.md` and `references/patterns.md` no longer mention a
  dash score or a per-language dash form, which `dashfix` 0.0.9 removed.

## [0.0.2] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.1] - 2026-09-26 - [0.0.55]

### Added

- Reader-first prose editing for docs, READMEs, PR and review replies, chat, email,
  articles, reports, and product copy, with rewrite, audit, and explain modes.
- A reader brief and register table, including a check for conversational
  over-explaining.
- A pattern catalog under stable semantic IDs with strong, contextual, and weak-alone
  signals, and a rule that an edit needs a named reader cost.
- Voice profiles from an author's sample, a claim ledger for meaning preservation, and
  English and Ukrainian guidance.
- Ownership boundaries: dash policy stays with `dashfix`, negative parallelism with
  `negafix`, and deciding whether a review finding is valid with `review-resolution`.
