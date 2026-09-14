# Changelog

All notable changes to the `debugging` skill. Versions refer to `metadata.version` in
`SKILL.md`. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.8] - 2026-09-14

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [1.0.7] - 2026-09-14

### Changed

- Move the instruction-boundary rule out of `Safety and cleanup` into a new
  `Security Model` section and complete it with trusted inputs, untrusted inputs, and a
  capability statement.

## [1.0.6] - 2026-09-13

### Changed

- Route a review finding with an unclear cause to `review-resolution` instead of the
  upstream `receiving-code-review` name.

## [1.0.5] - 2026-09-13

### Changed

- Route review acquisition and branch completion to `review-request` and `branch-finish`
  instead of the upstream `requesting-code-review` and `finishing-a-development-branch`
  names.

## [1.0.4] - 2026-09-13

### Changed

- Route plan execution failures to `inline-plan-dev` and `subagent-plan-dev` instead of the
  upstream `executing-plans` and `subagent-driven-development` names.
- Attribute execution state to the execution mode rather than naming `.sdd/`, which the
  inline mode does not use.

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
