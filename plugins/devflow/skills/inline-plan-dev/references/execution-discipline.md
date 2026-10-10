# Execution Discipline

How to keep inline execution moving without either stalling on ordinary work or running
past a decision that belongs to the user.

## Blocker decision table

Exactly two verdicts exist. Neither list is extended during execution.

| Situation | Verdict | Default action |
| --- | --- | --- |
| A test fails | `NOT_A_BLOCKER` | `investigate -> fix -> verify -> continue` |
| Lint fails | `NOT_A_BLOCKER` | Fix the violation or the rule's real cause, then continue. |
| Typecheck fails | `NOT_A_BLOCKER` | Resolve the type error rather than suppressing it. |
| An implementation bug appears | `NOT_A_BLOCKER` | Debug and fix within the task boundary; route to `debugging` when the cause is unclear. |
| Minor ambiguity in the task | `NOT_A_BLOCKER` | Choose the reading consistent with plan intent, record the choice, continue. |
| Repository structure differs from the plan | `NOT_A_BLOCKER` | Reconcile under the divergence categories and continue. |
| A small API mismatch | `NOT_A_BLOCKER` | Adapt the call site to the current contract. |
| A fix that needs investigation first | `NOT_A_BLOCKER` | Investigate, then fix. The need to investigate is not a reason to stop. |
| A required credential is missing | `BLOCKER` | Report what is needed and why; do not invent, guess, or bypass it. |
| A required external input is missing | `BLOCKER` | Name the input and who can supply it. |
| A permission is unavailable | `BLOCKER` | Report the exact operation and the permission it requires. |
| An irreversible decision needs a choice | `BLOCKER` | Present options and trade-offs; wait for the user. |
| Material product ambiguity | `BLOCKER` | The plan does not determine which behavior is correct; ask. |
| A destructive action without authorization | `BLOCKER` | Stop before the action, not after. |
| Contradictory plan intent | `BLOCKER` | Two requirements cannot both hold; surface the contradiction. |

The asymmetry is deliberate. Every `NOT_A_BLOCKER` row is work the executor is equipped
to do. Every `BLOCKER` row needs something the executor cannot obtain: an authority, a
secret, an external artifact, or a decision that is not the executor's to make.

Stopping on a `NOT_A_BLOCKER` item is the most common failure of this workflow. It
returns an unfinished plan plus a question the executor could have answered, and it costs
the user a full context switch to say "yes, fix the test".

## Risk gate

Assess before a high-risk or externally disruptive task:

| Dimension | Question |
| --- | --- |
| Blast radius | What else is affected if this goes wrong? |
| Reversibility | Can this be undone, and with what effort? |
| Data impact | Can data be lost, corrupted, or exposed? |
| Production impact | Does this reach a running system or real users? |
| External side effects | Does this touch a third party, a paid service, or a public artifact? |
| Rollback | Does a rollback path exist, and has it been identified before execution? |

High-risk work: database migration, data deletion, production config, deployment, cloud
infrastructure, destructive filesystem operation, public API migration, and auth or
security changes.

For a disruptive operation:

```text
validate preconditions
  -> identify rollback
  -> ensure verification exists
  -> obtain explicit authorization when required
  -> execute
```

**The counterweight.** Ordinary code edits get no approval gate. Editing a module,
adding a test, renaming a local symbol, updating a fixture: none of these enters this
section. A gate applied to every edit turns inline execution into a question queue and
trains the user to approve without reading, which removes the gate's value exactly when
it is needed.

## Deterministic scope check

Prefer a deterministic tool over model judgment wherever both could answer the same
question.

```bash
git status --porcelain
git diff --name-only HEAD
```

Compare the output against the task's expected file list.

**Worked example.** Task 3 declares it modifies `src/auth/session.ts` and
`tests/auth/session.test.ts`. The diff also shows `src/types/user.ts`.

Wrong response: revert the third file to make the diff match the plan.

Right response: explain it. The session change required a new field on the shared `User`
type, which the plan did not anticipate. That is a legitimate consequence, it is in
scope for the intent, and it triggers change-impact verification because a shared type
moved. Record it in the task, then check the dependents.

An unexpected path is a signal to look, not a violation to erase. The three readings are:
a necessary consequence the plan missed, a leftover from earlier work in the tree, or an
actual mistake. Only the third is reverted, and only after it is identified as one.

## Change-impact verification

After a fix or an unplanned implementation change, ask:

```text
What else depends on what I just changed?
```

Trigger when the change touched any of: a shared helper, a shared type, a public API,
config, a dependency, a base component, or a database schema.

Procedure:

1. find the dependents with a deterministic search (references to the symbol, importers
   of the module, consumers of the endpoint or schema);
2. decide which of them can actually observe the change;
3. run checks for those, at the depth their risk warrants;
4. record what was checked and what was deliberately not.

Run checks for the relevant dependents, not the full regression suite. The full suite is
the `HIGH` depth answer to a broad change, not the reflex response to every fix.

## Skill discovery and routing

Applicable skills are discovered at execution time: read what the project actually
provides rather than assuming a fixed set. A skill named in the routing table but absent
from the project is skipped without comment, and a project-local skill not named there is
still used when it owns the task's domain.

Routing is not delegation of responsibility for the plan. The executor stays accountable
for the task boundary: it enters `debugging` for a causal investigation and returns to
the same task, and it hands evidence to `verification-gate` without outsourcing the
decision to keep going.

## Execution-mode fidelity

Inline means inline. Once the user chose this mode:

- do not dispatch implementer subagents, even when the platform offers them;
- do not create orchestration state, a ledger, or a task queue in the filesystem;
- do not run reviewer agent loops or model routing;
- do not silently batch tasks out to any other execution mechanism.

A switch is a user decision, not an optimization. When a task genuinely is unreasonable
to execute inline, an acceptable recommendation looks like this:

```text
Task 7 migrates 40 call sites across 12 modules with an identical mechanical edit
and an independent test per module. Inline, this is one long sequential pass with
no review boundary between the edits.

`subagent-plan-dev` would run these as scoped units with a review gate per module.

I can continue inline, or you can switch modes. Which do you prefer?
```

It names the task, the concrete reason, the alternative, and it leaves the choice open
while continuing inline until the user answers. What it does not do is switch, or stop
work pending a reply.
