# Attribution and Adaptation

This skill is an original compact workflow informed by the workspace and execution practices in
obra/superpowers. It is not a copy of an upstream skill.

The upstream material was inspected at commit
[`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
(release `v6.3.0`, 2026-08-12):

- [using-git-worktrees](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/using-git-worktrees/SKILL.md)
- [finishing-a-development-branch](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/finishing-a-development-branch/SKILL.md)
- [subagent-driven-development](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/SKILL.md)
- [executing-plans](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/executing-plans/SKILL.md)

## Retained ideas

- inspect for existing isolation before creating a second workspace;
- distinguish linked-worktree metadata from a submodule boundary;
- record exact workspace identity and a starting baseline;
- prefer explicit workspace placement and branch context;
- keep worktree creation and lifecycle decisions deliberate.

## Changed mechanisms

- isolation is capability-based and includes harness-native and safe work-in-place outcomes;
- ownership has explicit provenance and discovery grants no cleanup authority;
- manual creation requires consent for new lifecycle state when policy does not decide it;
- baseline and setup are proportional to the selected workspace and project instructions;
- separate filesystem state is reported apart from runtime and shared-state isolation.

## Intentionally excluded

- `.gitignore` auto-commit;
- manifest-triggered package installation;
- an assumed base branch;
- assumed cleanup authority;
- automatic cleanup after handoff;
- implementation-task orchestration, integration, final verification, and branch completion.

The upstream project is licensed under MIT. This skill is distributed under the repository MIT
license, with attribution retained here.
