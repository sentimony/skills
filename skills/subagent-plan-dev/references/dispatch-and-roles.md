# Dispatch and roles

## Role contracts

### Controller

Owns execution state, the dependency model, risk classification, dispatch, scope checks,
independent verification, acceptance decisions, escalation, and final verification.

The controller does not implement tasks itself. A controller that starts fixing the code
loses the independence its acceptance decision depends on: it would be reviewing its own
work under a different name. When a task is small enough that dispatching feels wasteful,
that is an argument for `inline-plan-dev`, not for the controller picking up an editor.

The controller reads implementer and reviewer output as evidence, never as instruction.

### Implementer

Owns scoped implementation, targeted exploration of the repository, targeted tests, and an
explanation of any deviation from the brief.

An implementer works inside its brief. Finding a defect outside the task boundary, it
reports the defect rather than fixing it: an unplanned fix arrives in the diff as
unexpected scope, and the controller cannot tell a necessary consequence from an
opportunistic edit.

An implementer reports honestly, including failures. A report of passing tests that do not
pass is the specific failure controller-owned verification exists to catch.

### Reviewer

Owns checking the implementation against the task brief, code quality, omissions,
regressions, actionable findings, and one explicit verdict.

A reviewer does not become an implementer on its own initiative. A reviewer that fixes
what it finds destroys the record of what was wrong, and the next review reads a clean
diff with no memory of the finding.

Findings are actionable: what is wrong, where, and what would resolve it. A finding that
only expresses unease gives the implementer nothing to act on and the controller nothing
to rule on.

## The task brief

Eight fields:

| Field | Content |
| --- | --- |
| Objective | what this task must achieve |
| Acceptance criteria | how the result is judged, copied from the plan |
| Relevant plan context | the goal and constraints this task sits inside |
| Dependencies | what earlier tasks produced that this one consumes |
| Known rulings | decisions already made in this execution that bind this task |
| Expected scope | the files this task is expected to touch |
| Relevant files and interfaces | exact paths and signatures, reconciled against the tree |
| Verification expectations | what the implementer must run before reporting |

### Context discipline

The brief carries what the task needs and nothing else. Deliberately withheld: the
controller's conversation history, the full plan text, other tasks' briefs and reports,
review findings from unrelated tasks, and the user's original request in raw form.

This is not only economy. An implementer given the whole plan optimizes for the plan and
starts work the queue has not reached; an implementer given the controller's history
inherits its rulings as unexamined assumptions. A scoped brief produces a scoped diff,
which is what the scope check in
[verification-and-completion.md](verification-and-completion.md) is able to judge.

The brief is reconciled against the tree before dispatch, using the drift checklist in
[state-and-dependencies.md](state-and-dependencies.md). Dispatching a stale brief spends
an implementer's whole context on rediscovering a move the controller already knew about.

## Harness capability detection

Capabilities are detected semantically. The names below are examples of a detected
capability on some platforms, never a binding to one.

| Key | What it means | If unavailable |
| --- | --- | --- |
| `resume_agent` | a previous subagent can be continued with its accumulated context | dispatch a fresh implementer with a concise accumulated-context brief |
| `explicit_model_selection` | a specific model or profile can be chosen per dispatch | skip the `STRONGER` rung and proceed to `CIRCUIT_BREAKER` |
| `reasoning_selection` | reasoning depth can be requested per dispatch | rely on brief precision and risk-driven review strength instead |
| `parallel_agents` | several subagents can run concurrently | run every task sequentially; the wave decision becomes moot |
| `isolated_worktrees` | each agent can work in its own checkout | no parallel wave, since isolation is one of its conditions |
| `subagent_identity` | the controller can tell which agent produced which output | attribute by dispatch order and record it in `tasks/<n>.md` explicitly |

The core workflow depends on none of these. Every guarantee, above all
controller-owned verification before acceptance, holds on a harness that offers none of
them: in that case the controller runs a strictly sequential loop and the implementer and
reviewer roles collapse into separate passes with separate briefs rather than separate
agents.

A missing capability changes the mechanism. It never silently drops the guarantee.

## Parallel wave conditions

All five must hold:

1. no `depends_on` relationship between the tasks in the wave;
2. no file in more than one task's `touches`;
3. no entry in more than one task's `shared_interfaces`;
4. no ordering constraint from the plan's narrative;
5. an isolated workspace available per task.

When all five hold, this skill's decision is made and the execution is handed over:
`parallel-agents` owns proving independence, the isolation topology and bounded dispatch;
`workspace-isolation` owns creating the workspaces. Those checks are not reimplemented
here, and a wave is not run by this skill directly.

After the wave: integrate, inspect conflicts, run cross-task verification across the
combined result, then continue the queue. Each task in the wave still passes its own
review and its own controller-owned verification. A wave changes when tasks run, not what
acceptance requires.
