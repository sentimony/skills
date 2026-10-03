"""Standalone unit tests for cross_review command adapters and loop guard."""

import io
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cross_review as cr  # noqa: E402

SESSION = "11111111-1111-4111-8111-111111111111"
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cross_review.py")
ARTIFACTS = ("brief.md", "review.md", "session.txt", "run.log")


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


# Fake reviewer sources. Each runs as a real child process via sys.executable;
# argv[1] is the expected cwd, argv[2] the -o path (Codex only).
FAKE_CLAUDE = (
    "import os,sys; "
    "assert os.environ['CROSS_REVIEW_DEPTH']=='1', 'depth'; "
    "assert os.environ['TASK_SENTINEL']=='present', 'env'; "
    "assert os.path.realpath(os.getcwd())==os.path.realpath(sys.argv[1]), 'cwd'; "
    "assert sys.stdin.read()=='fixture brief', 'stdin'; "
    "sys.stderr.write('claude diagnostics\\n'); "
    "sys.stdout.write('Target reviewed: fixture\\nCoverage: complete\\n')"
)

FAKE_CODEX = (
    "import os,sys; "
    "assert os.environ['CROSS_REVIEW_DEPTH']=='1', 'depth'; "
    "assert os.path.realpath(os.getcwd())==os.path.realpath(sys.argv[1]), 'cwd'; "
    "assert sys.stdin.read()=='fixture brief', 'stdin'; "
    "sys.stdout.write('progress: thinking\\n'); "
    "sys.stderr.write('session id: " + SESSION + "\\n'); "
    "open(sys.argv[2],'w').write('Target reviewed: fixture\\nCoverage: complete\\n')"
)


def fake_builder(source, argv_extra=None):
    """Replace only the command builder; subprocess stays real."""
    def build(reviewer, repo, run_dir, model, effort, session_id):
        extra = [str(repo)]
        if reviewer == "codex":
            extra.append(str(Path(run_dir) / "review.md"))
        return [sys.executable, "-c", source] + extra + list(argv_extra or [])
    return build


def tree_snapshot(root):
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            st = os.lstat(path)
            snap[os.path.relpath(path, root)] = (st.st_mode, st.st_size, st.st_mtime_ns)
    return snap


class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.tmpdir = base / "tmp root"
        self.tmpdir.mkdir()
        self.repo = base / "target repo"
        self.repo.mkdir()
        (self.repo / "file.txt").write_text("content\n")
        self.brief = base / "brief input.md"
        self.brief.write_text("fixture brief", encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if k != "CROSS_REVIEW_DEPTH"}
        self.env["TASK_SENTINEL"] = "present"
        patches = [
            mock.patch.object(tempfile, "tempdir", str(self.tmpdir)),
            mock.patch.object(cr.shutil, "which", return_value=sys.executable),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self._tmp.cleanup()

    @property
    def root(self):
        return self.tmpdir / "cross-review"

    def run_dirs(self):
        return sorted(self.root.iterdir()) if self.root.exists() else []

    def run_fake(self, reviewer, source, **kwargs):
        with mock.patch.object(cr, "build_run_command", fake_builder(source)):
            return cr.run_review(reviewer, self.repo, self.brief, None, None,
                                 kwargs.get("env", self.env))

    def run_fake_error(self, reviewer, source):
        with self.assertRaises(cr.CrossReviewError) as caught:
            self.run_fake(reviewer, source)
        return caught.exception


class MainTests(RunnerTestCase):
    def call_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cr.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_cli_returns_21_without_spawn(self):
        with mock.patch.object(cr.shutil, "which", return_value=None), \
                mock.patch.object(cr.subprocess, "Popen") as popen, \
                mock.patch.object(cr.subprocess, "run") as run:
            code, _, err = self.call_main(["run", "--reviewer", "codex", "--repo",
                                           str(self.repo), "--brief", str(self.brief)])
        self.assertEqual(code, 21)
        popen.assert_not_called()
        run.assert_not_called()
        self.assertEqual(self.run_dirs(), [])
        self.assertIn("codex", err)

    def test_main_success_prints_absolute_paths(self):
        with mock.patch.dict(os.environ, {"TASK_SENTINEL": "present"}), \
                mock.patch.object(cr, "build_run_command", fake_builder(FAKE_CLAUDE)):
            os.environ.pop("CROSS_REVIEW_DEPTH", None)
            code, out, _ = self.call_main(["run", "--reviewer", "claude", "--repo",
                                           str(self.repo), "--brief", str(self.brief)])
        self.assertEqual(code, 0)
        [run_dir] = self.run_dirs()
        self.assertIn(str(run_dir), out)
        for name in ARTIFACTS:
            self.assertIn(str(run_dir / name), out)
        for line in out.splitlines():
            self.assertTrue(os.path.isabs(line.split(": ", 1)[1]), line)

    def test_invalid_input_returns_2(self):
        bad = self.brief.parent / "bad.md"
        bad.write_bytes(b"\xff\xfe broken")
        cases = [
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(bad)],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", "/nonexistent/b.md"],
            ["--reviewer", "codex", "--repo", "/nonexistent/repo", "--brief", str(self.brief)],
            ["--reviewer", "gemini", "--repo", str(self.repo), "--brief", str(self.brief)],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(self.brief),
             "--model", ""],
        ]
        for args in cases:
            with self.subTest(args=args), \
                    mock.patch.object(cr.subprocess, "Popen") as popen:
                code, _, _ = self.call_main(["run"] + args)
                self.assertEqual(code, 2)
                popen.assert_not_called()
        self.assertEqual(self.run_dirs(), [])


