# Changelog

All notable changes to the `workspace-isolation` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
