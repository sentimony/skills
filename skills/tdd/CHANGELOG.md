# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.15] - 2026-11-07 - [0.0.101]

### Changed

- The Composition Boundaries table names the agentflow counterparts `plan-craft`, `implement`
  and `verify` next to the devflow skills, and a new sentence says that in an agentflow plan
  `implement` runs this method inside each task (`20261027-1500`).

## [0.0.14] - 2026-11-04 - [0.0.99]

### Changed

- The Composition Boundaries table adds a `typescript` row: compiler and type errors are
  not a valid RED and stay with `typescript`, while behavioral tests follow `tdd`.

## [0.0.13] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.
- Three section headings that matched the upstream skill were renamed (Overview to Purpose,
  When to Use to Triggers, The Iron Law to The Core Rule); the rules are unchanged.

## [0.0.12] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.11] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.10] - 2026-10-10 - [0.0.76]

### Changed

- Shorter body, same behavior: each conditional mode is one line in the body; the full
  modes live in `references/test-quality.md`.

## [0.0.9] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.8] - 2026-10-04 - [0.0.67]

### Changed

- The title reads `# TDD: Test-Driven Development`, with a colon in place of the
  typographic dash.

## [0.0.7] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.6] - 2026-09-15 - [0.0.52]

### Added

- Named `verification-gate` as the owner of the completion decision, in the composition
  table and in the prose after it. A green cycle is evidence about one behavior, not a
  completion verdict.

### Changed

- Narrowed the trigger from "any feature, bug fix, refactor" to behavior changes and
  refactors with a checkable contract, and stated the exclusion of purely mechanical edits.
  The body already routed those away; the description claimed them.

## [0.0.5] - 2026-09-14 - [0.0.48]

### Added

- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [0.0.4] - 2026-09-14 - [0.0.47]

### Changed

- Add the fork maintainer to the LICENSE copyright notice, matching the other forked skills.

## [0.0.3] - 2026-09-13 - [0.0.44]

### Changed

- Route root-cause investigation to `debugging` instead of the upstream
  `systematic-debugging` name, in the invalid-RED guidance, the nondeterminism guidance,
  and the composition table.

## [0.0.2] - 2026-09-13 - [0.0.42]

### Changed

- Route task ordering, execution mode, task ledger, and subagent orchestration to
  `inline-plan-dev` and `subagent-plan-dev` instead of the upstream `executing-plans` and
  `subagent-driven-development` names.

## [0.0.1] - 2026-09-11 - [0.0.34]

### Added

- Added `tdd`, a framework-neutral workflow for behavior-first RED, GREEN, and REFACTOR.
- Added acceptance-boundary, test-level, risk, oracle, determinism, contract, legacy,
  property, sensitivity, impact, and manual-acceptance guidance.
