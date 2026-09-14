# Changelog

All notable changes to the `review-request` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.3] - 2026-09-14

Renamed skill reference.

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the composition table

## [1.0.2] - 2026-09-14

Renamed skill reference.

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the composition table

## [1.0.1] - 2026-09-14

Documented the skill's security model as a dedicated section.

### Changed

- Moved the instruction-boundary rule out of the workflow into a new `Security Model`
  section covering trusted inputs, untrusted inputs, the instruction boundary, and the
  skill's capability bounds; step 5 keeps a pointer to it.

## [1.0.0] - 2026-09-11

Initial release.

### Added

- A compact workflow for preparing and dispatching independent code review.
- Exact committed and working-tree review boundaries with relevant untracked files.
- Requirements-backed reviewer briefs, explicit verdict axes, risk routing, finding
  severity, review gaps, stale detection, and review-resolution handoff.
