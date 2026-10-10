# English

## Weak lexical signals

These words appear often in generic English prose. Each is `lexical/tell-word`:
`weak-alone`, never the reason for an edit by itself, and never fixed by a synonym swap.
When a paragraph is rewritten for a structural reason, ask what the sentence was meant to
say. Lexical tells also age as fashions change; treat the list as a hint.

`delve`, `tapestry`, `testament`, `pivotal`, `landscape` (figurative), `realm`,
`seamless`, `robust`, `leverage`, `empower`, `foster`, `underscore`, `showcase`,
`crucial`, `vibrant`, `intricate`, `navigate` (figurative).

Literal technical meanings are no signal: a `robust` estimator, a network `landscape`
diagram, `navigate` to a URL.

## Constructions

| Construction | Example | Entry |
| --- | --- | --- |
| Trailing participle comment | `, reflecting the team's commitment to quality` | `inflation/ing-rider` |
| Copula avoidance | `serves as the main entry point` | `inflation/copula-avoidance` |
| Announcing a point | `It's worth noting that`, `Here's the thing:` | `staging/fake-opener` |
| Stock stakes | `in today's fast-paced world`, `plays a crucial role` | `inflation/borrowed-significance` |
| Filler idiom | `at the end of the day`, `when all is said and done` | `staging/fake-opener` |
| Deep-sounding frame | `at its core`, `fundamentally` | `staging/borrowed-wisdom` |
| Hedging stack | `could potentially`, `may perhaps somewhat` | `density/stacked-qualifiers` |
| Chat wrapper | `I hope this helps`, `Happy to help further` | `residue/chatbot` |
| Summary transition | `In summary`, `All in all`, `To sum up` | `density/generic-conclusion` |
| Fake action alternative | `One might be tempted to`, `It would be easy to just` | `staging/fake-alternative` |

## Register

- Contractions are natural in chat, email, and blog posts. In reference docs follow the
  project's convention; without one, match the surrounding text.
- The Oxford comma is a style-guide convention, never a signal.
- A genuine `I think` or `I'm not sure` marks certainty; keep it.

## Technical prose

- One term per concept, verbs included: if the text says `deploy`, it does not switch to
  `ship` and `roll out` for the same action. Varying terms is `lexical/synonym-cycling`,
  which is `strong` in technical and reference prose.
- Requirement keywords keep their word, case, and strength. `must` and `must not` state
  obligation, `should` a recommendation, `may` a permission, `can` an ability. A rewrite
  never trades one for another; uppercase `MUST`, `SHOULD`, and `MAY` are normative.
- Identifiers, commands, flags, paths, error messages, and API names stay verbatim, in code
  formatting where the source uses it.
- `as of <version>` is precise technical writing, and no `residue/knowledge-disclaimer`.

## Punctuation

- Dash characters and their replacement belong to `dashfix`; a paragraph where
  dashes carry every connection is `rhythm/dash-connector`.
- Semicolons, straight versus curly quotes, and title versus sentence case are project
  conventions, never signals.
- A colon reveal (`The answer: caching.`) is `staging/fake-opener` when it only stages the
  point.