class GuardSubprocessTests(RunnerTestCase):
    def test_actual_main_with_depth_exits_20_before_cli_and_run_dir(self):
        env = dict(self.env, CROSS_REVIEW_DEPTH="", TMPDIR=str(self.tmpdir),
                   PATH="/nonexistent")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "run", "--reviewer", "codex", "--repo",
             str(self.repo), "--brief", str(self.brief)],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 20, proc.stderr)
        self.assertIn("already the cross-reviewer", proc.stderr)
        self.assertFalse(self.root.exists())

    def test_nested_child_run_is_refused(self):
        # The fake reviewer tries to delegate again through the real script.
        nested = (
            "import subprocess,sys; "
            "sys.stdin.read(); "
            "r = subprocess.run([sys.executable, %r, 'run', '--reviewer', 'codex', "
            "'--repo', sys.argv[1], '--brief', %r], stdin=subprocess.DEVNULL, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "print('nested-exit=%%d' %% r.returncode)"
        ) % (SCRIPT, str(self.brief))
        run_dir = self.run_fake("claude", nested)
        self.assertEqual((run_dir / "review.md").read_text().strip(), "nested-exit=20")
        self.assertEqual(self.run_dirs(), [run_dir])


class RunReviewTests(RunnerTestCase):
    def test_claude_artifacts(self):
        before = tree_snapshot(self.repo)
        run_dir = self.run_fake("claude", FAKE_CLAUDE)
        self.assertEqual(tree_snapshot(self.repo), before)
        self.assertTrue(run_dir.is_absolute())
        self.assertEqual(run_dir.parent, self.root)
        self.assertEqual((run_dir / "brief.md").read_text(), "fixture brief")
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")
        session = (run_dir / "session.txt").read_text().strip()
        self.assertRegex(session, cr._UUID_RE.pattern)
        log = (run_dir / "run.log").read_text()
        self.assertIn("claude diagnostics", log)
        self.assertNotIn("Target reviewed", log)

    def test_claude_session_id_is_passed_to_builder(self):
        seen = {}
        inner = fake_builder(FAKE_CLAUDE)

        def spy(reviewer, repo, run_dir, model, effort, session_id):
            seen["session"] = session_id
            seen["model"], seen["effort"] = model, effort
            return inner(reviewer, repo, run_dir, model, effort, session_id)

        with mock.patch.object(cr, "build_run_command", spy):
            run_dir = cr.run_review("claude", self.repo, self.brief, None, None, self.env)
        self.assertEqual((run_dir / "session.txt").read_text().strip(), seen["session"])
        self.assertEqual((seen["model"], seen["effort"]), cr.DEFAULTS["claude"])

    def test_codex_final_answer_comes_from_output_file(self):
        run_dir = self.run_fake("codex", FAKE_CODEX)
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")
        self.assertEqual((run_dir / "session.txt").read_text().strip(), SESSION)
        log = (run_dir / "run.log").read_text()
        self.assertIn("progress: thinking", log)
        self.assertIn("session id: " + SESSION, log)

    def test_codex_without_session_leaves_session_empty(self):
        source = FAKE_CODEX.replace("session id: ", "no id ")
        run_dir = self.run_fake("codex", source)
        self.assertEqual((run_dir / "session.txt").read_text(), "")
        self.assertIn("session id not found", (run_dir / "run.log").read_text())

    def test_log_header_is_first_json_line(self):
        run_dir = self.run_fake("codex", FAKE_CODEX)
        first, rest = (run_dir / "run.log").read_text().split("\n", 1)
        header = json.loads(first)
        self.assertEqual(header["schema_version"], 1)
        self.assertEqual(header["reviewer"], "codex")
        self.assertEqual(header["mode"], "unspecified")
        self.assertEqual(header["repo"], str(self.repo.resolve()))
        self.assertEqual((header["model"], header["effort"]), cr.DEFAULTS["codex"])
        self.assertTrue(header["cli_version"].startswith("Python"))
        self.assertNotIn("TASK_SENTINEL", first)
        self.assertNotIn("env", header)
        self.assertIn("progress: thinking", rest)

    def test_nonzero_exit_with_partial_result_is_22(self):
        source = "import sys; sys.stdin.read(); print('partial finding'); sys.exit(7)"
        err = self.run_fake_error("claude", source)
        self.assertEqual(err.code, 22)
        self.assertIn("7", err.message)
        self.assertEqual((err.run_dir / "review.md").read_text(), "partial finding\n")

    def test_empty_or_whitespace_result_is_23(self):
        for body in ("", "print('   ')"):
            with self.subTest(body=body):
                err = self.run_fake_error("claude", "import sys; sys.stdin.read()\n" + body)
                self.assertEqual(err.code, 23)
                self.assertTrue((err.run_dir / "run.log").exists())

    def test_codex_missing_output_is_23(self):
        source = "import sys; sys.stdin.read(); print('progress only')"
        err = self.run_fake_error("codex", source)
        self.assertEqual(err.code, 23)

    def test_cli_disappearing_after_which_is_21(self):
        def gone(*args):
            return [str(self.repo.parent / "vanished-cli")]
        with mock.patch.object(cr, "build_run_command", gone):
            with self.assertRaises(cr.CrossReviewError) as caught:
                cr.run_review("codex", self.repo, self.brief, None, None, self.env)
        self.assertEqual(caught.exception.code, 21)

    def test_unicode_brief(self):
        text = "Огляд плану: перевір усе \u2713 \U0001f600"
        self.brief.write_text(text, encoding="utf-8")
        source = ("import sys; data = sys.stdin.buffer.read().decode('utf-8'); "
                  "sys.stdout.buffer.write(('echo:' + data).encode('utf-8'))")
        run_dir = self.run_fake("claude", source)
        self.assertEqual((run_dir / "brief.md").read_text(encoding="utf-8"), text)
        self.assertEqual((run_dir / "review.md").read_text(encoding="utf-8"), "echo:" + text)

    def test_popen_has_no_shell_or_timeout_and_uses_child_env(self):
        real_popen = subprocess.Popen
        with mock.patch.object(cr.subprocess, "Popen", side_effect=real_popen) as popen:
            self.run_fake("claude", FAKE_CLAUDE)
        # The first Popen is the --version probe; the review spawn is the last one.
        calls = [c for c in popen.call_args_list if c.args[0][-1:] != ["--version"]]
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertIsInstance(args[0] if args else kwargs["args"], list)
        self.assertFalse(kwargs.get("shell", False))
        self.assertNotIn("timeout", kwargs)
        self.assertEqual(kwargs["cwd"], str(self.repo.resolve()))
        self.assertEqual(kwargs["env"]["CROSS_REVIEW_DEPTH"], "1")
        self.assertEqual(kwargs["umask"], 0o077)
        self.assertNotIn("capture_output", kwargs)


