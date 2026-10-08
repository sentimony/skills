# Changelog

All notable changes to the `git-worktree-isolation` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
entries are headed by date; older ones keep the skill version they shipped in.

## 2026-10-09

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.2.2] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.2.1] - 2026-09-15

### Fixed

- `inspect_workspace()` canonicalizes `workspace_root` for library callers that pass an
  unresolved path, so it matches `repo_root`, `git_dir` and the other already-canonical
  path fields. CLI output is unchanged: `--path` is resolved before the call.
- Dropped a `git rev-parse --is-inside-work-tree` call whose result was never used.
- The helper is described as available rather than forthcoming.

## [1.2.0] - 2026-09-14

### Changed

- Renamed from `worktree-isolation`. The name now says which mechanism the workflow reaches
  for most often; the selection hierarchy is unchanged, and reusing existing isolation, a
  harness-native workspace and safe work in place all remain valid outcomes

## [1.1.0] - 2026-09-14

### Changed

- Renamed from `workspace-isolation`. The skill keeps its full scope: a Git worktree is the
  mechanism it reaches for most often, while existing isolated checkouts, harness-native
  workspaces, containers and safe work in place remain equally valid outcomes

## [1.0.1] - 2026-09-14

### Changed

- Documented a Security Model section defining trusted and untrusted inputs, the instruction
  boundary for discovered text, and the bounds on this skill's detection, creation, setup, and
  baseline capabilities.

## [1.0.0] - 2026-09-13

### Added

- Added a safety-first workspace decision workflow with detection, provenance, baseline, and
  handoff contracts.
- Added reference guidance for Git detection, manual worktree fallback, safety boundaries, and
  upstream adaptation.
