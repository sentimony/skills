# Changelog

All notable changes to the `review-resolution` skill. Versions refer to
`metadata.version` in `SKILL.md`. This file is for maintainers and is never loaded by
agents using the skill.

## [1.0.2] - 2026-09-14

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [1.0.1] - 2026-09-14

### Changed

- Renamed the security section to `Security Model` and completed it with trusted inputs and
  a capability statement covering read-only Git inspection, no network calls, and edits
  bounded to accepted findings.

## [1.0.0] - 2026-09-12

### Added

- A compact workflow for validating, classifying, and resolving code-review findings.
- Separate assessment, reviewer severity, actual impact, priority, and disposition models.
- Stale, duplicate, contradictory, load-bearing, security, test-quality, and scope handling.
- Finding-level evidence, change-impact checks, proportional re-review, and bounded loop rules.
- Composition boundaries for review-request, verification-gate, debugging, tdd, UI, testing,
  planning, execution, workspace, parallel-agent, and branch lifecycle skills.
