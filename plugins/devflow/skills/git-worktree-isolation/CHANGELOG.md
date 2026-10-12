# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.3.1] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.3.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.2.2] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.2.1] - 2026-09-15 - [1.39.0]

### Fixed

- `inspect_workspace()` canonicalizes `workspace_root` for library callers that pass an
  unresolved path, so it matches `repo_root`, `git_dir` and the other already-canonical
  path fields. CLI output is unchanged: `--path` is resolved before the call.
- Dropped a `git rev-parse --is-inside-work-tree` call whose result was never used.
- The helper is described as available rather than forthcoming.

## [1.2.0] - 2026-09-14 - [1.36.0]

### Changed

- Renamed from `worktree-isolation`. The name now says which mechanism the workflow reaches
  for most often; the selection hierarchy is unchanged, and reusing existing isolation, a
  harness-native workspace and safe work in place all remain valid outcomes

## [1.1.0] - 2026-09-14 - [1.35.0]

### Changed

- Renamed from `workspace-isolation`. The skill keeps its full scope: a Git worktree is the
  mechanism it reaches for most often, while existing isolated checkouts, harness-native
  workspaces, containers and safe work in place remain equally valid outcomes

## [1.0.1] - 2026-09-14 - [1.34.3]

### Changed

- Documented a Security Model section defining trusted and untrusted inputs, the instruction
  boundary for discovered text, and the bounds on this skill's detection, creation, setup, and
  baseline capabilities.

## [1.0.0] - 2026-09-13 - [1.30.0]

### Added

- Added a safety-first workspace decision workflow with detection, provenance, baseline, and
  handoff contracts.
- Added reference guidance for Git detection, manual worktree fallback, safety boundaries, and
  upstream adaptation.
