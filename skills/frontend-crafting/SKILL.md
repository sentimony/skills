---
name: frontend-crafting
description: You MUST use this when creating, redesigning, reviewing, or polishing a user interface - landing pages, product and dashboard screens, marketing surfaces, component work, visual and UX critique, and design-quality passes over existing frontend code. Not for driving a browser to verify that a local web app works, which belongs to web-debug.
metadata:
  author: Ihor Orlovskyi
  version: "1.1.0"
license: Apache-2.0
---

# Frontend Crafting

Design and build interfaces that come from the subject, not from a template. This file is a
router: it fixes the contract every workflow shares and points to the one reference file the
current request actually needs. Design rules live in the references, never here.

## Scope

Use this skill when the request is about how an interface looks, reads, or behaves:

- building a new page, screen, or component from a brief;
- reworking an existing surface, whether the change preserves the current design or replaces it;
- critiquing a UI and reporting what is wrong;
- refining a surface that is already broadly right.

Do not use it to drive a browser, capture screenshots, or debug a running local app; that is
`web-debug`. This skill also does not pick a framework, a hosting target, or a data layer.

## Core principles

1. **The subject supplies the character.** Typography, palette, rhythm, and imagery come from
   what the product actually is and who uses it. Generic character is the default failure mode,
   and no amount of styling covers it.
2. **Structure carries information.** Every panel, card, divider, and badge must encode something
   true about the content. Structure that exists to fill space is decoration wearing a layout.
3. **Ambition is a function of the surface.** A marketing page and an operations console want
   different amounts of risk. Mode detection decides this before any styling decision.
4. **Correctness and accessibility are absolute; taste is not.** Aesthetic rules are defaults with
   stated exceptions, never bans. Accessibility, semantics, and behavioral correctness do not bend.
5. **Plan, critique, build, critique.** Judge the intent before writing code and judge the result
   after. Both passes are cheap; a wrong concept rendered well is not.

## Mode detection

Announce both modes in one line before working. The announcement - and the design read it leads
to - belongs in the visible reply before the first file is written or edited, never only in
private reasoning: it is a commitment the requester checks the result against, and an unseen
commitment binds nothing. If the two readings of the request genuinely diverge, ask exactly one
question - never a questionnaire.

**Workflow** - what kind of change is being asked for:

| Workflow | The request is |
|---|---|
| create | A surface that does not exist yet, or one being written from scratch |
| redesign | An existing surface changing its visual or structural design |
| review | A judgement of an existing surface, with no code change |
| polish | An existing surface that is broadly right and needs refinement |

**Surface mode** - what the surface is for. Read the surface, not the product: a marketing site
can contain a documentation page, and a product can contain a pricing page.

| Mode | The surface exists to | Default posture |
|---|---|---|
| Persuade | Convince a first-time visitor to act | Authored risk allowed where the brief leaves an axis free |
| Operate | Let a returning user do work | Restraint by default; boldness needs a reason in the brief |
| Read | Deliver text a reader came for | Restraint by default; typography carries the design |
| Experience | Be the thing itself, not a route to it | Authored risk allowed; the concept is the product |

## Workflow routing

Read only the file the current work needs. Loading more than the request calls for costs context
and produces rules that fight each other.

- Read `references/direction.md` for any request that needs design intent: brief inference,
  the one-line design read, the surface modes in detail, and the optional reasoning axes. Create
  and redesign always start here. Review and polish read it only when the intent is unclear.
- Read `references/create.md` when building a surface that does not exist yet.
- Read `references/redesign.md` when changing the design of a surface that already exists, in
  either direction: preserving the current design language or replacing it.
- Read `references/review.md` when the request is a critique, an audit, or a design review.
- Read `references/polish.md` when refining a surface that is already broadly right, including
  requests phrased as an intent such as bolder, quieter, better typeset, or more delightful.
- Read `references/quality-gate.md` before building a new surface or substantially modifying an
  existing one, and before writing any review findings. It is the technical floor: accessibility,
  semantics, focus, forms, motion, overflow, performance, states, and copy. A small local
  refinement does not need it; `polish.md` carries its own compact pre-flight.
- Read `references/anti-patterns.md` when a design decision feels familiar and you want to know
  whether that is convergence or a defect, and when a review needs the catalogue of default
  failures. It is the single source of truth for anti-default material.

## Precedence rules

When two considerations collide, resolve in this order.

1. **The brief wins.** An explicit instruction from the user overrides any default in this skill,
   including its aesthetic preferences. Quiet constraints count as brief: accessibility-first
   mandates, public sector work, regulated industries, and products for children all outrank
   visual ambition without being stated as design instructions.
2. **The incumbent stack wins.** Before introducing a dependency, a token, or a pattern, check
   what the project already uses: framework, styling approach, design system, component library,
   design tokens, animation library, naming conventions, and copy conventions such as
   capitalization. Match them. A new dependency needs a reason the existing one cannot cover.
3. **Preserve and redesign never mix silently.** Refinement keeps the existing design language;
   redesign replaces it. Splitting the difference produces a surface that is neither. If the right
   answer is the other one, say so and get agreement before switching.
4. **No universal aesthetic bans.** Absolutes are reserved for correctness and accessibility.
   Every aesthetic rule here is a default that a brief can earn back, and each one states when
   it legitimately does not apply.

## Framework neutrality

The core of this skill works for Vue and Nuxt, React and Next, Svelte and SvelteKit, and plain
HTML, CSS, and JavaScript. Rules are written in terms of HTML, CSS, and DOM behavior. Where an
example is specific to one framework or one styling approach it is labelled as such, for instance
"Example (React)", and is illustration rather than requirement.

## Bounded verification

Visual checking is bounded so it cannot become an open loop:

1. Build the surface completely first. Do not verify partial work.
2. Inspect desktop and mobile together in one batched pass.
3. Fix everything found in one batch.
4. Optionally confirm once that the batch landed. Then stop.

A review-only request never modifies code. Findings are reported, not applied, unless the user
asks for the fix afterwards.

## Definition of done

- Workflow and surface mode were announced, and the work matches them.
- Intent is traceable to the subject: someone could name why this looks the way it does.
- Every requirement in `references/quality-gate.md` that applies at MUST level holds, including
  keyboard operability and visible focus.
- Loading, empty, and error states exist wherever the surface can reach them.
- Desktop and mobile were both inspected, in one pass, and the findings were fixed.
- Nothing was silently replaced that the request only asked to refine.
- What was approximated, faked, or left for later is stated plainly rather than implied as done.
