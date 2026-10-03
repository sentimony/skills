# Changelog

All notable changes to the `inline-plan-dev` skill. Versions refer to
`metadata.version` in `SKILL.md`. This file is for maintainers and is never loaded by
agents using the skill.

## [1.1.0] - 2026-10-04

### Added

- An execution record at the end of the plan file with the resolved `BASE_SHA`, the
  repository root, and the initial dirty paths, written once before the first task edit.
  Resume keeps the recorded base, checks the boundary after a repository, worktree, or
  rebase change, and asks the user when no trustworthy base exists.
- A `cross-review` row in the routing table (section 9).

### Changed

- The final scope and diff review (section 11) runs through `cross-review` in
  `implementation` mode when it is available, and through `review-request` otherwise,
  with findings going to `review-resolution`. A deterministic footprint check against
  `BASE_SHA` runs before it and is no review of its own. The plan outcome review and the
  six-row final verification are unchanged.
- The Security Model names the diff that the final review may send through `cross-review`
  to the other agent CLI and its vendor API.
- `references/verification-and-completion.md` matches the new completion flow: a
  deterministic footprint check against `BASE_SHA`, then the independent scope and diff
  review, then `review-resolution`.

## [1.0.6] - 2026-10-01

### Fixed

- `references/attribution.md` points at the research file under its new
  `YYYYMMDD-HHMM-` name in the maintainer repository.

## [1.0.5] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.4] - 2026-09-15

### Added

- Report plan progress as a counted status line at each task boundary. It reads the task
  states already tracked, introduces no new state and no file, and carries no percentage:
  tasks are not equal in weight, and the investigate-and-fix stretches move such a number least while costing the most.
  The line is ordinary report text and depends on no vendor-specific output channel, so it
  behaves the same in any harness.

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
