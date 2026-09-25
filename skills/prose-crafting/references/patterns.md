# Pattern catalog

Each entry describes something that costs the reader attention, trust, or information.
The catalog makes no claim about who or what wrote a text. IDs are stable: they are never
renumbered or reused, and they are the only way to refer to an entry. The strength of an
entry is a default; the register and the author's voice can lower it. A match is never
the reason for an edit by itself: name the reader cost first, and leave the sentence when
no cost can be named.

An audit finding built on an entry carries the ID, the severity, the location (line or quoted anchor),
the quoted evidence, the reader cost in the reader's terms, and the direction of the fix.
A label such as "word order" or "flow" is a category, and a category is no reader cost.

## Strength levels

`strong` - a structural pattern worth fixing once its reader cost is visible in the text
at hand. One clear instance is enough.

`contextual` - a problem in some registers and normal in others. Act when two signals of
`contextual` strength or higher share a paragraph, or when the cost is plain in this
register; weak-alone signals only add weight.

`weak-alone` - never a finding by itself and never the reason for an edit. It only adds
weight to a paragraph that already has a `strong` or `contextual` finding.

These are the three strengths. The value `route` in the Strength field is an ownership
marker: another skill owns the pattern, this catalog records one pointer, and the owner's
rules decide everything else.

Observed in English prose; treat as contextual in other languages until evidence says
otherwise. This applies to every structural entry below. Lexical and punctuation signals
live in the language references and never cross languages.

## staging/fake-opener

**Strength:** strong
**Looks like:** A run-up that announces a point before making it: a stock phrase or filler
idiom (`at the end of the day`), a colon reveal, or the same framing reused at the top of
every section.
`Here's the thing: the export job runs once a night.`
**Reader cost:** The reader spends the first words of a sentence waiting for the content,
and the announced importance is never delivered.
**Keep when:** A transcript of speech; the author's own voice uses it on purpose; `Honestly`
or `look` inside a conversational sentence.
**Direction:** Start with the point. `The export job runs once a night.`

## staging/meta-commentary

**Strength:** strong
**Looks like:** Text about the text: announcing what a section will do, or telling the
reader how to interpret the sentence that follows. `This section will explain how the
export job is scheduled.`
**Reader cost:** A promise of content takes the place of the content.
**Keep when:** A long reference where a short map helps navigation.
**Direction:** Delete the announcement, or turn it into a heading if the reader needs the
map.

## staging/dramatic-closer

**Strength:** contextual
**Looks like:** A fragment or one-line paragraph added after the point for effect, a run of
fragments, including negative ones such as `No logs. No alerts.` (a clipped negative tail
such as `, no guessing` belongs to `negafix`), or typographic emphasis
such as ALL CAPS. `The job failed silently for a week. Silently.`
**Reader cost:** Repeats the point in a louder voice; the reader gets emphasis instead of
information.
**Keep when:** An essay or personal post in the author's voice; each fragment carries a
distinct fact; a short paragraph that adds something new.
**Direction:** End on the last informative sentence. `The job failed silently for a
week.`

## staging/borrowed-wisdom

**Strength:** contextual
**Looks like:** An aphorism or deep-sounding frame (`at its core`) that says nothing
checkable about the subject. `In the end, every system is only as good as its habits.`
**Reader cost:** The reader has to decide whether the line means anything here, and it
usually does not.
**Keep when:** The aphorism is the argument and the text backs it with specifics; literal
uses of `at its core` in technical prose.
**Direction:** Delete it, or replace it with the specific claim from the text it was
gesturing at.

## staging/fake-alternative

**Strength:** contextual
**Looks like:** Rejecting a course of action nobody proposed, to make the chosen one look
considered. `A tempting approach would be to poll the queue every second. Instead, the
worker subscribes to events.` Objection frames aimed at a claim (`I'm not saying`, `You
might think ... but`) belong to `contrast/negative-parallelism`.
**Reader cost:** The reader evaluates an option that was never on the table.
**Keep when:** The reader is genuinely weighing that option, or someone named proposed it.
**Direction:** State the choice, with its reason if the text has one. `The worker
subscribes to events.`

