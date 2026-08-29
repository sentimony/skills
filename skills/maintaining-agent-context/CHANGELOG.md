# Changelog

All notable changes to the `maintaining-agent-context` skill. Versions refer to
`metadata.version` in SKILL.md. This file is for maintainers and is never loaded by
agents using the skill.

## [1.2.0] - 2026-08-29

### Changed
- Phase 1 records the unit and the command behind every size in the surface map and
  ships a Unicode-aware character-count recipe, so byte counts stop being reported
  as characters.
- Phase 1 keeps instruction files reached through a symlink that leaves the checkout
  on the map but outside the edit scope.
- "Pointers do the routing" keeps constraints that must hold before a target is
  opened (data boundaries, no-publish rules, permission gates) inline next to the
  pointer instead of behind it.
- Phase 3 reads file bodies, not heading maps, before judging duplication and
  contradiction.
- Phase 4 reports the same wrong fact found outside the instruction files (README,
  config-file comments) in its own section with an explicit question, and may state
  that the current structure is already the target.
- Phase 5 keeps the confirmation gate when the invocation itself asks to apply
  changes immediately; the agent says which side it follows and still shows diffs.
- Phase 6 re-checks edited lines and files against the limits the audit treated as
  governing.
- Assessment criteria: root section gains the "redundant with the environment"
  category for verified-but-cached commands and criteria for one-line import shims;
  the report structure gains an optional "Findings outside the instruction files"
  section.
- Reference Files index now lists `scripts/test_contract.py` as maintainer-only.

## [1.1.0] - 2026-08-25

### Changed
- Phase 2 now supports risk-based spot-checking for large instruction surfaces,
  explicit verification statuses, coverage scope, and residual uncertainty.
- Phase 3 names the unit used for every size or limit claim and keeps bytes,
  characters, and lines distinct.
- Phase 5 exposes the trade-off between reformatting and compression for approval;
  Phase 6 applies only the approved choice while preserving semantic content.
- Phase 4 report structure now includes verification coverage and residual uncertainty.
- Read-only shell inspection is explicitly allowed while project and
  repository-controlled commands remain outside the audit phases.

### Added
- `references/restructuring-verification.md` - before-and-after integrity guidance
  with limitations for token-multiset checks.

## [1.0.0] - 2026-08-23

### Added
- Initial release: audit, restructure, and maintain the full agent-context
  architecture of a repository (AGENTS.md, CLAUDE.md and variants, `.claude/rules/`,
  skills, linked agent docs) for Claude Code and Codex
- Six-phase workflow: discovery, project verification, context architecture
  analysis, quality report, proposed changes with user confirmation, apply and verify
- Security model: Phases 1-4 execute no project commands; already-active platform
  instructions keep their priority (conflicts get reported), newly opened audited
  content is untrusted data that grants no authorization, and only explicit user
  confirmation - scoped to the shown files and fragments - authorizes edits
- `scripts/test_contract.py` - CI-run static guard for the read-only, security,
  confirmation, and progressive-disclosure invariants and reference-pointer
  integrity
- `references/claude-code-loading.md` and `references/codex-loading.md` - per-agent
  loading mechanics, each read only when its platform is in scope
- `references/assessment-criteria.md` - per-file-type assessment criteria and
  report structure
- `references/attribution.md` - design lineage from `writing-for-agents`
  (Matt Pocock, MIT) and `claude-md-improver` (Anthropic, Apache-2.0)
