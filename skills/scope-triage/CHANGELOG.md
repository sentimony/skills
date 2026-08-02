# Changelog

All notable changes to the `scope-triage` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.1] - 2026-08-02

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

## [1.0.0] - 2026-07-29

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
- `references/design-lenses.md` — six design lenses for Route C when a design
  will not converge
- `references/attribution.md` — fork source, license, and modifications
  relative to upstream
