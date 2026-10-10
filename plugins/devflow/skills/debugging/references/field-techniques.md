# Debugging Field Techniques

Use these techniques when the symptom needs them. They support the lifecycle in the parent
skill and do not replace its evidence threshold.

## Error identity and provenance

Read the first meaningful error in context. Capture the literal message, stack, exit code,
assertion, warning, source location, input, and relevant request or response. Search the
exact error string before reading large amounts of unrelated code or escalating.

An error can identify a proximate test double, wrapper, or consumer while lifecycle evidence
shows that the path should not have run. Keep two questions separate:

```text
What produced this error identity?
Why did execution reach this lifecycle point?
```

When evidence is delegated or transformed, verify its identity and provenance. A plausible
chain is not proof that the displayed value came from the assumed producer.

## Raw data before a parser

Before writing or trusting a parser, inspect one complete raw representative item and check
it against an independent expectation. Confirm which source field produced each derived
field. Inspect a second item when the first could be exceptional.

Red flags include:

- every record receives exactly the same value;
- threshold, label, or surrounding text is mistaken for a measurement;
- fields are merged or truncated;
- derived output conflicts with the visible or raw source.

Return to raw evidence and correct the extractor before drawing conclusions about the
dataset. A parser can produce a neat, internally consistent report from the wrong schema.

## Black-box control probes

For a private API, remote service, proxy, auth gateway, undocumented protocol, or opaque
CLI, first choose an input whose expected result is clearly different. Useful pairs include:

```text
known-valid-looking route vs deliberately nonexistent route
authorized request vs deliberately invalid credential shape
existing object id vs impossible object id
```

Record status, headers, body shape, timing, and correlation data. If plausible and
deliberately invalid controls behave identically, the decision likely occurs upstream of the
route, object lookup, or parser under investigation. This localizes the layer without naming
the exact component. Stop enumerating plausible permutations until the boundary is known.

## Boundary map and backward tracing

Make a small table for the path under test:

| Boundary | Input | Expected output | Actual output | Config or state | Status |
| --- | --- | --- | --- | --- | --- |
| client -> gateway | request | authenticated request | 401 | auth header | first incorrect |
| gateway -> service | ... | ... | ... | ... | not reached |

Instrument one boundary at a time. Prefer structured, bounded, redacted fields: request
identifier, state transition, status, timing, and invariant result. Remove temporary probes
after the causal mechanism is established.

For a deep failure, trace:

```text
detection point <- caller <- producer <- upstream transformation <- origin
```

Stop at the source that created invalid state or violated the contract. The first abnormal
line may only be propagation.

For complex causality, use a small graph rather than a chronology:

```text
cache key builder -> invalid key -> wrong lookup -> downstream crash
shared config ----^                  missing schema check
```

Label each edge as observed or inferred.

## Recent changes and known-good deltas

Inspect recent commits, dependency and toolchain updates, flags, config, migrations, and
generated files. Use this to generate hypotheses and to choose a comparison point. Verify
with a targeted test before assigning cause.

When a working counterpart exists, enumerate material deltas first:

```text
request, payload, dependency, config, runtime, permissions,
state, timing, code path, and output
```

Then test one delta or a minimally combined factor when the contract requires a pair. The
most suspicious difference is a candidate, not a verdict.

## Environment differences

For local-versus-CI, dev-versus-prod, or machine-specific failures, collect comparable
values for:

| Dimension | Examples |
| --- | --- |
| Runtime | language, runtime, package manager, compiler, browser, architecture |
| Dependencies | lockfile, installed tree, native modules, tool versions |
| Process | working directory, entrypoint, generated files, module resolution |
| Configuration | environment variables, flags, secrets presence, config precedence |
| Access | user, permissions, filesystem, network, proxy, DNS |
| Data | cache, database/schema version, fixtures, clock, timezone, locale |

Report the measured difference and its prediction. "Environment issue" is a starting label,
not a root-cause statement.

## Flaky and concurrent failures

Preserve the first failure before rerunning. Record attempts, failures, sample size, rate,
seed, clock, resource state, logs, traces, and artifacts. A clean rerun narrows the claim to
that run; it does not refute an intermittent failure.

Classify the investigation target as timing, race or concurrency, shared mutable state,
test-order dependency, randomness, clock or timezone, network, resource exhaustion,
eventual consistency, or external dependency. For a suspected race, write down:

```text
actors:
shared state:
ordering assumption:
synchronization boundary:
expected event sequence:
observed event sequence:
```

Use timestamps, event sequence numbers, state transitions, and correlation IDs to test the
ordering prediction. Intermittence alone does not establish a race.

Prefer waiting for a condition, event, or state transition over an arbitrary delay. A fixed
delay is valid when the domain contract genuinely requires elapsed time; document that
contract and test its boundary. A longer timeout changes the observation window, while
condition-based synchronization changes the ordering guarantee.

## Minimization and bisection

For a large input, fixture, config, flag set, or service path, remove irrelevant factors in
small steps and retain the smallest case that still fails. Do not spend minimization effort
when the causal mechanism is already clear and the reduction would add no evidence.

Use `git bisect` or an equivalent binary search when all of these are true:

1. a known-good commit is reliable;
2. a known-bad commit is reliable;
3. the failure is deterministic enough for repeated tests;
4. the history between them is meaningful and has not been rewritten in a way that breaks the boundary.

If the test is nondeterministic or the endpoints are uncertain, improve characterization or
use a different comparison. A bisect identifies an introduction point, not the complete
root cause.

## Performance anomalies

Start with a measured symptom and a baseline:

```text
define metric -> measure baseline -> profile -> identify dominant cost
  -> form causal hypothesis -> change one factor -> remeasure -> compare
```

Name the metric: latency, throughput, CPU, memory, I/O, network, rendering, or database
time. A page feeling slow or code looking expensive is a lead. Trace duplicate work or
unexpected cost to its source before optimizing. Keep workload, sample count, environment,
and measurement method comparable.

## Build, type, and toolchain failures

For build, lint, type, or module-resolution failures, inspect:

- the first meaningful error and its command exit code;
- runtime, package manager, compiler, linter, and plugin versions;
- working directory and config discovery or precedence;
- generated files, module resolution, lockfile, and installed dependencies;
- environment, permissions, filesystem, and CI differences.

Downstream cascade errors are consequences until the first failure is explained. Delegate
TypeScript compiler and module mechanics to `typescript`, and Vitest selection, mocks,
snapshots, and runner mechanics to `vitest`; return their measurements to this hypothesis
loop.

## External systems and safe observability

External causes require external evidence: provider metrics, request IDs, response timing,
network captures, service health, or a documented contract. If that state is unavailable,
write `UNVERIFIED HYPOTHESIS` and record the observability gap.

Durable diagnostic improvements can include structured error context, correlation IDs,
metrics, assertions, diagnostic events, or health checks. Keep data bounded and redacted.
Remove exploratory logs, dumps, flags, endpoints, screenshots, and test hooks unless the
change intentionally makes them durable.
