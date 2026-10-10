# Harness Handling

This is the only file in the package where platform tool names may appear, and they appear only
as examples of a capability that was detected. The skill reasons about capabilities, never about
brands.

## The five capabilities

Determine each semantically, from what the environment actually offers in this session:

| Capability | Question |
| --- | --- |
| native branch creation | Does the platform own branch creation, rather than raw Git? |
| native handoff | Does the platform provide a way to hand work back or exit a workspace? |
| push authority | Are outbound network operations to the remote permitted here? |
| pull request tooling | Is there a way to open or update a pull request from this session? |
| worktree ownership | Did the platform create and does it manage this working tree? |

A capability that cannot be established is absent. Attempting an operation to discover whether
it is permitted is not detection: a half-completed push or a partially created branch is state
the user did not ask for.

## Degradation per capability

| Missing | Behavior |
| --- | --- |
| native branch creation | Use Git directly only where the environment permits ref writes. Where it does not, preserve and hand off. |
| native handoff | Report the state precisely and leave the workspace in place. |
| push authority | `PUSH_OR_PR` is not offered. Say that outbound operations are unavailable. |
| pull request tooling | Offer push alone, and report the exact manual next step. |
| worktree ownership held by the platform | Workspace removal is never offered, whatever the finish outcome. |

## Detached HEAD under an agent harness

Common and not a defect. Platform-managed workspaces frequently check out a commit rather than a
branch. Handle it as follows:

- Do not repair it by creating a branch as a reflex. Ask whether the finish outcome needs one.
- If the outcome needs a branch and native branch creation exists, use it. The platform owns
  placement and cleanup, and bypassing it with `git branch` creates state the platform cannot
  see or manage.
- If no branch can be created, the commits are reachable only from HEAD. Say so in the report
  and name them, because they are lost when the workspace ends.

## Externally managed worktree

A working tree the platform created is `HARNESS_OWNED`. It is never removed by this skill,
regardless of how complete the work is. If the platform exposes an exit or teardown control,
that control is the correct way to end the workspace, and it belongs to the user's decision
rather than to a cleanup step.

## Sandbox without branch creation

Some environments deny writes to refs, or deny process spawning for Git entirely. The failure
mode is a permission error rather than a Git error. Report the limitation plainly, preserve the
work, and provide the handoff the platform does allow. Do not retry the same operation through a
lower-level command: a sandbox that denies `git branch` denies the plumbing underneath it too,
and working around it would be circumventing a restriction the user's environment placed
deliberately.

## Restricted push or authentication failure

A rejected push and a failed authentication are different:

- **Rejected push** means the remote moved. Inspect the divergence, report it, and let the user
  decide. Force is not a repair.
- **Authentication failure** is an external blocker. Report it with the exact error, and do not
  retry with alternative credentials, alternative remotes, or a different protocol.

Both leave the local branch intact. Neither authorizes cleanup, because the work has not reached
the destination.

## Native tooling examples

These names are examples of capabilities observed in some environments, not a list to check for:
a tool named `EnterWorktree` or a `/worktree` command indicates native worktree ownership; a
forge CLI indicates pull request tooling. The presence of any specific name is not required, and
its absence says nothing beyond that this particular tool is not here. Detect the capability,
then use whatever provides it.
