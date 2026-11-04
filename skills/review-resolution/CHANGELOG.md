# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.13] - 2026-11-04 - [0.0.98]

### Changed

1. The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.12] - 2026-10-31 - [0.0.96]

### Fixed

1. Pin the three local responsibility-boundary links in `references/attribution.md`
   to commit `61919613972e63f2c833c1c5ad4744d7c40ad05a` so they retain their source
   paths after a repository layout change.

## [0.0.11] - 2026-10-27 - [0.0.95]

### Fixed

- `references/attribution.md`: the links to `review-request`, `debugging`, and `tdd` point
  at `plugins/skills/skills/` instead of the `devflow` plugin path removed in 0.0.94. The
  skill instructions are unchanged.

## [0.0.10] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.9] - 2026-10-10 - [0.0.77]

### Changed

- Moved to the `devflow` plugin; attribution links follow the new path.

## [0.0.8] - 2026-10-10 - [0.0.76]

### Changed

- Shorter body, same behavior: steps 2, 4, and 7-10 keep their rules in the body;
  disposition meanings, special relationships, evidence, the re-review matrix, and the
  summary template live in `references/`.

## [0.0.7] - 2026-10-10 - [0.0.75]

### Added

- A mechanism counter: two consecutive rounds with new findings against the same stateful
  or concurrent design escalate to `scope-triage` with a proposal to simplify.
- A "Plan/spec findings" subsection lists the evidence accepted when the target is a
  document: a throwaway reproduction, evidence deferred to a named plan step, or a scoped
  re-review.

### Changed

- Points to the `cross-review` Automatic rounds rule when another round is needed.

## [0.0.6] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.5] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.4] - 2026-09-14 - [0.0.50]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [0.0.3] - 2026-09-14 - [0.0.49]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [0.0.2] - 2026-09-14 - [0.0.48]

### Changed

- Renamed the security section to `Security Model` and completed it with trusted inputs and
  a capability statement covering read-only Git inspection, no network calls, and edits
  bounded to accepted findings.

## [0.0.1] - 2026-09-12 - [0.0.37]

### Added

- A compact workflow for validating, classifying, and resolving code-review findings.
- Separate assessment, reviewer severity, actual impact, priority, and disposition models.
- Stale, duplicate, contradictory, load-bearing, security, test-quality, and scope handling.
- Finding-level evidence, change-impact checks, proportional re-review, and bounded loop rules.
- Composition boundaries for review-request, verification-gate, debugging, tdd, UI, testing,
  planning, execution, workspace, parallel-agent, and branch lifecycle skills.