class RunDirSafetyTests(RunnerTestCase):
    def permissive(self):
        old = os.umask(0)
        self.addCleanup(os.umask, old)

    def test_modes_and_owner_under_permissive_umask(self):
        self.permissive()
        run_dir = self.run_fake("codex", FAKE_CODEX)
        for path, mode in [(self.root, 0o700), (run_dir, 0o700)] + \
                [(run_dir / n, 0o600) for n in ARTIFACTS]:
            with self.subTest(path=path.name):
                st = os.lstat(path)
                self.assertEqual(stat.S_IMODE(st.st_mode), mode)
                self.assertEqual(st.st_uid, os.getuid())

    def test_codex_output_replaced_with_loose_mode_is_tightened(self):
        self.permissive()
        source = FAKE_CODEX.replace(
            "open(sys.argv[2],'w').write(",
            "os.unlink(sys.argv[2]); os.umask(0); "
            "os.close(os.open(sys.argv[2], os.O_WRONLY|os.O_CREAT, 0o666)); "
            "open(sys.argv[2],'w').write(")
        run_dir = self.run_fake("codex", source)
        self.assertEqual(stat.S_IMODE(os.lstat(run_dir / "review.md").st_mode), 0o600)

    def test_symlinked_root_is_rejected(self):
        target = self.tmpdir / "elsewhere"
        target.mkdir(mode=0o700)
        self.root.symlink_to(target)
        err = self.run_fake_error("claude", FAKE_CLAUDE)
        self.assertEqual(err.code, 2)
        self.assertEqual(list(target.iterdir()), [])

    def test_group_accessible_root_is_rejected(self):
        self.root.mkdir()
        os.chmod(self.root, 0o755)
        err = self.run_fake_error("claude", FAKE_CLAUDE)
        self.assertEqual(err.code, 2)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_same_second_runs_do_not_collide(self):
        with mock.patch.object(cr, "_timestamp", return_value="20261003-120000"):
            first = self.run_fake("claude", FAKE_CLAUDE)
            first_review = (first / "review.md").read_text()
            second = self.run_fake("claude", FAKE_CLAUDE)
            third = self.run_fake("claude", FAKE_CLAUDE)
        self.assertEqual(first.name, "20261003-120000")
        self.assertEqual(second.name, "20261003-120000-1")
        self.assertEqual(third.name, "20261003-120000-2")
        self.assertEqual((first / "review.md").read_text(), first_review)


