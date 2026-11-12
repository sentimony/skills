# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.25] - 2026-11-12 - [0.0.104]

### Changed

- New plans are saved as `docs/plans/YYMMDDTHHMM-<feature-name>.md`: local time from
  `date +%y%m%dT%H%M`, a kebab-case name of at most 24 characters, no overwrite of an
  existing file; files in the `YYYYMMDD-HHMM` format keep their names (20261112-0305).

## [0.0.24] - 2026-11-07 - [0.0.102]

### Changed

- Route to `plan-execution` (was `inline-plan-dev`), `plan-orchestration` (was `subagent-plan-dev`), renamed in 0.0.102.
- Preview handoff names `doc-preview`, the new name of `scope-check`.

## [0.0.23] - 2026-11-07 - [0.0.101]

### Changed

1. Make the task-level commit in the plan blueprint a conditional checkpoint, added only when the active Git workflow and the user permit commits (`20260915-1939`).
2. Preview handoff names `scope-check` again; `doc-preview` is removed in 0.0.101.

## [0.0.22] - 2026-11-05 - [0.0.100]

### Changed

1. Refresh localized plan conclusions and state-aware next-step prompts, and preview each saved or edited plan with `doc-preview`.
2. Validate approval provenance and keep prompts aligned with review and execution state.

## [0.0.21] - 2026-11-04 - [0.0.99]

### Changed

- Expected output that follows from a formatting rule is computed by script or by running existing code, marked `computed by script` with the reproduction command; what could not be computed is marked `verify during execution` (`20261024-2246`).

## [0.0.20] - 2026-11-04 - [0.0.98]

### Changed

1. Rewrote the skill text to remove material inherited from the upstream skill.
2. LICENSE now names one copyright holder: a word-run comparison with the fork base found no shared run of six or more words.

## [0.0.19] - 2026-11-04 - [0.0.98]

### Changed

- `20261024-2327`: the execution choice after a saved plan is always a numbered list in
  the reply text, never an interactive question tool (`AskUserQuestion`,
  `request_user_input`): the user may switch agent or compact the context at that moment.
  Execution still never starts without an explicit choice. The other proposals of the
  request (a Codex handoff option, `/compact` option) are not part of this change.

## [0.0.18] - 2026-10-21 - [0.0.89]

### Changed

- The Security Model names where `cross-review` now sends the plan and spec: the reviewer
  CLIs, by default the opposite agent CLI and Antigravity, and their vendor APIs.

## [0.0.17] - 2026-10-14 - [0.0.84]

### Changed

- The saved plan is handed to the `scope-check` skill for an HTML preview before the plan
  review and again after review corrections; skipped silently when it is not installed.

## [0.0.16] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.15] - 2026-10-10 - [0.0.79]

### Changed

- The execution choice is asked through an interactive question tool when the mode allows
  one (`AskUserQuestion` in Claude Code, `request_user_input` in Codex Plan mode),
  otherwise as a numbered list; execution never starts without an explicit choice.
- Options are named after the skills in a fixed order (`inline-plan-dev`,
  `subagent-plan-dev`, `cross-review`), each with its description, followed by the
  free-form answer and no `cancel`. The `cross-review` option names the next round by
  number, and the intro no longer counts the options.

## [0.0.14] - 2026-10-10 - [0.0.75]

### Added

- Behavior Over Code for Stateful Logic: stateful, concurrent, or cache logic is planned
  as behavior, invariants, and named test scenarios, and `tdd` writes the implementation.

### Changed

- Rename and delete steps stage with `git add -A -- <paths>`; browser scripts in a plan
  are drafts.
- Points to the `cross-review` Automatic rounds rule and offers "Cross-review again" only
  after the automatic rounds stop.

## [0.0.13] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.12] - 2026-10-05 - [0.0.68]

### Added

- The execution choice offers a third option, another `cross-review` of the corrected
  plan against the spec, when the plan references a spec and `cross-review` is
  installed. Its findings go to `review-resolution`, and the choice is offered again.

## [0.0.11] - 2026-10-04 - [0.0.65]

### Added

- `Execution Handoff` runs `cross-review` in `plan` mode after the plan is saved and
  before the execution choice, when the plan references a spec and the skill is
  installed. Findings go to `review-resolution`; product decisions go back to the user.
  Without a spec the step is skipped silently; an unavailable reviewer, a missing
  dependency, or a failed, empty, or incomplete run is reported in one line and the
  normal handoff continues.

### Changed

- The Security Model names the capability delegated to `cross-review`.

## [0.0.10] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.9] - 2026-09-14 - [0.0.49]

### Changed

- Plans are saved as `docs/plans/YYYYMMDD-HHMM-<feature-name>.md`, replacing the date-only
  name so that several plans written on one day order by creation time.

## [0.0.8] - 2026-09-14 - [0.0.48]

### Changed

- The `## Security Model` section now names which inputs are user-controlled, alongside the
  existing untrusted-input, instruction-boundary and capability statements.

## [0.0.7] - 2026-09-14 - [0.0.47]

### Changed

- Add the fork maintainer to the LICENSE copyright notice, matching the other forked skills.

## [0.0.6] - 2026-09-13 - [0.0.42]

### Changed

- Route plan execution to `inline-plan-dev` and `subagent-plan-dev` in both the plan header
  note and the execution handoff, replacing the upstream `executing-plans` and
  `subagent-driven-development` names.
- Present the two execution modes as an equal choice: the `(recommended)` label is dropped
  from the subagent option, and each mode is described by what it does.

## [0.0.5] - 2026-09-11 - [0.0.34]

### Changed

- Added a TDD-aware handoff: behavior-changing tasks state acceptance evidence and invoke
  `tdd` for the test-first micro-cycle instead of using test-after task wording.

## [0.0.4] - 2026-08-09 - [0.0.17]

### Changed

- Replaced every typographic dash (em and en) in SKILL.md with plain-hyphen phrasing
  per the repository dashfix style; no workflow change.

## [0.0.3] - 2026-08-02 - [0.0.15]

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

## [0.0.2] - 2026-07-31 - [0.0.14]

### Changed

- Added a Security Model: repository evidence and tool output are data, plan commands
  are shown rather than run, and the skill takes no shell or network actions.

## [0.0.1] - 2026-07-29 - [0.0.13]

### Added

- Added `plan-crafting`, an MIT-licensed adaptation of the pinned upstream
  `writing-plans` skill for approved designs and settled multi-step requirements.
- Uses neutral `docs/plans` artifact paths and unnamespaced execution handoff names.
- Replaces upstream `writing-plans` as the planning step that follows `scope-triage`.
