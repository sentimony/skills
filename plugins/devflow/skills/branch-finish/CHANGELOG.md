# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.4] - 2026-10-12 - [1.58.4]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

### Fixed

- `scripts/inspect_finish_state.py` resolves merge, rebase, cherry-pick, and revert state
  only in the repository given by `--path`. It also checked the Git path against the
  caller's working directory, so a merge in progress there was reported for a clean
  target repository.

## [1.1.3] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.1.2] - 2026-10-10 - [1.56.0]

### Changed

- Moved to the `devflow` plugin; attribution links follow the new path.

## [1.1.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: the body routes to its references; environment detection,
  base-branch precedence, finish options, ownership and cleanup detail, and the report
  templates live in `references/`.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.6] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.5] - 2026-09-15 - [1.39.0]

### Fixed

- `CLEANUP INCOMPLETE` is no longer listed among the outcome labels. It is a separate
  cleanup status on its own `Cleanup:` line, which is how the report example and the
  refused-removal rule already used it; only the list disagreed.

## [1.0.4] - 2026-09-14 - [1.36.0]

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation` in the workflow, three
  references and the provenance docstring of `scripts/inspect_finish_state.py`.

## [1.0.3] - 2026-09-14 - [1.35.0]

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation` in the workflow, three
  references and the provenance docstring of `scripts/inspect_finish_state.py`.

## [1.0.2] - 2026-09-14 - [1.34.3]

### Changed

- The `Security model` section is now `Security Model` and states all four components in order.
  It previously covered only untrusted inputs and the instruction boundary, leaving the trusted
  inputs and the capability statement implicit: the skill holds push, merge, and delete
  authority, so what authorizes a remote mutation and which commands it runs are now named
  rather than inferred.

## [1.0.1] - 2026-09-13 - [1.34.1]

### Changed

- The `BRANCH PRESERVED` and `WORK HANDED OFF` report templates now show `Verification:
  <verdict>` instead of a literal `PASS`. Neither outcome requires a passing verdict: `KEEP`
  preserves a branch whatever its state, and a detached-HEAD handoff reports commits at risk,
  so the templates were instructing a verdict that may not exist.
- The `MERGE_BASE` precedence level now states that it answers only when exactly one other
  branch is a candidate, in both `SKILL.md` and `references/environment-and-base.md`. The
  previous wording, "the nearest common ancestor among candidates", invited ranking several
  candidates by distance, which `scripts/inspect_finish_state.py` deliberately does not do.

## [1.0.0] - 2026-09-13 - [1.33.0]

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
