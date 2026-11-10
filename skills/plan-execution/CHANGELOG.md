# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.19] - 2026-11-07 - [0.0.102]

### Changed

- Renamed `inline-plan-dev` to `plan-execution`; invoke `/plan-execution`. Only the name and
  its mentions changed.
- Route workspace isolation to `worktree-isolation`, the new name of `git-worktree-isolation`.
- Preview handoff names `doc-preview`, the new name of `scope-check`.

## [0.0.18] - 2026-11-07 - [0.0.101]

### Changed

1. The final verification matrix of six rows is now the default set, and `verification-gate`
   owns the final applicable matrix; the matching wording in
   `references/verification-and-completion.md` and `references/attribution.md` is aligned
   (`20260915-1939`).
2. Preview handoff names `scope-check` again; `doc-preview` is removed in 0.0.101.

## [0.0.17] - 2026-11-05 - [0.0.100]

### Changed

1. Preserve numbered and bulleted task checkboxes, execution mode, and current preview handoff state.
2. Reconcile active work before changing mode and account for preview index edits in review.

## [0.0.16] - 2026-11-04 - [0.0.99]

### Changed

- Section 4 adds an optional per-task cross-review, on only when the user asks for it: one
  read-only reviewer after each task commit, findings through `review-resolution`, the
  final review of section 11 unchanged (`20261104-0912`).
- The execution record may hold one `BASE_SHA` and `Initial dirty paths` group per
  repository, written before that repository's first edit. The final review and the resume
  base check run per repository, and the verification matrix stays one per plan
  (`20261104-0915`).
- Section 2 and `plan-reconciliation.md` name the spec the plan cites as the second place to
  reconcile: an accepted divergence that changes a decision the spec describes updates the
  spec in the same pass or is recorded in the execution record (`20261019-0728`).
- The text names the `~/.sentimony` state of `subagent-plan-dev` next to the legacy `.sdd/`.

## [0.0.15] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.14] - 2026-10-21 - [0.0.89]

### Changed

- The final review runs `cross-review` when at least one of its reviewer CLIs is available,
  and the Security Model names its default destinations: the opposite agent CLI and
  Antigravity, and their vendor APIs.

## [0.0.13] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.12] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.11] - 2026-10-10 - [0.0.76]

### Changed

- Shorter body, same behavior: sections 6, 7, 10, and 11 keep their rules in the body;
  resume from the execution record and the status line rationale moved to
  `references/plan-reconciliation.md`.

## [0.0.10] - 2026-10-10 - [0.0.75]

### Changed

- Implementation review rounds follow the `cross-review` Automatic rounds rule: the next
  round starts without asking up to and including round 3 of the same target.

## [0.0.9] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.8] - 2026-10-04 - [0.0.65]

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

## [0.0.7] - 2026-10-01 - [0.0.63]

### Fixed

- `references/attribution.md` points at the research file under its new
  `YYYYMMDD-HHMM-` name in the maintainer repository.

## [0.0.6] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.5] - 2026-09-15 - [0.0.52]

### Added

- Report plan progress as a counted status line at each task boundary. It reads the task
  states already tracked, introduces no new state and no file, and carries no percentage:
  tasks are not equal in weight, and the investigate-and-fix stretches move such a number least while costing the most.
  The line is ordinary report text and depends on no vendor-specific output channel, so it
  behaves the same in any harness.

## [0.0.4] - 2026-09-14 - [0.0.50]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [0.0.3] - 2026-09-14 - [0.0.49]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [0.0.2] - 2026-09-14 - [0.0.48]

### Changed

- Renamed `Instruction hierarchy` to `Security Model` and completed it with the trusted
  input, the untrusted inputs read while executing tasks, and an honest capability
  statement naming the commands this skill runs and the three bounds that hold them.

## [0.0.1] - 2026-09-13 - [0.0.42]

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
