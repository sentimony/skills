# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.4.0] - 2026-10-12 - [1.58.4]

### Changed

- Pre-flight inspects the existing test setup before choosing verification commands;
  Vitest-covered tasks load `vitest` alongside `tdd`; acceptance of user-facing interface
  tasks includes `frontend-crafting` quality criteria, with `web-debug` for browser
  evidence; the final matrix loads `vitest` when runner knowledge is needed.
- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [1.3.2] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.3.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: sections 2, 5, 7, 8, and 13 keep their rules in the body;
  the dependency example, state files, resume, status line rationale, and the matrix
  example live in `references/`.

## [1.3.0] - 2026-10-10 - [1.55.0]

### Changed

- Implementation review rounds follow the `cross-review` Automatic rounds rule: the next
  round starts without asking up to and including round 3 of the same target.

## [1.2.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.1.0] - 2026-10-04 - [1.49.0]

### Added

- `base_sha`, `repo_root`, and `initial_dirty_paths` in `.sdd/<plan-id>/state.json`,
  written once in pre-flight. Resume keeps the recorded base, checks the boundary after a
  repository, worktree, or rebase change, and asks the user when no trustworthy base
  exists.
- A `cross-review` row in the routing table (section 12).

### Changed

- The whole-branch review (section 13) runs through `cross-review` in `implementation`
  mode when it is available, and through `review-request` otherwise, with findings going
  to `review-resolution`. Per-task review gates are unchanged.
- The Security Model names the diff that the whole-branch review may send through
  `cross-review` to the other agent CLI and its vendor API.
- `references/state-and-dependencies.md` documents the review base fields and the resume
  rule; `references/verification-and-completion.md` documents the whole-branch review
  through `cross-review` or `review-request`.

## [1.0.6] - 2026-10-01 - [1.48.2]

### Fixed

- `references/attribution.md` points at the research file under its new
  `YYYYMMDD-HHMM-` name in the maintainer repository.

## [1.0.5] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.4] - 2026-09-15 - [1.39.0]

### Added

- Report plan progress as a counted status line at each task boundary, optionally carrying the current risk level. It reads the task
  states already tracked, introduces no new state and no file, and carries no percentage:
  tasks are not equal in weight, and the fix loop and the escalation ladder move such a number least while costing the most.
  The line is ordinary report text and depends on no vendor-specific output channel, so it
  behaves the same in any harness.

## [1.0.3] - 2026-09-14 - [1.36.0]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow, the
  dispatch reference and the attribution notes

## [1.0.2] - 2026-09-14 - [1.35.0]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow, the
  dispatch reference and the attribution notes

## [1.0.1] - 2026-09-14 - [1.34.3]

### Changed

- Renamed the `Instruction hierarchy` section to `Security Model` and completed it with
  trusted inputs, untrusted inputs and a capability statement, bounded by risk-driven
  verification depth, the scope check and the proof required for a parallel wave.

## [1.0.0] - 2026-09-13 - [1.32.0]

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
