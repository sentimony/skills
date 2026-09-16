# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-09-15

### Fixed

- The trigger-boundary row of the evidence matrix now requires at least one
  should-not-trigger case in prose, and points to `references/evaluation.md`, section
  "5. Trigger boundary". The concept existed only as a table cell that required nothing;
  4 of 4 answers failed that expectation in both arms of eval-4. The reference prose and
  the negative-case quota are unchanged.

## [1.1.0] - 2026-09-15

### Added

- Portable eval contract, fresh-sandbox runner, and deterministic aggregator.
- Runtime-neutral repository adapters and package-owned evaluation execution.

## [1.0.0] - 2026-09-14

### Added

- Initial release of the skill-crafting methodology for creating, improving, evaluating, and
  optimizing agent skills.
- Category and verification-tier selection, failure-driven guidance, trigger boundaries,
  runtime-neutral evaluation, and completion evidence guidance.
