# Changelog

All notable changes to the `subagent-plan-dev` skill. Versions refer to
`metadata.version` in `SKILL.md`. This file is for maintainers and is never loaded by
agents using the skill.

## [1.0.4] - 2026-09-15

### Added

- Report plan progress as a counted status line at each task boundary, optionally carrying the current risk level. It reads the task
  states already tracked, introduces no new state and no file, and carries no percentage:
  tasks are not equal in weight, and the fix loop and the escalation ladder move such a number least while costing the most.
  The line is ordinary report text and depends on no vendor-specific output channel, so it
  behaves the same in any harness.

## [1.0.3] - 2026-09-14

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow, the
  dispatch reference and the attribution notes

## [1.0.2] - 2026-09-14

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow, the
  dispatch reference and the attribution notes

## [1.0.1] - 2026-09-14

### Changed

- Renamed the `Instruction hierarchy` section to `Security Model` and completed it with
  trusted inputs, untrusted inputs and a capability statement, bounded by risk-driven
  verification depth, the scope check and the proof required for a parallel wave.

## [1.0.0] - 2026-09-13

### Added

- An orchestration workflow for executing an existing implementation plan through scoped
  subagents under a controller, with sequential execution as the safe default.
- The core invariant that no task is accepted on an implementer's own report, and that
  acceptance requires controller-owned verification run against the tree.
- Three role contracts covering controller, implementer and reviewer, with an explicit
  rule that a reviewer does not become an implementer.
- A pre-flight pass that validates plan concreteness, scans for cross-task conflicts,
  builds the dependency model, classifies risk, detects harness capabilities, and
  initializes state.
- An explicit dependency model over five keys, serving execution order, drift detection,
  load-bearing findings, review context and the parallel-wave decision.
- Per-task risk classification on a three-level scale, driving implementer and review
  strength, verification depth, specialist review and integration checks, with file count
  ruled out as a basis.
- Semantic harness capability detection over six keys, where a missing capability changes
  the mechanism rather than the guarantee.
- Plan-scoped durable state in `.sdd/<plan-id>/`, with six task states, a deterministic
  `plan-id`, and a resume that reconciles the record against history and the working tree.
- A per-task loop with a targeted pre-task drift check, a scoped brief, a deterministic
  scope check against the real diff, general review, conditional domain review, and
  controller-owned verification.
- A three-value reviewer verdict, and domain review selected by discovery rather than a
  hardcoded mapping.
- Four stagnation signals and a four-step escalation ladder ending in a circuit breaker
  that is a last resort rather than the primary detection mechanism.
- A parallel wave permitted under five stated conditions and delegated to `parallel-agents`
  and `workspace-isolation`.
- A fixed six-row final verification matrix in which an inapplicable row is stated rather
  than dropped, and handoffs to `verification-gate` and `branch-finish`.
