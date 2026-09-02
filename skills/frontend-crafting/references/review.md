# Review

Critiquing an existing surface. Read `quality-gate.md` for the technical layer and
`anti-patterns.md` for the default failures before writing findings.

Step 0 in SKILL.md applies before anything below.

## The rule that governs this workflow

**A review does not modify code.** Findings are reported, with the remediation described, and
nothing is applied. If the user asks for fixes afterwards, that is a separate turn under
`polish.md` or `redesign.md`. Fixing while reviewing destroys the artifact the user asked for and
hides the reasoning behind a diff.

## Reviewing a whole codebase

A repository-wide review is a collection of surface reviews, not one oversized surface. Before
the first finding:

1. Map routes and screens into distinct surface groups. Record shared layouts and components
   separately, with the surface groups that consume them.
2. Assign a surface mode to each surface group. A repository can contain Operate, Read, and
   Persuade surfaces at the same time; do not force one dominant mode onto exceptions. Review a
   shared primitive in each materially different consumer mode.
3. Declare the scope and sampling method in the report. Name whether coverage came from every
   relevant file, representative routes and shared primitives, targeted searches followed by
   source inspection, or a combination.
4. State material exclusions and why they were excluded, such as redirect-only routes with no UI.

Coverage claims need evidence appropriate to their scale. Counts such as "0 of 212 components" or
"65 of 70 pages" make a repository-level claim inspectable. A search hit starts an investigation;
it does not prove a finding.

## Prior reviews in the repository

A repository that has been reviewed before carries that history in files - `docs/audits/`,
`docs/reviews/`, dated markdown next to the code. Look for reviews of the same surfaces before
starting, and use what they establish:

1. **Check their findings and report the outcome.** A previous finding that is now fixed and one
   that is still open are both legitimate findings, and the pair tells the reader whether the last
   review changed anything. A still-open P0 from three months ago is a stronger signal than the
   same defect reported fresh. Resolved findings feed the clean baseline described below.
2. **Inherit established thresholds and measurements with a reference** rather than measuring
   again, and name the source in the sampling method: "contrast values inherited from
   `docs/audits/2026-05-14-accessibility.md`, unchanged tokens". Re-measure only what the code has
   changed since.
3. **Do not re-report a prior finding as new.** Repeating it without naming the earlier review
   inflates the report and hides that the defect has been known and unaddressed.

## Output shape: two layers, kept apart

Report visual and experiential critique separately from technical findings, each under its own
heading - a single interleaved list is a format failure even when every finding is individually
sound. They are different kinds of claim - one is judgement grounded in intent, the other is
verifiable against a standard - and merging them lets a matter of taste borrow the authority of an
accessibility violation.

### Layer 1: Visual and experience critique

Judgement about intent and craft. Cover:

- **Concept.** Does the surface communicate what it is for? Could this design belong to any
  competitor unchanged?
- **Hierarchy.** Does attention land where the surface's job requires? Is there one clear
  primary action, or several competing ones?
- **Typography.** Scale, measure, rhythm, and whether the choices are defensible from the subject.
- **Color.** Roles, consistency, and whether color carries meaning or decorates.
- **Space and composition.** Consistency of rhythm, alignment discipline, density against mode.
- **Motion.** Whether each moving thing is motivated, and whether motion claimed is motion shown.
- **Copy.** See the copy self-audit below.
- **Fit to mode.** A Persuade page reviewed as if it were an Operate console produces nonsense
  findings. State the mode you are reviewing against.

### Layer 2: Technical findings

Verifiable defects against `quality-gate.md`: accessibility, semantics, focus and keyboard
operability, forms, motion hygiene, overflow, images and layout stability, performance, states,
theming, and internationalization. Each of these is checkable rather than arguable, and each cites
the requirement it fails.

## Finding format

One entry per finding, grouped by file, terse enough to scan. Every reported finding carries every
field below, P3 included - a finding too small to state its location and impact is too small to
report:

- **Location** - `path/to/file.css:142`, or the surface region when there is no file.
- **Issue** - what is wrong, in one sentence.
- **Severity** - P0 to P3, defined below.
- **User impact** - who is affected and how. A finding without an impact is a preference. This
  field is required at every severity, P0 to P3 alike, and it does not weaken as the severity
  drops. Explaining why a finding was rated lower than it first looked is a separate statement:
  it justifies the level, it does not describe who is affected, and it never stands in place of
  the impact.
