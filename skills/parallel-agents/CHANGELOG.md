# Changelog

All notable changes to the `parallel-agents` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2026-09-15

### Changed

- Removed the concrete agent count from the parallel-width guidance. It sat one clause away
  from "Never hardcode a number, because platform limits differ" and read as the number to
  hardcode. Both ideas are kept: task count is not agent count, and width follows balanced
  domains.

## [1.0.3] - 2026-09-14

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow and the
  attribution notes

## [1.0.2] - 2026-09-14

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow and the
  attribution notes

## [1.0.1] - 2026-09-14

### Changed

- Moved the instruction-boundary rule out of the safety invariants into a dedicated Security
  Model section and completed it with trusted inputs, untrusted inputs including agent
  results, and the capability statement.

## [1.0.0] - 2026-09-13

### Added

- Added a concurrency primitive that proves independence, maps mutable state, bounds wave
  width, and reconciles results before integration.
- Added reference guidance for independence and isolation, dispatch and briefs, integration
  and failures, and upstream adaptation.
