# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.21] - 2026-11-13 - [0.0.107]

### Changed

- Description rewritten as a thesis plus "Use when ..." without "You MUST", at a lower token cost; triggers unchanged.

## [0.0.20] - 2026-11-12 - [0.0.104]

### Changed

- The Composition boundaries table names the agentflow counterpart next to each devflow
  skill: `verify`, `implement`, `cr-received`, `cr-request`, `finalize` (20261027-1500).
- `references/field-techniques.md` gains "Live hangs and blocked processes": stack sampling
  of a live process, slow versus blocked, whether a deadline can run under the failure, the
  whole-call budget against external timeouts, and a `tdd` regression for the blocking state
  (20261111-0206).

## [0.0.19] - 2026-11-07 - [0.0.102]

### Changed

- Route to `plan-execution` (was `inline-plan-dev`), `plan-orchestration` (was `subagent-plan-dev`), renamed in 0.0.102.
- Route workspace isolation to `worktree-isolation`, the new name of `git-worktree-isolation`.

## [0.0.18] - 2026-11-07 - [0.0.101]

### Changed

- Routing now enters through `specify` (agentflow) or `scope-triage`, names `implement`
  as the entry from a failing agentflow plan task, and pairs `plan-craft` with
  `plan-crafting` and `verify` with `verification-gate` (`20261027-1500`).

## [0.0.17] - 2026-11-04 - [0.0.99]

### Changed

- The browser or runtime observation row and the web bug loop also name `webapp-debugger`
  for sessions where the user invoked `/webapp-debugger` themselves.

## [0.0.16] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.15] - 2026-10-12 - [0.0.83]

### Fixed

- `references/attribution.md` says the upstream copyright is acknowledged in the package
  `LICENSE`, which carries Jesse Vincent's notice, rather than in the repository license,
  which does not.

## [0.0.14] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.13] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.12] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.11] - 2026-09-15 - [0.0.52]

### Added

- Step 0 records symptom provenance as `PRE-EXISTING`, `INTRODUCED` or `UNKNOWN`. The step
  already required establishing the tree before attribution; the marker makes that decision
  reviewable instead of implicit, and names `UNKNOWN` as a legitimate value.

## [0.0.10] - 2026-09-14 - [0.0.50]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [0.0.9] - 2026-09-14 - [0.0.49]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [0.0.8] - 2026-09-14 - [0.0.48]

### Changed

- Move the instruction-boundary rule out of `Safety and cleanup` into a new
  `Security Model` section and complete it with trusted inputs, untrusted inputs, and a
  capability statement.

## [0.0.7] - 2026-09-13 - [0.0.44]

### Changed

- Route a review finding with an unclear cause to `review-resolution` instead of the
  upstream `receiving-code-review` name.

## [0.0.6] - 2026-09-13 - [0.0.43]

### Changed

- Route review acquisition and branch completion to `review-request` and `branch-finish`
  instead of the upstream `requesting-code-review` and `finishing-a-development-branch`
  names.

## [0.0.5] - 2026-09-13 - [0.0.42]

### Changed

- Route plan execution failures to `inline-plan-dev` and `subagent-plan-dev` instead of the
  upstream `executing-plans` and `subagent-driven-development` names.
- Attribute execution state to the execution mode rather than naming `.sdd/`, which the
  inline mode does not use.

## [0.0.4] - 2026-09-13 - [0.0.40]

### Changed

- Route independent evidence streams to `parallel-agents`, which owns independence assessment,
  isolation topology, and bounded dispatch.

## [0.0.3] - 2026-09-13 - [0.0.39]

### Changed

- Route safe workspace setup to `workspace-isolation`, which owns isolation and records the
  workspace that runs and inspects the code.

## [0.0.2] - 2026-09-12 - [0.0.38]

### Changed

- Route final verification to `verification-gate`, which owns the authoritative completion
  matrix and requires fresh evidence after a fix.

## [0.0.1] - 2026-09-11 - [0.0.35]

### Added

- Canonical root-cause-first methodology for bugs, regressions, failing tests, build and
  integration failures, flaky behavior, performance anomalies, and unexpected technical behavior.
- Evidence discipline for symptom contracts, reproduction states, raw data, black-box controls,
  component boundaries, falsifiable hypotheses, causal fixes, bounded investigation, and safe cleanup.
- Field reference and upstream attribution with explicit composition boundaries for `web-debug`,
  `tdd`, `vitest`, `typescript`, `verification-before-completion`, and neighboring workflow skills.
