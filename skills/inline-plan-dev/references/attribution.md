# Attribution and Adaptation

This skill is an original compact workflow informed by the plan-execution practices in
obra/superpowers. It is not a fork of an upstream skill.

The upstream material was inspected at commit
[`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
(release `v6.3.0`, 2026-08-12):

- [executing-plans](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/executing-plans/SKILL.md)
- [writing-plans](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans/SKILL.md)
- [finishing-a-development-branch](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/finishing-a-development-branch/SKILL.md)

The full analysis is recorded in the maintainer repository as
`docs/researches/2026-09-13-obra-superpowers-executing-plans.md`.

## Retained ideas

- a written plan is the input, and this skill does not write one;
- one critical pass over the whole plan happens before the first task;
- task status is explicit rather than implied by how far the work has progressed;
- execution happens in an isolated workspace rather than directly on a default branch;
- completion is an explicit separate step, not a judgment made in passing.

## Changed mechanisms

- plan fidelity is split into `PLAN INTENT`, `PLAN APPROACH` and `CURRENT REALITY`, so a
  stale implementation detail is adapted rather than followed or escalated;
- divergence is classified into seven named categories with a detection signal and a
  response for each;
- failures carry a two-value verdict, and the default for an ordinary failure is
  `investigate -> fix -> verify -> continue` rather than a stop;
- progress is durable in the plan file itself, and a recorded status is reconciled against
  `git log` and the working tree before it is trusted;
- verification depth is proportional on a three-level scale instead of a single
  instruction to run what the plan specifies;
- a verification must observe the same object, state and boundary as the operation it
  validates;
- scope is compared against the real diff with deterministic commands;
- the final check is a fixed six-row matrix in which an inapplicable row is stated rather
  than dropped.

## Intentionally excluded

- the advice to prefer a subagent-driven skill when subagents are available, because the
  two execution modes are an equal user choice and inline is not the weaker one;
- the instruction to follow every plan step exactly, which makes plan-versus-reality
  divergence unresolvable inside the workflow;
- the stop list that places a failing test beside a missing credential, which is the
  source of premature halts;
- ephemeral todo tracking as the record of progress, which does not survive an
  interrupted session;
- `.sdd/`, `.superpowers/` and any equivalent runtime state directory under another name;
- the mandatory handoff into branch finishing, which merges two separate decisions: this
  skill hands the verdict to `verification-gate` and the lifecycle to `branch-finish`;
- subagent orchestration, reviewer loops, model routing and task ledgers, which belong to
  `subagent-plan-dev`.

The upstream project is licensed under MIT. This skill is distributed under the repository
MIT license, with attribution retained here.