class InterruptTests(RunnerTestCase):
    def test_interrupt_keeps_partial_artifacts_and_fails(self):
        wrapper = (
            "import sys, tempfile; from unittest import mock; "
            "sys.path.insert(0, %r); import cross_review as cr; "
            "tempfile.tempdir = %r; "
            "src = \"import sys,time; sys.stdin.read(); sys.stdout.write('partial'); "
            "sys.stdout.flush(); sys.stderr.write('ready\\\\n'); sys.stderr.flush(); "
            "time.sleep(60)\"; "
            "cr.shutil.which = lambda name: sys.executable; "
            "cr.build_run_command = lambda *a: [sys.executable, '-c', src]; "
            "sys.exit(cr.main(['run', '--reviewer', 'claude', '--repo', %r, "
            "'--brief', %r]))"
        ) % (os.path.dirname(SCRIPT), str(self.tmpdir), str(self.repo), str(self.brief))
        proc = subprocess.Popen([sys.executable, "-c", wrapper], env=self.env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 20
        log = None
        while time.time() < deadline:
            logs = list(self.root.glob("*/run.log")) if self.root.exists() else []
            if logs and "ready" in logs[0].read_text():
                log = logs[0]
                break
            time.sleep(0.05)
        self.assertIsNotNone(log, "fake reviewer never became ready")
        proc.send_signal(signal.SIGINT)
        out, err = proc.communicate(timeout=20)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.returncode, 130, err)
        self.assertIn(str(log.parent), out)
        self.assertEqual((log.parent / "review.md").read_text(), "partial")
        self.assertIn("interrupted", log.read_text())


if __name__ == "__main__":
    unittest.main()
