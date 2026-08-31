# Review

Critiquing an existing surface. Read `quality-gate.md` for the technical layer and
`anti-patterns.md` for the default failures before writing findings.

## The rule that governs this workflow

**A review does not modify code.** Findings are reported, with the remediation described, and
nothing is applied. If the user asks for fixes afterwards, that is a separate turn under
`polish.md` or `redesign.md`. Fixing while reviewing destroys the artifact the user asked for and
hides the reasoning behind a diff.

## Output shape: two layers, kept apart

Report visual and experiential critique separately from technical findings. They are different
kinds of claim - one is judgement grounded in intent, the other is verifiable against a standard -
and merging them lets a matter of taste borrow the authority of an accessibility violation.

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

One entry per finding, grouped by file, terse enough to scan:

- **Location** - `path/to/file.tsx:142`, or the surface region when there is no file.
- **Issue** - what is wrong, in one sentence.
- **Severity** - P0 to P3, defined below.
- **User impact** - who is affected and how. A finding without an impact is a preference.
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
like pedantry rather than judgement. Report the P3 items that genuinely matter and summarize the
rest in a single line. If the P3 list is longer than everything above it combined, cut it.

## Systemic patterns before isolated defects

Report systemic findings first, as their own section, then isolated defects. A systemic pattern is
the same defect in three or more places, or a defect whose cause is a shared token, component, or
convention. Fixing the pattern at its source fixes every instance; listing fifteen instances of one
missing token wastes the reader's attention and invites fifteen local patches.

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

- Both layers present and clearly separated.
- Every finding has a location, a severity, and a user impact.
- Systemic patterns are separated from isolated defects.
- Positive findings are specific.
- No code was changed.