## contrast/fake-contrast

**Strength:** contextual
**Looks like:** A contrast with no tension between its halves. `While speed is important,
accuracy also matters.`
**Reader cost:** The reader looks for a trade-off that the sentence never describes.
**Keep when:** The text states a real trade-off between the two.
**Direction:** State both points plainly, or name the trade-off if the source gives it.

## contrast/negative-parallelism

**Strength:** route
**Looks like:** Defining something by denying a framing first: `It's not a cache, it's a
contract.`, `not just X`, objection frames such as `I'm not saying`.
**Owner:** `negafix`; an audit reports one finding with this ID and a pointer, with no
per-instance list, verdict, replacement, or score.

## rhythm/forced-triad

**Strength:** contextual
**Looks like:** Three items chosen for cadence, usually adjectives or parallel examples
without their own facts. `The new dashboard is clean, intuitive, and modern.`
**Reader cost:** The reader gets three labels and no fact to check; the third item is often
filler.
**Keep when:** The list really has three members, each with content.
**Direction:** Keep the items the text supports with a fact and drop the rest, or replace
the triad with that fact. Shape edits here often lose claims; check the ledger.

## rhythm/repeated-openings

**Strength:** contextual
**Looks like:** Consecutive sentences that start the same way with no rhetorical purpose.
`The tool reads the file. The tool parses it. The tool writes a report.`
**Reader cost:** Monotony hides which sentence carries the new information.
**Keep when:** Deliberate anaphora, especially in an essay or speech; the author's voice.
**Direction:** Merge the sentences into one sequence. `The tool reads the file, parses it,
and writes a report.`

## rhythm/uniform-length

**Strength:** weak-alone
**Looks like:** Every sentence in a paragraph has about the same length, or a stop-start run
of short sentences.
**Reader cost:** Only in combination: flat rhythm makes a padded paragraph harder to scan.
**Keep when:** Always, unless another finding in the same paragraph already justifies a
rewrite. Chat has short, even rhythm by norm.
**Direction:** When the paragraph is rewritten for another reason, let sentence length
follow the logic, and follow the voice profile when there is one.

## rhythm/dash-connector

**Strength:** route
**Looks like:** A paragraph where dashes carry every connection between clauses.
**Owner:** `dashfix`; an audit reports one finding with this ID and a pointer, with no
dash inventory, replacement table, verdict, or score.

## inflation/borrowed-significance

**Strength:** strong
**Looks like:** Importance claimed through vague stakes. `The migration marks a pivotal
moment for the team: it removes the last manual deploy step.`
**Reader cost:** The reader has to strip the wrapper to find the fact, and the wrapper
claims weight the text never shows.
**Keep when:** Never as wrapper. A factual claim inside it goes into the ledger.
**Direction:** Keep the concrete consequence the text already states and drop the wrapper.
`The migration removes the last manual deploy step.` With no concrete consequence in the
source, delete the sentence or ask.

## inflation/borrowed-authority

**Strength:** strong
**Looks like:** An appeal to unnamed authority. `Experts agree that short-lived tokens
are safer.`
**Reader cost:** The reader cannot check the source, so the sentence claims more
confidence than it can back.
**Keep when:** The source is named in the text.
**Direction:** Drop the appeal when the claim stands on its own in the text. Otherwise keep
the claim, and flag it in the notes or with a bracketed request for the source. Never
invent a source, and never delete the claim silently.

## inflation/sales-language

**Strength:** contextual
**Looks like:** Promotional adjectives outside marketing, or unbacked superlatives inside
it. `This powerful integration makes syncing effortless.`
**Reader cost:** The reader discounts the whole text once it starts selling.
**Keep when:** Product copy where a fact in the text backs the claim.
**Direction:** Replace the adjective with the fact the text gives, or delete it.

## inflation/vague-association

**Strength:** contextual
**Looks like:** `plays a role in`, `contributes to`, `is linked to` where the text knows the
actual relation. `The retry limit plays a role in how long a failed job lingers; after
five attempts the job is dropped.`
**Reader cost:** Hides a relation the reader needs and the text already has.
**Keep when:** The relation really is unknown in the source; literal technical uses.
**Direction:** State the known relation. `The retry limit is five attempts; after that a
failed job is dropped.`
Never invent a role the source does not state.

