# Changelog

All notable changes to the `scope-triage` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.1.0] - 2026-07-30

- Route C records approved designs in `docs/specs/YYYY-MM-DD-<topic>-design.md`.
- Route C now hands approved designs only to `implementation-planning`.

## [1.0.0] - 2026-07-29

Initial public release as `scope-triage`. Fork of the `brainstorming` skill from
`obra/superpowers` (MIT, © 2025 Jesse Vincent), rebuilt around a scope check that runs
before the design cycle.

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
- `references/design-lenses.md` — six design lenses for Route C when a design
  will not converge
- `references/attribution.md` — fork source, license, and modifications
  relative to upstream
