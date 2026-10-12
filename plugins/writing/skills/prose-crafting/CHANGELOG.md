# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

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

## [1.0.2] - 2026-10-04 - [1.50.0]

### Changed

- `references/ukrainian.md`: dashes in Ukrainian follow `dashfix` 2.0.0. The reference
  no longer forbids replacing a Ukrainian dash with a hyphen; it tells the agent not to
  flag a spaced hyphen as an error or suggest an em dash in its place.
- `SKILL.md`, `references/english.md` and `references/patterns.md` no longer mention a
  dash score or a per-language dash form, which `dashfix` 2.0.0 removed.

## [1.0.1] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.0] - 2026-09-26 - [1.42.0]

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
