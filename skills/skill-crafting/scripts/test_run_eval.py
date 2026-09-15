import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import run_eval


ADAPTER = '''import json, os, pathlib, sys, time
root = pathlib.Path.cwd()
prompt = sys.stdin.read()
transcript = pathlib.Path(os.environ["EVAL_TRANSCRIPT_PATH"])
observation = {
    "prompt": prompt, "cwd": str(root),
    "env": {key: os.environ[key] for key in (
        "EVAL_CONFIG", "EVAL_ID", "EVAL_NAME", "EVAL_MODEL")},
    "trees": [(root / tree / "skills" / "sample-skill").exists()
              for tree in (".agents", ".claude")],
    "fresh": not (root / "changed.txt").exists(),
}
transcript.write_text(json.dumps(observation) + "\\n")
print("adapter diagnostic", file=sys.stderr)
if prompt == "timeout":
    time.sleep(10)
if prompt == "change":
    (root / "changed.txt").write_text("new content")
if prompt == "nonzero":
    sys.exit(7)
if prompt == "malformed":
    print("invalid JSON")
    sys.exit(0)
answer = transcript.parent / "answer.txt"
if prompt != "missing":
    answer.write_text("behavioral answer")
result = {"status": "complete", "answer_path": str(answer), "tool_calls": 2}
if prompt == "reported-error":
    result["status"] = "error"
    result["error"] = "adapter failed"
print(json.dumps(result))
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="eval-session-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.template = self.root / "template"
        self.template.mkdir()
        source = self.root / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("skill content", encoding="utf-8")
        for tree in (".agents", ".claude"):
            skills = self.template / tree / "skills"
            skills.mkdir(parents=True)
            (skills / "sample-skill").symlink_to(source, target_is_directory=True)
            (skills / "other").mkdir()
        (self.template / "original.txt").write_text("original", encoding="utf-8")
        self.fixtures = self.root / "fixtures"
        self.fixtures.mkdir()
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text(ADAPTER, encoding="utf-8")
        self.case = {"id": "../odd/id", "name": "Example", "prompt": "change",
                     "expected_output": "expected", "files": [], "fixture": None,
                     "skill_name": "sample-skill"}

    def execute(self, prompt="change", config="baseline", name="run", timeout=5):
        case = dict(self.case, prompt=prompt)
        directory = self.root / name
        result = run_eval.run_case(case, self.template, directory, config,
                                   self.adapter, "test-model", timeout, self.fixtures)
        return result, directory

    def test_sandbox_copies_links_and_removes_only_target_skill_in_baseline(self):
        readonly = self.template / "original.txt"
        readonly.chmod(0o444)
        for config, present in (("baseline", False), ("with_skill", True)):
            sandbox = self.root / config
            run_eval.prepare_sandbox(self.template, sandbox, "sample-skill", config)
            self.assertTrue((sandbox / "original.txt").is_file())
            self.assertTrue((sandbox / "original.txt").stat().st_mode & stat.S_IWUSR)
            for tree in (".agents", ".claude"):
                target = sandbox / tree / "skills" / "sample-skill"
                self.assertEqual(target.exists(), present)
                self.assertFalse(target.is_symlink())
                self.assertTrue((target.parent / "other").is_dir())
                self.assertTrue((self.template / tree / "skills" / "sample-skill").is_symlink())

    def test_success_artifacts_stdin_environment_and_fresh_sandboxes(self):
        paths = []
        for config in ("baseline", "with_skill"):
            for repeat in range(2):
                result, directory = self.execute(config=config, name=f"{config}-{repeat}")
                self.assertEqual(result.get("status"), "complete")
                self.assertEqual(result["return_code"], 0)
                self.assertEqual(result["tool_calls"], 2)
                self.assertEqual(result["model"], "test-model")
                self.assertGreaterEqual(result["duration_seconds"], 0)
                self.assertTrue(result["changed"])
                for name in ("prompt.txt", "transcript.jsonl", "adapter-result.json",
                             "stderr.log", "timing.json", "tree.diff", "run.json", ".complete"):
                    self.assertTrue((directory / name).is_file(), name)
                observed = json.loads((directory / "transcript.jsonl").read_text())
                self.assertEqual(observed["prompt"], "change")
                self.assertEqual(observed["env"], {"EVAL_CONFIG": config, "EVAL_ID": "../odd/id",
                    "EVAL_NAME": "Example", "EVAL_MODEL": "test-model"})
                self.assertEqual(observed["trees"], [config == "with_skill"] * 2)
                self.assertTrue(observed["fresh"])
                self.assertNotIn("sample-skill", observed["cwd"])
                self.assertTrue(any(part.startswith("eval-session-") for part in Path(observed["cwd"]).parts))
                paths.append(observed["cwd"])
                self.assertIn("changed.txt", (directory / "tree.diff").read_text())
                self.assertEqual(json.loads((directory / "run.json").read_text()), result)
        self.assertEqual(len(set(paths)), 4)
        self.assertFalse((self.template / "changed.txt").exists())

    def test_unchanged_tree(self):
        result, directory = self.execute(prompt="unchanged")
        self.assertEqual(result.get("status"), "complete")
        self.assertIs(result["changed"], False)
        self.assertEqual((directory / "tree.diff").read_text(), "")

    def test_failures_preserve_diagnostics_without_complete(self):
        for prompt, status, return_code in (("nonzero", "error", 7), ("malformed", "error", 0),
                ("missing", "error", 0), ("reported-error", "error", 0), ("timeout", "timeout", None)):
            with self.subTest(prompt=prompt):
                result, directory = self.execute(prompt, name=prompt, timeout=0.2 if prompt == "timeout" else 5)
                self.assertEqual(result.get("status"), status)
                self.assertEqual(result["return_code"], return_code)
                self.assertTrue(result["error"])
                self.assertFalse((directory / ".complete").exists())
                for artifact in ("prompt.txt", "transcript.jsonl", "adapter-result.json", "stderr.log",
                                 "timing.json", "tree.diff", "run.json"):
                    self.assertTrue((directory / artifact).exists(), artifact)
                self.assertIn("adapter diagnostic", (directory / "stderr.log").read_text())

    def test_diff_failure_is_an_error_and_never_a_change(self):
        real_run = subprocess.run

        def fail_diff(command, *args, **kwargs):
            if command[:3] == ["git", "diff", "--no-index"]:
                return subprocess.CompletedProcess(command, 2, stdout=b"", stderr=b"diff failed")
            return real_run(command, *args, **kwargs)

        with mock.patch.object(subprocess, "run", side_effect=fail_diff):
            result, directory = self.execute()
        self.assertEqual(result.get("diff_status"), "error")
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["changed"])
        self.assertFalse((directory / ".complete").exists())

    def test_fixture_files_directory_and_setup(self):
        (self.fixtures / "nested").mkdir()
        (self.fixtures / "nested" / "input.txt").write_text("input")
        (self.fixtures / "setup.sh").write_text('cp "fixtures/nested/input.txt" "$1"\n')
        for fixture, files, expected in ((None, ["fixtures/nested/input.txt"], "nested/input.txt"),
                ("nested", [], "input.txt"), ('fixtures/setup.sh "output file.txt"', [], "output file.txt")):
            with self.subTest(fixture=fixture):
                sandbox = self.root / f"fixture-{len(list(self.root.iterdir()))}"
                sandbox.mkdir()
                run_eval.prepare_fixture(dict(self.case, fixture=fixture, files=files), self.fixtures, sandbox)
                self.assertTrue((sandbox / expected).is_file())
                self.assertEqual((sandbox / expected).read_text(), "input")
                if fixture and "setup.sh" in fixture:
                    self.assertTrue((sandbox / "fixtures" / "nested" / "input.txt").is_file())

    def test_manifest_safe_ids_and_repeats(self):
        spec = self.root / "evals.json"
        spec.write_text(json.dumps({"skill_name": "sample-skill", "harness": "test-runtime",
            "evals": [dict(self.case, prompt="unchanged"), dict(self.case, id=42, name="Second", prompt="unchanged")]}))
        workspace = self.root / "workspace"
        result = run_eval.run_eval(spec, self.template, workspace, self.adapter, 2, self.fixtures, "test-model", 5)
        self.assertIsInstance(result, dict)
        self.assertTrue((workspace / "manifest.json").exists())
        manifest = json.loads((workspace / "manifest.json").read_text())
        metadata = json.loads((workspace / "eval_metadata.json").read_text())
        for key, value in (("skill_name", "sample-skill"), ("harness", "test-runtime"),
                           ("model", "test-model"), ("runs_per_case", 2), ("configs", ["baseline", "with_skill"])):
            self.assertEqual(manifest[key], value)
            self.assertEqual(metadata[key], value)
        self.assertEqual(manifest["eval_spec_sha256"], hashlib.sha256(spec.read_bytes()).hexdigest())
        self.assertEqual(len(manifest["template_sha256"]), 64)
        runs = list(workspace.rglob("run.json"))
        self.assertEqual(len(runs), 8)
        self.assertEqual(len(list(workspace.rglob(".complete"))), 8)
        for record in runs:
            self.assertNotIn("score", json.loads(record.read_text()))

    def test_missing_envelope_answer_and_invalid_tool_count_are_errors(self):
        for field, value in (("answer_path", None), ("tool_calls", -1), ("tool_calls", True),
                             ("status", "fail")):
            with self.subTest(field=field, value=value):
                self.adapter.write_text(ADAPTER.replace("print(json.dumps(result))",
                    f"result[{field!r}] = {value!r}\nprint(json.dumps(result))"))
                result, directory = self.execute(name=f"bad-{field}-{value}")
                self.assertEqual(result["status"], "error")
                self.assertFalse((directory / ".complete").exists())

    def test_answer_from_sandbox_is_persisted_before_cleanup(self):
        self.adapter.write_text(ADAPTER.replace('answer = transcript.parent / "answer.txt"',
                                                'answer = pathlib.Path("answer.txt")'))
        result, directory = self.execute(prompt="unchanged")
        self.assertEqual(result["status"], "complete")
        self.assertEqual((directory / "answer.txt").read_text(), "behavioral answer")
        observed = json.loads((directory / "transcript.jsonl").read_text())
        self.assertFalse(Path(observed["cwd"]).exists())

    def test_existing_run_is_preserved(self):
        result, directory = self.execute()
        previous = (directory / "run.json").read_bytes()
        with self.assertRaises((ValueError, FileExistsError)):
            self.execute()
        self.assertEqual((directory / "run.json").read_bytes(), previous)
        self.assertTrue((directory / ".complete").exists())

    def test_fixture_setup_error_is_recorded(self):
        (self.fixtures / "setup.sh").write_text("echo fixture-failed >&2\nexit 3\n")
        self.case["fixture"] = "fixtures/setup.sh argument"
        result, directory = self.execute()
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["return_code"])
        self.assertIn("fixture-failed", (directory / "stderr.log").read_text())
        self.assertFalse((directory / ".complete").exists())

    def test_fixture_cannot_copy_parent_or_absolute_paths(self):
        sandbox = self.root / "sandbox"
        sandbox.mkdir()
        for path in ("../source/SKILL.md", str(self.root / "source" / "SKILL.md"),
                     "fixtures/../../source/SKILL.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                run_eval.prepare_fixture(dict(self.case, files=[path]), self.fixtures, sandbox)

    def test_manifest_hashes_are_repeatable_and_sensitive_to_content_and_paths(self):
        spec = self.root / "evals.json"
        spec.write_text(json.dumps({"skill_name": "sample-skill", "evals": []}))

        def manifest(index):
            return run_eval.run_eval(spec, self.template, self.root / f"workspace-{index}",
                self.adapter, 1, self.fixtures, "test-model", 5)["manifest"]

        first, second = manifest(1), manifest(2)
        self.assertEqual(first, second)
        self.assertEqual(first["harness"], "adapter")
        (self.root / "source" / "SKILL.md").write_text("updated content")
        third = manifest(3)
        self.assertNotEqual(first["template_sha256"], third["template_sha256"])
        (self.template / "original.txt").rename(self.template / "renamed.txt")
        fourth = manifest(4)
        self.assertNotEqual(third["template_sha256"], fourth["template_sha256"])
        with self.assertRaises(ValueError):
            manifest(1)

    def test_cli_runs_real_adapter_and_reports_execution_failure(self):
        spec = self.root / "evals.json"
        for prompt, exit_code in (("unchanged", 0), ("nonzero", 1)):
            spec.write_text(json.dumps({"skill_name": "sample-skill",
                "evals": [dict(self.case, prompt=prompt)]}))
            workspace = self.root / f"cli-{prompt}"
            command = [sys.executable, "-B", str(Path(run_eval.__file__).resolve()),
                str(spec), str(self.template), str(workspace), "--adapter", str(self.adapter),
                "--model", "test-model", "--runs", "1", "--fixtures-root", str(self.fixtures), "--timeout", "5"]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, exit_code, completed.stderr)
            self.assertEqual(len(list(workspace.rglob("run.json"))), 2)

    def test_empty_answer_is_an_error(self):
        self.adapter.write_text(ADAPTER.replace('answer.write_text("behavioral answer")',
                                                'answer.write_text("  ")'))
        result, directory = self.execute()
        self.assertEqual(result["status"], "error")
        self.assertFalse((directory / ".complete").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX process groups required")
    def test_timeout_stops_adapter_and_fixture_children(self):
        def exists(pid):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False
            return True

        def wait_gone(pid):
            deadline = time.monotonic() + 3
            while exists(pid) and time.monotonic() < deadline:
                time.sleep(0.01)
            return not exists(pid)

        for kind in ("adapter", "fixture"):
            with self.subTest(kind=kind):
                marker = self.root / f"{kind}-child.json"
                program = (
                    "import json, os, pathlib, signal, subprocess, time\n"
                    "child = subprocess.Popen(['sleep', '30'], "
                    "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                    "def stop(signum, frame):\n"
                    "    child.wait()\n"
                    "    raise SystemExit(0)\n"
                    "signal.signal(signal.SIGTERM, stop)\n"
                    f"pathlib.Path({str(marker)!r}).write_text(json.dumps("
                    "{'parent': os.getpid(), 'child': child.pid, 'cwd': os.getcwd()}))\n"
                    "time.sleep(30)\n"
                )
                self.case["fixture"] = None
                if kind == "adapter":
                    self.adapter.write_text(program)
                else:
                    self.adapter.write_text(ADAPTER)
                    (self.fixtures / "spawn.py").write_text(program)
                    (self.fixtures / "setup.sh").write_text(
                        f"exec {shlex.quote(sys.executable)} fixtures/spawn.py\n")
                    self.case["fixture"] = "fixtures/setup.sh"
                try:
                    result, directory = self.execute(name=f"timeout-{kind}", timeout=1)
                    self.assertTrue(marker.is_file(), "child must start before the timeout")
                    pids = json.loads(marker.read_text())
                    self.assertEqual(result["status"], "timeout")
                    self.assertFalse((directory / ".complete").exists())
                    self.assertFalse(Path(pids["cwd"]).exists())
                    self.assertFalse(exists(pids["parent"]), "adapter/setup parent survived timeout")
                    self.assertTrue(wait_gone(pids["child"]), "adapter/setup child survived timeout")
                finally:
                    if marker.exists():
                        pids = json.loads(marker.read_text())
                        for pid in (pids["child"], pids["parent"]):
                            if exists(pid):
                                try:
                                    os.kill(pid, signal.SIGKILL)
                                except ProcessLookupError:
                                    pass
                            self.assertTrue(wait_gone(pid), f"test cleanup left process {pid}")

    def test_baseline_removes_skill_restored_by_fixtures(self):
        restore = self.fixtures / "restore"
        for tree in (".agents", ".claude"):
            target = restore / tree / "skills" / "sample-skill"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text("restored by fixture")
        (self.fixtures / "setup.sh").write_text("cp -R fixtures/restore/. .\n")
        for fixture in ("restore", "fixtures/setup.sh"):
            for config in ("baseline", "with_skill"):
                with self.subTest(fixture=fixture, config=config):
                    self.case["fixture"] = fixture
                    result, directory = self.execute(prompt="unchanged", config=config,
                        name=f"restore-{Path(fixture).name}-{config}")
                    self.assertEqual(result["status"], "complete")
                    observed = json.loads((directory / "transcript.jsonl").read_text())
                    self.assertEqual(observed["trees"], [config == "with_skill"] * 2)
                    self.assertFalse(result["changed"])

    def test_fixture_rejects_sources_resolving_outside_root_before_copy(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("external content")
        bundle = self.fixtures / "bundle"
        (bundle / "nested").mkdir(parents=True)
        (bundle / "regular.txt").write_text("regular fixture")
        (self.fixtures / "setup.sh").write_text("exit 0\n")
        for link_kind in ("file", "directory"):
            link = bundle / "nested" / "escape"
            link.symlink_to(outside / "secret.txt" if link_kind == "file" else outside,
                            target_is_directory=link_kind == "directory")
            try:
                cases = (
                    dict(self.case, files=["bundle/nested/escape"]),
                    dict(self.case, fixture="bundle"),
                    dict(self.case, fixture="fixtures/setup.sh"),
                )
                for index, case in enumerate(cases):
                    with self.subTest(link_kind=link_kind, mode=index):
                        sandbox = self.root / f"escape-{link_kind}-{index}"
                        sandbox.mkdir()
                        with self.assertRaises(ValueError):
                            run_eval.prepare_fixture(case, self.fixtures, sandbox)
                        self.assertEqual(list(sandbox.iterdir()), [])
            finally:
                link.unlink()

    def test_fixture_preserves_internal_symlinks_as_copied_content(self):
        (self.fixtures / "regular.txt").write_text("regular fixture")
        (self.fixtures / "internal.txt").symlink_to("regular.txt")
        sandbox = self.root / "internal-fixture"
        sandbox.mkdir()
        run_eval.prepare_fixture(dict(self.case, files=["internal.txt"]), self.fixtures, sandbox)
        self.assertEqual((sandbox / "internal.txt").read_text(), "regular fixture")
        self.assertFalse((sandbox / "internal.txt").is_symlink())

    def test_reported_timeout_remains_timeout_without_complete(self):
        for has_answer in (False, True):
            with self.subTest(has_answer=has_answer):
                if has_answer:
                    self.adapter.write_text(ADAPTER.replace('"status": "complete"',
                                                           '"status": "timeout"'))
                else:
                    self.adapter.write_text(
                        'import json\nprint(json.dumps({"status": "timeout", "error": "adapter deadline"}))\n')
                result, directory = self.execute(name=f"reported-timeout-{has_answer}")
                self.assertEqual(result["status"], "timeout")
                self.assertEqual(result["return_code"], 0)
                self.assertFalse((directory / ".complete").exists())
                self.assertEqual(json.loads((directory / "run.json").read_text())["status"], "timeout")


if __name__ == "__main__":
    unittest.main()
