# Anti-Patterns

The single source of truth for default failures. Every entry here is a **diagnostic signal**, not
a ban: it names a choice that is usually a symptom of pattern-filling rather than design, explains
why, and states when it is legitimately the right answer.

Read an entry as a question - "is this deliberate, or is this what appeared by default?" - and
answer it from the brief and the subject. A brief can earn back any entry in this file. Nothing
here overrides a MUST in `quality-gate.md`, and where an entry also breaks a MUST, the MUST wins.

## The anti-default check

Before committing to a look, ask one question: **could someone guess this aesthetic from the
product category alone, without knowing anything about this product?** If yes, the character came
from the category rather than the subject, and the surface will be indistinguishable from its
neighbors however well it is executed.

The check is a mechanism, deliberately not a list of banned fonts or colors. Such lists date
badly: within a year they forbid what nobody uses anymore and miss whatever became the new
default. The question survives the change of defaults; a list does not.

### A dated example of what "default" means

As of 2026, these recur often enough to be recognizable as machine-generated defaults rather than
design decisions:

- a warm off-white background around `#F4F1EA` with a high-contrast serif display face and a
  terracotta accent;
- a near-black background with a single saturated neon accent and glowing borders;
- a purple-to-blue gradient, most often behind a centered hero over a dark mesh background;
- a broadsheet pastiche: heavy editorial serif, rules between columns, oversized drop caps.

**This list is a snapshot taken at the 1.0.0 release, not a rule.** Its purpose is to make
"default" concrete. When these look dated, the question in the section above is still the working
instrument; the examples are not.

## Generic AI composition

**Default:** a centered hero over a gradient or mesh background, followed by three equal cards,
followed by a logo strip, followed by an alternating text-and-image sequence, followed by a
centered call to action.

**Why it is usually wrong:** each block is a container waiting for content rather than a shape
derived from the content. The arrangement is what appears when nothing about the subject informed
the layout, and it is why so many pages read as the same page.

**Legitimate exceptions:** conventions carry real value where a visitor is scanning quickly and
comparison matters, and a well-executed conventional page beats a badly executed unusual one.
Choose the convention deliberately, and let the content decide section shape and count.

## Meaningless decorative structure

**Default:** panels, dividers, badges, borders, and pill labels that encode nothing.

**Why it is usually wrong:** structural elements are a promise that something is grouped,
separated, or categorized. When the promise is empty, structure becomes visual noise that the eye
still has to process.

**Legitimate exceptions:** deliberate ornament in an Experience surface where the ornament is the
point; rhythm devices in editorial layouts that guide the reading rather than imply grouping.

## Repetition without intent

**Default:** every section built from the same device - an eyebrow above every heading, the same
zigzag alternation repeated down the page, sections that share one layout, a grid whose cell count
was chosen to fill the grid.

**Why it is usually wrong:** repetition of a device is what template-filling looks like. An eyebrow
is legitimate when it encodes something true - a category, a step number, a section name - and is
filler when it exists because the pattern has a slot for it.

**Legitimate exceptions:** systematic repetition is correct where the items are genuinely parallel,
which is most of Operate: a settings page of identical rows is well designed, not repetitive. There
is no numeric quota here; the question is whether the repetition reflects the content's structure.

## Card monoculture

**Default:** every group of content wrapped in a rounded, shadowed, bordered box.

**Why it is usually wrong:** a card claims that its contents are a discrete, separable object at a
distinct elevation. Applied to everything, the claim becomes meaningless and the page turns into a
field of boxes with no hierarchy between them.

**Legitimate exceptions:** use a card when elevation communicates real hierarchy or when the
contents genuinely are a discrete object - a record, a product, a selectable item.

**Nested cards are close to absolute.** A card inside a card, with two shadows and two radii,
almost always means the hierarchy was not resolved. The visible symptoms are a child radius equal
to or larger than its parent's and stacked shadows. If a nested card is genuinely required, the
inner container should drop its elevation and keep only the grouping.

## Unnecessary glass, gradient, and glow

**Default:** frosted-glass panels, gradient text, colored glows, and heavy blur used as surface
treatment.

**Why it is usually wrong:** each of these costs contrast and legibility, and each is applied far
more often as a substitute for hierarchy than as a solution to one. Gradient text in particular
makes the most important line on the page the hardest to read.

**Legitimate exceptions:** glass over genuinely varied content, where translucency communicates
layering, such as a floating toolbar above scrolling media; a gradient that carries brand meaning
in one deliberate place; a glow representing a real state such as activity or focus.

## Arbitrary typography

**Default:** a display face chosen because it is currently fashionable, a scale with no ratio, a
second family with no role, or a monospaced face used to signal technicality.

