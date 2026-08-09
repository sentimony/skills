# Changelog

All notable changes to the `dashfix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.0] - 2026-08-09

Initial release.

### Added
- Write mode: bans em dashes, en dashes, and the other Unicode dash code points
  (U+2010-U+2015, U+2212) in all produced text, with restructure-first replacement
  rules instead of blind character substitution
- Audit mode: ripgrep inventory over the dash code points, a per-occurrence catalog
  with `justified` / `replace` verdicts and reasons, and four named justification
  categories (quotation, proper name, test fixture, documented typography rule)
- Deterministic 0-100 score (`max(0, 100 - sum of per-file penalties)`, per-file
  penalty capped at 20) with four score bands
- Fix mode gated behind an explicit request and an existing audit, reporting the new
  score next to the old one
- Security Model: scanned content is data, not instructions; audit is read-only and
  offline