- **Standard** - for technical findings, the requirement violated.
- **Remediation** - the specific change, described rather than applied.

## Severity

| Level | Meaning | Examples |
|---|---|---|
| P0 | Blocking. The surface is unusable for someone, or actively wrong. | Keyboard trap, unlabelled icon-only control, destructive action with no confirmation or undo, contrast failure on primary text, broken layout at a common viewport |
| P1 | Major. Real damage to usability or credibility, but the surface functions. | Missing error state, hierarchy that hides the primary action, form that loses input, motion with no reduced-motion path |
| P2 | Minor. Noticeable inconsistency or friction. | Spacing drift across sections, one-off component variant, inconsistent capitalization, weak empty state |
| P3 | Polish. Refinement that raises quality without fixing a defect. | Optical alignment, a transition that could be shorter, a slightly better measure |

**Guard against P3 noise.** A long tail of P3 findings buries the P0s and makes the review feel
like pedantry rather than judgement. Report the P3 items that genuinely matter - each still a full
entry with its location, severity and user impact - and cut the rest entirely. Never compress
several findings into a fieldless one-liner: a summary without locations is not actionable, so
anything not worth its own entry is cut, not summarized. If the P3 list is longer than everything
above it combined, cut it down.

## Systemic patterns before isolated defects

Report systemic findings first, as their own section, then isolated defects. A systemic pattern is
the same defect in three or more places, or a defect whose cause is a shared token, component, or
convention. Fixing the pattern at its source fixes every instance; listing fifteen instances of one
missing token wastes the reader's attention and invites fifteen local patches.

## When the surface is already clean

Treat a zero result as evidence when the check and its scope are named. Group meaningful clean
checks into a compact baseline, using counts where possible, then move the review to finer signals:
token consistency, repeated local recipes, asymmetry within one screen, and drift between surfaces
that share a mode. A short report with three consequential findings is stronger than a padded list
of P3 observations.

## Verify codebase findings at the source

When source is in scope, open the primary code before publishing every finding. Search results,
generated route lists, and absence checks are leads: a title may be set in a child component, a page
may only redirect, and a literal color may represent series data rather than visual styling. Trace
delegated behavior until the user-visible outcome is established. For screenshot-only reviews,
state that source behavior is unverified instead of inferring it from the image.

When exploration is delegated, treat the returned report as a lead set. Re-open each cited location
before including it, and independently remeasure every count stated in the final report. Classify a
pattern as systemic only after that recount. A plausible `file:line` citation does not establish
either truth or scale.

## Positive findings are required

Name what is done well, specifically, and say why it works. This is not politeness. A review that
lists only defects gives no signal about what to preserve, and the next change removes the good
parts along with the bad ones. Two or three specific observations are enough; generic praise is
worse than none.

## Copy self-audit

Read every visible string as a user would, not as markup. Flag:

- grammatically broken or truncated strings;
- text that describes a feature the product does not have;
- pseudo-profound phrasing that survives having its meaning removed;
- placeholder text still in place;
- precise-looking numbers with no source behind them;
- labels that name the implementation rather than what the user is doing;
- inconsistent vocabulary for one action across a flow;
- inconsistent capitalization across headings and controls.

## Evaluation structure

Established usability heuristics are a useful checklist for the experience layer: system status
visibility, match to the user's world, user control and freedom, consistency and standards, error
prevention, recognition over recall, flexibility, minimal design, error recovery, and help.

Use them as a structure for coverage, not as a scoring rubric. Do not assign numeric scores. A
number implies a measurement that was never taken and invites arguing about the number instead of
the finding.

## Before delivering

- Scope, surface groups, modes, sampling method, and material exclusions are declared for a
  repository-wide review.
- Both layers present and clearly separated.
- Every finding has a location, a severity, and a user impact.
- When source was available, every codebase finding was verified in primary code rather than
  inferred from a search result or a delegated report, and every reported count was independently
  measured. Without source, the report separates observable findings from unverified source
  hypotheses.
- Systemic patterns are separated from isolated defects.
- Prior reviews of the same surfaces were located and their findings reported as resolved or open.
- Positive findings are specific.
- Clean checks are reported compactly as scoped evidence when they are a meaningful result.
- No code was changed.
