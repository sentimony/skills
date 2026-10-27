#!/usr/bin/env python3
"""Tests for the PreToolUse commit guard that references/enforcement.md installs.

The hook command is read from the JSON block of enforcement.md, so the test covers
exactly what a user copies into .claude/settings.json.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
DASH = "\u2014"


def hook_command():
    text = (SKILL / "references" / "enforcement.md").read_text(encoding="utf-8")
    block = re.search(r"```json\n(.*?)\n```", text, re.DOTALL).group(1)
    hooks = json.loads(block)["hooks"]["PreToolUse"]
    return [h["command"] for entry in hooks if entry["matcher"] == "Bash" for h in entry["hooks"]][0]


class CommitGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("perl") is None:
            raise unittest.SkipTest("perl is not installed")
        cls.project = tempfile.mkdtemp()
        hooks = Path(cls.project) / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        # The reference tells the user to copy the bundled script here.
        script = SKILL / "scripts" / "dashfix-commit-guard"
        if script.is_file():
            shutil.copy(script, hooks / "dashfix-commit-guard")
        cls.command = hook_command()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.project, ignore_errors=True)

    def run_hook(self, command, raw=None):
        payload = raw if raw is not None else json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": command}})
        return subprocess.run(["sh", "-c", self.command], input=payload, text=True,
                              capture_output=True, env={"CLAUDE_PROJECT_DIR": self.project,
                                                        "PATH": "/usr/bin:/bin:/usr/local/bin"})

    def assertBlocked(self, command):
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 2, command)
        self.assertIn("dashfix:", result.stderr)

    def assertAllowed(self, command):
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0, (command, result.stderr))

    # 20261025-2100: dashes outside the commit message must not block the commit.

    def test_dash_replacement_before_commit_passes(self):
        self.assertAllowed("python3 -c \"import sys; t=t.replace('" + DASH + "', '-')\" "
                           "&& git commit -m \"Clean\"")

    def test_sed_replacement_then_commit_passes(self):
        self.assertAllowed("sed -i '' 's/" + DASH + "/-/g' doc.md; git commit -m \"Fix dashes\"")

    def test_heredoc_into_a_file_that_mentions_git_commit_passes(self):
        self.assertAllowed("cat >> notes.md <<'EOF'\nRun git commit " + DASH
                           + " never with this dash\nEOF\ngit add notes.md")

    def test_later_heredoc_outside_the_commit_passes(self):
        self.assertAllowed("git commit -F - <<'EOF'\nClean title\nEOF\n"
                           "cat > x.md <<'EOF'\na " + DASH + " b\nEOF")

    def test_plain_commit_passes(self):
        self.assertAllowed("git add . && git commit -m \"Plain message\"")

    def test_no_commit_passes(self):
        self.assertAllowed("echo 'a " + DASH + " b'")

    # The commit message itself is still checked.

    def test_dash_in_m_message_blocks(self):
        self.assertBlocked("git commit -m \"a " + DASH + " b\"")

    def test_dash_in_commit_with_global_option_blocks(self):
        self.assertBlocked("git -C repo commit -m \"a " + DASH + " b\"")

    def test_dash_in_heredoc_fed_to_commit_blocks(self):
        self.assertBlocked("git commit -F - <<'EOF'\nTitle\n\nbody " + DASH + " x\nEOF")

    def test_dash_in_command_substitution_heredoc_blocks(self):
        self.assertBlocked("git commit -m \"$(cat <<'EOF'\nfix " + DASH + " x\nEOF\n)\"")

    def test_escaped_dash_piped_into_commit_blocks(self):
        self.assertBlocked("printf 'a \\u2014 b' | git commit -F -")

    def test_dash_in_commit_after_other_commands_blocks(self):
        self.assertBlocked("git add -A && git commit -m \"x \u2013 y\"")

    def test_unparsable_payload_falls_back_to_the_whole_text(self):
        result = self.run_hook(None, raw="git commit -m \"a " + DASH + " b\" {not json")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
