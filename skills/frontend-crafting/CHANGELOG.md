# Changelog

All notable changes to the `frontend-crafting` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.2.0] - 2026-09-01

### Added
- A numbered Step 0 in SKILL.md that fixes the announcement format and requires the line before
  the first file write and before any finding or verdict, so a review workflow that writes no
  files is still covered
- Repository-wide announcements name the dominant surface modes present, with per-surface modes
  deferred to the surface table of the report
- Prior-review guidance in `review.md`: find earlier audits of the same surfaces, report their
  findings as resolved or still open, and inherit established measurements with a reference
- An anti-pattern for external CDN resources added to a brief that asked for plain HTML and CSS
  without naming them among the approximations

### Changed
- User impact is now required at every severity, and a justification for a lowered severity no
  longer substitutes for it
- The workflow table states which side of the polish/redesign boundary a surface that works but
  looks unfinished falls on, because the earlier wording admitted both readings
- The focus and scroll-padding requirement in `quality-gate.md` names `scroll-padding-block` as
  the check when a surface has a sticky element

## [1.1.0] - 2026-09-01

### Added
- Repository-wide review guidance that groups routes and components into surfaces, permits
  multiple surface modes, and requires the report to declare scope, sampling, and exclusions
- A clean-baseline path that records meaningful zero results quantitatively before shifting the
  review toward consistency, repeated recipes, and cross-surface drift
- Source-verification rules for search findings and delegated exploration, including independent
  recounting before a pattern is reported as systemic
- Mixed-language quality-gate checks for element-level `lang` and unintended partial translations

### Changed
- The review delivery checklist now requires coverage evidence, primary-source verification, and
  independently measured systemic counts

## [1.0.0] - 2026-09-01

Initial release. An original skill informed by four upstream sources: the `frontend-design`
skill from `anthropics/skills` (Apache-2.0), `design-taste-frontend` from `leonxlnx/taste-skill`
(MIT), `web-design-guidelines` from `vercel-labs/agent-skills` together with the rules in
`vercel-labs/web-interface-guidelines` (MIT), and `impeccable` from `pbakaus/impeccable`
(Apache-2.0). No substantial verbatim text was carried over; see `references/attribution.md`
for what each source contributed and for the license analysis.

### Added
- `SKILL.md` as a thin router: scope, five core principles, mode detection, workflow routing,
  precedence rules, framework neutrality, bounded verification, and a compact definition of done.
  Design rules live in the reference files so a request loads only what it needs
- Four workflows - create, redesign, review, polish - with refinement intents such as bolder,
  quieter, typeset, and delight living inside polish rather than as separate entry points
- Four surface modes - Persuade, Operate, Read, Experience - detected from the surface rather
  than the product, with ambition treated as a function of the mode
- Precedence chain: the brief wins, then the incumbent stack wins, preserving and replacing are
  never mixed silently, and no aesthetic rule is a universal ban
- Framework neutrality: the core is written in terms of HTML, CSS, and DOM behavior and works for
  Vue and Nuxt, React and Next, Svelte and SvelteKit, and plain HTML, CSS, and JavaScript;
  framework-specific material is labelled as an example
- Bounded visual verification: build fully, inspect desktop and mobile in one batched pass, fix in
  one batch, confirm at most once, stop. Review-only requests never modify code
- `references/direction.md` - brief inference from six signals, the one-line design read, the
  single-question rule, three optional reasoning axes without numeric thresholds, the four surface
  modes in detail including the product slop test, and theme choice derived from the scene of use
- `references/create.md` - greenfield workflow: plan with palette, typography, composition, and one
  signature idea; plan critique before code; hero as a thesis for Persuade and Experience; color
  dosage; honesty rules
- `references/redesign.md` - three kinds of change, discovering the incumbent design truth
  including the search baseline, what never changes silently, modernization levers ordered by risk,
  and visual authority treated as evidence rather than a filename
- `references/review.md` - visual critique reported separately from technical findings, P0-P3
  severity with definitions, finding format with location and user impact, systemic patterns before
  isolated defects, required positive findings, a guard against P3 noise, and the copy self-audit
- `references/polish.md` - the rule that polish is never a concealed redesign, eight refinement
  intents, triage order, drift classification with the extraction threshold of three occurrences,
  motion motivation and duration guidance, browser surfaces, the delight test, and a compact
  pre-flight for small refinements
- `references/quality-gate.md` - the vendored technical floor classified MUST, SHOULD, and
  CONTEXTUAL, covering semantics, accessible naming, contrast, keyboard operability and focus,
  forms, motion, interactive states, layout stability, performance, safe areas,
  internationalization, application state and deep linking, theming, and content and copy
- `references/anti-patterns.md` - the single source of truth for anti-default material: the
  anti-default self-check, a dated example of current defaults marked as a snapshot, and thirteen
  categories where each entry is stated as default, rationale, and legitimate exceptions rather
  than as a ban
- `references/attribution.md` - maintainer-facing record of the four sources with commit hashes,
  what each contributed conceptually, the nature of the adaptation, and the license analysis
  concluding that no NOTICE file is required
