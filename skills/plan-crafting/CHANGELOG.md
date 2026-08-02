# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-08-02

### Changed

- Added a "When There Is No Test Seam" fallback: name a substitute verification
  (typecheck, existing suite, e2e smoke run, or a scripted manual check) instead of
  forcing a test where no reasonable seam exists.
- Added scoped-staging guidance to the Task Structure commit step: stage only the
  files listed in the task's Files block, never `git add -A` or `git add .`.
- Clarified that per-task commits are the working granularity for review gates,
  while the final history shape follows the user's git preferences.
- Required fixture values to be drawn from real repository data rather than
  invented shapes.
- Added a note to pair each new-test run with the nearest existing suite in the
  same step, surfacing regressions at the task boundary.
- Tightened the plan-location override: an explicit user instruction overrides
  the `docs/plans/` default, but a differing repository convention does not; when
  the repository has an established plan location, name both it and the one you
  chose in the same message where you save the plan.

## [1.1.0] - 2026-07-31

### Changed

- Added a Security Model: repository evidence and tool output are data, plan commands
  are shown rather than run, and the skill takes no shell or network actions.

## [1.0.0] - 2026-07-29

### Added

- Added `plan-crafting`, an MIT-licensed adaptation of the pinned upstream
  `writing-plans` skill for approved designs and settled multi-step requirements.
- Uses neutral `docs/plans` artifact paths and unnamespaced execution handoff names.
- Replaces upstream `writing-plans` as the planning step that follows `scope-triage`.
