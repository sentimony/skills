# Test Quality

Use this reference when the behavior has a weak oracle, a cross-module boundary, broad input
space, legacy constraints, or a meaningful risk of false confidence. It supplements the
operational cycle in `SKILL.md`.

## Oracle gate

An oracle should be derived from the requirement and the behavior's owner. Before calling a
test convincing, name a realistic defect that should make it fail. Then check that the
assertion observes that defect through the selected boundary.

Prefer assertions about:

- a result that a caller can use;
- a state transition visible at the public boundary;
- persisted data that another operation can read;
- an emitted event or message with contract-level fields;
- an API response, status, or domain error;
- a component interaction a user can perform.

Shape checks have a narrow purpose. They can establish a serialization or type contract when
that shape is the requirement. They are weak evidence for a workflow that promises validity,
usability, or a side effect.

```text
Weak oracle: the generated object has `id`, `status`, and `items` fields.
Stronger oracle: the generated object can be submitted to the promised workflow and the
workflow produces the documented result.
```

Derive expected values independently from the implementation. A helper that calls the same
production mapper, builds the same expression, or reads the result back through the same
defect can reproduce a bug while the test remains green. Literal expected values are useful
when they express a small contract; a separate domain calculation is useful for larger input.

## Boundary and level review

Choose the smallest boundary that owns the promise. Use these questions in order:

1. Where can a real consumer observe the behavior?
2. Which lower boundary still includes every decision involved in that behavior?
3. What setup would be removed by moving lower without removing the contract?
4. What evidence would be lost by moving lower?

Keep a double at a boundary when the real dependency is slow, destructive, unavailable, or
owned by another system. Make the double represent the dependency contract. Include response
fields, errors, ordering, and side effects that the behavior relies on. A mock interaction is
an oracle when the interaction itself is a documented contract, such as an emitted command or
an authorization decision. Call-count assertions alone usually describe implementation
choreography.

## Risk and depth

Use the requirement's impact to decide how many behaviors require evidence:

| Risk | Evidence to cover |
| --- | --- |
| Low | Happy path and obvious boundaries |
| Medium | Happy path, important errors, boundary values, and meaningful collaboration |
| High | Positive and negative paths, authorization or security, state transitions, recovery,
integration boundary, and important regressions |

High-risk signals include authentication, authorization, payment or billing, data loss,
migrations, permissions, concurrency, critical business rules, and public APIs. For a high-risk
change, split the requirement into named behaviors before writing tests. An evidence map can
remain small:

```text
REQ-1: rejected request is retried -> retry succeeds
REQ-2: retry limit is three -> a fourth request is absent
REQ-3: final failure is exposed -> caller receives the final error
```

Every line needs a test, contract check, or manual evidence. A passing subset does not close
the requirement.

## Characterization mode

Use characterization tests to protect intended behavior during a legacy refactor. Observe the
public boundary, record representative inputs and outputs, and add a sensitivity check so the
test can detect a meaningful change. Refactor behind the captured contract, then rerun it.

A surprising result needs a product or domain decision before it becomes a compatibility
contract. If it is a known defect, write the corrected outcome as a regression RED. A
characterization test records an existing promise; it does not authorize adding new behavior
after implementation.

## Sensitivity and mutation

For normal-risk work, mentally apply one small defect to each important assertion:

- swap a strict boundary for an inclusive one;
- remove a validation or authorization branch;
- change a state transition or returned value;
- return an empty collection or the wrong error;
- remove a required side effect.

The targeted test should fail for the defect. For high-risk work, or whenever the answer is
unclear, introduce one temporary real mutation, run the narrow test, confirm RED, and revert
the mutation immediately. Keep the mutation local and meaningful. A project mutation tool may
replace the manual mutation when its targeted mode has a clear scope.

Mutation evidence complements an oracle review. A mutation score or coverage percentage does
not establish that the test proves the requirement.

## Property and invariant triggers

Consider a property when examples leave a large input space or a relation matters more than a
specific fixture. Good candidates include parsers, serializers, sorters, converters,
validators, financial calculations, normalizers, and state machines.

Useful properties include:

- serialize then parse preserves the relevant value;
- output remains sorted according to the documented order;
- a conversion preserves length or units;
- normalization is idempotent;
- an invalid state cannot be reached through a public transition.

Keep named examples for important boundaries and error messages. Add property-based evidence
when the invariant catches classes of defects that examples would leave open.

## External contracts

Draw the ownership chain before choosing a test:

```text
external service -> adapter -> domain behavior
```

Test the adapter contract at the adapter boundary and the domain promise at the domain
boundary. Unit tests can use a contract-shaped double for the external service; contract or
integration tests should verify that the adapter still matches the real dependency when the
project can run them safely. Avoid rebuilding the SDK's internal algorithm in a unit test.

For a double, state which behavior it controls and why the real call is excluded. A double that
omits an error field, response status, pagination rule, or side effect can create a green test
with an unusable production integration.

## Determinism gate

Treat timing, random values, timezone, test order, shared state, network access, and async
scheduling as possible causes of false evidence. If a targeted test is intermittent, repeat it
enough to establish the signal and investigate the cause. Stabilize the source with a controlled
clock, deterministic input, isolated state and cleanup, a controlled network boundary, or an
explicit synchronization point.

Retrying until green changes the observation rather than the behavior. Record an unavailable
environment separately from a behavioral pass or failure.

## Impact and human evidence

After GREEN, list changed consumers for shared helpers, types, public APIs, base components,
configuration, parsers, schemas, and common utilities. Run focused regression checks for those
consumers. The final workflow can decide whether broader repository verification is needed.

For visual hierarchy, responsive layout, animation, browser rendering, and subjective
usability, name a manual or visual check alongside automated evidence. Browser-driving skills
can provide the mechanics. A DOM assertion may prove a semantic state while leaving visual
acceptance untested. When a manual check reveals a reproducible defect, add an automated
regression RED when the defect has an observable automated boundary.

## Quick oracle review

Before accepting a green test, answer:

```text
What promised behavior does this assert?
Where can a real consumer observe it?
What meaningful defect would make it fail?
Is the expected result independent of the implementation?
Which acceptance criteria remain evidenced elsewhere?
```

If these answers are vague, improve the boundary or oracle before increasing test count.
