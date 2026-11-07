# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.16] - 2026-11-07 - [0.0.102]

### Changed

1. Preview handoff names `doc-preview`, the new name of `scope-check`.

## [0.0.15] - 2026-11-07 - [0.0.101]

### Changed

1. Scope the "for every request" rule to requests that activate this skill, so it no longer contradicts the description's direct-to-implementation cases (`20260915-1939`).
2. Preview handoff names `scope-check` again; `doc-preview` is removed in 0.0.101.

## [0.0.14] - 2026-11-05 - [0.0.100]

### Changed

1. Refresh localized spec conclusions and state-aware next-step prompts, and preview each saved or edited spec with `doc-preview`.
2. Preserve explicit approval of the reviewed spec and report the preview link.

## [0.0.13] - 2026-11-04 - [0.0.99]

### Changed

1. Route C step 9 and Red Flags now require explicit approval of the saved spec itself before `plan-crafting`; approval of step 4 design portions does not count.

## [0.0.12] - 2026-11-04 - [0.0.98]

### Changed

1. Rewrote the HARD-GATE, approaches, rationalizations, self-review, and flow wording to
   remove passages shared with the upstream skill.
2. LICENSE now names one copyright holder: a word-run comparison with the fork base found no shared run of six or more words.

## [0.0.11] - 2026-10-14 - [0.0.84]

### Changed

- Route C invokes the `scope-check` skill after the spec self-review and after each spec
  edit, so the user reviews an HTML preview; skipped silently when it is not installed.

## [0.0.10] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.9] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.8] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.7] - 2026-09-15 - [0.0.52]

### Changed

- Route B checks compatibility in the repository and the dependency's documentation first,
  and asks the user only when the open question is a policy or product choice. Route C
  already carried "Retrieve facts yourself; ask only about the user's decisions", and the
  red flags already listed asking a question the repository answers; Route B did not say it.

## [0.0.6] - 2026-09-14 - [0.0.49]

### Changed
- Route C saves the approved design as `docs/specs/YYYYMMDD-HHMM-<topic>.md`, replacing the
  date-only name and dropping the `-design` suffix: a timestamped name orders same-day specs
  by creation and makes the suffix redundant

## [0.0.5] - 2026-09-13 - [0.0.45]

### Changed
- Route A now names `tdd` and `debugging` as backticked skill references instead of the
  bare words "TDD" and "debugging", so the root router's handoff into implementation reads
  as the local skills rather than as methodology nouns; routing semantics are unchanged

## [0.0.4] - 2026-08-09 - [0.0.17]

### Changed
- Replaced every typographic dash (em and en) in SKILL.md, including the frontmatter
  description, and in `references/design-lenses.md` and `references/attribution.md` with
  plain-hyphen phrasing per the repository dashfix style; no workflow change

## [0.0.3] - 2026-08-09 - [0.0.16]

### Fixed
- Snyk W007 again: 0.0.2 kept the instruction to repeat "the literal values, names, and
  numbers from the request" and placed the secrets carve-out in a following paragraph,
  which the audit still read as forcing the model to echo user-supplied secrets verbatim.
  Step 0 and Route A now ask for the request's domain values, the prohibition leads its
  own paragraph, and credentials are referenced by placeholder name throughout
- Security Model states that the hypothesis, ledger, announced contract, done criterion,
  spec file, and every shown command reference credentials by placeholder name, so no
  secret is written back to the user or to a file

## [0.0.2] - 2026-08-02 - [0.0.15]

### Fixed
- Snyk W007: added a `## Security Model` section stating that repository files, command
  output, and tool logs are untrusted evidence, not instructions, and that this skill runs
  no shell commands and makes no network calls
- Step 0 and Route A now name the boundary around secrets explicitly: literal values mean
  domain values, never secrets, tokens, keys, passwords, connection strings, or personal
  data; a credential in the request is referenced by name, never echoed, in the done
  criterion and in every command

### Changed
- Route C step 6 states an explicit priority for the spec's save location: an explicit
  user instruction overrides the `docs/specs/YYYY-MM-DD-<topic>-design.md` default; a
  differing repository convention does not, and both locations are named when they differ
- Step 0 point 2 spells out the retrieval strategy: one broad fan-out search aimed at the
  unverified ledger rows first, then targeted reads of the contract files the design
  depends on
- Route C step 4 allows batching design sections into one message when the whole design
  fits a single readable message, keeping per-section approval only where sections are
  separately contentious; also states that a reply carrying both a revision and a new
  question applies the revision first

## [0.0.1] - 2026-07-29 - [0.0.13]

Initial release. Fork of the `brainstorming` skill from `obra/superpowers`
(MIT, © 2025 Jesse Vincent), rebuilt around a scope check that runs before the
design cycle.

### Added
- Step 0 scope check with three routes: A (direct implementation),
  B (light spec), C (full design), plus an uncertainty rule that sends every
  unclear case to Route C
- Assumption ledger (`verified` / `assumed` / `contradicted`, where a
  contradicted entry forces Route C) and a confidence-rated hypothesis as the
  required output of classification
- Route announcement must be self-contained and carry the literal values from
  the request; in Route A whatever proves the done criterion must reproduce
  that exact case
- Explicit user overrides ("just do it" → Route A with a named risk,
  "grill me" → Route C) and a non-interactive-run rule that stops instead of
  guessing when Route C is impossible
- Route C carries the upstream hard gate verbatim in force, plus per-question
  recommended answers and a coverage check before the spec is written
- Common Rationalizations table mirrored to catch under-scoping, six Red Flags
  and a Verification checklist
- Route C writes the approved design to `docs/specs/YYYY-MM-DD-<topic>-design.md`
  and hands it to `plan-crafting` as its terminal state
- `references/design-lenses.md`: six design lenses for Route C when a design
  will not converge
- `references/attribution.md`: fork source, license, and modifications
  relative to upstream
