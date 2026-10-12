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

- Shorter body, same behavior: sections 2, 6, and 7 keep their rules in the body; the git
  inspection block, severity definitions, and staleness detail live in `references/`.

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

- Use one `UNASSESSED` literal across all four verdicts. The risk/domain verdict read
  `NOT ASSESSED` in SKILL.md and in the reviewer brief template, so a reviewer reproducing
  the block verbatim had to guess which spelling the enum wanted.

## [1.0.3] - 2026-09-14 - [1.36.0]

Renamed skill reference.

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the composition table

## [1.0.2] - 2026-09-14 - [1.35.0]

Renamed skill reference.

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the composition table

## [1.0.1] - 2026-09-14 - [1.34.3]

Documented the skill's security model as a dedicated section.

### Changed

- Moved the instruction-boundary rule out of the workflow into a new `Security Model`
  section covering trusted inputs, untrusted inputs, the instruction boundary, and the
  skill's capability bounds; step 5 keeps a pointer to it.

## [1.0.0] - 2026-09-11 - [1.27.0]

Initial release.

### Added

- A compact workflow for preparing and dispatching independent code review.
- Exact committed and working-tree review boundaries with relevant untracked files.
- Requirements-backed reviewer briefs, explicit verdict axes, risk routing, finding
  severity, review gaps, stale detection, and review-resolution handoff.
