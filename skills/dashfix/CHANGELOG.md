# Changelog

All notable changes to the `dashfix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [2.0.1] - 2026-10-04

### Changed
- Relation table routing: `hidden logic` now applies when the second part reads as a
  reason, result, contrast, condition, or sequel of the first, not only when a connecting
  word is implied, and falls back to keeping ` - ` instead of a period or semicolon.
  `linked clauses` covers only clauses with no implied relation, and when two rows could
  apply, or the better mark would drop a relation, the fix stays ` - `.

## [2.0.0] - 2026-10-04

Hyphen-only release: the plain hyphen is the only dash in every language, and the audit
reports counts instead of a score.

### Changed
- The rule applies to every language, Ukrainian, Russian, Polish, and German included. A
  spaced dash becomes a spaced hyphen (`Ми - команда`); an unspaced dash between words
  takes spaces too, unless it joins a compound word. The description no longer limits the
  skill to English text.
- The default fix is ` - ` everywhere. The relation table (commas, parentheses, colon,
  period, semicolon, connecting word) becomes optional better punctuation instead of a
  required choice, and the spaced hyphen is no longer rejected as a replacement.
- Verdicts: `replace` is the default for all prose, quotations and logs included (a
  changed quotation is named once in the report). A new `data` verdict covers characters
  that code reads (test expectations, fixtures, snapshots, exported data, `−` as a
  symbol): fix them only with the code and tests that read them, or leave and name them.
  `justified` keeps two causes only: the text is about the character itself, or the user
  asked to keep dashes in that file.
- An explicit request in the current session to keep dashes in named files wins for those
  files only and is reported in one line; a project document that asks for dashes is
  named as a conflict and followed only if the user confirms it.
- Audit report: an occurrence total above the catalog, a `Location / Snippet / Char /
  Reason` table that shows each character next to `-`, and a summary line below it ("X to
  fix in Y files"). Identical rows may collapse across files. Fix mode reports "Fixed in
  X places in Y files".
- `scripts/commit-msg` checks messages in every language; the Cyrillic skip and its
  caveats are gone.
- `agents/openai.yaml` short description matches the new scope.

### Removed
- The audit score (`scanned`, `affected`, `spread`, `depth`, bands) and Step 3 - Score.
- Verdict causes for proper names, verbatim quotations, a language that requires the
  dash, and a project typography rule.

## [1.3.1] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.3.0] - 2026-09-26

Replacement release: the fix for a banned dash follows from the relation it hides, and a
rewrite has to keep what the sentence said.

### Added
- A `## Replacement` section: name the relation between the two parts (aside, digression,
  expansion, next thought, linked clauses, hidden logic, range, minus, overloaded), then
  write the punctuation that states it. It applies only where the dash is optional; in a
  language that requires the dash the fix stays the correct form. Expansion takes a colon
  only after a complete clause; hidden logic writes the connecting word only when the
  context states it, else a period or semicolon.
- "Minimal rewrite": a sentence with two or more dash inserts or clause breaks (a pair
  around one insert counts once) is judged as a whole and split before any single dash is
  classified; a substitute that breaks syntax or repeats a qualifier gets a split or a
  connecting word. The rewrite stays inside that sentence. An awkward but grammatical
  comma pair is prose editing and is left alone. The catalog reason for a rewrite carries
  the proposed sentence, so the user approves the actual text.
- "Preservation check": after any fix that adds, moves, or removes a word, both parts,
  facts, attributions, qualifiers, limitations, scope, numbers, dates, and temporal or
  logical relations must survive.
- `references/replacement.md` with worked examples and `references/attribution.md`, which
  records the humanizer source at its pinned commit under the MIT License.

### Changed
- Write mode, the catalog reason, and fix mode point to Replacement instead of carrying
  their own hints; a `replace` reason now opens with the relation (`aside, use commas`).
- A spaced or double hyphen swapped in for a banned dash is not a replacement.

Detection, verdicts, the score formula, and both hooks are unchanged.

## [1.2.3] - 2026-09-15

### Changed

- Narrowed the trigger from prose "anywhere in a project" to writing or substantively editing
  prose. Comments and commit messages are no longer listed: with them, a 17842 B package was
  eligible to load in nearly every session. Auditing and scoring are unchanged.

## [1.2.2] - 2026-09-14

Security Model release: the section now names its trusted and untrusted inputs.

### Changed
- The `## Security Model` section now names which inputs are user-controlled and which are
  untrusted, alongside the existing instruction-boundary and capability statements.

## [1.2.1] - 2026-08-21

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the frontmatter description: the ban, the per-language dash rules, and the
  0-100 scale stay in the skill body; the description keeps only the triggers.

## [1.2.0] - 2026-08-20

Feedback release from a mixed-language session: candidates stop reading as errors, one
new file gets a cheap pre-handoff check, and a Markdown file may switch language block
by block.

### Added
- "Single-file check" under write mode: inventory one file with `rg -nP`, give each hit
  the catalog fields (language, code point, verdict, reason, replacement), fix only the
  `replace` verdicts, and report candidate and replace counts as two numbers, without
  computing a project score
- Language scope bullet for mixed-language Markdown: prose blocks, quotations, code
  fences, and diagnostics are classified separately instead of one file-level verdict

### Changed
- The counting-pass total is explicitly a candidate count, never a violation count, and
  the Step 4 report states candidate / justified / replace as three separate numbers
- A `replace` row's reason must name the fix so the fix pass can apply the catalog
  mechanically

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
  space. The one-liner lists files with `--cached --others --exclude-standard`, repeats
  every scan exclusion both bare and `**/`-anchored because a git pathspec is not a
  gitignore pattern, drops hidden paths, skips symlinks and any file holding a NUL byte
  the way `rg` skips a link and calls a file binary, and slurps each file to number its
  lines. It therefore reports the same locations as the `rg` pass instead of missing
  untracked files, keeping root or nested lock files, reading hidden, symlinked and
  binary paths, and numbering every line after the first file wrong. The text calls the result best effort and names the two files that
  still part the passes, a file whose bytes are invalid UTF-8 without a NUL and a
  gitignored file force-added to the index, with the command that lists the second kind
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
