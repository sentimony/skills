# Redesign

Changing the design of a surface that already exists. The existing surface holds decisions,
constraints, and accumulated knowledge that are invisible until someone breaks them. Read
`quality-gate.md` before editing, and `anti-patterns.md` before choosing a new direction.

Step 0 in SKILL.md applies before anything below.

## 1. Establish which kind of change this is

Three kinds, announced before touching anything.

| Kind | What changes | What is kept |
|---|---|---|
| Greenfield | Everything | Nothing, because nothing exists |
| Redesign, preserving | Execution within the existing design language | The visual language, the structure, the vocabulary |
| Redesign, replacing | The design language itself | Product truth, functionality, constraints, useful structure |

Never split the difference between preserving and replacing. Half-replaced design languages
produce surfaces where two eras sit next to each other and neither reads as intentional. If the
request says refine but the concept underneath is wrong, say so and get agreement before
replacing.

**Visual authority is evidence, not a filename.** A file being new, small, or scaffold-shaped does
not make the work greenfield. If the rendered surface already carries deliberate design decisions -
a considered palette, a real type scale, established components - it is an incumbent design, and
this workflow applies even if the code looks provisional.

## 2. Discover the incumbent design truth before editing

Audit before touching. Reading the existing surface is cheaper than restoring what you removed.

- **Design language.** Palette and where each color is used, typefaces and scale, spacing rhythm,
  corner radii, elevation and shadow use, iconography, motion conventions.
- **System layer.** Design tokens, theme files, utility configuration, component library, variants
  already defined. Fixing an inconsistency in the token beats fixing it in one component.
- **Structure.** Information architecture, navigation, the grouping that already exists. Structure
  that works is knowledge about the users, not scaffolding.
- **Constraints.** Browser and device targets, performance budgets, accessibility commitments,
  content management limits, whatever the templating layer can actually express.
- **Search and links baseline.** Existing URLs, page titles, meta descriptions, headings,
  structured data, canonical links, image alt text. A redesign that silently changes URLs or
  heading structure is the most expensive redesign failure available, and it is invisible in a
  screenshot.
- **Behavior.** Analytics hooks, tracked events, form endpoints, feature flags, anything wired to
  a selector or an identifier in the markup.

## 3. What never changes silently

These can change, but only with the change stated explicitly and agreed:

- URLs, route paths, and slugs;
- navigation labels users have learned;
- form field names and identifiers, including anything a backend or an integration reads;
- the logo, its lockup, and its clear space;
- legal, compliance, and policy text;
- pricing, plan names, and any published commitment;
- documented keyboard shortcuts and established interaction contracts;
- heading text that search engines and deep links depend on.

Changing any of these as a side effect of a visual change is a defect, however good the new
design looks.

## 4. Modernization levers, ordered by risk

When a surface needs to feel current without being replaced, work up this ladder and stop as soon
as the surface is right. Each rung is more visible, more expensive, and more likely to break
something than the one before.

1. **Typography.** Type scale, weights, line height, measure, letter spacing. The cheapest change
   with the largest perceived effect.
2. **Spacing rhythm.** Consistent spacing scale, section padding, alignment discipline. Most dated
   surfaces are inconsistent rather than ugly.
3. **Color.** Refresh values within the existing roles, improve contrast, reduce the count of
   near-duplicate grays. Keep the roles; change the values.
4. **Motion.** Add or calm transitions on state changes. See `polish.md` for what earns motion.
5. **Recomposing a key section.** Restructuring the hero or the primary layout region. This is
   where preserving ends and a design decision starts.
6. **Replacing a block.** New component, new structure, new content model. Highest risk; needs the
   same planning a create workflow needs, and usually a stated agreement.

## 5. Redesign that preserves

Start from a reading of the existing surface, not from a blank baseline. The current design is the
reference: match its variance, its density, and its motion posture, then execute better within
them. Success is a surface that looks like the same product on a good day.

Concretely: use the existing tokens, extend the existing scale rather than introducing a parallel
one, reuse existing components before creating new ones, and match the existing copy conventions
including capitalization. New patterns need a reason the existing ones cannot cover.

## 6. Redesign that replaces

Everything in `create.md` applies, with one addition: the product truth survives. Functionality,
content, constraints, and structure that works are carried forward. Replacing the design language
does not license dropping a feature, losing content, or discarding an information architecture
that reflects how the product actually works.

Run the plan and its critique from `create.md` before writing code, then verify within the bounds
in SKILL.md.

## 7. Before reporting done

- The kind of change performed is the kind that was agreed.
- Nothing on the never-changes-silently list moved without being stated.
- The search and links baseline is intact or its changes are listed.
- Tokens, components, and conventions were extended rather than duplicated.
- Applicable MUST items in `quality-gate.md` hold on the changed surface.
