#!/usr/bin/env python3
"""Inspect Git workspace identity and state without mutating the repository."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def empty_result():
    """Return the result for a path that is not a Git worktree."""
    return {
        "git_repository": False,
        "repo_root": None,
        "workspace_root": None,
        "git_dir": None,
        "git_common_dir": None,
        "branch": None,
        "head": None,
        "detached": False,
        "submodule": False,
        "linked_worktree": False,
        "dirty_tracked": False,
        "staged": False,
        "untracked": [],
        "registered_worktrees": [],
    }


def git_output(target, *args, preserve_whitespace=False):
    """Run a read-only Git command and return its stripped stdout on success."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(target),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout if preserve_whitespace else result.stdout.strip()


def resolve_git_path(value, target):
    """Resolve Git output relative to the Git command's working directory."""
    path = Path(value)
    if not path.is_absolute():
        path = target / path
    return str(path.resolve())


def inspect_workspace(target):
    """Return deterministic Git identity and working-tree state for target."""
    repo_root_output = git_output(target, "rev-parse", "--show-toplevel")
    if repo_root_output is None:
        return empty_result()

    repo_root = resolve_git_path(repo_root_output, target)
    git_dir_output = git_output(target, "rev-parse", "--git-dir")
    git_common_dir_output = git_output(target, "rev-parse", "--git-common-dir")
    branch_output = git_output(target, "rev-parse", "--abbrev-ref", "HEAD")
    head = git_output(target, "rev-parse", "HEAD")
    git_output(target, "rev-parse", "--is-inside-work-tree")
    superproject = git_output(
        target, "rev-parse", "--show-superproject-working-tree"
    )

    git_dir = (
        resolve_git_path(git_dir_output, target)
        if git_dir_output is not None
        else None
    )
    git_common_dir = (
        resolve_git_path(git_common_dir_output, target)
        if git_common_dir_output is not None
        else None
    )
    submodule = bool(superproject)
    linked_worktree = bool(
        git_dir and git_common_dir and git_dir != git_common_dir and not submodule
    )
    detached = branch_output == "HEAD"
    branch = None if detached else branch_output

    status = (
        git_output(target, "status", "--porcelain", preserve_whitespace=True) or ""
    )
    dirty_tracked = False
    staged = False
    untracked = []
    for line in status.splitlines():
        if len(line) < 3:
            continue
        index_status, worktree_status = line[:2]
        path = line[3:]
        if index_status == "?" and worktree_status == "?":
            untracked.append(path)
            continue
        if index_status != " " or worktree_status != " ":
            dirty_tracked = True
        if index_status != " ":
            staged = True

    worktree_listing = git_output(target, "worktree", "list", "--porcelain") or ""
    registered_worktrees = []
    for line in worktree_listing.splitlines():
        if line.startswith("worktree "):
            registered_worktrees.append(resolve_git_path(line[9:], target))

    return {
        "git_repository": True,
        "repo_root": repo_root,
        "workspace_root": str(target),
        "git_dir": git_dir,
        "git_common_dir": git_common_dir,
        "branch": branch,
        "head": head,
        "detached": detached,
        "submodule": submodule,
        "linked_worktree": linked_worktree,
        "dirty_tracked": dirty_tracked,
        "staged": staged,
        "untracked": untracked,
        "registered_worktrees": registered_worktrees,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect Git workspace identity and state without mutation."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="directory to inspect (default: current working directory)",
    )
    args = parser.parse_args(argv)

    target = Path(args.path).expanduser()
    try:
        if not target.is_dir():
            parser.error(f"path is not a directory: {target}")
        target = target.resolve()
        data = inspect_workspace(target)
    except OSError as error:
        parser.error(str(error))

    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
