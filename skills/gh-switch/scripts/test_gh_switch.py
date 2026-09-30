#!/usr/bin/env python3
"""Tests for gh_switch.py against a generated fake gh."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "gh_switch.py"
# No real-token prefix: this file ships in the public package that skills.sh scans.
SYNTH = "SYNTHETIC-NOT-A-TOKEN-7d2a9c4e"
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Probe",
    "GIT_AUTHOR_EMAIL": "probe@example.com",
    "GIT_COMMITTER_NAME": "Probe",
    "GIT_COMMITTER_EMAIL": "probe@example.com",
}

FAKE_GH = r'''
import json, os, sys
state_path = os.environ["FAKE_GH_STATE"]
with open(state_path) as handle:
    state = json.load(handle)
args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
if args == ["--version"]:
    print("gh version %s (2026-07-02)" % state.get("version", "2.96.0"))
    sys.exit(0)
if args[:2] == ["auth", "status"]:
    if state.get("status_fatal"):
        print("fatal: cannot read config", file=sys.stderr)
        sys.exit(1)
    if state.get("status_garbage"):
        print("not json")
        sys.exit(0)
    entries = [{"host": "github.com", "login": login, "active": login == state.get("active"),
                "state": value, "tokenSource": "keyring", "gitProtocol": "ssh", "scopes": "repo"}
               for login, value in state["accounts"].items()]
    print(json.dumps({"hosts": {"github.com": entries} if entries else {}}))
    sys.exit(0)
if args[:2] == ["auth", "switch"]:
    if state.get("switch_fails"):
        print("switch failed", file=sys.stderr)
        sys.exit(1)
    user = args[args.index("--user") + 1]
    if not state.get("switch_noop"):
        state["active"] = user
    if state.get("fatal_after_switch"):
        state["status_fatal"] = True
    with open(state_path, "w") as handle:
        json.dump(state, handle)
    print("Switched active account for github.com to " + user, file=sys.stderr)
    sys.exit(0)
print("unexpected: " + " ".join(args), file=sys.stderr)
sys.exit(1)
'''


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, env=GIT_ENV).stdout.strip()


class GhSwitchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="evgs-unit-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        fake = self.bin / "gh"
        fake.write_text(f"#!{sys.executable}\n{FAKE_GH}", encoding="utf-8")
        fake.chmod(0o755)
        self.state = self.tmp / "state.json"
        self.log = self.tmp / "calls.jsonl"
        self.project = self.tmp / "project"
        self.project.mkdir()
        git(self.project, "init", "-q")
        git(self.project, "remote", "add", "origin", "git@github.com:sentimony/demo-app.git")
        self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "success"})

    def tearDown(self):
        for call in self.calls():
            self.assertNotIn(call[:2], (["auth", "token"], ["auth", "login"]))
            self.assertNotIn("--show-token", call)

    def set_state(self, **state):
        self.state.write_text(json.dumps(state), encoding="utf-8")

    def write_env(self, text, root=None):
        directory = (root or self.project) / ".env"
        directory.mkdir(exist_ok=True)
        (directory / ".env").write_bytes(text.encode("utf-8"))
        return directory / ".env"

    def run_helper(self, *args, cwd=None, env=None, path=None):
        environ = {key: value for key, value in os.environ.items()
                   if key not in ("GH_TOKEN", "GITHUB_TOKEN", "GH_REPO", "GH_HOST")}
        environ.update(PATH=path or f"{self.bin}{os.pathsep}{environ['PATH']}",
                       FAKE_GH_STATE=str(self.state), FAKE_GH_LOG=str(self.log),
                       GH_CONFIG_DIR=str(self.tmp / "gh-config"))
        environ.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT), "--cwd", str(cwd or self.project), *args],
                              capture_output=True, text=True, env=environ)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def switch_calls(self):
        return [call for call in self.calls() if call[:2] == ["auth", "switch"]]

    def active(self):
        return json.loads(self.state.read_text(encoding="utf-8"))["active"]

    def assert_switched(self, result, line="gh-switch: io-upstars -> ihororlovskyi"):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, line + "\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.switch_calls(), [["auth", "switch", "--hostname", "github.com", "--user", "ihororlovskyi"]])
        self.assertEqual(self.active(), "ihororlovskyi")

    def assert_silent_noop(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.switch_calls(), [])

    # Switching

    def test_switches_wrong_account_and_confirms(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper())
        kinds = [call[:2] for call in self.calls()]
        self.assertEqual(kinds, [["--version"], ["auth", "status"], ["auth", "switch"], ["auth", "status"]])
        status = ["auth", "status", "--hostname", "github.com", "--json", "hosts"]
        self.assertEqual([call for call in self.calls() if call[:2] == ["auth", "status"]], [status, status])

    def test_login_case_follows_gh_spelling(self):
        self.write_env("GH_ACC=IhorOrlovskyi\n")
        self.assert_switched(self.run_helper())

    def test_silent_when_account_already_active(self):
        self.set_state(active="ihororlovskyi", accounts={"io-upstars": "success", "ihororlovskyi": "success"})
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_silent_noop(self.run_helper())

    def test_reports_none_when_no_account_was_active(self):
        self.set_state(active=None, accounts={"ihororlovskyi": "success"})
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper(), "gh-switch: none -> ihororlovskyi")

    def test_failure_of_another_stored_account_is_ignored(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "error", "ihororlovskyi": "success"})
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper())

    # No configuration

    def test_silent_without_env_file(self):
        self.assert_silent_noop(self.run_helper())
        self.assertEqual(self.calls(), [])

    def test_silent_without_key(self):
        self.write_env("OTHER=1\n# GH_ACC=commented-out\n")
        self.assert_silent_noop(self.run_helper())
        self.assertEqual(self.calls(), [])

    def test_silent_outside_git_project(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.write_env("GH_ACC=ihororlovskyi\n", root=plain)
        self.assert_silent_noop(self.run_helper(cwd=plain))
        self.assertEqual(self.calls(), [])

    def test_silent_for_other_host(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_silent_noop(self.run_helper(env={"GH_HOST": "ghe.example.test"}))
        self.assertEqual(self.calls(), [])

    def test_github_host_is_case_insensitive(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper(env={"GH_HOST": "GitHub.com"}))

    # Configuration errors

    def test_rejects_malformed_values_without_echoing_them(self):
        cases = {
            "empty": "GH_ACC=\n",
            "invalid": "GH_ACC=bad_login!\n",
            "duplicate": "GH_ACC=ihororlovskyi\nGH_ACC=io-upstars\n",
            "export": "export GH_ACC=ihororlovskyi\n",
            "quoted": 'GH_ACC="ihororlovskyi"\n',
            "comment": "GH_ACC=ihororlovskyi # work\n",
            "spaced": "GH_ACC = ihororlovskyi\n",
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.log.unlink(missing_ok=True)
                self.write_env(text)
                result = self.run_helper()
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("gh-switch: "))
                for fragment in ("bad_login!", '"ihororlovskyi"', "# work"):
                    self.assertNotIn(fragment, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_unreadable_file_is_an_error(self):
        path = self.write_env("GH_ACC=ihororlovskyi\n")
        path.write_bytes(b"GH_ACC=\xff\xfe\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])
        if os.geteuid() != 0:
            path.write_text("GH_ACC=ihororlovskyi\n", encoding="utf-8")
            path.chmod(0)
            self.addCleanup(path.chmod, 0o600)
            self.assertEqual(self.run_helper().returncode, 2)

    @unittest.skipUnless(os.geteuid() != 0, "root ignores directory permissions")
    def test_unreadable_env_directory_is_an_error(self):
        directory = self.write_env("GH_ACC=ihororlovskyi\n").parent
        directory.chmod(0)
        try:
            result = self.run_helper()
        finally:
            directory.chmod(0o755)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_error_path_does_not_echo_secrets(self):
        self.write_env(f"DEPLOY_TOKEN={SYNTH}\nGH_ACC=ihororlovskyi\nGH_ACC=io-upstars\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(SYNTH, result.stdout + result.stderr)

    def test_secrets_and_substitutions_are_never_executed_or_printed(self):
        self.write_env(f"DEPLOY_TOKEN={SYNTH}\nRELEASE_NOTE=$(touch gs-pwned.txt)\nGH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assert_switched(result)
        self.assertNotIn(SYNTH, result.stdout + result.stderr)
        self.assertFalse((self.project / "gs-pwned.txt").exists())
        self.assertFalse(Path("gs-pwned.txt").exists())

    def test_crlf_line_endings(self):
        self.write_env("OTHER=1\r\nGH_ACC=ihororlovskyi\r\n")
        self.assert_switched(self.run_helper())

    # Project resolution

    def test_nested_cwd_uses_project_root(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        nested = self.project / "src" / "deep"
        nested.mkdir(parents=True)
        self.assert_switched(self.run_helper(cwd=nested))

    def test_worktree_uses_its_own_root(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        git(self.project, "commit", "-q", "--allow-empty", "-m", "init")
        worktree = self.tmp / "project-wt"
        git(self.project, "worktree", "add", "-q", str(worktree))
        self.assert_silent_noop(self.run_helper(cwd=worktree))
        self.assertEqual(self.calls(), [])
        self.write_env("GH_ACC=ihororlovskyi\n", root=worktree)
        self.assert_switched(self.run_helper(cwd=worktree))

    def test_clone_behind_symlink_ignores_outer_workspace(self):
        outer = self.tmp / "workspace"
        (outer / "repositories").mkdir(parents=True)
        git(outer, "init", "-q")
        self.write_env("GH_ACC=io-upstars\n", root=outer)
        link = outer / "repositories" / "demo"
        link.symlink_to(self.project)
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper(cwd=link))

    # Explicit targets

    def test_matching_target_switches(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper("--target", "Sentimony/Demo-App"))

    def test_matching_gh_repo_with_host_prefix_switches(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper(env={"GH_REPO": "github.com/sentimony/demo-app"}))

    def test_https_remote_matches(self):
        git(self.project, "remote", "set-url", "origin", "https://github.com/sentimony/demo-app.git")
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper("--target", "sentimony/demo-app"))

    def test_lookalike_remote_host_does_not_match(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        for url in ("https://notgithub.com/sentimony/demo-app.git",
                    "git@github.com.evil.example:sentimony/demo-app.git",
                    "https://evil.example/github.com/sentimony/demo-app.git"):
            with self.subTest(url):
                git(self.project, "remote", "set-url", "origin", url)
                result = self.run_helper("--target", "sentimony/demo-app")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "gh-switch: no project config for this target; account unchanged\n")
                self.assertEqual(self.calls(), [])

    def test_foreign_target_does_not_switch(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        for kwargs in ({"args": ("--target", "other/repo")}, {"env": {"GH_REPO": "other/repo"}}):
            with self.subTest(kwargs):
                result = self.run_helper(*kwargs.get("args", ()), env=kwargs.get("env"))
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "gh-switch: no project config for this target; account unchanged\n")
                self.assertEqual(self.calls(), [])

    # Overrides and gh state

    def test_token_override_blocks_without_printing_values(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        for name in ("GH_TOKEN", "GITHUB_TOKEN"):
            with self.subTest(name):
                result = self.run_helper(env={name: SYNTH})
                self.assertEqual(result.returncode, 4)
                self.assertIn(name, result.stderr)
                self.assertNotIn(SYNTH, result.stdout + result.stderr)
                self.assertEqual(self.calls(), [])

    def test_empty_token_variable_is_not_an_override(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assert_switched(self.run_helper(env={"GH_TOKEN": ""}))

    def test_missing_account_suggests_login(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "success"})
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 3)
        self.assertIn("gh auth login --hostname github.com", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_empty_hosts_suggests_login(self):
        self.set_state(active=None, accounts={})
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_invalid_credentials_of_wanted_account(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "error"})
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 5)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_unusable_status(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        for flag in ("status_fatal", "status_garbage"):
            with self.subTest(flag):
                self.set_state(active="io-upstars", accounts={"ihororlovskyi": "success"}, **{flag: True})
                result = self.run_helper()
                self.assertEqual(result.returncode, 5)
                self.assertEqual(result.stdout, "")
                self.assertEqual(self.switch_calls(), [])

    def test_old_gh_is_rejected(self):
        self.set_state(active="io-upstars", accounts={"ihororlovskyi": "success"}, version="2.80.0")
        self.write_env("GH_ACC=ihororlovskyi\n")
        self.assertEqual(self.run_helper().returncode, 5)
        self.assertEqual(self.switch_calls(), [])

    def test_gh_version_boundary(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        for version, accepted in (("2.80.9", False), ("2.81.0", True), ("2.100.0", True)):
            with self.subTest(version):
                self.log.unlink(missing_ok=True)
                self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "success"},
                               version=version)
                result = self.run_helper()
                if accepted:
                    self.assert_switched(result)
                else:
                    self.assertEqual(result.returncode, 5)
                    self.assertEqual(self.switch_calls(), [])

    def test_missing_gh_is_reported(self):
        self.write_env("GH_ACC=ihororlovskyi\n")
        git_only = self.tmp / "git-only"
        git_only.mkdir()
        (git_only / "git").symlink_to(shutil.which("git"))
        result = self.run_helper(path=str(git_only))
        self.assertEqual(result.returncode, 5)
        self.assertIn("gh", result.stderr)

    def test_failed_switch_prints_no_success(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "success"},
                       switch_fails=True)
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")

    def test_unconfirmed_switch_prints_no_success(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "success"},
                       switch_noop=True)
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("->", result.stderr)

    def test_status_failure_after_switch_prints_no_success(self):
        self.set_state(active="io-upstars", accounts={"io-upstars": "success", "ihororlovskyi": "success"},
                       fatal_after_switch=True)
        self.write_env("GH_ACC=ihororlovskyi\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("->", result.stderr)


if __name__ == "__main__":
    unittest.main()
