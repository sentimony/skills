# Changelog

All notable changes to the `inline-plan-dev` skill. Versions refer to
`metadata.version` in `SKILL.md`. This file is for maintainers and is never loaded by
agents using the skill.

## [1.0.3] - 2026-09-14

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [1.0.2] - 2026-09-14

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [1.0.1] - 2026-09-14

### Changed

- Renamed `Instruction hierarchy` to `Security Model` and completed it with the trusted
  input, the untrusted inputs read while executing tasks, and an honest capability
  statement naming the commands this skill runs and the three bounds that hold them.

## [1.0.0] - 2026-09-13

### Added

- A compact workflow for executing an existing implementation plan inline, in the current
  agent and session, task by task.
- Plan-versus-reality reconciliation built on `PLAN INTENT`, `PLAN APPROACH` and
  `CURRENT REALITY`, with seven named divergence categories.
- A two-value blocker taxonomy whose default for an ordinary failure is
  `investigate -> fix -> verify -> continue`.
- A per-task loop with a targeted pre-task drift check, a risk gate for disruptive work,
  proportional `LOW`, `MEDIUM` and `HIGH` verification depth, and a verification
  equivalence test.
- A deterministic scope check against the real diff and change-impact verification for
  shared code.
- Durable resume in the plan file, with the rule that a recorded status is reconciled
  against history and the working tree before it is trusted.
- A fixed six-row final verification matrix in which an inapplicable row is stated rather
  than dropped.
- An execution-mode contract that keeps inline execution inline, and composition
  boundaries for planning, TDD, debugging, review, verification, workspace, parallel
  agent, subagent orchestration, and branch lifecycle skills.
