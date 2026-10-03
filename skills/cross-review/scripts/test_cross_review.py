"""Standalone unit tests for cross_review command adapters and loop guard."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cross_review as cr  # noqa: E402

SESSION = "11111111-1111-4111-8111-111111111111"


def expected_claude(model="claude-opus-5-5", effort="medium"):
    # Literal list on purpose: never derive expectations from production constants.
    return [
        "claude", "-p", "--model", model, "--effort", effort,
        "--permission-mode", "default", "--tools", "Read,Grep,Glob",
        "--allowedTools", "Read,Grep,Glob", "--disallowedTools",
        "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*",
        "--strict-mcp-config", "--disable-slash-commands", "--safe-mode",
        "--setting-sources", "project",
        "--session-id", SESSION,
    ]


def expected_codex(repo, run, model="gpt-6.1-sol", effort="low"):
    return [
        "codex", "exec", "-s", "read-only", "-m", model,
        "-c", 'model_reasoning_effort="%s"' % effort,
        "-C", str(repo), "-o", str(run / "review.md"), "-",
    ]


class GuardTests(unittest.TestCase):
    def test_depth_blocks(self):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.ensure_not_nested({"CROSS_REVIEW_DEPTH": "1"})
        self.assertEqual(caught.exception.code, 20)

    def test_empty_depth_also_blocks(self):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.ensure_not_nested({"CROSS_REVIEW_DEPTH": ""})
        self.assertEqual(caught.exception.code, 20)

    def test_absent_depth_passes(self):
        self.assertIsNone(cr.ensure_not_nested({"PATH": "/usr/bin"}))

    def test_child_inherits_depth_without_mutating_parent(self):
        parent = {"TASK_SENTINEL": "present"}
        cr.ensure_not_nested(parent)
        child = cr.reviewer_environment(parent)
        self.assertEqual(child["CROSS_REVIEW_DEPTH"], "1")
        self.assertEqual(child["TASK_SENTINEL"], "present")
        self.assertNotIn("CROSS_REVIEW_DEPTH", parent)

    def test_child_environment_keeps_host_markers(self):
        # Task 1 probe showed no host-marker scrub is needed for nested claude -p.
        parent = {"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "HOME": "/h"}
        child = cr.reviewer_environment(parent)
        self.assertEqual(child, dict(parent, CROSS_REVIEW_DEPTH="1"))


class ConstantsTests(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(cr.DEFAULTS, {"codex": ("gpt-6.1-sol", "low"),
                                       "claude": ("claude-opus-5-5", "medium")})

    def test_exit_codes(self):
        self.assertEqual(
            (cr.EXIT_OK, cr.EXIT_INVALID_INPUT, cr.EXIT_NESTED, cr.EXIT_MISSING_CLI,
             cr.EXIT_REVIEWER_FAILED, cr.EXIT_EMPTY_RESULT, cr.EXIT_NO_SESSION),
            (0, 2, 20, 21, 22, 23, 24),
        )

    def test_error_carries_code_and_message(self):
        err = cr.CrossReviewError(23, "empty")
        self.assertEqual((err.code, err.message), (23, "empty"))


class ArgvTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.repo = base / "my repo"
        self.repo.mkdir()
        self.run = base / "run dir"

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, reviewer, model, effort, repo=None):
        return cr.build_run_command(reviewer, repo or self.repo, self.run,
                                    model, effort, SESSION)

    def test_claude_run_security_argv(self):
        self.assertEqual(self.build("claude", "claude-opus-5-5", "medium"),
                         expected_claude())

    def test_claude_override_changes_only_model_and_effort(self):
        self.assertEqual(self.build("claude", "claude-sonnet-x", "high"),
                         expected_claude("claude-sonnet-x", "high"))

    def test_codex_run_argv(self):
        self.assertEqual(self.build("codex", "gpt-6.1-sol", "low"),
                         expected_codex(self.repo, self.run))

    def test_codex_override_changes_only_model_and_effort(self):
        self.assertEqual(self.build("codex", "gpt-other", "high"),
                         expected_codex(self.repo, self.run, "gpt-other", "high"))

    def test_paths_with_spaces_stay_single_tokens(self):
        argv = self.build("codex", "gpt-6.1-sol", "low")
        self.assertIn(str(self.repo), argv)
        self.assertIn(str(self.run / "review.md"), argv)

    def test_shell_metacharacters_are_literal(self):
        repo = self.repo.parent / "r; rm -rf $HOME `x` | & >out"
        repo.mkdir()
        argv = self.build("codex", "m;$(id)", "e|x", repo=repo)
        self.assertEqual(argv, expected_codex(repo, self.run, "m;$(id)", "e|x"))
        self.assertTrue(all(isinstance(token, str) for token in argv))

    def test_returns_fresh_list(self):
        first = self.build("claude", "claude-opus-5-5", "medium")
        first.append("--dangerously-skip-permissions")
        self.assertEqual(self.build("claude", "claude-opus-5-5", "medium"),
                         expected_claude())

    def assertInvalid(self, *args, **kwargs):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.build_run_command(*args, **kwargs)
        self.assertEqual(caught.exception.code, 2)

    def test_invalid_reviewer(self):
        for reviewer in ("gemini", "", "Codex"):
            self.assertInvalid(reviewer, self.repo, self.run, "m", "e", SESSION)

    def test_empty_model_or_effort(self):
        for reviewer in ("codex", "claude"):
            self.assertInvalid(reviewer, self.repo, self.run, "", "low", SESSION)
            self.assertInvalid(reviewer, self.repo, self.run, "m", "", SESSION)
            self.assertInvalid(reviewer, self.repo, self.run, "  ", "low", SESSION)

    def test_codex_effort_cannot_escape_toml_string(self):
        self.assertInvalid("codex", self.repo, self.run, "m", 'low" x="y', SESSION)

    def test_missing_repo(self):
        missing = self.repo.parent / "absent repo"
        for reviewer in ("codex", "claude"):
            self.assertInvalid(reviewer, missing, self.run, "m", "e", SESSION)

    def test_claude_requires_uuid_session(self):
        self.assertInvalid("claude", self.repo, self.run, "m", "e", "not-a-uuid")


class SafetyMutantTests(unittest.TestCase):
    """Removing any safety flag from the expected argv must break equality."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.run = self.repo / "run"

    def tearDown(self):
        self._tmp.cleanup()

    def test_claude_mutants_detected(self):
        actual = cr.build_run_command("claude", self.repo, self.run,
                                      "claude-opus-5-5", "medium", SESSION)
        good = expected_claude()
        self.assertEqual(actual, good)
        mutants = {
            "--tools": lambda a: a[:a.index("--tools")] + a[a.index("--tools") + 2:],
            "--strict-mcp-config": lambda a: [t for t in a if t != "--strict-mcp-config"],
            "--safe-mode": lambda a: [t for t in a if t != "--safe-mode"],
            "--setting-sources": lambda a: (a[:a.index("--setting-sources")]
                                            + a[a.index("--setting-sources") + 2:]),
            "deny pattern": lambda a: [t.replace(",mcp__*", "") for t in a],
        }
        for name, mutate in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(mutate(list(good)), actual)

    def test_codex_sandbox_mutant_detected(self):
        actual = cr.build_run_command("codex", self.repo, self.run,
                                      "gpt-6.1-sol", "low", SESSION)
        good = expected_codex(self.repo, self.run)
        self.assertEqual(actual, good)
        mutant = good[:2] + good[4:]
        self.assertNotEqual(mutant, actual)


class SessionParserTests(unittest.TestCase):
    def test_parses_session_line(self):
        log = "OpenAI Codex\n--------\nsession id: 0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5b\n"
        self.assertEqual(cr.parse_codex_session(log),
                         "0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5b")

    def test_ignores_malformed_and_takes_valid(self):
        log = ("session id: not-a-uuid\n"
               "session id: 0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5bXX\n"
               "session id: 0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5c\n")
        self.assertEqual(cr.parse_codex_session(log),
                         "0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5c")

    def test_only_malformed_returns_none(self):
        self.assertIsNone(cr.parse_codex_session("session id: 1234\n"))

    def test_absent_returns_none(self):
        self.assertIsNone(cr.parse_codex_session("no metadata here\n"))
        self.assertIsNone(cr.parse_codex_session(""))


if __name__ == "__main__":
    unittest.main()
