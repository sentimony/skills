# Ukrainian

## Status of carried-over heuristics

The structural entries of the catalog were observed in English prose. In Ukrainian text
treat each of them as `contextual` until evidence says otherwise, and act only when the
reader cost is plain. English lexical lists do not carry over. `inflation/ing-rider` and
`inflation/copula-avoidance` have no checked Ukrainian evidence either; possible forms are
`виступає` or `слугує` in place of `є`, and a trailing adverbial participle such as
`, підкреслюючи ...`. `rhythm/repeated-openings` was observed on repeated pronoun
subjects; Ukrainian often drops the subject, so the English form rarely appears.

In mixed text, decide per block: a Ukrainian paragraph gets this file, an English one gets
the English reference.

## Norm errors, calques, pleonasms

Report these as `lexical/calque`. Fix them directly with the normative form; keep one only
inside quoted text.

| Pattern | Example | Direction |
| --- | --- | --- |
| `приймати участь` | `приймати участь у тестуванні` | `брати участь` |
| Prepositional calques | `у відповідності до`, `на протязі`, `в залежності від` | `відповідно до`, `протягом`, `залежно від` |
| `в той же час` | `в той же час ми оновили документацію` | `водночас` for contrast; `тим часом` only for simultaneity |
| English calques | `робить сенс`, `на щоденній основі` | `має сенс`, `щодня` |
| Pleonasm | `вільна вакансія`, `спільна співпраця` | `вакансія`, `співпраця` |

## Bureaucratic register

Report these as `register/officialese` (`канцелярит`): `contextual`, a cost in text that
is not official. Keep the form in legal, regulatory, and official documents, where the
register is required, and in quoted text. Elsewhere rebuild the sentence around the verb;
a word-for-word swap often leaves the bureaucratic structure in place.

| Pattern | Example | Direction |
| --- | --- | --- |
| Verbal noun with an empty verb | `здійснив оновлення`, `провести перевірку` | The verb itself: `оновив`, `перевірити` |
| `являється` as a copula | `Сервіс являється частиною платформи` | `є`: `Сервіс є частиною платформи`; dropping the copula needs a dash (`Сервіс — частина платформи`), whose form belongs to `dashfix` |
| `у якості` | `у якості адміністратора` | `як`: `як адміністратор` |
| `даний` for "this" | `даний розділ` | `цей`: `цей розділ` |
| `на сьогоднішній день` | `на сьогоднішній день підтримуємо дві версії` | `сьогодні` or `зараз`; drop it only when time is not part of the claim |
| `з метою` | `з метою зменшення навантаження` | `щоб`: `щоб зменшити навантаження` |
| `слід зазначити, що` | `Слід зазначити, що ключ діє добу.` | Drop the frame: `Ключ діє добу.` |
| Genitive chains | `забезпечення підвищення якості обслуговування клієнтів` | Split and use a verb: `покращити обслуговування клієнтів` |

Each replacement in either table must keep the meaning: check it against the claim ledger,
especially where a noun phrase carried a qualifier.

## Passive and impersonal forms

`Було прийнято рішення` hides who decided. If the source names the agent, name it: `Команда
вирішила`. If it does not, keep the form: preservation outranks style, and an invented
agent is a new claim. This follows `syntax/passive-missing-agent`.

## Punctuation

The dash in Ukrainian is grammatical and no signal; its form belongs to `dashfix`. Never
recommend replacing Ukrainian dashes with hyphens or commas. Quotation marks `«»` are a
convention. For orthography and punctuation norms, the reference is the state language
standard «Український правопис» (National Commission on State Language Standards, 2026);
this file does not restate it.

## Register

- Keep `ти` or `ви` consistent through the text, as the author chose it.
- Established English terms in technical text (`деплой`, `пул-реквест`, `API`) are normal.
  Replace one only when the project uses a Ukrainian term for it.
