# Changelog

All notable changes to the `branch-finish` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-09-13

### Changed

- The `BRANCH PRESERVED` and `WORK HANDED OFF` report templates now show `Verification:
  <verdict>` instead of a literal `PASS`. Neither outcome requires a passing verdict: `KEEP`
  preserves a branch whatever its state, and a detached-HEAD handoff reports commits at risk,
  so the templates were instructing a verdict that may not exist.
- The `MERGE_BASE` precedence level now states that it answers only when exactly one other
  branch is a candidate, in both `SKILL.md` and `references/environment-and-base.md`. The
  previous wording, "the nearest common ancestor among candidates", invited ranking several
  candidates by distance, which `scripts/inspect_finish_state.py` deliberately does not do.

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
