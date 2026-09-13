# Changelog

All notable changes to the `debugging` skill. Versions refer to `metadata.version` in
`SKILL.md`. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.3] - 2026-09-13

### Changed

- Route independent evidence streams to `parallel-agents`, which owns independence assessment,
  isolation topology, and bounded dispatch.

## [1.0.2] - 2026-09-13

### Changed

- Route safe workspace setup to `workspace-isolation`, which owns isolation and records the
  workspace that runs and inspects the code.

## [1.0.1] - 2026-09-12

### Changed

- Route final verification to `verification-gate`, which owns the authoritative completion
  matrix and requires fresh evidence after a fix.

## [1.0.0] - 2026-09-11

### Added

- Canonical root-cause-first methodology for bugs, regressions, failing tests, build and
  integration failures, flaky behavior, performance anomalies, and unexpected technical behavior.
- Evidence discipline for symptom contracts, reproduction states, raw data, black-box controls,
  component boundaries, falsifiable hypotheses, causal fixes, bounded investigation, and safe cleanup.
- Field reference and upstream attribution with explicit composition boundaries for `web-debug`,
  `tdd`, `vitest`, `typescript`, `verification-before-completion`, and neighboring workflow skills.
