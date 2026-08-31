# Create

Greenfield workflow: a surface that does not exist yet. Assumes `direction.md` has produced a
design read. Read `quality-gate.md` before writing code, and `anti-patterns.md` before committing
to a look.

## 1. Plan the design before writing code

Write a short plan first. It is prose, not a document; depth is a function of the mode and the
size of the surface. A single component needs three lines. A marketing page needs all four
sections below. The plan covers:

**Palette.** Four to six named colors with actual hex values and a stated role for each: surface,
raised surface, primary text, secondary text, accent, and any semantic colors the surface needs.
Naming the role prevents a palette from becoming decoration hunting for a use. Derive the colors
from the subject: what the product is about, what its world looks like, what its existing brand
already says.

**Typography.** The typefaces and the roles they serve. At minimum two distinguishable roles -
for example display and body, or body and interface. State the scale and the reason for the
ratio: tight for dense product work, wider for editorial. Every typographic choice should be
defensible from the subject rather than from habit.

**Composition.** How the surface is organised: the sections in order, what each one is for, and
where the eye is meant to go. A sketch is welcome in whatever form is fastest - a list, a text
outline, an ASCII sketch - but no particular form is required. What matters is that the layout
concept exists before the markup does.

**One signature idea.** Name the single thing this surface will be remembered for: a typographic
treatment, a structural device, a distinctive use of the product's own material, one authored
moment of motion. One. The rest of the surface stays quiet so that this one lands. Boldness spent
everywhere reads as noise, not confidence.

## 2. Critique the plan before building

Read the plan back and answer three questions honestly:

1. Could this plan describe any other product in the same category? If yes, the character is
   coming from the category rather than the subject. Go back to the subject.
2. Does the signature idea come from what this product actually is, or from a visual trend?
3. Does anything in the plan contradict the design read, the brief, or the surface mode?

Check the plan against `anti-patterns.md` at this point, while changing direction is still free.

## 3. Hero as a thesis

For Persuade and Experience surfaces, the first screen states one thing and states it well. It is
a thesis, not a template to fill: a headline that says something only this product could say,
enough supporting text to make it credible, and one primary action. Restraint pays here - a small
number of text elements, with generous space around them, outperforms a stack of competing
messages.

Operate and Read surfaces often have no hero at all. A dashboard opening with a marketing banner
is a defect, not a design. Do not manufacture a hero because the pattern is familiar.

## 4. Color dosage

Decide how much color the surface carries, as a deliberate choice rather than an accident of
accumulation. Useful positions, in ascending order:

- **Restrained** - a near-neutral surface with color reserved for action and status.
- **Committed** - one strong color used confidently across several elements.
- **Full palette** - several colors working as a system, each with a job.
- **Saturated** - color as the environment itself, backgrounds included.

Pick the position first and apply it consistently. Operate surfaces usually sit at restrained or
committed, because color there is carrying meaning that arbitrary decoration would dilute.

## 5. Build

Follow the plan. While building:

- Work with real content, or content as close to real as available. Placeholder prose hides
  layout failures that appear the moment real text arrives - too long, too short, missing.
- Respect the incumbent stack. Check what the project already has before introducing anything:
  framework, styling approach, component library, tokens, animation library, naming conventions.
- Verify a dependency exists before importing it. An import of a package that is not installed is
  a broken build, not a design decision.
- Use the official package rather than reimplementing a well-known component by hand, unless the
  project deliberately avoids the dependency.
- Cover the states a surface can actually reach: loading, empty, error, and the long-content case.

## 6. Honesty rules

- Anything approximated is labelled as approximated. A placeholder is called a placeholder.
- Numbers presented as facts come from real data. Invented precision such as a specific
  percentage or multiplier is either sourced or clearly marked as an example.
- If part of the brief was not built, say which part. Silence reads as completion.

## 7. Critique the result

After building, before reporting done:

- Compare against the design read line. Does the built surface do the one job it named?
- Run the applicable MUST items from `quality-gate.md`.
- Run the anti-default check in `anti-patterns.md`: is the aesthetic guessable from the category
  alone?
- Verify within the bounds set in SKILL.md: build fully, inspect desktop and mobile in one pass,
  fix in one batch, confirm at most once, stop.
