# Changelog

All notable changes to the `prose-crafting` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.2] - 2026-10-04

### Changed

- `references/ukrainian.md`: dashes in Ukrainian follow `dashfix` 2.0.0. The reference
  no longer forbids replacing a Ukrainian dash with a hyphen; it tells the agent not to
  flag a spaced hyphen as an error or suggest an em dash in its place.
- `SKILL.md`, `references/english.md` and `references/patterns.md` no longer mention a
  dash score or a per-language dash form, which `dashfix` 2.0.0 removed.

## [1.0.1] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.0] - 2026-09-26

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
