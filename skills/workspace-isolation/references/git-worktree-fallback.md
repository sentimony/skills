# Manual Git Worktree Fallback

Manual Git worktrees are a fallback after existing safe isolation and a discovered
harness-native mechanism. Use one only when all four conditions hold:

1. The task needs isolation.
2. Active instructions permit worktrees.
3. No suitable existing or native workspace is available.
4. Git metadata and filesystem mutation are safe in the current environment.

## Preflight

Resolve the actual task repository and inspect it before mutation. Determine the target branch,
source or base revision, target path, parent-directory safety, existing branch and path use, and
registered worktrees. Do not guess `main`, `master`, `origin/main`, or the current branch as the
base. Use explicit request context, repository instructions, feature context, ancestry, or remote
default information. Resolve material ambiguity before creating a workspace.

Select a project-local parent in this order:

1. Explicit user or project instruction.
2. Established repository convention.
3. Existing safe project-local worktree parent.
4. The skill default, `.worktrees/`.

The default never overrides repository policy. When both `.worktrees/` and `worktrees/` exist,
follow the active convention. Before using a parent under the repository root, verify through Git
ignore semantics that the parent is ignored. An unignored parent blocks that location. Do not edit
or commit `.gitignore` as a workspace-setup side effect. Choose another safe location or obtain
separate authorization for the minimal ignore change.

Check whether the desired branch already exists, is checked out in another registered worktree,
or conflicts with a relevant remote branch. Check that the target path is empty or absent and
does not hold unrelated data. A collision requires a different safe name or a proven matching
workspace to reuse. Never remove, cannibalize, rename, or switch another checkout to satisfy a
preferred name.

## Creation and failure handling

Create only with the resolved branch, base, and path. Preserve the original checkout completely:
do not switch it, reset it, clean it, stash it, commit it, or copy its uncommitted changes. A dirty
original checkout can supply a known committed base, but its working state is not a clean source.

Treat stale or prunable worktree registrations as unrelated administration unless they block this
operation and ownership is understood. Do not prune them automatically. If Git metadata or
filesystem creation fails because of a sandbox, stop variant retries. Reassess native isolation,
safe work in place, or `BLOCKED`.

The only rollback allowed here is removal of the exact worktree and branch created by this
invocation after creation fails before handoff, with no implementation or user changes and certain
ownership. Leave every other workspace, registration, and branch for its owner.
