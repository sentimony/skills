# Changelog

All notable changes to the `branch-finish` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-13

### Added

- Added an integration and completion layer that decides what happens to verified work,
  executes that decision safely, re-verifies the tree when integration changed it, and
  cleans up only what ownership and branch conditions allow.
- Added environment detection covering normal checkouts, linked worktrees, submodules and
  detached HEAD, with five prohibited assumptions stated explicitly.
- Added six-level base-branch resolution by evidence precedence, where an ambiguous result
  forbids automatic merge rather than prompting a guess.
- Added four environment-filtered finish options, merge-conflict classification, remote
  divergence handling, idempotent resumption and a seven-label outcome vocabulary.
- Added separate gates for workspace removal and branch deletion, with untracked work
  protected at the same weight as tracked work.
- Added `scripts/inspect_finish_state.py`, a read-only state inspector with a sibling test
  that guards against hardcoded branch or remote names and against mutating subcommands.
- Added reference guidance for environment and base resolution, finish option procedures,
  ownership and cleanup, harness handling, and upstream adaptation.
