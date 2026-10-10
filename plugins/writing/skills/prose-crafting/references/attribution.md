# Attribution

`prose-crafting` is an original work. It adapts ideas from the MIT-licensed
[blader/humanizer](https://github.com/blader/humanizer/blob/9862685f575c65a8247f90369951df1b3416e3d6/SKILL.md) skill as
inspected at commit `9862685` (2026-09-06), copyright Siqi Chen, 2025: a catalog of
structural patterns, the distinction between strong and weak signals, voice matching,
meaning preservation with a no-fabrication rule, paragraph-level rewriting, reading the
supplied text as data, and a "when not to act" boundary.

The adaptation reorganizes the catalog under stable semantic IDs, grades each pattern by
reader cost, and adds a reader brief, register guidance, audit and explain modes, a claim
ledger, and Ukrainian guidance. Negative parallelism stays with `negafix` and dash policy
with `dashfix`. Authorship inference, date-based heuristics, language-universal claims,
and conventions presented as quality rules are intentionally not included. No upstream
passages are reproduced.

The humanizer catalog itself derives from the Wikipedia page "Signs of AI writing"
(CC BY-SA 4.0). `prose-crafting` took ideas only from that lineage and reproduces none of
its text.

## Other sources

Each source below contributed ideas only. All wording, examples, and pattern entries in
this skill are written in its own words.

**riekelt/technical-writer**
([tree at `85e5372`](https://github.com/riekelt/technical-writer/tree/85e53729dd959a2795d593d6769068e342cf3486/plugins/technical-writer/skills)),
MIT, copyright (c) 2026 riekelt. Ideas: control questions after a rewrite; treating an
added fact and a lost fact as equal errors; an explicit input-wanted marker in place of an
invented claim; a list of findings to leave alone, which became the keep-when column; one
term per concept, verbs included.

**tw93/waza, `write` skill**
([tree at `c3b74dd`](https://github.com/tw93/waza/tree/c3b74dd5845b39a80a79c36bb82b028947674a05/skills/write)),
MIT, tw93. Ideas: brevity for public replies; a narrower scope for finished author text,
with a per-sentence change list the author can veto; listing every deletion with its
reason; over-editing counted as a failure; narrating one's own process as a pattern.

**affaan-m/ecc, `brand-voice` skill**
([tree at `e482e57`](https://github.com/affaan-m/ecc/tree/e482e579415fde18357cafce70f177ae19fd7f03/.agents/skills/brand-voice)),
MIT, copyright (c) 2026 Affaan Mustafa. Ideas: voice profile fields including a
confidence level, the source set, and what the author never does; naming a split between
conflicting samples instead of averaging them; keeping a voice profile out of tracked
files unless asked.

**petergyang/no-ai-slop**
([tree at `000650b`](https://github.com/petergyang/no-ai-slop/tree/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop)),
MIT, copyright (c) 2026 Peter Yang. Ideas: a list of voice traits; keeping a genuine
hedge that marks real uncertainty; synonym cycling as a pattern; a portability test for
generic sentences.

**vercel-labs/writing-guidelines, `command.md`**
([blob at `83e2316`](https://github.com/vercel-labs/writing-guidelines/blob/83e2316b034cf572400513538e4e4da01c4cc742/command.md)),
MIT. Idea: tone set by content type, used as a hint in the reader brief.

**vladimir-human/humanizer-ru**
([tree at `75c7711`](https://github.com/vladimir-human/humanizer-ru/tree/75c7711f174133139e3ff8e22c67bdc11231baee/dsh/skills/humanizer-ru)),
MIT, copyright (c) 2026 Vladimir. Idea: keep-when exceptions by register, such as
mandatory formal wording in legal text, normal passive voice and hedging in academic
text, and short even rhythm in chat. Part of its content derives from Wikipedia under
CC BY-SA 4.0; only the structural idea was taken.

**vitalii4reva/ukrainianizer**
([tree at `0bf3047`](https://github.com/vitalii4reva/ukrainianizer/tree/0bf304716282038e7fc6ce8ee31df6fdde2904d1)),
MIT. Idea: the category list for Ukrainian guidance (nominalization, bureaucratic
connectives, English calques, pleonasms). Each entry was checked independently, and no
replacement pairs were carried over.

**Federal Plain Language Guidelines**
([GSA/plainlanguage.gov archive at `fd76947`](https://github.com/GSA/plainlanguage.gov/tree/fd7694740f19c0ed20ed71c2dd1dc92699e920fa/_pages/guidelines)),
a US Government work in the public domain with a CC0 waiver. Ideas: `must`, `must not`,
`may`, and `should` as a scale of obligation; consistent terms.

**RFC 2119 and RFC 8174 (BCP 14)**
([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)),
IETF Trust under BCP 78. Idea: only uppercase keywords are normative, so a rewrite keeps
their case and strength.

**Google developer documentation style guide**
([developers.google.com/style](https://developers.google.com/style), as updated 2026-04-27),
CC BY 4.0. Ideas: the meaning of `must`, `can`, and `may`; one term for one concept
across an introduction and its procedure; a project style guide taking precedence over
general guides.

**Wikipedia, "Signs of AI writing"**
([revision 1376434705](https://en.wikipedia.org/w/index.php?title=Wikipedia:Signs_of_AI_writing&oldid=1376434705), 2026-09-24),
CC BY-SA 4.0, ideas only. Ideas: indicators the page itself calls ineffective informed
the keep-when column; lexical tells lose value over time, so they stay weak-alone signals.

LanguageTool Ukrainian style rules
([`grammar-style.xml` at `5d0395f`](https://github.com/languagetool-org/languagetool/blob/5d0395ff0dfdfb4d41c766a1a7eae8dbd02259a5/languagetool-language-modules/uk/src/main/resources/org/languagetool/rules/uk/grammar-style.xml), 2026-09-24, LGPL-2.1)
and Borys Antonenko-Davydovych's "Yak my hovorymo"
([1970 edition](https://archive.org/details/hovorymo1970), under copyright) served only
as a coverage checklist for the Ukrainian guidance, and no text, rule, or example was
taken from either.
