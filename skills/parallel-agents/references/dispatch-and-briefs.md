# Dispatch and Briefs

Detailed guidance for what each agent receives and how wide the wave should be.

## The focused brief contract

Each work unit gets a self-contained brief. The fields:

- **Objective.** The outcome this unit must produce, in one or two sentences.
- **Scope.** The domain, paths, and components this unit owns.
- **Known inputs.** Facts, artifacts, and prior findings the agent would otherwise have to
  rediscover.
- **Do not touch.** Paths, interfaces, and resources reserved by other units or by policy.
- **Workspace and snapshot.** Where the agent works and the exact state it starts from.
- **Mutation permissions.** `READ_ONLY`, or mutation allowed within the stated scope.
- **Relevant dependencies.** `none`, or the specific dependency and how it is satisfied.
- **Expected output.** The shape of the result, matched to the task type.
- **Evidence required.** The commands, observations, or artifacts that must back the claims.
- **Integration contract.** What the agent leaves behind and who integrates it.
- **Result budget.** An upper bound on the size of the returned result, a mandatory status line
  (`DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, `NEEDS_CONTEXT`, or `FAILED`), and a list of the
  sources the agent actually read, so the controller can judge coverage without re-reading.

### Coverage of a corpus

For research over a corpus (many files, requests, or documents), the brief carries the
expected inventory and asks the agent to state, for every source, one reading mode:

1. `enumerated` - the name was listed only.
2. `metadata scan` - a script read sizes, lines, headers or other metadata.
3. `excerpt` - a bounded fragment was read.
4. `full read` - the whole document was read.
5. `substantive analysis` - the document was read and the brief's questions were answered from it.

The names may differ; the distinction must survive. Bytes or lines collected by a script
count as a metadata scan, never as substantive analysis. The result body lists `expected`,
`covered` and `uncovered` sources for the level of work the brief required. A finding names
its source and the range actually read; a local finding is proven by the fragment that
shows it, and the full document is not required for it. Coverage gaps are returned whatever
the transport status says: an agent that finished the process (`COMPLETED`) with gaps still
reports them. Acceptance of the task stays with the caller and final verification with its
owner (`verify` or `verification-gate`); this skill does not take over either.

Keep the brief compact. The template is a coverage checklist, not a form to reproduce
verbatim.

## Read-only wave

When every unit is `READ_ONLY`, reads one shared snapshot (section 9) and touches no shared
external resource, skip sections 5-7. Keep classification, the snapshot, independence by
topic (no overlapping questions and no conclusion that depends on another unit's answer),
the brief with its result budget (section 10), and reconciliation (sections 12-13). A caller
skill that defines a single read-only child itself (for example one reviewer dispatched by
`cr-request` or `review-request`) already owns that child's contract: when the host only
inspects the same frozen snapshot and shares no mutable state, no separate wave is needed.
A wave of several read-only units meeting the first sentence's conditions skips sections 5-7
too; shared mutable state, or several units outside those conditions, keeps the full assessment.

## Why the parent transcript stays behind

Never pass the whole conversation on the chance that some of it helps. A focused brief avoids
context pollution, bias toward the parent's current hypothesis, irrelevant assumptions,
unnecessary token cost, and instruction conflicts between the parent's history and the unit's
actual task. Prefer a clean child context when the harness offers one, without hardcoding a
vendor-specific mechanism into the methodology.

## Narrow scope without a dictated solution

A focused brief constrains the domain. It does not supply an answer the evidence has not
reached yet.

```text
Poor:
Fix the race condition by replacing the timeout with an event listener.

Better:
Investigate the failures in subsystem X.
Determine the root cause using debugging methodology.
Return the evidence and a proposed fix.
```

The first brief presumes a root cause and a remedy. If the presumption is wrong, the agent
delivers a confident change to the wrong mechanism. Keep the agent's scope narrow and its
reasoning genuine.

## Harness capability detection

Determine which capabilities are actually available before depending on them:

```text
spawn                          wait
parallel dispatch              cancel
clean child context            resume
model or reasoning selection   native isolation
agent identity
```

Describe these semantically. Platform tool names may appear as examples of a detected
capability, clearly marked as examples, and never as a required call. Never invent a tool call
that the current harness does not expose.

### Graceful degradation

```text
parallel dispatch unavailable
-> run the independent units sequentially
```

The decomposition and the context isolation remain valuable on their own. A harness without
concurrent dispatch still benefits from coherent domains, focused briefs, and structured
results. Cancellation and resume are equally optional: when the harness lacks safe
cancellation, do not fabricate one, and account for the cost of work that cannot be stopped.

## Bounded concurrency

Width follows from the situation, not from the platform maximum. The inputs:

```text
number of independent units     task weight
available isolation             harness limits
resource contention             integration overhead
                                context/controller capacity
```

```text
Use the smallest parallel width
that captures most of the available independence.
```

Twelve tiny independent tasks rarely justify twelve agents. Three or four balanced domains
usually capture nearly all of the available parallelism with a fraction of the dispatch and
reconciliation overhead, and each agent then carries enough work to be worth its startup cost.
Never hardcode a number; platform limits differ and so does task weight.

## Optional model and reasoning selection

When the harness allows it, task complexity may inform the choice of agent:

```text
simple isolated lookup         -> cheaper, faster agent
complex architecture analysis  -> stronger agent
high-risk specialist review    -> appropriate strong or specialist agent
```

This is an optional refinement. This skill does not become a model-routing framework, and when
selection is unavailable, use the default agent.

## Agent specialization

A brief may name the skill that applies to its domain, such as `debugging`, `vitest`,
`typescript`, `frontend-crafting`, `web-debug`, or `cr-request`/`review-request`. Name only the applicable
capability. No agent receives the whole skill ecosystem, and naming a skill does not transfer
ownership of that skill's decisions to the worker.
