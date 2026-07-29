---
name: scope-triage
description: You MUST use this when a request needs design decisions before code — new features, product or UX behavior, architecture changes, unclear success criteria, or two materially different approaches. Explicitly specified mechanical refactors, localized fixes with known expected behavior, and single-outcome config changes go straight to implementation.
metadata:
  author: Ihor Orlovskyi
  version: "1.0.0"
license: MIT
---

# Scope Triage Before Design

Turn a request into either an implementation contract or a fully formed design. Classification comes
first, always: one turn that states a hypothesis, records assumptions, and picks a route. Only Route C
runs the full design cycle — A and B exist so an already-specified change is not taxed with a design.

## Step 0 — Scope Check

Do this before any other action, in a single turn, for every request.

1. **Hypothesis with confidence.** One sentence naming what the user wants to end up with, plus an
   honest 0-100% confidence. Below 70%, add one line stating what is missing.
2. **Assumption ledger.** List the assumptions the answer rests on; mark each `verified` (confirmed in
   code or docs this session), `assumed`, or `contradicted` (checked and found false). Retrieve
   repository facts yourself; ask only user decisions. Any `contradicted` entry means Route C.
3. **Classify** against the route conditions below.
4. **Announce the route** in one self-contained sentence — it must repeat the target contract in full,
   with the literal values, names, and numbers from the request, and read correctly on its own.

**Route C (full design) — if ANY of these hold:**

- requirements are ambiguous or contradictory;
- the user-visible outcome or the success criteria are still undefined;
- there is a product, UX, or visual decision to make;
- two or more materially different architectural approaches exist;
- the change creates a new capability or public contract, or materially alters data flow;
- you would have to pick a behavior the user never specified;
- an `assumed` entry about product, UX, or a public contract is still unverified;
- you cannot predict the user's answers to the next three questions you would ask.

**Route A (direct implementation) — only if ALL of these hold:**

- the user stated the target outcome explicitly;
- the done criterion is unambiguous and checkable by a test or a deterministic check;
- no product, UX, or architectural choice is unresolved;
- the change is a localized fix or a mechanical transformation of an existing contract;
- you are not widening scope or adding behavior of your own;
- every assumption affecting the result is marked `verified`.

**Route B (light spec) — the boundary:** Route A conditions hold, but the change is large-scale
(a migration, many consumers) or exactly one compatibility question is open.

**Uncertainty rule:** any uncertainty about the classification means Route C. File count and line count
are NOT criteria in either direction.

**User overrides, honored from the current message only:**

- "skip design", "just do it", "no spec" → Route A is permitted despite doubt, but name in
  one sentence the risk this instruction takes off your hands.
- "design this properly", "grill me", "full cycle" → Route C regardless of classification.

**Non-interactive runs** (CI, autonomous loop, subagent with no channel to the user) cannot run Route C.
If classification yields Route A, proceed; otherwise stop and report the blocker. Do NOT guess past it.

## Route A — Direct Implementation

- Say one sentence: the repeated target contract, the done criterion, and the route.
- The done criterion carries the literal values from the request, and whatever proves it — a test, a
  command, a grep — must reproduce that exact case, not a convenient neighbouring one. A bug reported
  as "asked for 10, got 9" is proven by a test asserting 10, not by one asserting 5.
- Continue with the matching implementation skill — TDD for behavior changes, debugging for bugs with
  known expected behavior, a direct edit for configuration. No spec file, no plan, no approval gate.
- If an unresolved product or architectural decision surfaces mid-work, stop and switch to Route C —
  mandatory, not a judgment call.

## Route B — Light Spec

- Write a 5-10 line spec: goal, target contract, out of scope, done criterion.
- Settle the single open compatibility question with the user, then implement.
- No full design cycle, no design approval loop, no mandatory `plan-crafting` handoff.

## Route C — Full Design

<HARD-GATE>
Inside Route C, do NOT invoke any implementation skill, write any code, scaffold any project, or take
any implementation action until you have presented a design and the user has approved it. This applies
to EVERY project routed here, regardless of perceived simplicity.
</HARD-GATE>

1. **Explore project context** — files, docs, recent commits.
2. **Ask clarifying questions** — one per message, each carrying your own recommended answer so the
   user can confirm rather than compose. Retrieve facts yourself; ask only about the user's decisions.
3. **Propose 2-3 approaches** — with trade-offs; lead with your recommendation and why.
4. **Present the design in sections** — each scaled to its complexity, approval after each.
5. **Coverage check** — before finalizing, ask whether everything is covered, whether a topic is
   still uncovered, and whether the user wants to go deeper. Repeat until they confirm coverage.
6. Write the approved design to `docs/specs/YYYY-MM-DD-<topic>-design.md`.
7. **Spec self-review** — placeholders, contradictions, scope, ambiguity; fix inline.
8. **User reviews the written spec** — wait; on requested changes, revise and re-run the review.
9. Terminal state: invoke plan-crafting. Do not invoke another skill from here.

If the request spans several independent subsystems, decompose it first — name the independent pieces,
how they relate, and the build order; each sub-project then gets its own spec → plan → implementation
cycle. When a design will not converge, work through `references/design-lenses.md`.

## When NOT to Use

- Purely informational requests ("how does X work?", "explain this file").
- Running tests or builds, and other read-only inspection with no change requested.
- Continuing work whose design was already approved in this conversation — resume it, don't reclassify.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user said 'just do it', so no design is needed" | That waives the process, not the risk. Name the decision you're taking on yourself in one line, then proceed. |
| "It's only a config change" | A config change with one deterministic outcome is Route A. A config change that alters product behavior users will notice is Route C. |
| "It's just a rename, it touches many files but it's mechanical" | Correct — file count is not a criterion in either direction. Check for an unresolved contract decision instead. |
| "I'll clarify the ambiguity while implementing" | Discovery during implementation is rework, and the user already paid for the wrong direction. |
| "I can infer what they'd want here" | If you're inferring product behavior the user never stated, that's Route C by definition. |
| "The spec would only be two lines, so it's not worth writing" | Then write the two lines (Route B). Cheap artifacts are not the same as no artifact. |
| "We discussed this earlier, the design is settled" | Settled in this conversation with an explicit target contract is Route A. Remembered from a past session is not. |

## Red Flags

- Classifying without writing an assumption ledger.
- Choosing Route A while the ledger still holds an `assumed` entry about product behavior, or holds
  any `contradicted` entry at all.
- Asking the user a question whose answer is sitting in the repository.
- Asking a question without offering your own recommended answer.
- Reaching `plan-crafting` in Route C without an approved spec.
- Silently downgrading from Route C to Route A part-way through the work.

## Verification

- The route was announced explicitly, with the target contract repeated, and a ledger was written.
- Every `assumed` entry that influenced a decision was verified or raised with the user.
- Route A stated the repeated target contract and the done criterion; Route C ended with an approved
  spec and a handoff to `plan-crafting`.
- Scope was never widened silently.

## Reference Files

- `references/design-lenses.md` — six lenses for Route C, for when a design will not converge.
- `references/attribution.md` — fork source, license, and modifications relative to upstream.
