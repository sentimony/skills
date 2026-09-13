# Environment and Base Resolution

Answers two questions before any option is offered: where are we, and where would integration
go. Both are read-only. Nothing in this file mutates a repository.

## Detection procedure

Run these in the workspace being finished, before anything changes directory. Cleanup runs from
outside the workspace, so a value read after the change of directory describes the wrong place.

```bash
git rev-parse --show-toplevel        # repository root of this working tree
git rev-parse --abbrev-ref HEAD      # branch name, or HEAD when detached
git rev-parse HEAD                   # the commit being finished
git rev-parse --git-dir              # per-worktree git dir
git rev-parse --git-common-dir       # shared git dir
git status --porcelain               # tracked changes and untracked files
git rev-parse --abbrev-ref '@{u}'    # upstream, if the branch has one
git remote                           # configured remote names
git worktree list --porcelain        # every registered working tree
```

`scripts/inspect_finish_state.py` runs the equivalent set and emits one JSON object. Prefer it:
the merge-state derivation below is the part shell heuristics get wrong, and the script is
covered by a test that fails if a mutating subcommand is ever added to it.

## Interpreting each field

| Field | Meaning | What it does not mean |
| --- | --- | --- |
| `repository` | Root of the working tree being finished. | Not necessarily the main checkout. |
| `branch` | Current branch name, or `null` when detached. | A name here does not imply the branch is pushed or merged. |
| `head` | The commit being finished. | Not the base, and not the integrated result. |
| `detached` | `true` when HEAD points at a commit rather than a branch. | Not an error state; see below. |
| `linked_worktree` | `true` when the git dir differs from the common git dir and this is not a submodule. | Not evidence of ownership. |
| `worktree` | Absolute path of this working tree. | Not permission to remove it. |
| `worktree_owner` | `CURRENT_CHECKOUT` for the main working tree, `UNKNOWN` for a linked one. | Never `SKILL_OWNED`; see the limitation below. |
| `dirty` | `true` when tracked files are modified or staged. | Does not cover untracked or ignored files. |
| `untracked` | List of untracked paths, by name. | Does not include ignored paths. |
| `upstream` | The configured upstream ref, or `null`. | Not automatically the base. |
| `remotes` | Configured remote names. | An empty list is a valid state, not a failure. |
| `base_candidate` | The base the strongest Git-visible source supports, or `null`. | Not a decision; `EXPLICIT_CONTEXT` outranks it. |
| `base_evidence` | Which precedence level produced the candidate. | Absent evidence means ask, not guess. |
| `merge_state` | One of the five merge states. | Anything but `CLEAN` blocks a new operation. |

### The ownership limitation

The inspector never returns `SKILL_OWNED`. `workspace-isolation` is stateless by design: it
reports ownership in context and writes nothing to disk, so there is no handoff file for a
script to read. The inspector reports `CURRENT_CHECKOUT` when the path is the main working tree
and `UNKNOWN` when it is a linked one. Promotion to any other value is the caller's decision,
made from the `workspace-isolation` handoff present in the conversation.

This is a deliberate floor. A script that guessed ownership from a path would be wrong in
exactly the case that matters: a worktree someone else created under a path that looks familiar.

### The submodule guard

A submodule satisfies `git dir != git common dir` exactly as a linked worktree does. Before
concluding anything about isolation:

```bash
git rev-parse --show-superproject-working-tree
```

A non-empty result means a submodule. Treat it as a normal checkout: it has no worktree to
remove, and worktree cleanup rules do not apply to it.

### Merge state

Derived from the presence of service files under the per-worktree git dir, resolved with
`git rev-parse --git-path` so the answer is correct inside a linked worktree:

| Path present | State |
| --- | --- |
| `MERGE_HEAD` | `MERGE_IN_PROGRESS` |
| `rebase-merge/` or `rebase-apply/` | `REBASE_IN_PROGRESS` |
| `CHERRY_PICK_HEAD` | `CHERRY_PICK_IN_PROGRESS` |
| `REVERT_HEAD` | `REVERT_IN_PROGRESS` |
| none of the above | `CLEAN` |

Reconcile any state other than `CLEAN` before starting a new integration operation. Reconciling
means completing or aborting the operation already underway, with the user's decision where the
conflict is `SEMANTIC`.

### Detached HEAD

Treat it as its own state. The questions, in order:

1. **Can a branch be created here?** Attempt nothing to find out. Read the environment: a
   sandbox that denies writes to refs will fail the create, and that failure is not recoverable
   by retrying with lower-level commands.
2. **Is the workspace harness owned?** A detached HEAD in a platform-managed workspace is normal
   for that platform and is not a defect to repair.
3. **Does the platform expose a native branch or handoff control?** If it does, it owns the
   transition. See `harness-handling.md`.
4. **Are the commits preserved?** Commits reachable only from a detached HEAD are lost when the
   workspace is discarded. This is the fact the report must state accurately.

If the environment forbids branch and push operations, preserve the work and provide a
platform-appropriate handoff. A sandbox limitation is respected, never worked around with
low-level Git.

## Base-branch precedence

Six levels, strongest first. Each example below is illustrative only: every branch and remote
name shown is an example value, never a default this skill would reach for.

### 1. `EXPLICIT_CONTEXT`

The user or the plan metadata named the base. This outranks everything, including a configured
upstream, because a stated intention is stronger evidence than a stale configuration.

> Example: the plan header reads `Base: release/2026-09`. That is the base, even if the branch's
> upstream points somewhere else.

### 2. `UPSTREAM`

The upstream of the current branch, read with `git rev-parse --abbrev-ref '@{u}'`.

> Example: the command returns `upstream/trunk` (an example remote and branch, not a default).
> The base is `trunk` on the remote named `upstream`.

Note the shape: the upstream of the *feature* branch often points at the feature branch's own
remote copy rather than at the integration target. Read what it actually returns rather than
assuming it names the base.

### 3. `PR_METADATA`

An existing pull request declares its target. If PR tooling is available and a pull request
exists for this branch, its target branch is the base.

> Example: an open pull request targets `develop`. That is the base, and merging elsewhere would
> desynchronize the review from the integration.

### 4. `REMOTE_HEAD`

The default branch of the remote repository, read from the remote's `HEAD` symbolic ref rather
than assumed.

> Example: `git remote show <remote>` reports `HEAD branch: trunk`. Where no stronger source
> answers, `trunk` is the candidate.

### 5. `MERGE_BASE`

The nearest common ancestor among the candidate branches, found with `git merge-base`.

> Example: two long-lived branches exist. The feature's merge base with one is three commits
> back and with the other is two hundred, so the first is the candidate.

This level is weaker than it looks. It identifies where a branch forked, which is usually the
base but is not the same question, and it is silent when the candidate set is itself unclear.

### 6. `CONVENTION`

The repository's own stated convention, from its contributing guide, its agent instructions, or
a documented workflow.

> Example: the repository's instructions state that feature branches merge into `integration`.

### The decision rule

Take the strongest source that answers. If it yields exactly one candidate, that is the base.

If no source yields an unambiguous candidate, automatic merge is forbidden. Present what was
found and take the user's choice:

```text
Base branch is ambiguous. Candidates found:

  trunk       REMOTE_HEAD   remote <name> reports HEAD branch: trunk
  develop     MERGE_BASE    nearest common ancestor, 4 commits back

No stronger evidence is available. Which base should this merge into?
```

Naming the evidence beside each candidate lets the user correct the reasoning rather than only
the answer.
