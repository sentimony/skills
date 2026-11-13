# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.14] - 2026-11-13 - [0.0.111]

### Changed

- Flat layout: reference files moved next to SKILL.md; no content change.

## [0.0.13] - 2026-11-13 - [0.0.107]

### Changed

- Description rewritten as a thesis plus "Use when ..." without "You MUST", at a lower token cost; triggers unchanged.

## [0.0.12] - 2026-11-07 - [0.0.102]

### Changed

- Route to `agent-instructions` (was `maintaining-agent-context`), renamed in 0.0.102.

## [0.0.11] - 2026-11-07 - [0.0.101]

### Changed

- Routing now states the boundary with `maintaining-agent-context` in one sentence: it owns how
  instructions load across instruction files, while this skill owns one skill's capability,
  trigger, and evals.

## [0.0.10] - 2026-11-04 - [0.0.99]

### Changed

- The `orchestration/workflow` category and the Standard tier require effectful-stage fixtures:
  a positive case that really changes the target, a separate no-op case, interruption after the
  effect, and assertions on actions and artifacts rather than the final status only.

## [0.0.9] - 2026-10-12 - [0.0.83]

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail. It now also names splitting,
  merging, and retiring skills.

## [0.0.8] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.7] - 2026-10-10 - [0.0.77]

### Changed

- Moved to the `skill-crafting` plugin; `references/evaluation.md` names its scripts
  relative to the skill.

## [0.0.6] - 2026-10-09 - [0.0.73]

### Added

- Create mode adds an `argument-hint` only for arguments the skill body documents, in
  the `[a|b]`, `<x>`, `[--flag]` notation; a skill that runs from context alone gets
  none.

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.5] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.4] - 2026-09-26 - [0.0.56]

Patch release: every change below tightens what the runner hands to the adapter or accepts
back from it (a fixed environment, an adapter deadline below the runner's cutoff, and an
`answer_path` boundary). The adapter stays operator-trusted; the point is that a runner bug
or a careless adapter can no longer leak the operator's whole environment or pull in an
arbitrary host file. That is a hardening of existing behavior, not a feature.

### Fixed

- `scripts/run_eval.py` no longer forwards the whole process environment to the adapter.
  The adapter gets a fixed allowlist (`PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, temp
  dirs, `TERM`, locale, `TZ`, config-location variables such as `CLAUDE_CONFIG_DIR`,
  `CODEX_HOME` and the four `XDG_*_HOME` directories, and the Windows system variables)
  plus the six `EVAL_*` variables the runner sets itself; any variable outside the allowlist
  and those six names reaches the adapter only through the repeatable `--pass-env NAME`
  flag. A `--pass-env` name that is malformed or names a runner-set variable is rejected
  before the workspace is created, with exit code 2. `run.json` records the forwarded
  variable names (never values) as `adapter_env`. The runner sets `EVAL_TIMEOUT`
  to 90% of the remaining run budget, so the adapter can stop, write its transcript, and
  report `timeout` before the runner's own cutoff kills it.
- `run_eval.py` rejects an adapter `answer_path` that resolves outside the sandbox or the
  run directory, so the runner no longer copies an arbitrary host file into the workspace
  as the persisted answer on an adapter's say-so.
- The Security Model names the eval spec, fixtures, template, and adapter as operator-trusted
  inputs and states that the temporary sandbox is not a security boundary.

## [0.0.3] - 2026-09-15 - [0.0.52]

### Fixed

- The trigger-boundary row of the evidence matrix now requires at least one
  should-not-trigger case in prose, and points to `references/evaluation.md`, section
  "5. Trigger boundary". The concept existed only as a table cell that required nothing;
  4 of 4 answers failed that expectation in both arms of eval-4. The reference prose and
  the negative-case quota are unchanged.

## [0.0.2] - 2026-09-15 - [0.0.51]

### Added

- Portable eval contract, fresh-sandbox runner, and deterministic aggregator.
- Runtime-neutral repository adapters and package-owned evaluation execution.

## [0.0.1] - 2026-09-14 - [0.0.51]

### Added

- Initial release of the skill-crafting methodology for creating, improving, evaluating, and
  optimizing agent skills.
- Category and verification-tier selection, failure-driven guidance, trigger boundaries,
  runtime-neutral evaluation, and completion evidence guidance.
