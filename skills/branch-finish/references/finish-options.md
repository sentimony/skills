# Finish Option Procedures

Four options, in fixed order: `MERGE_LOCALLY`, `PUSH_OR_PR`, `KEEP`, `DISCARD`. An option the
environment does not permit is not offered. Determine availability from the detected
environment, not from what is usually possible.

## Availability

| Condition | Consequence |
| --- | --- |
| No remote configured | `PUSH_OR_PR` is unavailable in both halves. |
| Remote present, no PR tooling | Push is available; pull request creation is not. Offer push with an explicit handoff. |
| Detached HEAD, branch creation permitted | `MERGE_LOCALLY` requires a branch first; say so rather than silently creating one. |
| Detached HEAD, branch creation forbidden | Only `KEEP` with a platform handoff remains. |
| Harness-owned workspace | Workspace removal is unavailable regardless of the chosen option. |
| Normal checkout, no linked worktree | No worktree cleanup applies; this is an absence, not a refusal. |
| Merge state not `CLEAN` | Every option waits until the in-progress operation is reconciled. |

State why an unavailable option is unavailable. A user who is told "no pull request, because
this repository has no remote configured" can fix the situation; one who is shown three options
where they expected four cannot.

## `MERGE_LOCALLY`

1. **Confirm fresh verification.** The verdict must be `PASS` and must describe the current
   feature tree. Anything else routes to `verification-gate` first.
2. **Identify the base** by the precedence in `environment-and-base.md`. Ambiguity stops the
   merge and asks.
3. **Ensure the destination workspace is safe.** The merge happens in a working tree that has
   the base checked out. Confirm that tree is clean before checking out the base there: an
   unrelated dirty state in the destination is a stop, not something to stash away.
4. **Integrate.** Merge the feature branch into the base. Do not run `git pull` or `git rebase`
   first as an automatic step; if the base is behind its remote, surface that and let the update
   be a decision.
5. **Resolve integration state if needed.** Classify each conflict `MECHANICAL` or `SEMANTIC`.
   Resolve mechanical conflicts and inspect the resulting diff. Preserve or abort on semantic
   conflicts and surface the decision.
6. **Run `verification-gate` on the merged tree.** The pre-merge `PASS` describes a tree that no
   longer exists. This step is not optional and not replaceable by reasoning that the merge was
   clean.
7. **Delete the feature branch if appropriate,** by the three branch conditions in
   `ownership-and-cleanup.md`.
8. **Remove an owned worktree if safe,** by the ownership gate in the same reference.

A failure at step 6 stops everything after it. The branch and the workspace stay exactly where
they are, because they are the recovery source, and the failure routes to `debugging`.

## `PUSH_OR_PR`

1. **Confirm fresh verification,** as above.
2. **Inspect branch and remote state.** Is the branch already pushed, is the remote copy ahead,
   behind, or diverged, does a pull request already exist. Divergence is reported, never
   force-overwritten.
3. **Push safely.** Push the branch to the resolved remote. A rejected push means the remote
   moved: investigate and report. Force is not a repair and is not used without explicit
   authorization for this specific push.
4. **Create or update the pull request if the capability exists.** An existing pull request is
   updated or reported, never duplicated. Where creation tooling is absent, report the pushed
   branch and the exact next step available to the user.
5. **Report.** Name the pull request only if one exists.

The workspace is preserved on this path. Review feedback is iterated in it, and removing it
turns the next round of comments into a re-setup task.

## `KEEP`

No integration operation runs. Confirm nothing is left half-done: an in-progress merge is
reconciled even here, because leaving `MERGE_HEAD` in place hands the user a repository in a
state they did not choose.

Report branch, HEAD, workspace path, and verification status. This is a successful outcome with
the label `BRANCH PRESERVED`, not a partial one.

## `DISCARD`

A separate destructive operation. It runs only on explicit user confirmation, or on an explicit
prior instruction to discard this specific work. Finishing work is not permission to destroy it,
and an inference that the user has lost interest is not authorization.

Before discarding, show the impact:

```text
This will permanently delete:

Branch: <branch>
Commits: <list, oldest first>
Uncommitted files: <list, or none>
Untracked files: <list, or none>
Worktree: <path, or none>
Remote branch: <reference, or none>
```

Then wait. On confirmation, remove only the artifacts named in that block. Broad cleanup
commands are forbidden: `git clean -fd`, `git reset --hard`, and recursive deletes by pattern
all reach beyond the scope shown to the user.

If part of the discard fails, report what was and was not removed. A partial discard reported
accurately is recoverable; one reported as complete is not.

## Report templates

`MERGE_LOCALLY`, fully successful:

```text
Branch Finish

Outcome: MERGED AND VERIFIED
Source: <branch>
Base: <branch>
Integrated HEAD: <sha>
Verification: PASS
Source branch: removed
Worktree: removed
Remote changes: none
```

`PUSH_OR_PR` with a pull request:

```text
Branch Finish

Outcome: PR CREATED
Branch: <branch>
Remote: pushed
Verification: PASS
Workspace: preserved
PR: <reference>
```

`PUSH_OR_PR` where creation tooling is absent:

```text
Branch Finish

Outcome: BRANCH PUSHED
Branch: <branch>
Remote: <name>
Verification: PASS
Workspace: preserved
PR: not created, no pull request tooling detected
Next: open the pull request against <base> manually
```

`KEEP`:

```text
Branch Finish

Outcome: BRANCH PRESERVED
Branch: <branch>
HEAD: <sha>
Verification: <verdict>
Workspace: <path>
```

A detached-HEAD handoff:

```text
Branch Finish

Outcome: WORK HANDED OFF
State: detached HEAD, branch creation unavailable in this environment
HEAD: <sha>
Commits at risk: <list>
Verification: <verdict>
Workspace: preserved, <ownership value>
Next: <platform-appropriate handoff>
```

A successful merge with refused cleanup:

```text
Branch Finish

Outcome: MERGED AND VERIFIED
Cleanup: CLEANUP INCOMPLETE
Reason: untracked files remain in <path>
Files: <list>
Workspace: preserved
```

`DISCARD`, after confirmation:

```text
Branch Finish

Outcome: WORK DISCARDED
Branch: <branch>, deleted
Commits: <count> discarded
Worktree: <path>, removed
Remote branch: <reference, deleted or none>
```
