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

Keep the brief compact. The template is a coverage checklist, not a form to reproduce
verbatim.

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
`typescript`, `frontend-crafting`, `web-debug`, or `review-request`. Name only the applicable
capability. No agent receives the whole skill ecosystem, and naming a skill does not transfer
ownership of that skill's decisions to the worker.
