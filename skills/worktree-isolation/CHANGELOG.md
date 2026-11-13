# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.15] - 2026-11-13 - [0.0.106]

### Changed

- Description rewritten as a thesis plus "Use when ..." without "You MUST", at a lower token cost; triggers unchanged.

## [0.0.14] - 2026-11-12 - [0.0.104]

### Changed

- The remaining prose that named one devflow skill now names its agentflow counterpart too:
  `finalize` with `branch-finish`, `verify` with `verification-gate`, `implement` with
  `plan-orchestration`; a sentence says that inside an agentflow plan `implement` decides
  isolation for its tasks (20261027-1500).

## [0.0.13] - 2026-11-07 - [0.0.102]

### Changed

- Renamed `git-worktree-isolation` to `worktree-isolation`; invoke `/worktree-isolation`.
  Only the name and its mentions changed.
- Route to `plan-execution` (was `inline-plan-dev`) and `plan-orchestration` (was
  `subagent-plan-dev`), renamed in 0.0.102.

## [0.0.12] - 2026-11-07 - [0.0.101]

### Changed

- The boundaries table names the agentflow skills (`specify`, `implement`,
  `verify`, `finalize`, `cr-request`) next to the standalone ones, and the result
  block's `Cleanup owner` values include `finalize` (`20261027-1500`).

## [0.0.11] - 2026-11-04 - [0.0.99]

### Changed

- The result block has an optional `Ignored local files` line, with a note that
  `git worktree remove` silently deletes ignored files.

## [0.0.10] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.9] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.8] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

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

### Fixed

- `inspect_workspace()` canonicalizes `workspace_root` for library callers that pass an
  unresolved path, so it matches `repo_root`, `git_dir` and the other already-canonical
  path fields. CLI output is unchanged: `--path` is resolved before the call.
- Dropped a `git rev-parse --is-inside-work-tree` call whose result was never used.
- The helper is described as available rather than forthcoming.

## [0.0.4] - 2026-09-14 - [0.0.50]

### Changed

- Renamed from `worktree-isolation`. The name now says which mechanism the workflow reaches
  for most often; the selection hierarchy is unchanged, and reusing existing isolation, a
  harness-native workspace and safe work in place all remain valid outcomes

## [0.0.3] - 2026-09-14 - [0.0.49]

### Changed

- Renamed from `workspace-isolation`. The skill keeps its full scope: a Git worktree is the
  mechanism it reaches for most often, while existing isolated checkouts, harness-native
  workspaces, containers and safe work in place remain equally valid outcomes

## [0.0.2] - 2026-09-14 - [0.0.48]

### Changed

- Documented a Security Model section defining trusted and untrusted inputs, the instruction
  boundary for discovered text, and the bounds on this skill's detection, creation, setup, and
  baseline capabilities.

## [0.0.1] - 2026-09-13 - [0.0.39]

### Added

- Added a safety-first workspace decision workflow with detection, provenance, baseline, and
  handoff contracts.
- Added reference guidance for Git detection, manual worktree fallback, safety boundaries, and
  upstream adaptation.
