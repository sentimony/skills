"""Tests for inspect_workspace.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "inspect_workspace.py"
EXPECTED_KEYS = {
    "git_repository",
    "repo_root",
    "workspace_root",
    "git_dir",
    "git_common_dir",
    "branch",
    "head",
    "detached",
    "submodule",
    "linked_worktree",
    "dirty_tracked",
    "staged",
    "untracked",
    "registered_worktrees",
}


def git(cwd, *args):
    """Run a git command in cwd and return its stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_repo(path):
    """Create a repository with one commit and a stable identity."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "--quiet", "--initial-branch", "main")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    (path / "file.txt").write_text("content\n", encoding="utf-8")
    git(path, "add", "file.txt")
    git(path, "commit", "--quiet", "-m", "initial")
    return path


def run_inspect(path, *, env=None, use_path=True, cwd=None, check=True):
    """Run the helper against path and return its completed process."""
    command = [sys.executable, str(SCRIPT)]
    if use_path:
        command.extend(["--path", str(path)])
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


def inspect(path):
    """Run the helper against path and parse its JSON output."""
    result = run_inspect(path)
    return json.loads(result.stdout)


class InspectWorkspaceTest(unittest.TestCase):
    def test_result_has_exact_keys_and_default_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = inspect(Path(tmp))
            self.assertEqual(set(data), EXPECTED_KEYS)
            self.assertIsInstance(data["git_repository"], bool)
            for key in (
                "detached",
                "submodule",
                "linked_worktree",
                "dirty_tracked",
                "staged",
            ):
                self.assertIsInstance(data[key], bool)
            for key in ("repo_root", "workspace_root", "git_dir", "git_common_dir"):
                self.assertIsNone(data[key])
            self.assertIsNone(data["branch"])
            self.assertIsNone(data["head"])
            self.assertIsInstance(data["untracked"], list)
            self.assertIsInstance(data["registered_worktrees"], list)

    def test_plain_checkout_is_not_a_linked_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            data = inspect(repo)
            self.assertEqual(set(data), EXPECTED_KEYS)
            self.assertTrue(data["git_repository"])
            self.assertFalse(data["linked_worktree"])
            self.assertFalse(data["submodule"])
            self.assertFalse(data["detached"])
            self.assertEqual(data["branch"], "main")

    def test_linked_worktree_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            linked = Path(tmp) / "linked"
            git(repo, "worktree", "add", "--quiet", str(linked), "-b", "feature")
            data = inspect(linked)
            self.assertTrue(data["linked_worktree"])
            self.assertFalse(data["submodule"])
            self.assertEqual(data["branch"], "feature")

    def test_submodule_is_not_reported_as_linked_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            inner = init_repo(Path(tmp) / "inner")
            outer = init_repo(Path(tmp) / "outer")
            git(
                outer,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "--quiet",
                str(inner),
                "sub",
            )
            git(outer, "commit", "--quiet", "-m", "add submodule")
            data = inspect(outer / "sub")
            self.assertTrue(data["submodule"])
            self.assertFalse(data["linked_worktree"])

    def test_detached_head_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            head = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "--quiet", "--detach", head)
            data = inspect(repo)
            self.assertTrue(data["detached"])
            self.assertIsNone(data["branch"])

    def test_dirty_and_untracked_state_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            (repo / "file.txt").write_text("changed\n", encoding="utf-8")
            (repo / "new.txt").write_text("new\n", encoding="utf-8")
            data = inspect(repo)
            self.assertTrue(data["dirty_tracked"])
            self.assertFalse(data["staged"])
            self.assertIn("new.txt", data["untracked"])

    def test_staged_status_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            (repo / "file.txt").write_text("staged\n", encoding="utf-8")
            git(repo, "add", "file.txt")
            data = inspect(repo)
            self.assertTrue(data["dirty_tracked"])
            self.assertTrue(data["staged"])
            self.assertEqual(data["untracked"], [])

    def test_registered_worktrees_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            linked = Path(tmp) / "linked"
            git(repo, "worktree", "add", "--quiet", str(linked), "-b", "feature")
            data = inspect(repo)
            self.assertEqual(
                data["registered_worktrees"],
                [str(repo.resolve()), str(linked.resolve())],
            )

    def test_default_path_uses_current_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = init_repo(Path(tmp) / "repo")
            data = json.loads(run_inspect(repo, use_path=False, cwd=repo).stdout)
            self.assertEqual(data["workspace_root"], str(repo.resolve()))
            self.assertEqual(data["repo_root"], str(repo.resolve()))

    def test_help_reports_cli_usage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("usage:", result.stdout)
        self.assertIn("--path PATH", result.stdout)

    def test_missing_git_executable_degrades_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()
            empty_bin = Path(tmp) / "empty-bin"
            empty_bin.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty_bin)
            result = run_inspect(workspace, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertFalse(data["git_repository"])
            self.assertEqual(set(data), EXPECTED_KEYS)

    def test_non_git_directory_degrades_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = inspect(Path(tmp))
            self.assertFalse(data["git_repository"])
            self.assertIsNone(data["repo_root"])


if __name__ == "__main__":
    unittest.main()
