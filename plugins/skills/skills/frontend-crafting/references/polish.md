# Polish

Refining a surface that is already broadly right. The concept stays; the execution improves.
For a substantial modification rather than a refinement, read `quality-gate.md` as well; a small
local refinement is covered by the pre-flight at the end of this file.

Step 0 in SKILL.md applies before anything below.

## The rule that governs this workflow

**Polish is refinement, never a concealed redesign.** If the underlying concept is wrong, polish
cannot save it. Say so directly, explain why, and recommend a redesign. Quietly replacing the
design language while calling it polish gives the user a result they did not ask for and cannot
review, and it is the single most common failure of this workflow.

## Refinement intents

Requests arrive as an intent rather than a specification. These are modes within polish, not
separate workflows; each still respects the existing design language.

| Intent | The user wants | What actually changes |
|---|---|---|
| bolder | More presence and confidence | Type scale contrast, weight, color commitment, spacing at the focal point |
| quieter | Less noise, more calm | Fewer competing elements, reduced color and decoration, more space, softer motion |
| typeset | Better reading and typographic craft | Scale ratio, measure, line height, rhythm, hyphenation, optical alignment |
| layout | Better structure and flow | Grouping, alignment, order, spacing rhythm, responsive behavior |
| colorize | Color used with more intent | Palette roles, contrast, semantic color, dosage |
| animate | Motion added or corrected | Transitions on state changes, entrances, feedback, with the motivation test below |
| distill | Less of everything, sharper | Removing elements, collapsing variants, shortening copy |
| delight | One memorable moment | A single authored detail, tested against the delight test below |

An intent is a direction, not a licence to change scope. "Bolder" means bolder within this design,
not a new design that is bolder.

When the request names a specific side, edge, element, or region, the change stays within what
was named. A matching adjustment on the opposite side looks like hygiene, but it is a scope
extension: propose it, do not apply it. The same holds for a threshold, counter, or badge the
brief did not ask for: it is a product decision to raise, not a refinement to apply.

## Triage order

Work in this order. Each level is more discretionary than the one before, and stopping early is
a legitimate outcome.

1. **Broken tasks.** Anything a user cannot do: dead control, trapped focus, unreachable state,
   layout collapse at a common viewport. Polish never proceeds over a broken task.
2. **Missing states.** Loading, empty, error, disabled, long-content. Absent states are the most
   common gap in surfaces that otherwise look finished.
3. **Hierarchy and system drift.** Attention landing in the wrong place; spacing, type, and color
   that have wandered away from the system.
4. **Visual inconsistencies.** One-off values, misalignment, inconsistent radii and shadows,
   mismatched icon weights.
5. **Code tidiness.** Dead styles, duplicated variants, unused tokens. Last, and only if the
   levels above are clear.

## Classify drift before fixing it

When something is inconsistent, name what kind of inconsistency it is and fix it at the narrowest
correct level. Fixing a local defect globally is how a polish pass becomes a redesign.

| Kind | Signal | Fix at |
|---|---|---|
| Missing token | The value is right but hardcoded, and it recurs | The token or theme layer |
| One-off implementation | A component reimplements what a shared component does | The shared component, by adding a variant |
| Conceptual mismatch | The element is the wrong element for the job | The component choice, after saying so |
| Local defect | One instance is wrong; the system is fine | That one instance |

**Extraction threshold.** Extract a token, variant, or component when the same decision appears
three or more times with the same intent. Below that, leave the duplication. Premature abstraction
is more expensive than duplication, because it fixes a pattern before the pattern is known.

## Motion

**Motion must be motivated.** Every animation answers one of four questions, and an animation that
answers none is removed:

1. Does it clarify hierarchy or spatial relationship?
2. Does it carry a narrative beat the surface needs?
3. Is it feedback for something the user did?
4. Does it explain a change of state?

**Motion claimed is motion shown.** Either the motion is really implemented or the surface is
honestly static. A transition described in a comment, an entrance that never fires, an interactive
element that only looks interactive - each is worse than no motion at all.

Duration is a starting point, not a rule. Microfeedback lands around 100 to 150 milliseconds,
standard transitions around 150 to 300, entrances and larger movements around 300 to 500, and
deliberate narrative moments up to roughly 800. Exits are faster than entrances: a user leaving
has already decided. Every duration is adjustable against the surface mode - Operate stays at the
short end.

Technical requirements for motion, including reduced-motion support and which properties are safe
to animate, are in `quality-gate.md`.

## Browser surfaces

Cheap details that read as finish, because most surfaces leave them at the browser default:

- text selection colors that belong to the palette;
- caret color in inputs;
- scrollbar treatment where the platform allows it, without harming usability;
- focus rings that match the design and remain clearly visible;
- link underlines with considered offset and thickness;
- tabular figures for numbers in tables and any number that changes in place;
- consistent icon optical weight against adjacent text.

## The delight test

A delightful moment must be specific enough that a neighboring product could not use it unchanged.
If it could be lifted into any other surface in the category, it is a generic effect, not delight.
One such moment per surface; a second one competes with the first.

## Pre-flight for a small refinement

For a local refinement that does not add or restructure a surface, this checklist replaces
`quality-gate.md`:

- The change stayed inside the existing design language.
- Interactive elements still show a visible focus ring and remain reachable and operable by
  keyboard.
- Contrast still holds for text and for interactive boundaries.
- Motion added or changed respects the reduced-motion preference and animates only transform and
  opacity.
- Hover, active, focus, disabled, loading, empty, and error states still render correctly.
- Nothing changed layout stability: no new content shifting after load.
- The result was checked at desktop and mobile widths in one pass.
