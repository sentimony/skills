# Attribution and Adaptation

This skill is an original compact workflow informed by the parallel dispatch practices in
obra/superpowers. It is not a copy of an upstream skill.

The upstream material was inspected at commit
[`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
(release `v6.3.0`, 2026-08-12):

- [dispatching-parallel-agents](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/dispatching-parallel-agents/SKILL.md)
- [subagent-driven-development](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/SKILL.md)
- [using-git-worktrees](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/using-git-worktrees/SKILL.md)

## Retained ideas

- a child agent does not inherit the parent transcript or session history;
- each agent receives a focused, self-contained brief for one problem domain;
- parallel dispatch is limited to units without shared state or sequential dependencies;
- all eligible independent units are dispatched as one bounded wave;
- the coordinator reads the returned summaries, checks for conflicts, and verifies jointly;
- over-broad scope, implicit context, missing constraints, and undefined expected output are
  rejected before dispatch.

## Changed mechanisms

- independence requires a recorded mutation map, dependency edges, and external-state
  ownership rather than a judgment that units look unrelated;
- independence confidence is explicit on a four-value scale, with `UNCERTAIN` routed to
  investigation instead of a binary parallel decision;
- returned results carry status, mutation targets actually touched, evidence, and residual
  risks, so the integration check has something to verify;
- semantic conflict detection is separate from textual merge conflict, because a clean merge
  does not prove compatible assumptions;
- isolation is assessed as four separate kinds, and a Git worktree is treated as filesystem
  isolation only;
- the examples cover general read-only and mutating work rather than test failures alone.

## Intentionally excluded

- task loop, ledger, and review-fix cycle ownership, which belong to `subagent-plan-dev`;
- workspace and worktree creation and cleanup, which belong to `workspace-isolation` and the
  integration owner;
- plan parsing, task acceptance, and plan-level completion;
- persistent orchestration state of any kind.

The upstream project is licensed under MIT. This skill is distributed under the repository MIT
license, with attribution retained here.
