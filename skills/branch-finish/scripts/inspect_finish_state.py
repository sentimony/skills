#!/usr/bin/env python3
"""Report the Git state a finish decision depends on, as JSON on stdout.

Read-only by construction: every git subcommand this script invokes is an inspection
command, and the sibling test enforces that with an allowlist over this source.

One limitation is deliberate and matters to callers. ``worktree_owner`` never returns
``SKILL_OWNED``. Workspace provenance comes from the ``git-worktree-isolation`` handoff,
which is reported in conversation rather than written to disk, so no script can read it.
This inspector returns ``CURRENT_CHECKOUT`` for the main working tree and ``UNKNOWN`` for
a linked one; promoting that to any other ownership value is the caller's decision.

Base resolution is likewise partial. Of the six precedence levels, only ``UPSTREAM``,
``REMOTE_HEAD`` and ``MERGE_BASE`` are visible to Git. ``EXPLICIT_CONTEXT``,
``PR_METADATA`` and ``CONVENTION`` live outside the repository, and a stronger one of
those overrides whatever this script reports.
"""

import argparse
import json
import os
import subprocess
import sys

MERGE_STATE_FILES = [
    ("MERGE_HEAD", "MERGE_IN_PROGRESS"),
    ("rebase-merge", "REBASE_IN_PROGRESS"),
    ("rebase-apply", "REBASE_IN_PROGRESS"),
    ("CHERRY_PICK_HEAD", "CHERRY_PICK_IN_PROGRESS"),
    ("REVERT_HEAD", "REVERT_IN_PROGRESS"),
]


def git(path, *args):
    """Run a read-only git command, returning stripped stdout or None on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_lines(path, *args):
    out = git(path, *args)
    if not out:
        return []
    return [line for line in out.splitlines() if line]


def is_repository(path):
    return git(path, "rev-parse", "--is-inside-work-tree") == "true"


def resolve_branch(path):
    name = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if name in (None, "HEAD"):
        return None
    return name


def resolve_merge_state(path):
    for name, state in MERGE_STATE_FILES:
        located = git(path, "rev-parse", "--git-path", name)
        if located and os.path.exists(os.path.join(str(path), located)):
            return state
        if located and os.path.exists(located):
            return state
    return "CLEAN"


def resolve_worktree_kind(path):
    """Distinguish a linked worktree from a submodule and from the main working tree."""
    git_dir = git(path, "rev-parse", "--git-dir")
    common = git(path, "rev-parse", "--git-common-dir")
    if git_dir is None or common is None:
        return False, None, None
    superproject = git(path, "rev-parse", "--show-superproject-working-tree")
    differs = os.path.realpath(
        os.path.join(str(path), git_dir)
    ) != os.path.realpath(os.path.join(str(path), common))
    linked = bool(differs) and not superproject
    return linked, git_dir, common


def resolve_untracked(path):
    entries = git_lines(path, "status", "--porcelain")
    return [line[3:] for line in entries if line.startswith("??")]


def resolve_dirty(path):
    entries = git_lines(path, "status", "--porcelain")
    return any(not line.startswith("??") for line in entries)


def resolve_remote_head(path, remotes):
    """Read the remote's default branch from its symbolic ref, without network access."""
    for remote in remotes:
        ref = git(path, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
        if ref:
            return ref
    return None


def resolve_base(path, upstream, remotes, branch):
    if upstream:
        return upstream, "UPSTREAM"
    remote_head = resolve_remote_head(path, remotes)
    if remote_head:
        return remote_head, "REMOTE_HEAD"
    if branch:
        others = [
            line[2:].strip()
            for line in git_lines(path, "branch", "--list")
            if line[2:].strip() and line[2:].strip() != branch
        ]
        # Only an unambiguous candidate set produces a MERGE_BASE answer. With several
        # other branches this level cannot rank them, and reporting the first one would
        # dress a guess up as evidence.
        if len(others) == 1 and git(path, "merge-base", branch, others[0]):
            return others[0], "MERGE_BASE"
    return None, None


def inspect(path):
    if not is_repository(path):
        return {"repository": None, "error": "not a git working tree"}

    linked, _, _ = resolve_worktree_kind(path)
    branch = resolve_branch(path)
    upstream = git(path, "rev-parse", "--abbrev-ref", f"{branch}@{{u}}") if branch else None
    remotes = git_lines(path, "remote")
    base_candidate, base_evidence = resolve_base(path, upstream, remotes, branch)

    return {
        "repository": git(path, "rev-parse", "--show-toplevel"),
        "branch": branch,
        "head": git(path, "rev-parse", "HEAD"),
        "detached": branch is None,
        "linked_worktree": linked,
        "worktree": git(path, "rev-parse", "--show-toplevel"),
        "worktree_owner": "UNKNOWN" if linked else "CURRENT_CHECKOUT",
        "dirty": resolve_dirty(path),
        "untracked": resolve_untracked(path),
        "upstream": upstream,
        "remotes": remotes,
        "base_candidate": base_candidate,
        "base_evidence": base_evidence,
        "merge_state": resolve_merge_state(path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Report the Git state a finish decision depends on, as JSON."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="working tree to inspect (default: current directory)",
    )
    args = parser.parse_args()
    json.dump(inspect(args.path), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
