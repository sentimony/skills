# Changelog

All notable changes to the `negafix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.1.0] - 2026-08-10

Carries the `dashfix` 1.1.0 feedback fixes that apply to this skill: the audit reaches
commit messages, the score is normalized, and write mode gains a guard.

### Added
- Commit-message inventory: `git log --all -i -P --grep=...` selects the commits,
  including merge commits and commits whose only match sits in the body, and an inner
  `rg` pass prints the matching lines as `<hash>:<line>:<snippet>`, so the separate
  history table reads like the working-tree one. It stays out of the score, since
  history needs a rewrite to change
- `PATTERN` is set once at the head of Step 1 and every later block opens with
  `: "${PATTERN:?...}"`, so a block run on its own aborts instead of handing `rg` an
  empty pattern that matches every line and reports a meaningless total
- Counting pass (`rg -niP --count-matches`) alongside the line-oriented inventory,
  because `rg -n` prints a sentence tripping two patterns once. The occurrence total
  comes from the counting pass, a catalog row states how many matches its line carries,
  and a line whose matches disagree on the verdict splits into a row each
- `not a ... but a` joins the inventory regex and the hook; the pattern list documented
  it while neither command looked for it
- "Enforcement" section with a bundled `scripts/commit-msg` hook. The hook warns and
  lets the commit through, because the detection patterns overmatch by design and a
  match still needs a reader. Also states that write mode does not survive a context
  compaction and belongs in CLAUDE.md or AGENTS.md for long sessions
- Write mode inherits the `quotation` verdict for verbatim text, diagnostics, and this
  skill's own examples, so reporting a violation no longer breaks the rule
- Note that the ban holds in every language, and that the Ukrainian patterns are noisier
  than the English ones: `не лише` and `не тільки` usually score as plain negation,
  while `не стільки X, скільки Y` is the construction proper

### Changed
- Score is normalized by project size: `max(0, 100 - spread - depth)` where `spread` is
  the share of scanned files that carry a violation and `depth` is the capped average
  violation count per affected file, with all four inputs reported next to the score. A
  scan with no files in scope reports that instead of dividing by zero
- Scan exclusions are stated as a rule (everything generated, and every file whose text
  is data rather than prose) instead of a two-entry list, and each added exclusion is
  named in the report
- The `quotation` verdict covers diagnostics alongside external text and translation
  source strings

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
