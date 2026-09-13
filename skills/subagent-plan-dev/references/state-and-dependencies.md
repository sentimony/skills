# State and dependencies

## The `.sdd/` layout

```text
.sdd/
└── <plan-id>/
    ├── state.json
    ├── tasks/<n>.md
    └── verification/<n>.md
```

One directory per plan. Two plans executed in the same repository do not collide, and a
re-run of the same plan finds its own state without guessing.

### Deriving `plan-id`

`plan-id` is the basename of the plan file without its extension.

```text
docs/plans/2026-09-12-user-import.md  ->  2026-09-12-user-import
```

Never generate a random identifier. A random id makes resume impossible for a controller
that did not create the state, which is exactly the case after an interruption.

### `state.json`

Holds the queue, task states, the dependency model, risk levels, and the detected
capabilities.

```json
{
  "plan": "docs/plans/2026-09-12-user-import.md",
  "capabilities": {
    "resume_agent": true,
    "explicit_model_selection": false,
    "reasoning_selection": false,
    "parallel_agents": true,
    "isolated_worktrees": true,
    "subagent_identity": true
  },
  "tasks": [
    {
      "id": 1,
      "state": "accepted",
      "risk": "LOW",
      "depends_on": [],
      "touches": ["src/import/parser.ts"],
      "consumes": [],
      "produces": ["parseRow"],
      "shared_interfaces": []
    },
    {
      "id": 2,
      "state": "in_review",
      "risk": "HIGH",
      "depends_on": [1],
      "touches": ["src/import/loader.ts", "src/db/schema.ts"],
      "consumes": ["parseRow"],
      "produces": ["ImportLoader"],
      "shared_interfaces": ["ImportLoader"]
    }
  ]
}
```

Task state is one of exactly six values: `pending`, `in_progress`, `in_review`, `blocked`,
`accepted`, `failed`.

`in_review` and `accepted` are separate states on purpose. An implementer finishing its
work does not accept the task; acceptance is the controller's decision, taken after its
own verification. Collapsing the two states erases the distinction the core invariant
rests on.

### `tasks/<n>.md`

One file per task, holding four things in order: the brief the implementer received, the
implementer's report, review findings with the verdict, and the controller's decision.

```markdown
# Task 2: Import loader

## Brief
Objective, acceptance criteria, dependencies, expected scope, verification expectations.

## Implementer report
What was built, deviations from the brief and why, the implementer's own test results.

## Review
Findings, each actionable. Verdict: PASS_WITH_FINDINGS.

## Controller decision
Accepted after controller-owned verification. Finding 2 deferred: cosmetic, recorded in
the plan follow-ups rather than fixed in this task.
```

These four belong in one file. Split across separate files, a report and the decision that
answered it drift apart, and a later reader cannot tell which finding the controller
actually ruled on.

### `verification/<n>.md`

The controller's own commands and their results, separate from the narrative, because
acceptance rests on these and nothing else.

```markdown
# Task 2 verification

Depth: HIGH (shared interface, database schema)

Command:
npm run test -- tests/import/loader.test.ts
Result:
PASS 14 tests

Command:
npm run typecheck
Result:
0 errors

Command:
npm run test:integration -- tests/integration/import.test.ts
Result:
PASS 6 tests
```

### The ignore rule

```bash
grep -qxF '.sdd/' .gitignore || printf '.sdd/\n' >> .gitignore
git check-ignore -q .sdd && echo ".sdd/ is ignored"
```

Run this during pre-flight, before the first dispatch. Runtime state is not part of the
project's history, and a controller that discovers this after twelve tasks has twelve
tasks' worth of state to remove from the index.

### What state holds and what it does not

State is readable by a human and holds only what coordination, resume, review and
verification need: briefs, reports, findings, decisions, commands and results.

It does not hold transcript dumps, full conversation history, or the plan's own text
copied over. The plan file stays the source of intent; `.sdd/` records what happened to
it.

## Resume

```text
read state.json
  -> reconcile recorded task states against git log and the working tree
  -> re-verify the last accepted boundary when the record is thin
  -> continue from the first task that is not accepted
```

A recorded state the repository does not corroborate is reset rather than trusted. A task
recorded `accepted` whose changes exist nowhere in the tree or in history goes back to
`pending` and is re-executed, and the discrepancy is reported to the user rather than
quietly corrected.

The reverse case is equally real: a task recorded `in_progress` whose changes are fully
present and passing was interrupted after the work and before the record. Verify it as if
it had just been reported, then accept or continue accordingly. Do not re-dispatch work
that is already done, and do not accept it because the tree looks plausible.

## The dependency model

Five keys, recorded per task:

| Key | Meaning |
| --- | --- |
| `depends_on` | task ids that must be accepted first |
| `touches` | files this task modifies |
| `consumes` | symbols and interfaces this task uses from earlier tasks |
| `produces` | symbols and interfaces later tasks will use |
| `shared_interfaces` | surfaces more than one task depends on |

### Five uses

1. **Execution order.** `depends_on` gives the queue.
2. **Drift detection.** When a task's `consumes` names a symbol an earlier task changed,
   the brief is stale before dispatch.
3. **Identifying load-bearing findings.** A finding against something in
   `shared_interfaces` reaches other tasks; the same finding against a private helper does
   not. This decides whether a fix must land before the next dispatch.
4. **Review context.** The reviewer is told what this task consumes and produces, so it
   can check the contract rather than guess at it.
5. **Parallel wave permission.** Disjoint `touches`, no mutual `depends_on`, and no shared
   entry in `shared_interfaces` are the conditions the wave decision rests on.

### Worked example

Tasks 5 and 6 both list `touches: [src/api/routes.ts]`. They have no `depends_on`
relationship and look independent from the plan's narrative. They are not: a wave would
have both implementers editing one file in separate workspaces, and the integration step
would resolve a conflict neither implementer knew about. Run them sequentially.

## The pre-task drift checklist

Before constructing a brief, check six things against the tree:

1. the files the task references still exist at the paths given;
2. the symbols and interfaces it names still exist under those names;
3. its dependencies are accepted, and their `produces` match what this task `consumes`;
4. the previous task's actual effects match what it was expected to produce;
5. rulings already made in this execution still hold;
6. current `HEAD` matches what the last accepted task left behind.

This is targeted and cheap. It samples what the task points at rather than re-reading the
repository, so it stays affordable before every single dispatch.

Drift found here is reconciled into the brief before dispatch, preserving plan intent. An
implementer handed a brief naming a file that moved two tasks ago spends its context
rediscovering the move, and reports it as a deviation the controller already knew about.
