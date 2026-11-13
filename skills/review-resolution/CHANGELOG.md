# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.19] - 2026-11-13 - [0.0.110]

### Changed

- Flat layout: reference files moved next to SKILL.md; no content change.

## [0.0.18] - 2026-11-13 - [0.0.109]

### Changed

- Step 0 and the Security Model allow one read-only `gh api` or `gh pr view` fetch of the review source when the argument is a PR, issue, or comment URL. The text stays untrusted evidence; no writes and no other network calls (`20261018-1123`, item 1; decided by the agent at tier ultra, following the request's recommendation, since the URL-argument call is the main use and the old no-network rule contradicted it).

## [0.0.17] - 2026-11-13 - [0.0.105]

### Changed

- Description rewritten as a thesis plus "Use when ..." without "You MUST", at a lower token cost; triggers unchanged.

## [0.0.16] - 2026-11-07 - [0.0.102]

### Changed

- Route to `plan-execution` (was `inline-plan-dev`), `plan-orchestration` (was `subagent-plan-dev`), renamed in 0.0.102.
- Route workspace isolation to `worktree-isolation`, the new name of `git-worktree-isolation`.

## [0.0.15] - 2026-11-07 - [0.0.101]

### Changed

1. The target-identity list records the review and capture times as informational only; the
  revision and fingerprints decide identity, and a missing identity field stays a review gap
  (`20260915-1939`, item 2).

## [0.0.14] - 2026-11-04 - [0.0.99]

### Changed

1. Step 0 gets a repeated-call rule: when `updated_at`, the reviewed-SHA marker, and the
  tree are unchanged, show the standing decision table and pending steps without new
  edits; a new comment or SHA starts a new round (`20261018-1123`, item 2).
2. The orchestrator-state example names the `subagent-plan-dev` state under `~/.sentimony`
  instead of `.sdd/`.

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
