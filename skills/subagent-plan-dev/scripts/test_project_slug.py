#!/usr/bin/env python3
"""Tests for project_slug.py: the same slug algorithm as context-transfer."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_slug  # noqa: E402

ENV = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@e.test",
           GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@e.test")


def git(path, *args):
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, env=ENV)


class ProjectSlugTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="sdd-slug-")))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_root_and_digest(self):
        self.assertEqual(project_slug.slug("/"), "root-8a5edab28263")

    def test_long_unicode_name_is_cut_on_a_character_boundary(self):
        path = self.tmp / ("щ" * 100)
        path.mkdir()
        result = project_slug.slug(path)
        name, _, digest = result.rpartition("-")
        self.assertEqual(digest, hashlib.sha256(os.fsencode(str(path))).hexdigest()[:12])
        self.assertEqual(name, "щ" * 32)
        self.assertLessEqual(len(os.fsencode(name)), 64)

    def test_symlink_gives_the_target_slug(self):
        target = self.tmp / "real"
        target.mkdir()
        link = self.tmp / "link"
        link.symlink_to(target, target_is_directory=True)
        self.assertEqual(project_slug.slug(link), project_slug.slug(target))

    def test_worktrees_share_the_main_checkout_key(self):
        main = self.tmp / "main"
        main.mkdir()
        git(main, "init", "-q")
        (main / "f").write_text("x")
        git(main, "add", "f")
        git(main, "commit", "-qm", "c")
        tree = self.tmp / "linked"
        git(main, "worktree", "add", "-q", str(tree), "-b", "other")
        self.assertEqual(project_slug.project_key(str(tree)), main)
        self.assertEqual(project_slug.project_key(str(main / ".")), main)

    def test_non_git_directory_uses_itself(self):
        self.assertEqual(project_slug.project_key(str(self.tmp)), self.tmp)

    def test_bare_common_dir_is_its_own_key(self):
        bare = self.tmp / "x.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        self.assertEqual(project_slug.project_key(str(bare)), bare)

    def test_state_root_lives_under_home(self):
        home = self.tmp / "home"
        root = project_slug.state_root(str(self.tmp), home=home)
        self.assertEqual(root.parent, home / ".sentimony" / "skills" / "subagent-plan-dev")
        self.assertEqual(root.name, project_slug.slug(self.tmp))
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