## inflation/ing-rider

**Strength:** contextual
**Looks like:** A trailing participle clause that comments on the sentence. `The service
now caches responses, highlighting the team's focus on speed.`
**Reader cost:** Adds an interpretation dressed as a fact.
**Keep when:** The clause carries a fact of its own.
**Direction:** Cut the rider, or make its fact a separate sentence.

## inflation/copula-avoidance

**Strength:** weak-alone
**Looks like:** `serves as`, `stands as`, `boasts` where `is` or `has` would do. `The
schema boasts over 40 tables.`
**Reader cost:** Only in combination with inflation.
**Keep when:** The verb carries meaning; `represents` in a data model is literal.
**Direction:** When rewriting the sentence anyway, use the plain verb and keep every
qualifier. `The schema has over 40 tables.`

## density/over-explaining

**Strength:** strong in conversational registers; contextual elsewhere
**Looks like:** Explaining what the reader already knows: defining terms the reader uses
daily, re-explaining the change under review, recapping shared context from the thread.
**Reader cost:** The reader reads known material to find the new part, and may read it as
condescension.
**Keep when:** The reader is genuinely new to the topic.
**Direction:** Keep only what is new to this reader: the fact, the reason, the next step.

## density/restated-question

**Strength:** strong in conversational registers; contextual elsewhere
**Looks like:** Repeating the question before answering. `You asked why the job runs at
night. It runs at night because...`
**Reader cost:** The asker already knows the question; the answer arrives late.
**Keep when:** The question is ambiguous and the restatement fixes which reading you
answer.
**Direction:** Open with the answer.

## density/excessive-completeness

**Strength:** contextual
**Looks like:** Covering every case when the purpose needs one.
**Reader cost:** The case the reader needs is buried among the ones they do not.
**Keep when:** A reference where completeness is the purpose.
**Direction:** Keep the cases the purpose needs; move the rest to a pointer if they must
survive.

## density/stacked-qualifiers

**Strength:** weak-alone
**Looks like:** Hedges piled on one claim. `This may possibly reduce load.`
**Reader cost:** Only in combination: the reader cannot tell how certain the claim is.
**Keep when:** A single ordinary hedge; scope, legal, and safety qualifiers.
**Direction:** Remove duplicates and keep the level of certainty. `This may reduce load.`

## density/generic-conclusion

**Strength:** contextual
**Looks like:** A closing paragraph or transition that restates or generalizes (`In
summary`, `Overall, X is a great choice`).
**Reader cost:** The reader rereads what they just read and learns nothing new.
**Keep when:** A real summary, TL;DR, or executive summary of a long document, or a
conclusion that adds a decision or next step.
**Direction:** End on the last concrete fact or the plan the source states.

## density/heading-echo

**Strength:** contextual
**Looks like:** The first sentence repeats the heading. Under `## Retention`: `This section
covers retention.`
**Reader cost:** The first line of the section carries nothing.
**Keep when:** Rarely; a heading too terse to stand alone.
**Direction:** Start with the first fact of the section.

## residue/chatbot

**Strength:** strong
**Looks like:** Wrapper aimed at whoever ordered the draft: `Great question`, `I hope
this helps`, `Let me know if you have any other questions`.
**Reader cost:** Words addressed to someone other than the reader.
**Keep when:** Greetings and sign-offs the channel's norms expect, such as an email
signature.
**Direction:** Delete.

## residue/knowledge-disclaimer

**Strength:** strong
**Looks like:** `As of my last update` and similar notes on the writer's knowledge limits.
**Reader cost:** The reader cannot tell what the text actually knows.
**Keep when:** An honest statement that the source does not show something; `as of
<version>` in technical docs.
**Direction:** Delete the disclaimer. Add a date or source only when the user supplies it.

## residue/version-narration

**Strength:** contextual
**Looks like:** A current-state document narrating its own edits. `The limit is now updated
to 50.`
**Reader cost:** The reader of current docs does not need the history, and may read it as
unstable.
**Keep when:** Changelogs, release notes, migration guides.
**Direction:** State the current fact. `The limit is 50.`

