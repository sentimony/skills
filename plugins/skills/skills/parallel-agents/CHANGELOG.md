# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.2] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.1.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: sections 4-6 and 12-16 keep their rules in the body;
  independence, isolation, result body, reconciliation, and integration detail live in
  `references/`, and the Security Model points to Safety invariants instead of repeating
  two of them.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.5] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.4] - 2026-09-15 - [1.39.0]

### Changed

- Removed the concrete agent count from the parallel-width guidance. It sat one clause away
  from "Never hardcode a number, because platform limits differ" and read as the number to
  hardcode. Both ideas are kept: task count is not agent count, and width follows balanced
  domains.

## [1.0.3] - 2026-09-14 - [1.36.0]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow and the
  attribution notes

## [1.0.2] - 2026-09-14 - [1.35.0]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow and the
  attribution notes

## [1.0.1] - 2026-09-14 - [1.34.3]

### Changed

- Moved the instruction-boundary rule out of the safety invariants into a dedicated Security
  Model section and completed it with trusted inputs, untrusted inputs including agent
  results, and the capability statement.

## [1.0.0] - 2026-09-13 - [1.31.0]

### Added

- Added a concurrency primitive that proves independence, maps mutable state, bounds wave
  width, and reconciles results before integration.
- Added reference guidance for independence and isolation, dispatch and briefs, integration
  and failures, and upstream adaptation.
