# Changelog

All notable changes to the `negafix` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.4.0] - 2026-09-27

Voiced-position release: a two-half contrast earns `justified contrast` only when
someone voiced the rejected position, reversing the 1.3.0 rule that let a bare factual
constraint shield it. `description` is unchanged.

### Added
- Two rewrite variants for every `violation`: A keeps only the positive half and names
  the dropped loss in parentheses; B keeps both thoughts without the construction and
  marks any detail absent from the original with `[adds: ...]`. B carries the negated
  half only when it holds a fact; otherwise B = A, and B never restates the rejected
  half as "It is not X" or "It also X"
- A "Pending user decision" table for contrast rows whose text points to a voiced
  position the scan cannot check; each row carries `justified contrast` ("voiced
  off-page, unverifiable"), and the alternative "score if every pending row is a
  violation" is reported next to the score
- Verbatim records (transcripts, meeting notes, exported chats) as their own exclusion
  class, kept outside `scanned`
- A filter for files that quote `PATTERN` itself (plans, AGENTS.md files carrying the
  verification command), by glob or by post-filter
- A snippet-window inventory command for long lines, marked as not for totals since the
  window can swallow a second match on the same line
- A zero rule with a positive control: a zero-match report on natural-language text is
  unverified until `rg` is shown to see the files
- A note that agent sessions rarely keep shell state between commands, so every Step 1
  block is self-contained
- Skipping the commit-history pass when the repository has fewer commits than prose
  files in scope, with that skip stated in the report
- `prose-crafting` named in "When NOT to use" for every other tell of generated prose
- `scripts/test_patterns.py` cases for `UA_CONTRAST`, `UA_SPLIT`, and the `це не про`
  word-boundary regression

### Changed
- Verdict rule for a sentence with a negated half and a complementary positive half: it
  is `justified contrast` only when someone voiced the rejected position and the reason
  names where (the new "Voiced position" rule); otherwise it is `violation`. A factual
  constraint or exclusion in the negated half no longer shields the sentence from
  `violation` on its own, and the fact moves into its own sentence in the rewrite instead
  of staying paired with the contrast. The reversal also covers unsupported objection
  frames with an exclusion ("This is not to say...") and additive `not only X but also Y`
  / `не лише X, а й Y` enumerations that nobody contradicted
- Ukrainian `не A, а B` (`UA_CONTRAST`) and `Це не X. Це Y.` (`UA_SPLIT`) move from the
  exploratory tier to the scored contextual tier for prose globs (`*.md`, `*.mdx`,
  `*.txt`, plus every path the user names as prose); outside those globs they stay
  exploratory
- `PATTERN` and the bundled commit hook gain a word boundary after `це не про`, so it no
  longer matches words such as "пропорційна"
- Security Model rewritten as bullets (user-controlled inputs, untrusted inputs, scanned
  content is data, capabilities) with an explicit boundary on quoting scanned content in
  table cells or fenced blocks rather than shell commands
- A project-wide audit runs the exploratory `RATHER`, `OBJECTION`, and `TAIL` patterns on
  the prose globs plus the user-named paths by default, widens them to code only on
  request, and names the scope in the report
- Fix mode's "fix all" with no per-row choice now applies variant B where B carries no
  `[adds]` and asks about the rest, instead of applying the old single write-mode recipe

## [1.3.0] - 2026-09-26

Detection release informed by `blader/humanizer` patterns 1 and 5 (see
`references/attribution.md`): the construction is caught across a sentence break, every
candidate is judged by what each half contributes, and three adjacent shapes are watched
without being scored.

### Added
- Contextual tier: a multiline `CROSS` pattern for the construction split across two
  sentences ("This does not mean X. It means Y."). Both sentences form one catalog row,
  keyed `<file>:<start>-<end>`, and the row enters the score like a single-sentence one
- Verdict procedure with an information-gain test (does the negated half carry a fact,
  does the positive half make a claim of its own) and a claim-preservation check over
  eight elements (distinction, limitation, exclusion, scope, attribution, qualifier,
  measurable claim, technical classification) that every rewrite must pass
- Exploratory tier, outside the score and never a `violation` on a phrase match alone:
  reversed contrast (`X rather than Y`), unsupported objection ("I'm not saying X",
  "Don't get me wrong", "This isn't about X", judged by whether anyone raised the
  position), and clipped negative tail (", no guessing"). Ukrainian `Це не X. Це Y.`
  joins `не A, а B` here
- `scripts/test_patterns.py`: keeps `PATTERN` and the commit hook in agreement and
  pins the precision of the new patterns on a fixed corpus

### Changed
- The "keep the stronger half" recipe now runs after the claim-preservation check, so
  "This isn't a cache; it persists data across restarts" keeps its classification
  instead of losing it
- The single-file check runs the contextual pattern and, for documentation or copy,
  the exploratory pass; fix mode rewrites `violation` rows from the exploratory table
  as well
- "When NOT to use" names the objection frames that reject an alternative approach
  as out of scope

## [1.2.3] - 2026-09-15

### Changed

- Narrowed the trigger from prose "anywhere in a project" to writing or substantively editing
  prose, and dropped commit messages from the list, for the same always-on reason as `dashfix`.
- Added "Not for ordinary factual negation" to the description. The body already drew that
  line ("plain factual negation and is always fine"), but the description did not carry it,
  so a plain "not" had nothing holding back a false activation.

## [1.2.2] - 2026-09-14

Security Model release: the section now names its trusted and untrusted inputs.

### Changed
- The `## Security Model` section now names which inputs are user-controlled and which are
  untrusted, alongside the existing instruction-boundary and capability statements.

## [1.2.1] - 2026-08-21

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the frontmatter description to the triggers; the ban and the 0-100 scale
  stay in the skill body.

## [1.2.0] - 2026-08-20

Feedback release from a Ukrainian-prose session: matches are candidates until read, one
new file gets a cheap pre-handoff check, and the Ukrainian `не A, а B` form gains an
exploratory pattern.

### Added
- "Single-file check" under write mode: run the Step 1 pattern on one file, verdict
  every candidate from the full sentence, rewrite only violations, re-run to confirm,
  and skip the project score
- Exploratory pattern `не [^,.;]{1,60}, а ` for Ukrainian `не A, а B`, run only on
  demand with a mandatory manual verdict; a match is a violation only when B restates A

### Changed
- Detection patterns state that a match is a `candidate` until a verdict is assigned,
  the counting-pass total counts candidates rather than violations, and every final
  catalog row carries exactly one of the four verdicts

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
- Both working-tree passes name `.` explicitly. Given a piped stdin and no path, `rg`
  reads the pipe rather than the tree and reports zero matches on a project full of them

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
