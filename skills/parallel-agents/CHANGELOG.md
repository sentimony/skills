# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.14] - 2026-11-12 - [0.0.104]

### Changed

- Roles with both skill names where the text still named one skill: the plan owner
  (`implement` or `plan-orchestration`) in section 1 and the Security Model, `cr-request`
  next to `review-request`, `finalize` next to `branch-finish` (20261022-0252).
- A corpus brief states the reading mode of every source (enumerated, metadata scan,
  excerpt, full read, substantive analysis); results list expected, covered and uncovered
  sources and return coverage gaps whatever the transport status; five coverage scenarios
  (20261104-1703).
- New section 3a "Read-only wave" skips sections 5-7 for read-only units on one snapshot
  and lets a caller skill with a single read-only child skip the wave; the cost gate
  multiplies width by the result budget (20261022-0251).

## [0.0.13] - 2026-11-07 - [0.0.102]

### Changed

- Route to `plan-execution` (was `inline-plan-dev`), `plan-orchestration` (was `subagent-plan-dev`), renamed in 0.0.102.
- Route workspace isolation to `worktree-isolation`, the new name of `git-worktree-isolation`.

## [0.0.12] - 2026-11-07 - [0.0.101]

### Changed

- Findings resolution, plan ownership, final proof, and the boundary rows name each role by
  both its agentflow skill and its standalone skill (`cr-received` or `review-resolution`,
  `implement` or `subagent-plan-dev`, `verify` or `verification-gate`, `finalize` or
  `branch-finish`), with a "use whichever is installed" rule under the table, in `SKILL.md`
  and `references/integration-and-failures.md` (`20261022-0252`).

## [0.0.11] - 2026-11-04 - [0.0.99]

### Changed

- Briefs gain a result budget field (size bound, mandatory status line, list of sources read);
  large combined results are consolidated into a file before the wave counts as complete.
- The `subagent-plan-dev` ownership row names its state under `~/.sentimony` (legacy `.sdd/`).

## [0.0.10] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.9] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.8] - 2026-10-10 - [0.0.76]

### Changed

- Shorter body, same behavior: sections 4-6 and 12-16 keep their rules in the body;
  independence, isolation, result body, reconciliation, and integration detail live in
  `references/`, and the Security Model points to Safety invariants instead of repeating
  two of them.

## [0.0.7] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.6] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.5] - 2026-09-15 - [0.0.52]

### Changed

- Removed the concrete agent count from the parallel-width guidance. It sat one clause away
  from "Never hardcode a number, because platform limits differ" and read as the number to
  hardcode. Both ideas are kept: task count is not agent count, and width follows balanced
  domains.

## [0.0.4] - 2026-09-14 - [0.0.50]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow and the
  attribution notes

## [0.0.3] - 2026-09-14 - [0.0.49]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow and the
  attribution notes

## [0.0.2] - 2026-09-14 - [0.0.48]

### Changed

- Moved the instruction-boundary rule out of the safety invariants into a dedicated Security
  Model section and completed it with trusted inputs, untrusted inputs including agent
  results, and the capability statement.

## [0.0.1] - 2026-09-13 - [0.0.40]

### Added

- Added a concurrency primitive that proves independence, maps mutable state, bounds wave
  width, and reconciles results before integration.
- Added reference guidance for independence and isolation, dispatch and briefs, integration
  and failures, and upstream adaptation.
