# Verification and completion

## Why an implementer's report is insufficient

An implementer's report is a claim about work the implementer did. Accepting on it makes
the implementer the judge of its own output, and the whole orchestration reduces to a
sequence of self-assessments with extra dispatch cost.

The failure is concrete: an implementer reports "all tests pass" after running a filtered
subset, after running against a stale build, or after an exit code it misread. None of
these require dishonesty, and none are visible in the report.

The controller runs its own commands against the tree, records them in
`verification/<n>.md`, and accepts on those.

## Verification depth

| Depth | What it runs |
| --- | --- |
| `LOW` | targeted tests or checks of the changed behavior |
| `MEDIUM` | `LOW` plus typecheck, lint, or build where relevant |
| `HIGH` | `MEDIUM` plus integration or regression verification and broader checks of the affected area |

Depth follows the task's risk level from the pre-flight classification.

```text
LOW
npm run test -- tests/import/parser.test.ts

MEDIUM
npm run test -- tests/import/loader.test.ts
npm run typecheck

HIGH
npm run test -- tests/import/loader.test.ts
npm run typecheck
npm run lint
npm run test:integration -- tests/integration/import.test.ts
```

Running the full suite after every small task is explicitly wrong. It is slow, it hides
which change broke what behind a wall of unrelated output, and its cost is what trains a
controller to stop verifying at all.

### Observing the right object

A command that exits zero is evidence only if it observed the thing the task changed.

```text
Does this verification observe the same relevant object,
state and boundary as the operation being validated?
```

Apply it to permissions, filesystem state, auth, environment boundaries, privileged
operations, network or service state, migrations, and external integrations. A migration
verified against an empty database, or a permission verified as root, observes a different
object than the one the acceptance criteria names.

The check has a limit: it is not applied to trivial unit tests, where the assertion
already names the object it observes.

## The deterministic scope check

```bash
git status --porcelain
git diff --name-only HEAD
```

Compare against the brief's expected file list.

```text
planned:
src/foo.ts
tests/foo.test.ts

actual:
src/foo.ts
tests/foo.test.ts
package.json
src/auth.ts

unexpected scope:
package.json
src/auth.ts
```

An unexpected path is detected, explained by the implementer, and reviewed.

Automatic failure is wrong. `package.json` may be a dependency the task genuinely needed
and the plan failed to anticipate, which is a plan defect rather than an implementer
defect. `src/auth.ts` in the same diff is a different matter: it is a security-relevant
surface nobody scoped, and it warrants a domain review before the task is accepted.

Silent acceptance is equally wrong. The point of the check is that the controller learns
about the extra path from `git`, not from whether the implementer chose to mention it.

Where a deterministic tool and model judgment could answer the same question, use the
tool. Judgment is spent on what the extra path means, not on noticing it.

## The whole-branch review

After every task is accepted, one review reads the branch as a whole.

Per-task review cannot see what only the accumulation shows: an abstraction three tasks
introduced and none completed, duplicated helpers each task added locally, an interface
that drifted across tasks while every individual change looked reasonable, and dead code
left behind by a later task's approach.

Findings here follow the same disposition rules. Integration fixes land before the final
matrix runs.

## The final verification matrix

```text
Final verification

[x] unit tests
[x] integration tests
[x] typecheck
[x] lint
[x] build
 -  e2e: not applicable
```

Six rows, in that order, always all present. A row that does not apply says so explicitly
rather than being dropped, because a dropped row reads as a passed check to every later
reader.

Each passing row is backed by a command run against the current tree in this session.
Neither a subagent's report nor a run from three tasks ago satisfies a row.

A reviewer `PASS` does not end the work by itself, and neither does a complete matrix.

## Evidence format

```text
Command:
npm run test:unit -- tests/unit/foo.test.ts

Result:
PASS 8 tests
```

A claim, evidence and a verdict are three different things. The record holds enough for a
reader to re-run the check and judge the result, and nothing more. A full transcript
carries the same evidence with the signal buried in it.

## Handoff

```text
all tasks accepted
  -> whole-branch review
  -> integration fixes
  -> final verification matrix
  -> verification-gate
  -> branch-finish
```

`verification-gate` owns the authoritative completion verdict; this skill supplies fresh
evidence to it and does not rule on its own work. `branch-finish` owns merge, cleanup and
the branch lifecycle.

These are two separate decisions. "Is this done" and "what happens to the branch now" have
different owners, and merging them is how an unverified branch gets merged because the
work felt finished.