**Why it is usually wrong:** typography is the largest single contributor to how a surface reads,
so an arbitrary choice is the most expensive arbitrary choice available. Monospace deserves its own
mention: it means machine-readable content - code, identifiers, aligned numbers - and using it as
costume for a non-technical product signals nothing except that the costume was available.

**Legitimate exceptions:** monospace is correct for code and identifiers and legitimate as a
deliberate stylistic register when the subject really is technical. A fashionable face is fine when
it fits the subject; the flag is choosing it because it is fashionable.

## Fake technical aesthetics

**Default:** terminal chrome around non-terminal content, fake code blocks with invented output,
scan lines, a blinking cursor on marketing text, a fake status indicator that is always green.

**Why it is usually wrong:** it borrows credibility the product has not demonstrated, and it is a
short step from a fake status indicator to an actively misleading one.

**Legitimate exceptions:** a real terminal for real terminal output; genuine code examples; a
status indicator wired to real status.

## Excessive and decorative motion

**Default:** every section fading in on scroll, parallax on backgrounds, elements sliding from
alternating directions, a page-load choreography before the content is readable.

**Why it is usually wrong:** motion that is not motivated delays the content and turns scrolling
into a performance. Scroll-triggered entrances also break the moment a user scrolls quickly, and
they cost anyone with a motion sensitivity.

**Legitimate exceptions:** Experience surfaces where the motion is the work; one authored moment on
a Persuade surface; feedback motion anywhere. The four motivations that justify motion are in
`polish.md`, and the technical requirements are in `quality-gate.md`.

## Design-system drift

**Default:** hardcoded colors beside a token system, one-off spacing values, a fourth button
variant, a locally reimplemented component that already exists in the library.

**Why it is usually wrong:** each instance is small and the aggregate is a system nobody trusts,
after which every new piece of work is a fresh decision.

**Legitimate exceptions:** a deliberate exception, made once, for a genuinely exceptional surface,
and stated as an exception. See the drift classification in `polish.md` for fixing at the right
level.

## Unannounced external resources

**Default:** a webfont from a font CDN, an icon set from a script tag, a reset stylesheet pulled
from a third-party host, added to a brief that asked for plain HTML and CSS with no build step.

**Why it is usually wrong:** "no build step" and "no framework" are not the whole of the
constraint the requester meant. An external resource adds a network dependency, a privacy
consideration and an offline failure mode to a project that was scoped to be self-contained. It is
not banned, but it is a decision the requester never made.

**Legitimate exceptions:** the brief names the resource or the host; or the resource is genuinely
needed and is stated plainly among the approximations, alongside the placeholder imagery and the
invented copy, so the requester can accept or remove it.

## Placeholder content and fake claims

**Default:** lorem ipsum, stock imagery unrelated to the product, invented testimonials, logo
strips of companies that are not customers, precise-looking numbers with no source.

**Why it is usually wrong:** placeholder content hides layout failures that real content exposes,
and fabricated numbers or endorsements are a credibility problem rather than a design one. A
figure such as a specific percentage improvement reads as evidence; if it is invented, the surface
is making a false claim.

**Legitimate exceptions:** clearly marked example data in a prototype or a demo; illustrative
figures that are explicitly labelled as examples.

## Inaccessible interaction

**Default:** a clickable element that is not a button or a link, hover-only affordance, focus
outlines removed for tidiness, contrast reduced for a softer look, an icon-only control with no
name.

**Why it is usually wrong:** each of these removes the interface for some users entirely. This
category is where diagnostics stop and requirements start.

**Legitimate exceptions:** none. These are MUST items in `quality-gate.md` and no brief overrides
them. Replacing a default focus ring with a clearly visible custom one is not an exception; it is
the correct implementation.

## Inconsistent and missing states

**Default:** only the happy path is designed. No empty state, no loading state, no error state,
disabled styling that looks identical to enabled, hover states on some controls and not others.

**Why it is usually wrong:** the happy path is the state a user sees least often over time. Empty
is the first state of every new account, and error is the state a user remembers.

**Legitimate exceptions:** a state that genuinely cannot be reached does not need a design. Verify
that it cannot be reached rather than assuming it.

## Responsive failure

**Default:** a desktop layout squeezed into a phone width; horizontal overflow; hit targets too
small for touch; a data table that becomes unreadable; text that stays at its desktop measure.

**Why it is usually wrong:** most surfaces are seen on a phone at least as often as on a desktop,
and the mobile view is usually the one that was verified least.

**Legitimate exceptions:** genuinely desktop-only tools - a professional editor, a dense
operations console - can prioritize the desktop layout, provided that is a stated decision rather
than an untested assumption, and the surface still degrades legibly.
