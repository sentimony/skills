# Review and escalation

## The general review

The reviewer receives the task brief, the diff, and the implementer's report. It checks
the implementation against the brief, plus code quality, omissions and regressions, and
returns findings with exactly one verdict.

| Verdict | Meaning | What follows |
| --- | --- | --- |
| `PASS` | meets the brief, no findings worth acting on | controller-owned verification, then acceptance |
| `PASS_WITH_FINDINGS` | meets the brief; findings exist but none block acceptance | controller rules on each finding: fix now, defer, or dismiss |
| `FAIL` | does not meet the brief, or carries a defect that must not land | fix loop |

The middle verdict exists so that a cosmetic finding does not force a fix loop. Without
it, a reviewer either inflates a naming quibble into a failure or stays silent to avoid
the cost, and both distort the record.

The verdict is the reviewer's. The disposition of each finding is the controller's: a
`PASS_WITH_FINDINGS` with three deferred findings is a legitimate acceptance when the
controller records why. Deferred findings go to the plan's follow-ups, not to silence.

A `PASS` does not accept the task. Controller-owned verification still runs.

## Domain review

Runs after the general review, and only when risk or domain warrants it.

Triggers: security, database, API compatibility, frontend and UI, accessibility,
performance, concurrency, testing, and build and tooling.

```text
discover the applicable project skills and instructions
  -> select only the specialist review the domain and risk warrant
  -> run it as an additional gate
```

Discovery happens at execution time against the project actually in front of you. A
specialist skill absent from the project is skipped without comment, and no substitute is
invented for it.

Running every specialist on every task is the failure this section guards against. Nine
specialist passes on a `LOW`-risk fixture rename cost more than the task and train the
controller to skip the gate when it matters. The trigger is the domain the task touched,
narrowed by its risk level.

## The fix loop

```text
review returns FAIL, or the controller rules a finding must be fixed
  -> dispatch the fix with the finding stated concretely
  -> implementer fixes
  -> re-review against the original brief and the finding
  -> controller-owned verification
  -> accept, or iterate
```

The re-review checks the finding and the brief, not the finding alone. A fix that resolves
the finding by breaking the acceptance criteria is a new failure, and a review scoped only
to the finding will pass it.

## Stagnation signals

Four signals. Any one of them means the loop is not converging.

| Signal | Concrete example |
| --- | --- |
| The same finding survives two rounds | Round 1: "the loader does not close the file handle." Round 2, after a fix touching error handling: the same finding, unchanged. |
| The same test failure survives two rounds | `tests/import/loader.test.ts` fails on the same assertion, same expected and actual values, after two different fixes. |
| The same failure signature repeats | Two different-looking fixes both end with `TypeError: cannot read property 'id' of undefined` at the same frame. |
| The same implementation strategy repeats without new evidence | The implementer re-applies "add a null check at the call site" a third time, having learned nothing about why the value is undefined. |

The fourth signal is the one that hides. The diff looks new every round, so a controller
comparing diffs sees progress. Compare the strategy and the evidence, not the patch.

### Comparing failure signatures

Compare: the error type, the message text with variable values normalized, the failing
test identity, the assertion that failed, and the top frames of the stack that lie inside
the project.

Ignore as noise: timestamps, durations, absolute paths, process and worker ids, run
ordering, and any temporary directory name. Two runs of the same failure differ in all of
these, and a naive string comparison reports them as different failures. That is the
mechanism by which a stalled loop looks like progress.

## The escalation ladder

Four steps, in this order:

| Step | What changes | When to move on |
| --- | --- | --- |
| `RESUME` | the same implementer continues with its accumulated context | a stagnation signal fires after the resumed attempt |
| `FRESH` | a new implementer, clean context, explicit root-cause framing | a stagnation signal fires again, or the fresh attempt reproduces the same signature |
| `STRONGER` | a stronger model or profile, same root-cause framing | the stronger attempt also stagnates |
| `CIRCUIT_BREAKER` | the task stops and goes to the user | terminal |

`STRONGER` is skipped when `explicit_model_selection` is unavailable. The ladder then
proceeds from `FRESH` to `CIRCUIT_BREAKER` rather than repeating `FRESH`.

### What a `FRESH` dispatch carries

An explicit root-cause framing of why the previous attempts failed: what was tried, what
the evidence showed, and which explanations are ruled out. Not the original brief again.

Re-sending the brief that already failed twice produces the same diff a third time, at
full cost, and the clean context that was supposed to be the advantage is spent
rediscovering what the controller already knows.

When the cause is genuinely unclear rather than merely unfixed, route to `debugging`
before escalating further. The ladder replaces the agent; it does not replace an
investigation nobody has run.

### The circuit breaker

A finite last resort. The task stops, and the user receives what was tried, what the
evidence showed, and what the controller believes is blocking.

It is not the primary detection mechanism. The four signals catch a stalled loop well
before the hard limit, and a controller relying on the breaker alone spends every round up
to it before admitting the loop was stuck after the second.

The remaining tasks are not silently abandoned. Tasks that do not depend on the stopped
one may continue; tasks that do are marked `blocked` with the reason.
