# Finish Option Procedures

Five options, in fixed order: `MERGE_LOCALLY`, `PUSH_OR_PR`, `MERGE_ON_FORGE`, `KEEP`,
`DISCARD`. An option the environment does not permit is not offered. Determine availability from the detected
environment, not from what is usually possible.

## Availability

| Condition | Consequence |
| --- | --- |
| No remote configured | `PUSH_OR_PR` and `MERGE_ON_FORGE` are unavailable. |
| Remote present, no PR tooling | Push is available; pull request creation and `MERGE_ON_FORGE` are not. Offer push with an explicit handoff. |
| Detached HEAD, branch creation permitted | `MERGE_LOCALLY` requires a branch first; say so rather than silently creating one. |
| Detached HEAD, branch creation forbidden | Only `KEEP` with a platform handoff remains. |
| Harness-owned workspace | Workspace removal is unavailable regardless of the chosen option. |
| Normal checkout, no linked worktree | No worktree cleanup applies; this is an absence, not a refusal. |
| Merge state not `CLEAN` | Every option waits until the in-progress operation is reconciled. |

State why an unavailable option is unavailable. A user who is told "no pull request, because
this repository has no remote configured" can fix the situation; one who is shown three options
where they expected five cannot.

The user's choice is authoritative. The one exception is a choice already made in context: a
request phrased as implement this and open a pull request has already selected the PR path, and
asking again is noise.

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

## `MERGE_ON_FORGE`

The pull request is merged by the forge, not by a local `git merge`. Offered when a remote and
forge tooling that can merge a pull request (such as `gh`) are both present.

1. **Confirm fresh verification** of the branch head, as above, and record that head's full
   SHA and tree (`git rev-parse <head> <head>^{tree}`).
2. **Find or create the pull request** as in `PUSH_OR_PR` steps 2-4: push only if the remote
   copy is behind, never duplicate a pull request.
3. **Wait for required checks.** Watch them (`gh pr checks <n> --watch --required`). A merge
   refused by branch policy while checks run is a wait, not an obstacle. The forge may suggest
   `--admin` or another bypass; it runs only with the user's explicit permission for this pull
   request. A failed check stops the path and routes to `debugging`.
4. **Merge with the chosen method,** pinned to the verified head:
   `gh pr merge <n> --squash --match-head-commit <full sha>`. Take the method from the user's
   request or the repository's history convention; do not assume squash. The flag takes only
   a full SHA; a short one fails. Leave out `--delete-branch`: it also deletes the local
   branch before the merged tree is checked; step 7 deletes it instead.
   A pull request that changed after verification fails the pin: stop and re-verify.
5. **Sync the base.** `git fetch --prune`, switch to the base in a clean working tree, then
   `git pull --ff-only`. A refused fast-forward means local base commits that are not on the
   remote: stop and report them.
6. **Prove or re-verify the merged tree.** The verification may carry over without a new run
   only when the merge commit's tree equals the verified tree
   (`git rev-parse <merge sha>^{tree}` is the tree from step 1). A squash on a base that did
   not move since the branch was verified gives exactly that. Record both hashes in the report
   as the evidence. Different trees mean the base moved: run `verification-gate` on the merged
   base.
7. **Delete the branch if the user asked,** after step 6. Delete the remote branch unless the
   forge already did (`git push <remote> --delete <branch>`), then confirm
   `git ls-remote --heads <remote> <branch>` is empty. After a squash or rebase merge Git
   cannot see the branch as merged, so `git branch -d` refuses. Use `git branch -D` only when
   the user asked to delete this branch and `git diff <branch> <merge sha>` is empty, which
   proves its content is on the base; otherwise preserve the branch and report why.
8. **Remove an owned worktree if safe,** by the ownership gate in `ownership-and-cleanup.md`.

A branch built on another branch that was already squash-merged shows false conflicts in its
pull request. Resolving them with `git merge -s ours <base>` is safe only when the tree of the
squash commit equals the tree of the merged branch's head; otherwise the conflicts are real
and follow the conflict rules above.

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

Every outcome follows this shape: the label, then the facts a reader needs to act on, then the
state of every resource the operation touched.

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

`MERGE_ON_FORGE`, with the tree carried over:

```text
Branch Finish

Outcome: MERGED AND VERIFIED
Source: <branch>
Base: <branch>, synced with <remote>
PR: <reference>, <method> merge
Merge commit: <full sha>
Verification: PASS, merged tree <tree> equals verified tree
Source branch: removed on <remote> and locally
Worktree: <removed, or preserved with ownership value>
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
