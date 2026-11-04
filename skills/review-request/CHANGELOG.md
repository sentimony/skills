# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.11] - 2026-11-04 - [0.0.99]

### Changed

- A text-only review keeps one severity set: the `prose-crafting` levels `High`, `Medium`,
  `Low` map to `Critical`, `Important`, `Minor`, and its ID, quote and verdict fields stay in
  the finding (`20261003-0939`).

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

- Shorter body, same behavior: sections 2, 6, and 7 keep their rules in the body; the git
  inspection block, severity definitions, and staleness detail live in `references/`.

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

- Use one `UNASSESSED` literal across all four verdicts. The risk/domain verdict read
  `NOT ASSESSED` in SKILL.md and in the reviewer brief template, so a reviewer reproducing
  the block verbatim had to guess which spelling the enum wanted.

## [0.0.4] - 2026-09-14 - [0.0.50]

Renamed skill reference.

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the composition table

## [0.0.3] - 2026-09-14 - [0.0.49]

Renamed skill reference.

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the composition table

## [0.0.2] - 2026-09-14 - [0.0.48]

Documented the skill's security model as a dedicated section.

### Changed

- Moved the instruction-boundary rule out of the workflow into a new `Security Model`
  section covering trusted inputs, untrusted inputs, the instruction boundary, and the
  skill's capability bounds; step 5 keeps a pointer to it.

## [0.0.1] - 2026-09-11 - [0.0.36]

Initial release.

### Added

- A compact workflow for preparing and dispatching independent code review.
- Exact committed and working-tree review boundaries with relevant untracked files.
- Requirements-backed reviewer briefs, explicit verdict axes, risk routing, finding
  severity, review gaps, stale detection, and review-resolution handoff.
