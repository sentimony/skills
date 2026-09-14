# Changelog

All notable changes to the `git-worktree-isolation` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
