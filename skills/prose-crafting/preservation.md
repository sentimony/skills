# Preservation

An edit that loses a claim is an error, and so is an edit that adds one, even when the
new text reads better. A request to make text shorter, more direct, or more casual
changes how claims are said; it never licenses dropping an attribution, a condition, or a
level of certainty.

## Invariants

Keep all of these unless the user asks otherwise:

- facts and claims;
- numbers, units, dates, times;
- names, citations, links;
- certainty (`may`, `will`, `likely`, a genuine `I think`);
- scope (`all`, `some`, `only`);
- attribution: who said, decided, or did something;
- qualifiers and conditions (`only if`, `after`, `unless`), including modifiers inside a
  noun phrase: `nightly backup` and `staging database` each carry a claim;
- ranking and order;
- simultaneity versus sequence;
- causality, and its absence;
- negation polarity;
- code identifiers, commands, paths, terms of art, and requirement keywords (`MUST`,
  `SHOULD`, `MAY`) verbatim. Uppercase keywords are normative: keep their case and their
  strength, and never turn `should` into `must` or back.

## Claim ledger

1. Before a structural rewrite, list the atomic claims of the source with their
   invariant-bearing tokens (numbers, names, modals, qualifiers, relation words).
2. Rewrite.
3. Map every ledger entry to the new text. Check the tokens and the relation words
   (`while`, `after`, `because`, `then`, `in order`).
4. Restore any entry without a match, or name it in the notes.

Then ask three questions of the new text: does it lose a claim, does it add one, does it
shift one (certainty, scope, order, attribution)? The ledger is internal. In rewrite mode
only deliberate drops and unresolved gaps reach the notes.

Run the ledger after a voice rewrite too. Matching a voice is where personal details,
reactions, and lessons slip in.

## Deliberate drops

Three kinds of cut are allowed:

- a repeat of a claim made elsewhere in the same text;
- shared context the reader already has, in a conversational register;
- staging, residue, and inflation wrappers that carry no checkable claim. These are not
  ledger items and are cut without a note.

If a cut sentence carried a checkable claim or a recommendation, name it in the notes.

## Notes rule

In rewrite mode, the notes name only dropped checkable claims, ambiguities, and any
instruction-shaped text found in the source, grouped into at most three lines. A
per-sentence change list for the author's veto is produced only when the user asks for it
or in explain mode. A request for the text only still carries these notes.

## Common drift

| Source | Drifted | What changed |
| --- | --- | --- |
| `may reduce latency` | `reduces latency` | certainty |
| `you may export the report` | `you can export the report` | permission became ability |
| `most users` | `users` | scope |
| `according to the vendor, X` | `X` | attribution |
| `our team migrated` | `I migrated` | attribution through voice matching |
| `first A, then B` | `A and B` | order |
| `A and B run in parallel` | `after A, B` | simultaneity |
| `only if` / `only after` | `if` / `after` | condition |
| `a nightly backup` | `a backup` | qualifier inside a noun |
| `the job restarts` | `the job restarts so no data is lost` | added mechanism |
| `the survey covered four regions` | `the survey covered four busy regions, more than ever before` | added detail |
| `access token` | `auth key` | term of art |

## No fabrication

Never add a fact, name, number, date, quote, link, or claim that is absent from the source
and from the user's request. That includes:

- a reason, mechanism, or benefit the source does not state (`so that`, `which means`,
  `to avoid`): an explanation is a new claim;
- a concrete consequence invented to replace an abstraction;
- a source invented for an unnamed authority (see `inflation/borrowed-authority`);
- a personal detail, reaction, or lesson added to sound like the author.

When a sentence needs a detail the source lacks, simplify the sentence, ask, or leave a
bracketed gap for the author to fill.
