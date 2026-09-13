# Ownership and Cleanup

Cleanup is where this skill can destroy work that was correct a moment earlier. Every rule here
exists because some specific loss is possible without it.

## The six ownership values

Emitted by `workspace-isolation` and consumed verbatim. This skill does not define a seventh and
does not translate them into a parallel vocabulary.

| Value | How it is recognized | Removal |
| --- | --- | --- |
| `CURRENT_CHECKOUT` | The working tree existed before this invocation began; typically the user's own checkout. | Nothing to remove. |
| `HARNESS_OWNED` | The active platform created or manages the workspace, and usually provides its own exit or teardown control. | Never by this skill. |
| `SKILL_OWNED` | `workspace-isolation` created it during this invocation, with permission, and said so in its handoff. | Permitted, subject to the state checks below. |
| `USER_OWNED` | The user created or designated it explicitly. | Never; the user removes their own workspace. |
| `EXTERNAL` | CI, a sandbox, or another external system owns it. | Never. |
| `UNKNOWN` | Provenance cannot be established safely. | Never. |

`UNKNOWN` is the default when no handoff is present, and it preserves. A worktree created by
hand, by a previous session, or by another tool all land here. That is the correct answer: the
absence of evidence of ownership is not evidence of disposability.

A linked worktree reported by `git rev-parse --git-dir` differing from `--git-common-dir` is
evidence that a worktree exists. It is not evidence of who owns it.

## Two operations, two gates

```text
workspace removal  -> permitted only for SKILL_OWNED with a workspace-isolation handoff
branch deletion    -> permitted by the three branch conditions, independent of ownership
```

Conflating these produces one of two failures. Gating branch deletion on ownership means a user
who merged in their own checkout can never delete the merged feature branch, because their
ownership is permanently `CURRENT_CHECKOUT`. Gating workspace removal on the branch conditions
means a verified merge authorizes deleting a directory that belongs to someone else.

The invariant's phrase `THE WORKSPACE IS PROVABLY OURS` governs workspace removal. Branch
deletion falls under the invariant's first half, about the verified integrated tree.

## Cleanup ordering

```text
integration
  -> verification of the resulting tree
  -> confirm the destination preserves the work
  -> clean up the source
```

The third step is the one most often skipped. Before removing a source, confirm the destination
actually contains the work: the merge commit exists on the base, the pushed branch matches local,
the pull request references the right head. A merge that appeared to succeed and a merge that
landed are different claims.

## What cleanup covers

Ownership-gated:

- removal of a feature worktree this invocation created;
- pruning of stale worktree registrations left by that removal;
- temporary metadata this skill or `workspace-isolation` created for this invocation.

Condition-gated:

- deletion of a local branch.

Nothing else. Unrelated worktrees, unrelated branches, build outputs, caches, and directories
that merely look stale are not touched. A workspace that looks abandoned belongs to someone.

## Protecting untracked work

Before any cleanup, inspect the target workspace:

```bash
git -C <workspace> status --porcelain
```

Uncommitted tracked changes or untracked files stop the cleanup. Name the files, preserve the
workspace, and report `CLEANUP INCOMPLETE` on top of whatever integration succeeded. Do not
auto-stash: a stash is a hiding place, and the user did not ask for one.

Untracked work carries the same safety weight as tracked work. An uncommitted design note or a
scratch script exists in exactly one place, which is more precarious than a tracked change, not
less.

### What Git's own refusal does and does not cover

Observed on git 2.39.5, in a probe repository built for this purpose. The `.gitignore` was
committed in the base repository before any worktree was added, so the ignored-file case tests
ignored content rather than an untracked `.gitignore`.

| Worktree state | `git worktree remove` | Directory afterwards |
| --- | --- | --- |
| clean | no output, exit 0 | removed |
| modified tracked file | `fatal: '<path>' contains modified or untracked files, use --force to delete it` | still present |
| untracked file only | `fatal: '<path>' contains modified or untracked files, use --force to delete it` | still present |
| ignored file only | no output, exit 0 | removed |

Three consequences:

1. **The refusal message does not distinguish the two blocking cases.** Git says "modified or
   untracked" for both. The skill inspects `status --porcelain` itself to tell the user which
   files are at stake.
2. **Ignored files do not block removal.** An ignored local configuration file, a scratch file
   matched by a pattern, or a local environment file is destroyed by a plain
   `git worktree remove` without any warning at all. `status --porcelain` does not show them
   either. When the workspace may hold ignored files the user would miss, list them with
   `status --porcelain --ignored` before removing.
3. **A single untracked file is enough to refuse.** This confirms that Git treats untracked work
   as blocking, which is the standard this skill applies.

`git worktree remove --force` is never used to get past the refusal. The refusal means files
exist in that workspace and nowhere else.

After a successful removal, `git worktree prune` clears the stale registration. This is
self-healing and safe: it removes bookkeeping for directories that are already gone.

## Branch deletion

Three conditions, all of which must hold:

1. **The integration outcome makes deletion appropriate.** A verified local merge does. A push
   awaiting review does not.
2. **The branch contents are preserved elsewhere.** On the base after a merge, on the remote
   after a push, or in an artifact the user named. "The work is finished" is not preservation.
3. **The working state is safe.** No workspace still has the branch checked out with uncommitted
   changes, and no in-progress operation depends on it.

| Situation | Deletion |
| --- | --- |
| Verified local merge into the base | Permitted |
| Open pull request still under review | Preserve; the branch is the review target |
| `KEEP` chosen | Preserve |
| Post-merge verification failed | Preserve; it is the recovery source |
| Branch pushed but not merged | Preserve unless the user states the remote copy is sufficient |

Use the safe deletion, which refuses on unmerged commits. Force-delete discards commits that
exist nowhere else and requires explicit destructive authorization naming this branch.

## Cleanup failure

A refused or failed cleanup is reported as `CLEANUP INCOMPLETE` alongside the integration
outcome that did succeed. It never converts a verified implementation into data loss, and it
never reads as an implementation failure. The report names what remains and where, so the user
can finish the cleanup themselves in one step.
