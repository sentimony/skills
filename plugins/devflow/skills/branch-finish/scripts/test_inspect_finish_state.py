#!/usr/bin/env python3
"""Tests for inspect_finish_state.py."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "inspect_finish_state.py"

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Probe",
    "GIT_AUTHOR_EMAIL": "probe@example.com",
    "GIT_COMMITTER_NAME": "Probe",
    "GIT_COMMITTER_EMAIL": "probe@example.com",
}


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    ).stdout.strip()


def run_inspector(path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        check=True,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return json.loads(result.stdout)


def seed_repo(root, default_branch):
    repo = Path(root) / "repo"
    repo.mkdir()
    git(repo.parent, "init", "-q", "-b", default_branch, "repo")
    (repo / "seed.txt").write_text("seed\n")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-q", "-m", "seed")
    return repo


class InspectorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bf-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_reports_non_default_branch_name_without_assuming_main(self):
        repo = seed_repo(self.tmp, "trunk")
        data = run_inspector(repo)
        self.assertEqual(data["branch"], "trunk")
        self.assertFalse(data["detached"])
        self.assertEqual(data["merge_state"], "CLEAN")

    def test_reports_detached_head(self):
        repo = seed_repo(self.tmp, "trunk")
        head = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-q", "--detach", head)
        data = run_inspector(repo)
        self.assertTrue(data["detached"])
        self.assertIsNone(data["branch"])

    def test_reports_untracked_and_dirty_separately(self):
        repo = seed_repo(self.tmp, "trunk")
        (repo / "seed.txt").write_text("seed\nchanged\n")
        (repo / "extra.txt").write_text("new\n")
        data = run_inspector(repo)
        self.assertTrue(data["dirty"])
        self.assertIn("extra.txt", data["untracked"])

    def test_reports_linked_worktree_without_claiming_ownership(self):
        repo = seed_repo(self.tmp, "trunk")
        linked = Path(self.tmp) / "linked"
        git(repo, "worktree", "add", "-q", str(linked), "-b", "feature")
        data = run_inspector(linked)
        self.assertTrue(data["linked_worktree"])
        self.assertEqual(data["worktree_owner"], "UNKNOWN")

    def test_reports_merge_in_progress(self):
        repo = seed_repo(self.tmp, "trunk")
        git(repo, "checkout", "-q", "-b", "side")
        (repo / "seed.txt").write_text("side\n")
        git(repo, "commit", "-q", "-am", "side change")
        git(repo, "checkout", "-q", "trunk")
        (repo / "seed.txt").write_text("trunk\n")
        git(repo, "commit", "-q", "-am", "trunk change")
        subprocess.run(
            ["git", "-C", str(repo), "merge", "side"],
            capture_output=True,
            text=True,
            env=GIT_ENV,
        )
        data = run_inspector(repo)
        self.assertEqual(data["merge_state"], "MERGE_IN_PROGRESS")

    def test_base_candidate_uses_upstream_over_convention(self):
        origin = seed_repo(self.tmp, "trunk")
        clone = Path(self.tmp) / "clone"
        subprocess.run(
            ["git", "clone", "-q", "--origin", "upstream", str(origin), str(clone)],
            check=True,
            capture_output=True,
            text=True,
            env=GIT_ENV,
        )
        git(clone, "checkout", "-q", "-b", "feature")
        git(clone, "branch", "--set-upstream-to", "upstream/trunk", "feature")
        data = run_inspector(clone)
        self.assertEqual(data["base_candidate"], "upstream/trunk")
        self.assertEqual(data["base_evidence"], "UPSTREAM")
        self.assertIn("upstream", data["remotes"])
        self.assertNotIn("origin", data["remotes"])

    def test_ambiguous_candidate_set_yields_no_base_rather_than_a_guess(self):
        """Several sibling branches and no remote must produce no candidate at all.

        Returning the first branch that shares an ancestor would label alphabetical
        luck as MERGE_BASE evidence, which is the exact failure this skill exists to
        prevent: a confident wrong base is worse than an absent one.
        """
        repo = seed_repo(self.tmp, "trunk")
        git(repo, "branch", "develop")
        git(repo, "branch", "release")
        git(repo, "checkout", "-q", "-b", "feature")
        data = run_inspector(repo)
        self.assertIsNone(data["base_candidate"])
        self.assertIsNone(data["base_evidence"])
        self.assertEqual(data["remotes"], [])

    def test_script_invokes_only_allowlisted_git_subcommands(self):
        """Guard by allowlist, because a blocklist of multi-word commands cannot match.

        A subprocess call is built as a list, so ``git worktree remove`` appears in the
        source as the separate tokens ``"worktree"`` and ``"remove"``. Searching for the
        joined string ``"worktree remove"`` would never match and the guard would pass on
        a mutating inspector. The allowlist inverts that: any git token the inspector uses
        must be named here deliberately.
        """
        source = SCRIPT.read_text()
        allowed = {
            "rev-parse",
            "status",
            "branch",
            "log",
            "remote",
            "worktree",
            "config",
            "merge-base",
            "symbolic-ref",
            "for-each-ref",
            "ls-files",
            # flags and arguments these subcommands take
            "--git-path", "--git-dir", "--git-common-dir", "--show-toplevel",
            "--abbrev-ref", "--porcelain", "--short", "--list", "--verify",
            "--quiet", "-C", "HEAD", "list", "get-url", "show",
            # this inspector's own CLI, not passed to git
            "--path", "--help",
            # detection flags this inspector passes to the subcommands above
            "--show-superproject-working-tree", "--is-inside-work-tree",
        }
        # Every quoted token passed to git in this source must be allowlisted.
        used = set(re.findall(r'"([a-zA-Z][a-zA-Z0-9_-]*|--[a-z-]+)"', source))
        git_verbs = {
            "merge", "push", "pull", "fetch", "commit", "add", "rm", "mv",
            "reset", "clean", "rebase", "checkout", "switch", "restore",
            "cherry-pick", "revert", "stash", "tag", "prune", "remove",
            "-d", "-D", "-f", "--force", "--hard",
        }
        leaked = sorted(used & git_verbs)
        self.assertEqual(
            leaked, [], f"inspector must stay read-only; found mutating tokens: {leaked}"
        )
        unknown = sorted(t for t in used if t.startswith("--") and t not in allowed)
        self.assertEqual(
            unknown, [], f"unrecognized git flags, review before allowlisting: {unknown}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