## residue/process-narration

**Strength:** strong in conversational replies; contextual elsewhere
**Looks like:** Narrating how the writer worked instead of what they found. `I looked
into the logs, then checked the config, and it turns out the timeout is 90 seconds.`
**Reader cost:** The result arrives at the end of a story the reader did not ask for.
**Keep when:** The reader asked how it was found, or the method is what makes the result
trustworthy.
**Direction:** Lead with the result. `The timeout is 90 seconds.` Keep a method only when
it matters to the reader.

## format/decorative-bold

**Strength:** contextual
**Looks like:** Bold on phrases nobody will scan for, often several per paragraph.
**Reader cost:** When everything is emphasized, the reader cannot find what matters.
**Keep when:** Bold labels in metadata blocks, definition lists, and reference lists, when
that is the project's convention; one warning the reader must not miss.
**Direction:** Remove the emphasis; keep it only where a reader scans for it.

## format/decorative-headings

**Strength:** contextual
**Looks like:** Headings on a short text or a chat reply; emoji or arrows as decoration; a
rule between every section; a top heading that repeats the document title. Title case
versus sentence case is a style-guide convention and no signal.
**Reader cost:** Structure the length does not need breaks the reading into pieces.
**Keep when:** A document long enough that the reader navigates by headings.
**Direction:** Fold short sections into paragraphs; strip decoration.

## format/bullets-for-prose

**Strength:** contextual
**Looks like:** An argument split into bullets, losing `because`, `so`, and `unless`.
**Reader cost:** The reader has to rebuild the logic the bullets removed.
**Keep when:** A real list of parallel items, steps, or options.
**Direction:** Write the argument as sentences that carry the relations.

## lexical/tell-word

**Strength:** weak-alone
**Looks like:** A word from the language lists in the language references.
**Reader cost:** None by itself; lexical tells also age as fashions change.
**Keep when:** Always, alone. Technical meanings of a word are literal.
**Direction:** When the sentence is rewritten for a structural reason, ask what it was
meant to say. Never swap the word for a synonym.

## lexical/synonym-cycling

**Strength:** contextual; strong in technical and reference prose
**Looks like:** Varying the term for one concept for elegance. `Create a workspace. Each
project then gets its own environment.`, where `workspace` and `environment` name the same
thing.
**Reader cost:** The reader assumes a new term is a new thing and looks for the
difference.
**Keep when:** The terms name different things; literary prose where variation is
harmless.
**Direction:** One term per concept, verbs included. Use the term the source defines.

## lexical/calque

**Strength:** strong
**Looks like:** Normative errors, calques, and pleonasms that break the language norm. The
lists live in the language references; for Ukrainian they cover prepositional calques,
wrong verb collocations, calques from English, and pleonasms.
**Reader cost:** A reader who knows the norm stumbles on the phrase and trusts the text
less; some calques also blur the meaning.
**Keep when:** Quoted text only.
**Direction:** Use the normative form, and check that it keeps the meaning.

## register/officialese

**Strength:** contextual
**Looks like:** Bureaucratic register built from verbal nouns with empty verbs and from
formulaic links such as `utilize`, `in order to`, `prior to`. Ukrainian examples live in
the Ukrainian reference. `Prior to deployment, perform a verification of the config.`
**Reader cost:** The reader has to turn nouns back into actions, and the sentence grows
longer while hiding who does what.
**Keep when:** Legal, regulatory, and official documents where the register is required;
quoted text.
**Direction:** Rebuild the sentence around the verb. `Before you deploy, verify the
config.`

## syntax/passive-missing-agent

**Strength:** weak-alone; contextual when the agent is information the reader needs
**Looks like:** A passive that hides who acted. `The decision was made to delay the
release.`
**Reader cost:** Only when the reader needs to know who decided or who acts next.
**Keep when:** The agent is named in the sentence or the one before; the agent is unknown
or unimportant; UI copy conventions. A passive with a named agent is never a finding.
**Direction:** Name the agent only when the source names it; never invent one.
