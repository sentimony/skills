# Voice

## When a voice profile applies

Build a profile when the user supplies a sample they identify as their own writing, or
identifies the text under edit as their own finished personal writing (an essay, a post). Around 150 words of sample support a
confident profile. With less, apply only the obvious traits, and state the low confidence
in explain mode. When samples disagree (a public post and an internal note, say), name the
split and ask which one applies; never average them.

For a finished text by its author, narrow the scope: fix typos, broken sentences, and
clear `strong` findings. List each changed sentence for the author's veto only on request
or in explain mode (see the notes rule). An explicit rewrite request lifts the narrowed
scope.

## Profile fields

| Field | Read from the sample | Apply as |
| --- | --- | --- |
| Sentence length | Typical length and spread | Target range for the rewrite |
| Openings | How sentences start: subject, connective, fragment | Same mix; no imported connectives |
| Paragraph density | Sentences per paragraph | Same paragraph shape |
| Directness | Claim first, or context first | Same order of claim and support |
| Formality | Contractions, slang, register words | Same level |
| Vocabulary | Plain or technical, recurring words | Words the author uses; no new jargon |
| Punctuation | Semicolons, parentheses, question marks | Same habits, under project typography policy |
| Contractions | Frequent, rare, none | Same frequency |
| Rhythm | Short runs, long builds, fragments | Same pattern |
| Transitions | Explicit connectives or bare juxtaposition | Same style |
| Fragments | Used, and where | Allowed where the author uses them |
| Person | `I`, `we`, `you` | Same person, never changing who acted |
| Never does | Traits the sample had an occasion for and avoided, or that the user names | Avoid them in the rewrite |

## Precedence

Highest first: the user's explicit instruction, the project's style guide and typography
policy, the author's voice, the register defaults, the pattern catalog.

- Project typography policy (for example `dashfix`) outranks the sample's punctuation
  habits.
- Voice never outranks preservation. A sample written in the first person singular does
  not turn team work into personal work: `we deployed` stays `we`.
- Voice changes how a claim is said and never adds one. A rewrite in the author's voice
  adds no lesson, reaction, number, or detail the draft lacks; run the claim ledger after
  it.

## Keep deliberate choices

A choice the author repeats on purpose is voice: fragments, long sentences, rhetorical
questions, anaphora, antithesis in an essay. The catalog does not correct it. In an essay
or personal post, `rhythm/repeated-openings` and `staging/dramatic-closer` are voice unless
they obscure a claim, and an audit leaves them out of the findings.

## Profile format

A compact block of five to eight `field: value` lines, shown only in explain mode or on
request. Keep it in the conversation; do not write it to a tracked file unless asked.

```text
sentence length: long, 20-30 words, rare short ones
openings: often a subordinate clause (when, if, because)
contractions: none
fragments: none
person: I for opinions, the project name for decisions
never does: rhetorical questions, direct address
confidence: medium (about 200 words, one sample)
```
