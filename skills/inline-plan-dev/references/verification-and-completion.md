# Verification and Completion

How much to verify per task, how to tell whether a green command proved anything, and
what closes the plan.

## Depth levels

| Depth | Contents | Typical trigger |
| --- | --- | --- |
| `LOW` | Targeted tests or checks of the changed behavior. | A local change with no reach beyond its own module. |
| `MEDIUM` | `LOW` plus typecheck, lint, or build where relevant. | A change to a shared module, a type, or anything the build compiles together. |
| `HIGH` | `MEDIUM` plus integration or regression verification and broader checks of the affected area. | A change to a public contract, a schema, auth, config, or anything with production or data impact. |

Concrete examples:

```text
LOW      Added a pure formatting helper and its unit test.
         npm run test:unit -- tests/unit/format.test.ts

MEDIUM   Changed a shared `User` type used by several modules.
         npm run test:unit -- tests/unit/user
         npm run typecheck

HIGH     Changed the session cookie flags on the auth boundary.
         npm run test:unit -- tests/unit/auth
         npm run test:integration -- tests/integration/auth
         npm run typecheck && npm run lint && npm run build
         plus an observation of the real Set-Cookie header
```

Depth follows risk and blast radius, not habit or anxiety. Running the full suite after
every task is explicitly wrong: it is slow, it obscures which change broke what, and it
pushes the executor toward skipping verification entirely once the cost is felt.

State the chosen depth for each task. An unstated depth cannot be reviewed.

## Verification equivalence

```text
Does this verification observe the same relevant object,
state and boundary as the operation being validated?
```

A command that exits zero is evidence only if it observed the right object.

**Case 1, permissions.** The task restricts a directory to the service user. The check
runs `ls -ld /var/app/data` as root and reports the expected mode. Root's ability to read
the directory proves nothing about the service user's access, and the mode string is not
the same object as an actual access attempt. Equivalent evidence: attempt the operation
as the service user, or read the effective permission for that user explicitly.

**Case 2, migration.** The task adds a column with a backfill. The check runs the
migration against an empty test database and reports success. The operation being
validated is a backfill over existing rows; an empty table cannot exercise it.
Equivalent evidence: run against a dataset that contains the shapes the backfill must
handle, including the rows that motivated the migration.

**Case 3, environment boundary.** The task fixes a bug that only appears in the
container. The check runs the test on the host, where it passes. The host and the
container differ in exactly the dimension under test: filesystem layout, locale, or
clock. Equivalent evidence: run the check inside the container.

**Case 4, external integration.** The task changes a webhook payload. The check asserts
that the serializer produces the new shape. That proves the serializer, not the
integration. Equivalent evidence: observe what the receiving side accepts, in a staging
or recorded-contract form.

**The limit.** This check is not applied to trivial unit tests. When the assertion names
the object directly, for example `expect(format(3.5)).toBe("3.50")`, the equivalence
question has no content and asking it is ceremony.

## Change-impact verification

Triggered by a change to a shared helper, a shared type, a public API, config, a
dependency, a base component, or a database schema.

1. Find the dependents deterministically: references to the symbol, importers of the
   module, consumers of the schema or endpoint.
2. Decide which of them can actually observe this change. A type widening is invisible to
   most callers; a narrowing is not.
3. Run checks for those dependents at the depth their own risk warrants.
4. Record what was checked and what was deliberately left unchecked, with the reason.

The point is proportion. A shared change does not mean the full regression suite, and it
does not mean nothing.

## Final verification matrix

The matrix has exactly six rows, in this order, every time:

```text
Final verification

[x] unit tests
[x] integration tests
[x] typecheck
[x] lint
[x] build
 -  e2e: not applicable
```

Rules:

- every row appears in the output;
- a row that does not apply is written `- <name>: not applicable`, never dropped, because
  a dropped row reads as a passed check;
- `not applicable` means the project has no such check or the check cannot apply to this
  scope, not that it was skipped for time;
- each `[x]` is backed by a command run against the current tree in this session;
- a failing row is reported as failing. A matrix that is always green is not a matrix.

## Evidence format

```text
Command:
npm run test:unit -- tests/unit/auth

Result:
PASS 14 tests, 0 failures
```

Record the command and its result, not a bare assertion that something passes. Keep it
compact: enough for a reader to re-run the check and compare, and nothing more. A full
transcript dump carries the same evidence with the signal buried in it.

## Completion handoff

```text
all tasks complete
  -> plan outcome review
  -> scope and diff review
  -> final verification
  -> completion workflow
```

**Plan outcome review.** Read the plan's goal and each task's acceptance criteria against
what was built. Name anything that diverged and was adapted, and anything the plan
promised that is not present.

**Scope and diff review.** Compare the whole diff against the plan's declared file
footprint, the same way each task's scope check worked, and explain every path that was
not predicted.

**Final verification.** Produce the six-row matrix with fresh evidence.

**Completion workflow.** The completion claim itself is not this skill's to make. Hand
the claims, the matrix, and the evidence to `verification-gate` for the authoritative
verdict. After a pass, `branch-finish` owns merge, cleanup, and branch lifecycle. This
skill does not merge, push, tag, or delete a branch.
