# Attribution

scope-triage is derived from the brainstorming skill in obra/superpowers.
The active workflow no longer requires upstream brainstorming and hands approved designs to plan-crafting.

It is based on the `brainstorming` skill by Jesse Vincent
(https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md),
licensed under MIT, © 2025 Jesse Vincent. Forked from upstream HEAD `44c9b2d`
(2026-07-27).

Forked 2026-07-29 by Ihor Orlovskyi.

Modifications relative to upstream:

- **Scope check before the design cycle.** A mandatory Step 0 classifies every
  request into one of three routes — A (direct implementation), B (light spec),
  C (full design) — instead of sending every request through the design cycle.
- **Narrowed description.** Upstream triggers on "any creative work"; this fork
  triggers on requests that need design decisions and names the cases that route
  straight to implementation, so mechanical refactors and single-outcome config
  changes do not open a design cycle.
- **Branched terminal state.** `plan-crafting` is the terminal state of Route C
  only; Routes A and B hand off to implementation with no plan artifact.
- **Hard gate scoped to Route C.** The upstream gate text is kept at full force,
  but it governs Route C rather than every request.
- **Per-question recommended answer.** Every clarifying question carries the
  agent's own recommended answer, so the user confirms instead of composing.
- **Assumption ledger.** Classification must list its assumptions and mark each
  `verified` or `assumed`; facts obtainable from the repository are retrieved by
  the agent, not asked of the user.
- **Coverage check.** Before the design doc is written, the agent loops on
  "is anything still uncovered?" until the user confirms coverage.
- **Mirrored rationalizations table.** Upstream's "this is too simple to need a
  design" anti-pattern is replaced by a table of the excuses an agent uses to
  under-scope work, each paired with the reality.
- **Visual companion not carried over.** The browser-based companion, its
  just-in-time offer, and `visual-companion.md` are dropped; this fork is
  text-only and ships no scripts.
