# Plan Reconciliation

How to keep a plan authoritative about intent while its implementation details age.

## The triad in practice

| Term | Question it answers |
| --- | --- |
| `PLAN INTENT` | which outcome is required |
| `PLAN APPROACH` | how the plan expected to reach it |
| `CURRENT REALITY` | how the repository looks now |

The plan is binding on `PLAN INTENT` and advisory on `PLAN APPROACH`. Executing the
approach faithfully while missing the intent is a failure, not fidelity.

**Worked example, approach only.** The task says: add the rate limit to
`src/api/handler.ts:44`. The handler moved to `src/api/routes/handler.ts` and the
surrounding function was renamed. Intent (requests are rate limited at the API edge) is
unchanged. Adapt, record `FILE_MOVED` and `SYMBOL_RENAMED`, continue without asking.

**Worked example, intent touched.** The task says: store the limit counter in Redis.
The project dropped Redis and now has no shared cache at all. Any substitute changes the
architecture, the operational surface, or the behavior under multiple instances. That is
`APPROACH_NO_LONGER_SUITABLE` reaching intent: present the options and the trade-offs,
and let the user choose before implementing.

**Worked example, already done.** The task's acceptance criteria are already met by code
in the tree. Verify the criteria against real behavior rather than against the presence
of similar-looking code. If they hold, record `ALREADY_IMPLEMENTED`, mark the task `done`
with that note, and move on. If they hold partially, execute only the remainder.

## Divergence categories

| Category | Detection signal | Response |
| --- | --- | --- |
| `FILE_MOVED` | The referenced path does not exist; a file with the same responsibility exists elsewhere. | Retarget to the real path, verify it is the same unit and not a copy, and record the new path in the task. |
| `SYMBOL_RENAMED` | The named function, type, or constant is absent; a renamed equivalent is present. | Use the current name, confirm the signature still matches the task's use, and record the mapping once for later tasks. |
| `API_CHANGED` | The symbol exists, but its parameters, return type, or error contract differ from the plan's use. | Adapt the call site to the current contract. If the change removes a capability the task needs, treat it as reaching intent. |
| `ALREADY_IMPLEMENTED` | The acceptance criteria already hold before the task runs. | Verify against behavior, record the finding, mark the task `done` or execute only the remaining part. |
| `DEPENDENCY_VERSION_DIFFERS` | The installed version differs from the one the plan assumed. | Check whether the used capability exists in the installed version. Adapt to it; do not upgrade or downgrade a dependency to match a plan. |
| `INTERFACE_CHANGED_BY_PRIOR_TASK` | An earlier task in this same execution produced a different interface than the plan predicted. | Propagate the real interface to the dependent tasks now and update their briefs, so the drift is fixed once instead of at every consumer. |
| `APPROACH_NO_LONGER_SUITABLE` | The approach still runs, but its premise is gone: a removed subsystem, a changed platform constraint, a superseded pattern. | Check whether the intended outcome is still required. If it is, present alternatives with trade-offs and obtain a decision. |

Record every divergence you act on with its category, the evidence, and the adaptation.
A silent adaptation is indistinguishable from a mistake when the diff is reviewed later.

## What is material enough to ask about

Ask the user before proceeding when the divergence changes any of:

- the outcome the plan promises, or an acceptance criterion;
- material architecture: a storage boundary, a process boundary, a public contract;
- product behavior a user or caller can observe;
- agreed scope, including work the plan explicitly excluded;
- security, privacy, or data handling posture;
- an irreversible or externally visible action.

Do not ask about: paths, names, signatures, import order, local structure, test file
placement, or any detail the plan could not have known at writing time.

When you do ask, present the finding, the options, and a recommendation. An open question
with no recommendation moves the work back to the user without progress.

## Pre-task drift check

Run before each task. Targeted, not exhaustive.

1. **Files.** Does every path the task names exist? Any that does not is a divergence,
   not an error.
2. **Symbols and interfaces.** Do the named functions, types, and signatures match what
   the task expects to call?
3. **Dependencies.** Are the packages and versions the task relies on installed, and do
   they carry the capability it uses?
4. **Previous task effects.** What did the last task actually change, and does this task
   still fit that result?
5. **Prior rulings.** Which decisions were already made in this execution, by the user or
   by reconciliation, that this task must respect?
6. **Current `HEAD`.** Did the tree move since the plan review, for example through an
   external commit, a rebase, or a branch change?

The check reads the task and samples what the task points at. It does not re-read the
repository, and it does not re-run the full plan review from section 1.

## Plan-update policy

The plan file is updated as execution proceeds, within limits.

**Update:**

- task status, using `pending`, `in_progress`, `done`, `blocked`;
- step checkboxes, from `- [ ]` to `- [x]`;
- material task-level details that diverged: real paths, real names, real signatures;
- rulings made during execution, recorded where the affected task can see them.

**Do not update:**

- the plan's goal, architecture section, or global constraints, which record what was
  agreed;
- the narrative and rationale, which explain why the plan was written that way;
- earlier tasks' history, to make the record look cleaner than the execution was.

The plan is a record of what was agreed and what happened, not a document polished after
the fact. A reviewer reading the plan and the diff together should be able to see where
reality diverged and what was done about it.
