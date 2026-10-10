# Workspace Detection

Detection is read-only and precedes every workspace decision. Inspect the repository root,
working-tree root, Git directory, common Git directory, branch, `HEAD`, detached state,
superproject relationship, registered worktrees, and staged, tracked, and untracked changes.
Resolve the task's repository boundary before interpreting the result: a nested repository or
submodule may own the files under change instead of its parent monorepo.

## Deterministic helper

Task 4 adds `../scripts/inspect_workspace.py`. Run it with `--path <directory>` when Python 3
is available. It uses read-only Git commands, performs no network access or repository mutation,
and writes one JSON object to stdout. It accepts `--path` with `.` as the default.

| Key | Value |
| --- | --- |
| `git_repository` | Boolean Git-repository detection result. |
| `repo_root`, `workspace_root` | Canonical path or `null`. |
| `git_dir`, `git_common_dir` | Canonical Git metadata path or `null`. |
| `branch`, `head` | Branch or commit identity, each nullable. |
| `detached`, `submodule`, `linked_worktree` | Boolean identity flags. |
| `dirty_tracked`, `staged` | Boolean status flags. |
| `untracked`, `registered_worktrees` | Lists of paths. |

The helper degrades gracefully for a non-Git directory: `git_repository` is `false`, path and
identity values are `null`, booleans are `false`, and lists are empty. It is an optional
convenience. When Python is unavailable, run equivalent read-only Git inspection and record the
same facts manually.

## Classification guard

`git rev-parse --git-dir` and `git rev-parse --git-common-dir` can differ for a linked
worktree. The inequality is a signal, not proof. First run
`git rev-parse --show-superproject-working-tree`; a non-empty result identifies a submodule
checkout. A submodule is not a linked worktree for this classification, even when Git metadata
paths differ.

Detached `HEAD` is a first-class state. It may represent a harness-managed workspace, an
external CI or sandbox checkout, or a manually detached repository. Record the observed identity
and ownership evidence. Do not infer a disposable branch or create one as a reflex.

## Canonical paths and non-Git workspaces

Use a canonical physical path when comparing workspace identity or handing work to another
skill. Logical paths can pass through symlinks and resolve to a different physical directory.
Never remove or overwrite a target merely because its displayed path resembles an expected
workspace.

If Git inspection fails, report that Git lifecycle information is unavailable. A container,
sandbox, temporary checkout, or platform workspace can still be safe for the task. Record the
available canonical path, known owner, and actual isolation mechanism without inventing a branch
or cleanup lifecycle.
