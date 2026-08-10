# Changelog

All notable changes to the `dashfix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.1.0] - 2026-08-10

Feedback release: the ban becomes language-aware, the audit reaches commit messages, and
write mode gains deterministic guards.

### Added
- "Language scope" section: the ban binds per file rather than per project. English and
  other dash-optional languages keep the full ban; in Ukrainian, Russian, Polish, and
  German the em dash is orthography, so the skill checks the form of the dash (em vs en,
  spacing, hyphen inside compounds) instead of its presence. A style-guide conflict is
  named in one line and the work continues under the repository convention
- Fifth `justified` category for a dash that a language's orthography requires, with the
  catalog naming the file's language wherever a verdict depends on it
- Commit-message inventory: `git log --all -P --grep=...` selects the commits, including
  merge commits and commits whose only dash sits in the body, and an inner `rg` pass
  prints the matching lines as `<hash>:<line>:<snippet>`, so the separate history table
  reads like the working-tree one. It stays out of the score, since history needs a
  rewrite to change
- Counting pass (`rg -P --count-matches`) alongside the line-oriented inventory, because
  `rg -n` prints a line holding two dashes once. The occurrence total comes from the
  counting pass, a catalog row states how many occurrences its line carries, and a line
  whose occurrences disagree on the verdict splits into rows keyed `<location>#<n>`
- "Enforcement" section with a bundled `scripts/commit-msg` hook that rejects a banned
  dash in a commit message, a `PreToolUse` snippet for `.claude/settings.json`, and the
  statement that write mode does not survive a context compaction. The hook applies
  Language scope the only way a hook can and skips a message written in Cyrillic; the
  snippet reads its payload with perl alone, because a `jq` pipeline exits 0 on a machine
  without `jq` and lets the commit through in silence
- Write mode inherits the `justified` verdict for verbatim quotations, diagnostics, and
  this skill's own character table, so reporting a violation no longer breaks the rule

### Changed
- Score is normalized by project size: `max(0, 100 - spread - depth)` where `spread` is
  the share of scanned files that carry a violation and `depth` is the capped average
  violation count per affected file. Five bad files no longer force a score of 0 in a
  2000-file repository, and the report shows all four inputs. A scan with no files in
  scope reports that instead of dividing by zero
- Scan exclusions are stated as a rule (everything generated, and every file whose text
  is data rather than prose) instead of a three-entry list, and each added exclusion is
  named in the report
- The `grep -rnP` fallback is replaced by `ggrep -rnP` and a perl one-liner over
  `git ls-files -z | xargs -0`, because BSD grep on macOS has no `-P` even where an agent
  session aliases `grep` to `ugrep`, and unquoted `xargs` breaks on a filename with a
  space. The one-liner repeats the scan exclusions as `:(exclude)` pathspecs and closes
  `ARGV` at each `eof`, so it now reports the same locations as the `rg` pass instead of
  scanning more files and numbering every line after the first file wrong
- Both working-tree passes name `.` explicitly. Given a piped stdin and no path, `rg`
  reads the pipe rather than the tree and reports zero matches on a project full of them

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
