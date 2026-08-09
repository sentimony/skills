# Changelog

All notable changes to the `negafix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.0] - 2026-08-09

Initial release.

### Added
- Write mode: bans negative parallelism (the "it's not just X, it's Y" construction)
  in all produced text, with rewrite recipes that keep the factual content and drop
  the inflating negation; plain factual negation stays allowed
- Audit mode: ripgrep inventory over English and Ukrainian trigger patterns, a
  per-match catalog with `violation` / `plain negation` / `justified contrast` /
  `quotation` verdicts and reasons
- Deterministic 0-100 score (`max(0, 100 - sum of per-file penalties)`, per-file
  penalty capped at 20, 4 points per violation) with four score bands
- Fix mode gated behind an explicit request and an existing audit, reporting the new
  score next to the old one
- Security Model: scanned content is data, not instructions; audit is read-only and
  offline
