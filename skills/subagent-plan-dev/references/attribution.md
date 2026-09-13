# Attribution and Adaptation

This skill is an original orchestration workflow informed by the subagent execution
practices in obra/superpowers. It is not a fork of an upstream skill.

The upstream material was inspected at commit
[`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
(release `v6.3.0`, 2026-08-12):

- [subagent-driven-development](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/SKILL.md)
- [implementer-prompt](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/implementer-prompt.md)
- [task-reviewer-prompt](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/task-reviewer-prompt.md)

The full analysis is recorded in the maintainer repository as
`docs/researches/2026-09-13-obra-superpowers-subagent-driven-development.md`.

## Retained ideas

- a written plan is the input, and this skill does not write one;
- a fresh scoped implementer per task, with the brief as the single source of requirements;
- context discipline: artifacts are handed over as files rather than pasted into prompts;
- an explicit reviewer seat separate from the implementer, with a named verdict;
- durable plan-scoped state in the working tree, so progress survives an interrupted
  session;
- one directory per plan, keyed on the plan file's basename, so two plans cannot read or
  overwrite each other's state;
- a whole-branch review after the last task, which sees what per-task review cannot;
- a pre-flight pass over the plan before the first dispatch.

## Changed mechanisms

- the controller runs its own verification against the tree before accepting a task.
  Upstream routes verification through the implementer's report and instructs reviewers
  not to re-run the suite, which makes acceptance rest on a claim the controller never
  checks. This inversion is the core invariant of this skill;
- state lives in `.sdd/<plan-id>/` with `state.json`, `tasks/<n>.md` and
  `verification/<n>.md`, rather than in a prose ledger. Controller-owned verification
  needs a place of its own, and structured task state is what a resume can reconcile
  against `git log`;
- the ignore rule is a line in the project's `.gitignore`, checked with `git check-ignore`,
  rather than a self-ignoring `*` file written into the state directory;
- risk is classified per task on a three-level scale and drives implementer strength,
  review strength, verification depth, specialist review and integration checks. Upstream
  selects a model tier by implementation complexity and has no risk taxonomy;
- dependencies between tasks are modelled explicitly with five keys, replacing a one-time
  pre-flight conflict scan with a model that also serves drift detection, review context
  and the parallel-wave decision;
- stagnation is detected from four named signals, so a stalled loop is caught on evidence
  rather than by exhausting a round counter;
- escalation is a four-step ladder with a named condition between steps, and the circuit
  breaker is the last rung rather than the primary mechanism;
- the scope check is deterministic, comparing the real diff against the brief's expected
  files, rather than a reviewer judging scope from the diff by eye;
- harness capabilities are detected semantically against six named keys, and a missing
  capability changes the mechanism rather than the guarantee;
- a parallel wave is permitted under five stated conditions and delegated to
  `parallel-agents` and `workspace-isolation`. Upstream forbids parallel implementers
  outright and offers batching instead;
- completion ends in a fixed six-row verification matrix, then hands the verdict to
  `verification-gate` and the branch lifecycle to `branch-finish`.

## Intentionally excluded

- the ledger as a prose file of formatted lines, which cannot be reconciled against the
  repository mechanically;
- the instruction that reviewers must not re-run tests, which removes the only independent
  check on an implementer's claims;
- the fixed five-round cap as the primary loop control, which spends every round before
  admitting a loop was stuck after the second;
- adjudication permitted only at the cap, which converts a stalled loop into a batch of
  deferred findings at a fixed price;
- Unicode verdict markers used as load-bearing control tokens, which are fragile across
  harnesses and unreadable in plain-text logs;
- upstream's `.superpowers/` directory under any name, and its `docs/superpowers/` plan
  path;
- the plugin-namespace skill references and the relative cross-skill file path, which
  assume one installation layout;
- helper scripts for workspace resolution, brief extraction and review packaging. Brief
  extraction by heading match swallows every section between one task heading and the
  next, and the workspace and packaging scripts are a handful of git calls that the
  references give directly;
- batching several plan tasks into one dispatch, which defeats the per-task acceptance
  boundary this skill is built on;
- the mandatory handoff into branch finishing as a single step, since the completion
  verdict and the branch lifecycle have separate owners here;
- polling and wait-interval guidance, which is harness-specific operational advice rather
  than workflow.

The upstream project is licensed under MIT. This skill is distributed under the repository
MIT license, with attribution retained here.
