# Direction

The shared entry point for design work. It turns a request into a stated intent cheaply, before
any layout or styling decision is made. Create and redesign always pass through here. Review and
polish come here only when the intent behind the surface is unclear.

## 1. Infer the brief before asking for it

Most requests carry more direction than they appear to. Read the request and the repository for
six signals before asking anything:

1. **Surface type.** Landing page, pricing page, dashboard, settings screen, docs page, form,
   marketing site, editorial piece, portfolio, interactive piece.
2. **Vibe words.** Adjectives the user used, however casual: clean, serious, playful, premium,
   technical, warm, brutal, quiet. These are direction, not decoration.
3. **References.** Named products, screenshots, links, or a phrase like "similar to X". A named
   reference is the strongest signal available and outranks your own preference.
4. **Audience.** Who is on the other side: a first-time visitor, a paying customer mid-task, an
   internal operator, a developer evaluating an API, a reader.
5. **Brand assets.** Existing logo, colors, fonts, tone of voice, screenshots, design tokens,
   an existing component library. Anything already in the repository is an asset.
6. **Quiet constraints.** Constraints implied rather than stated: accessibility-first contexts,
   public sector, healthcare, finance, regulated industries, products for children, low-bandwidth
   or low-end-device audiences. These outrank visual ambition and are rarely spelled out.

## 2. Write the design read

State the intent in one line before working. This is the cheapest artifact in the skill and the
one that makes everything after it checkable.

Format: **subject - audience - surface mode - the one job this surface has - the character it
should carry.**

Example: "Incident timeline for on-call engineers - Operate - make the current state legible in
five seconds - dense, calm, no ornament."

The line is a commitment. If the built surface does not match it, one of the two is wrong.

## 3. Ask at most one question

Ask a question only when two readings of the request genuinely diverge and the divergence would
change the design itself rather than its details. Ask exactly one, phrase it as a choice between two
concrete options, and proceed on a stated assumption if there is no answer available.

Never open with a questionnaire. Requirements gathering is a different activity, and a request
for an interface is not a request for an interview.

## 4. Optional reasoning axes

Three axes help talk through intent. They are aids, never measurements: no rule in this skill has
a numeric threshold on them, and no decision should be justified by a number on a scale.

- **Variance** - how much the layout departs from the expected shape of its category. Levels:
  conventional, varied, unconventional.
- **Motion intensity** - how much the surface moves. Levels: still, functional, expressive.
- **Information density** - how much is on screen at once. Levels: airy, balanced, dense.

Naming a level makes an intent arguable. Persuade and Experience surfaces can defend varied or
unconventional layouts; Operate surfaces usually land conventional and dense, and a departure
needs a reason from the brief.

## 5. Surface modes in detail

The mode belongs to the surface, not to the product. Detect it from what the surface is for.

### Persuade

A visitor who does not yet know the product decides whether to care. Hierarchy is steep: one
claim dominates and everything else supports it. This is where an authored, memorable idea earns
its cost, provided the brief leaves an axis free. Copy is doing as much work as layout.

Failure mode: a page that is beautiful and says nothing specific about the product.

### Operate

A returning user is doing work and the interface is the tool, not the destination. Defaults:

- one typeface, used across the whole surface;
- a fixed spacing and type scale, with a tighter ratio than editorial work uses;
- short motion, in the range of roughly 150 to 250 milliseconds, used only for feedback and state;
- no page-load choreography; the operator arrived to do something;
- reach for a panel, a drawer, or an inline expansion before reaching for a modal.

Failure mode is not flatness. The **product slop test**: a product surface fails when it has
strangeness without purpose - a decorative gradient behind a data table, an animated entrance on a
row of numbers, a card wrapping something that is not a discrete object. Ask of each unusual
element: what does a user learn or do because of this? No answer means remove it.

### Read

Someone came for the text. The design's job is to get out of the way and stay legible for a long
session: measure, line height, and vertical rhythm carry the work. Typography choices are the
design; almost everything else is restraint. Long-form surfaces earn generous space in a way
Operate surfaces do not.

Failure mode: styling that competes with the reading.

### Experience

The surface is the point: an interactive piece, a showcase, a deliberate moment. The concept
governs, motion is allowed to be expressive, and convention is a starting point rather than a
constraint. This mode still owes accessibility everything the others owe; expressiveness is not
an exemption from keyboard operability or reduced-motion support.

Failure mode: an effect stack with no idea underneath it.

## 6. Deliberate risk is permitted, never required

When the brief leaves an axis free and the mode allows it, an authored risk is legitimate and
often the difference between a competent surface and a memorable one. It is a permission, not an
obligation. A brief that specifies its direction is not an invitation to exceed it, and a
conservative result that fits the brief is a correct result.

## 7. Choose a theme from the scene of use

Light, dark, or both is a design decision derived from where and how the surface is used: who is
looking, in what environment, at what time, on what device, and next to what other tools. A
tool used in a dim studio and a public information page in daylight want different answers.

There is no default requirement for a dark theme. What is required is that whatever themes exist
are technically correct: adequate contrast in each, no hardcoded colors that break the other one,
and the browser told which themes are supported. See `quality-gate.md`.

## 8. Then choose the workflow file

With the design read written, continue to `create.md`, `redesign.md`, `review.md`, or
`polish.md`. Before checking whether familiar-looking choices are convergence or a defect, read
`anti-patterns.md`.
