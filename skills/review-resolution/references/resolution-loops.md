# Resolution Loops

Use this reference after findings have individual assessments. It keeps multi-finding work
coherent, measurable, and bounded while leaving final completion proof to `verification-gate`.

## Lightweight resolution order

Build a dependency-aware order before editing:

```text
blocking security/data/correctness or root cause
  -> dependent correctness and compatibility findings
  -> regression and test-quality findings
  -> maintainability, documentation, and style findings
  -> explicitly accepted optional suggestions
```

For every material root-cause group, record:

```text
Group: G1
Primary finding: F1
Impacted findings: F2, F3
Dependencies inspected: <callers, types, APIs, config, schema, auth, components>
Fix boundary: <files, symbols, or contract>
Expected changed files: <explicit list>
```

Reassess dependent findings after the primary fix. This prevents a later comment from
preserving a defect that the root fix already removed and reduces patch churn.

## One fix wave

For each `ACCEPT` or `PARTIAL` group:

1. State the validated problem and observable contract.
2. Select the smallest causal fix that preserves required behavior.
3. Route root-cause uncertainty to `debugging` before changing production code.
4. Route an automatable behavior bug to `tdd` for valid RED, minimum GREEN, and REFACTOR.
5. Run the targeted checks that observe the affected boundary.
6. Inspect the actual diff, including selected untracked files.
7. Run relevant checks for shared dependents.
8. Record evidence for every impacted finding.

One fix wave may contain several edits when they share a verified root cause. Separate waves
when the hypotheses, contracts, or verification evidence differ.

## Diff and impact check

After a material change, compare the intended boundary with the actual tree:

```text
Expected files/hunks -> actual files/hunks -> explanation for each difference
```

For unexpected changes, classify them as supporting, unrelated, generated, or unresolved.
Exclude unrelated files and hunks from the resolution boundary and report them. Do not alter,
discard, restore, or clean user changes under this skill. Escalate when a supporting change
expands the contract or changes a public, security, schema, auth, or shared boundary.

Inspect dependents for changes to:

- shared types and base interfaces;
- public APIs, serialization, and error contracts;
- auth helpers, permissions, and trust boundaries;
- configuration and feature flags;
- database schema, migrations, and persistence;
- shared parsers, utilities, and base components.

Agent or implementer reports are context, not proof. The controller or resolution owner must
compare the actual tree and evidence with the finding record.

## Finding-level evidence

Each accepted or partial finding gets a closure entry:

```text
F1: <claim>
Assessment: VALID | PARTIALLY VALID
Disposition: ACCEPT | PARTIAL
Fix: <causal change>
Evidence:
  - Command or observation: <exact check>
  - Result: <relevant output or behavior>
  - Interpretation: <why this proves the claim is resolved>
Impact checks: <affected dependents and results>
Residual risk: <none, bounded risk, or routed decision>
```

For `REJECT`, `DEFER`, and `ESCALATE`, record the evidence supporting the action, the
remaining uncertainty, and the owner or route where applicable. A green test proves only
what its boundary observes. A passing review does not prove final current-tree correctness.

## Re-review matrix

Choose the smallest review that covers changed risk:

| Change after review | Minimum action |
| --- | --- |
| No code change; stale or duplicate record closed with current evidence | Record disposition; no full re-review |
| Localized mechanical fix with unchanged contract and isolated diff | Targeted checks; scoped re-review when the original review cannot see the fix |
| Material implementation change or several interacting fixes | Re-review the affected implementation scope |
| Architecture, public API, security, schema, auth, compatibility, or shared boundary change | Re-review required, with specialist coverage when justified |
| Current `HEAD`, working tree, or selected untracked content differs from review identity | Obtain a fresh target through `review-request` before relying on old findings |

Re-review the changed risk surface, not every line by ritual. If the change invalidates the
original boundary, create a new review target rather than appending fixes to stale findings.

## Bounded convergence

Count attempts by root cause. An attempt is a causal production change or a fix wave intended
to resolve a finding; a diagnostic experiment does not count until it changes production code.

Stagnation is present when:

- the same finding remains after scoped re-review;
- equivalent comments return under new wording;
- the same root cause reappears in another path;
- a fix repeatedly creates the same regression;
- each proposed patch grows the scope without stronger evidence.

Set any caller-provided finite cap before the first fix and never increase it silently. When
the caller provides no cap, use the local `debugging` convention of three failed causal fix
attempts for the same root cause as the hard stop. A localized mechanical finding receives
one fix wave and a scoped re-review; an unresolved result then requires a ruling or escalation.

At the circuit breaker:

```text
stop patch churn
  -> record the evidence and attempted changes
  -> distinguish invalidity from unresolved cause
  -> route to debugging, scope-triage, plan-crafting, or specialist review
  -> escalate material unresolved risk
```

Do not use a bounded loop to force acceptance of a doubtful finding. A reviewer disagreement
is resolved with code, contract, and test evidence; a material unresolved disagreement is
escalated.

## Summary contract

The final summary is compact and factual:

```text
Review Resolution
Target: <reviewed and current-tree identities>
Accepted: <N>
Rejected: <N>
Partial: <N>
Deferred: <N>
Escalated: <N>

Resolved:
- F1 <claim> - <change and evidence>

Rejected or stale:
- F2 <claim> - <evidence and rationale>

Duplicates:
- F3 -> F1 - <shared root cause and coverage>

Deferred or escalated:
- F4 <claim> - <scope, owner, or decision needed>

Re-review required: <yes | no>
Reason: <risk and scope change>
Final verification: delegated to verification-gate
```

The summary closes review findings for this workflow. `verification-gate` remains the
authoritative owner of integrated current-tree verification and completion claims.
