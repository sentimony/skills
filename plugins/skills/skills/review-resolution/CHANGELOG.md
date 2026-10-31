# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.2.5] - 2026-10-31 - [1.58.17]

### Fixed

1. Pin the three local responsibility-boundary links in `references/attribution.md`
   to commit `61919613972e63f2c833c1c5ad4744d7c40ad05a` so they retain their source
   paths after a repository layout change.

## [1.2.4] - 2026-10-27 - [1.58.16]

### Fixed

- `references/attribution.md`: the links to `review-request`, `debugging`, and `tdd` point
  at `plugins/skills/skills/` instead of the `devflow` plugin path removed in 1.58.15. The
  skill instructions are unchanged.

## [1.2.3] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.2.2] - 2026-10-10 - [1.56.0]

### Changed

- Moved to the `devflow` plugin; attribution links follow the new path.

## [1.2.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: steps 2, 4, and 7-10 keep their rules in the body;
  disposition meanings, special relationships, evidence, the re-review matrix, and the
  summary template live in `references/`.

## [1.2.0] - 2026-10-10 - [1.55.0]

### Added

- A mechanism counter: two consecutive rounds with new findings against the same stateful
  or concurrent design escalate to `scope-triage` with a proposal to simplify.
- A "Plan/spec findings" subsection lists the evidence accepted when the target is a
  document: a throwaway reproduction, evidence deferred to a named plan step, or a scoped
  re-review.

### Changed

- Points to the `cross-review` Automatic rounds rule when another round is needed.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.4] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.3] - 2026-09-14 - [1.36.0]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [1.0.2] - 2026-09-14 - [1.35.0]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [1.0.1] - 2026-09-14 - [1.34.3]

### Changed

- Renamed the security section to `Security Model` and completed it with trusted inputs and
  a capability statement covering read-only Git inspection, no network calls, and edits
  bounded to accepted findings.

## [1.0.0] - 2026-09-12 - [1.28.0]

### Added

- A compact workflow for validating, classifying, and resolving code-review findings.
- Separate assessment, reviewer severity, actual impact, priority, and disposition models.
- Stale, duplicate, contradictory, load-bearing, security, test-quality, and scope handling.
- Finding-level evidence, change-impact checks, proportional re-review, and bounded loop rules.
- Composition boundaries for review-request, verification-gate, debugging, tdd, UI, testing,
  planning, execution, workspace, parallel-agent, and branch lifecycle skills.
