# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2026-09-15

### Added

- Named `verification-gate` as the owner of the completion decision, in the composition
  table and in the prose after it. A green cycle is evidence about one behavior, not a
  completion verdict.

### Changed

- Narrowed the trigger from "any feature, bug fix, refactor" to behavior changes and
  refactors with a checkable contract, and stated the exclusion of purely mechanical edits.
  The body already routed those away; the description claimed them.

## [1.0.4] - 2026-09-14

### Added

- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [1.0.3] - 2026-09-14

### Changed

- Add the fork maintainer to the LICENSE copyright notice, matching the other forked skills.

## [1.0.2] - 2026-09-13

### Changed

- Route root-cause investigation to `debugging` instead of the upstream
  `systematic-debugging` name, in the invalid-RED guidance, the nondeterminism guidance,
  and the composition table.

## [1.0.1] - 2026-09-13

### Changed

- Route task ordering, execution mode, task ledger, and subagent orchestration to
  `inline-plan-dev` and `subagent-plan-dev` instead of the upstream `executing-plans` and
  `subagent-driven-development` names.

## [1.0.0] - 2026-09-11

### Added

- Added `tdd`, a framework-neutral workflow for behavior-first RED, GREEN, and REFACTOR.
- Added acceptance-boundary, test-level, risk, oracle, determinism, contract, legacy,
  property, sensitivity, impact, and manual-acceptance guidance.
