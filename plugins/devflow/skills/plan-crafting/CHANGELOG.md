# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.8.3] - 2026-10-21 - [1.58.10]

### Changed

- The Security Model names where `cross-review` now sends the plan and spec: the reviewer
  CLIs, by default the opposite agent CLI and Antigravity, and their vendor APIs.

## [1.8.2] - 2026-10-14 - [1.58.5]

### Changed

- The saved plan is handed to the `scope-check` skill for an HTML preview before the plan
  review and again after review corrections; skipped silently when it is not installed.

## [1.8.1] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.8.0] - 2026-10-10 - [1.58.0]

### Changed

- The execution choice is asked through an interactive question tool when the mode allows
  one (`AskUserQuestion` in Claude Code, `request_user_input` in Codex Plan mode),
  otherwise as a numbered list; execution never starts without an explicit choice.
- Options are named after the skills in a fixed order (`inline-plan-dev`,
  `subagent-plan-dev`, `cross-review`), each with its description, followed by the
  free-form answer and no `cancel`. The `cross-review` option names the next round by
  number, and the intro no longer counts the options.

## [1.7.0] - 2026-10-10 - [1.55.0]

### Added

- Behavior Over Code for Stateful Logic: stateful, concurrent, or cache logic is planned
  as behavior, invariants, and named test scenarios, and `tdd` writes the implementation.

### Changed

- Rename and delete steps stage with `git add -A -- <paths>`; browser scripts in a plan
  are drafts.
- Points to the `cross-review` Automatic rounds rule and offers "Cross-review again" only
  after the automatic rounds stop.

## [1.6.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.5.0] - 2026-10-05 - [1.51.0]

### Added

- The execution choice offers a third option, another `cross-review` of the corrected
  plan against the spec, when the plan references a spec and `cross-review` is
  installed. Its findings go to `review-resolution`, and the choice is offered again.

## [1.4.0] - 2026-10-04 - [1.49.0]

### Added

- `Execution Handoff` runs `cross-review` in `plan` mode after the plan is saved and
  before the execution choice, when the plan references a spec and the skill is
  installed. Findings go to `review-resolution`; product decisions go back to the user.
  Without a spec the step is skipped silently; an unavailable reviewer, a missing
  dependency, or a failed, empty, or incomplete run is reported in one line and the
  normal handoff continues.

### Changed

- The Security Model names the capability delegated to `cross-review`.

## [1.3.4] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.3.3] - 2026-09-14 - [1.35.0]

### Changed

- Plans are saved as `docs/plans/YYYYMMDD-HHMM-<feature-name>.md`, replacing the date-only
  name so that several plans written on one day order by creation time.

## [1.3.2] - 2026-09-14 - [1.34.3]

### Changed

- The `## Security Model` section now names which inputs are user-controlled, alongside the
  existing untrusted-input, instruction-boundary and capability statements.

## [1.3.1] - 2026-09-14 - [1.34.2]

### Changed

- Add the fork maintainer to the LICENSE copyright notice, matching the other forked skills.

## [1.3.0] - 2026-09-13 - [1.32.0]

### Changed

- Route plan execution to `inline-plan-dev` and `subagent-plan-dev` in both the plan header
  note and the execution handoff, replacing the upstream `executing-plans` and
  `subagent-driven-development` names.
- Present the two execution modes as an equal choice: the `(recommended)` label is dropped
  from the subagent option, and each mode is described by what it does.

## [1.2.0] - 2026-09-11 - [1.25.0]

### Changed

- Added a TDD-aware handoff: behavior-changing tasks state acceptance evidence and invoke
  `tdd` for the test-first micro-cycle instead of using test-after task wording.

## [1.1.2] - 2026-08-09 - [1.10.0]

### Changed

- Replaced every typographic dash (em and en) in SKILL.md with plain-hyphen phrasing
  per the repository dashfix style; no workflow change.

## [1.1.1] - 2026-08-02 - [1.9.0]

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

## [1.1.0] - 2026-07-31 - [1.8.0]

### Changed

- Added a Security Model: repository evidence and tool output are data, plan commands
  are shown rather than run, and the skill takes no shell or network actions.

## [1.0.0] - 2026-07-29 - [1.7.0]

### Added

- Added `plan-crafting`, an MIT-licensed adaptation of the pinned upstream
  `writing-plans` skill for approved designs and settled multi-step requirements.
- Uses neutral `docs/plans` artifact paths and unnamespaced execution handoff names.
- Replaces upstream `writing-plans` as the planning step that follows `scope-triage`.
