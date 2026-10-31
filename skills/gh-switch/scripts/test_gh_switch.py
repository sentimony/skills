#!/usr/bin/env python3
"""Tests for gh_switch.py against a generated fake gh."""

import base64
import contextlib
import http.server
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_switch  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "gh_switch.py"
# No real-token prefix: this file ships in the public package that skills.sh scans.
SYNTH = "SYNTHETIC-NOT-A-TOKEN-7d2a9c4e"
# URL-encoding, standard and URL-safe Base64, and padding all give distinct strings for it.
GL_SYNTH = "SYNTH/GL+NOT?A~TOKEN-7d2a9c4e"


def secret_forms(token):
    standard = base64.b64encode(token.encode("utf-8")).decode("ascii")
    urlsafe = base64.urlsafe_b64encode(token.encode("utf-8")).decode("ascii")
    return {token, urllib.parse.quote(token, safe=""), standard, standard.rstrip("="),
            urlsafe, urlsafe.rstrip("=")}


class FakeGitLab(http.server.BaseHTTPRequestHandler):
    reply = (200, {"username": "io-upstars"})
    seen = []

    def do_GET(self):
        type(self).seen.append((self.path, self.headers.get("PRIVATE-TOKEN")))
        code, body = type(self).reply
        if body == "truncated":
            self.send_response(code)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b'40\r\n{"username": "io-')
            return
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        if 300 <= code < 400:
            self.send_header("Location", "http://127.0.0.1:9/elsewhere")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass
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
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "success"})

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

    def assert_switched(self, result, line="gh-switch: octo-work -> octo-home"):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, line + "\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.switch_calls(), [["auth", "switch", "--hostname", "github.com", "--user", "octo-home"]])
        self.assertEqual(self.active(), "octo-home")

    def assert_silent_noop(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.switch_calls(), [])

    # Switching

    def test_switches_wrong_account_and_confirms(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper())
        kinds = [call[:2] for call in self.calls()]
        self.assertEqual(kinds, [["--version"], ["auth", "status"], ["auth", "switch"], ["auth", "status"]])
        status = ["auth", "status", "--hostname", "github.com", "--json", "hosts"]
        self.assertEqual([call for call in self.calls() if call[:2] == ["auth", "status"]], [status, status])

    def test_login_case_follows_gh_spelling(self):
        self.write_env("GH_ACC=Octo-Home\n")
        self.assert_switched(self.run_helper())

    def test_silent_when_account_already_active(self):
        self.set_state(active="octo-home", accounts={"octo-work": "success", "octo-home": "success"})
        self.write_env("GH_ACC=octo-home\n")
        self.assert_silent_noop(self.run_helper())

    def test_reports_none_when_no_account_was_active(self):
        self.set_state(active=None, accounts={"octo-home": "success"})
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper(), "gh-switch: none -> octo-home")

    def test_failure_of_another_stored_account_is_ignored(self):
        self.set_state(active="octo-work", accounts={"octo-work": "error", "octo-home": "success"})
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper())

    def test_gl_acc_does_not_change_github_switch(self):
        git(self.project, "remote", "add", "gitlab", "git@gitlab.example.test:io/okr.git")
        self.write_env(f"GH_ACC=octo-home\nGL_ACC=io-upstars\nGITLAB_TOKEN='{SYNTH}'\n")
        self.assert_switched(self.run_helper())

    # No configuration

    def assert_no_acc(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, gh_switch.NO_ACC + "\n")
        self.assertEqual(self.switch_calls(), [])

    def env_text(self, root=None):
        path = (root or self.project) / ".env" / ".env"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def ignore_env(self, root=None):
        ((root or self.project) / ".gitignore").write_text(".env/\n", encoding="utf-8")

    def sibling(self, name, remote, env=None):
        repo = self.tmp / name
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "remote", "add", "origin", remote)
        if env is not None:
            self.write_env(env, root=repo)
        return repo

    # Adding a missing GH_ACC

    def test_adds_owner_login_and_switches(self):
        git(self.project, "remote", "set-url", "origin", "git@github.com:octo-home/app.git")
        self.ignore_env()
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "gh-switch: GH_ACC=octo-home added to .env/.env; octo-work -> octo-home\n")
        self.assertEqual(self.env_text(), "# used by gh-switch skill\nGH_ACC=octo-home\n")
        self.assertEqual(self.active(), "octo-home")
        self.assertEqual(self.run_helper().stdout, "")

    def test_insert_keeps_other_lines_and_puts_gh_acc_first(self):
        git(self.project, "remote", "set-url", "origin", "git@github.com:octo-home/app.git")
        self.ignore_env()
        for before, after in (
            (f"# used by gh-switch skill\nGL_ACC=io-upstars\nGITLAB_TOKEN='{SYNTH}'\n",
             f"# used by gh-switch skill\nGH_ACC=octo-home\nGL_ACC=io-upstars\nGITLAB_TOKEN='{SYNTH}'\n"),
            ("OTHER=1\r\n", "# used by gh-switch skill\r\nGH_ACC=octo-home\r\nOTHER=1\r\n"),
        ):
            with self.subTest(before):
                path = self.write_env(before)
                path.chmod(0o600)
                result = self.run_helper("--no-switch")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(SYNTH, result.stdout + result.stderr)
                self.assertEqual(path.read_bytes().decode("utf-8"), after)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(sorted(p.name for p in path.parent.iterdir()), [".env"])

    def test_no_switch_reports_addition_with_prefix(self):
        git(self.project, "remote", "set-url", "origin", "git@github.com:octo-home/app.git")
        self.ignore_env()
        result = self.run_helper("--no-switch")
        self.assertEqual(result.stdout, 'gh-switch: GH_ACC=octo-home added to .env/.env; prefix the command with '
                                        'GH_TOKEN="$(gh auth token --hostname github.com --user octo-home)"; '
                                        'account unchanged\n')
        self.assertEqual(self.switch_calls(), [])

    def test_adds_login_all_sibling_clones_of_the_owner_agree_on(self):
        self.ignore_env()
        self.sibling("site", "git@github.com:sentimony/site.git", "GH_ACC=octo-home\n")
        self.sibling("tools", "https://github.com/sentimony/tools", "X=1\nGH_ACC=Octo-Home\n")
        self.sibling("other", "git@github.com:someone/else.git", "GH_ACC=octo-work\n")
        self.sibling("bare", "git@github.com:sentimony/bare.git")
        result = self.run_helper()
        self.assertEqual(result.stdout, "gh-switch: GH_ACC=octo-home added to .env/.env; octo-work -> octo-home\n")
        self.assertEqual(self.env_text(), "# used by gh-switch skill\nGH_ACC=octo-home\n")

    def test_already_active_account_is_reported_with_the_addition(self):
        self.ignore_env()
        self.set_state(active="octo-home", accounts={"octo-work": "success", "octo-home": "success"})
        self.sibling("site", "git@github.com:sentimony/site.git", "GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.stdout, "gh-switch: GH_ACC=octo-home added to .env/.env; account already active\n")

    def test_ambiguous_or_unusable_account_is_not_added(self):
        self.ignore_env()
        self.sibling("site", "git@github.com:sentimony/site.git", "GH_ACC=octo-home\n")
        self.sibling("tools", "git@github.com:sentimony/tools.git", "GH_ACC=octo-work\n")
        self.assert_no_acc(self.run_helper())
        shutil.rmtree(self.tmp / "tools")
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "error"})
        self.assert_no_acc(self.run_helper())
        self.set_state(active="octo-work", accounts={"octo-work": "success"})
        self.assert_no_acc(self.run_helper())

    def test_two_owner_logins_are_not_guessed_between(self):
        git(self.project, "remote", "set-url", "origin", "git@github.com:octo-home/app.git")
        git(self.project, "remote", "add", "upstream", "git@github.com:octo-work/app.git")
        self.ignore_env()
        self.assert_no_acc(self.run_helper())
        result = self.run_helper("--target", "octo-work/app")
        self.assertEqual(result.stdout, "gh-switch: GH_ACC=octo-work added to .env/.env; account already active\n")

    def test_not_added_when_env_file_is_tracked_or_override_is_set(self):
        git(self.project, "remote", "set-url", "origin", "git@github.com:octo-home/app.git")
        self.assert_no_acc(self.run_helper())
        self.assertFalse((self.project / ".env").exists())
        self.ignore_env()
        self.log.unlink()
        self.assert_no_acc(self.run_helper(env={"GH_TOKEN": SYNTH}))
        self.assertEqual(self.calls(), [])

    def test_reports_missing_env_file(self):
        self.assert_no_acc(self.run_helper())

    def test_reports_missing_key(self):
        self.write_env("OTHER=1\n# GH_ACC=commented-out\n")
        self.assert_no_acc(self.run_helper())
        self.assert_no_acc(self.run_helper("--no-switch"))

    def test_silent_without_key_and_github_remote(self):
        git(self.project, "remote", "set-url", "origin", "git@gitlab.example.test:io/okr.git")
        self.assert_silent_noop(self.run_helper())
        self.assertEqual(self.calls(), [])

    def test_silent_outside_git_project(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.write_env("GH_ACC=octo-home\n", root=plain)
        self.assert_silent_noop(self.run_helper(cwd=plain))
        self.assertEqual(self.calls(), [])

    def test_silent_for_other_host(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_silent_noop(self.run_helper(env={"GH_HOST": "ghe.example.test"}))
        self.assertEqual(self.calls(), [])

    def test_github_host_is_case_insensitive(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper(env={"GH_HOST": "GitHub.com"}))

    # Configuration errors

    def test_rejects_malformed_values_without_echoing_them(self):
        cases = {
            "empty": "GH_ACC=\n",
            "invalid": "GH_ACC=bad_login!\n",
            "duplicate": "GH_ACC=octo-home\nGH_ACC=octo-work\n",
            "export": "export GH_ACC=octo-home\n",
            "quoted": 'GH_ACC="octo-home"\n',
            "comment": "GH_ACC=octo-home # work\n",
            "spaced": "GH_ACC = octo-home\n",
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.log.unlink(missing_ok=True)
                self.write_env(text)
                result = self.run_helper()
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("gh-switch: "))
                for fragment in ("bad_login!", '"octo-home"', "# work"):
                    self.assertNotIn(fragment, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_unreadable_file_is_an_error(self):
        path = self.write_env("GH_ACC=octo-home\n")
        path.write_bytes(b"GH_ACC=\xff\xfe\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])
        if os.geteuid() != 0:
            path.write_text("GH_ACC=octo-home\n", encoding="utf-8")
            path.chmod(0)
            self.addCleanup(path.chmod, 0o600)
            self.assertEqual(self.run_helper().returncode, 2)

    @unittest.skipUnless(os.geteuid() != 0, "root ignores directory permissions")
    def test_unreadable_env_directory_is_an_error(self):
        directory = self.write_env("GH_ACC=octo-home\n").parent
        directory.chmod(0)
        try:
            result = self.run_helper()
        finally:
            directory.chmod(0o755)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_error_path_does_not_echo_secrets(self):
        self.write_env(f"DEPLOY_TOKEN={SYNTH}\nGH_ACC=octo-home\nGH_ACC=octo-work\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(SYNTH, result.stdout + result.stderr)

    def test_secrets_and_substitutions_are_never_executed_or_printed(self):
        self.write_env(f"DEPLOY_TOKEN={SYNTH}\nRELEASE_NOTE=$(touch gs-pwned.txt)\nGH_ACC=octo-home\n")
        result = self.run_helper()
        self.assert_switched(result)
        self.assertNotIn(SYNTH, result.stdout + result.stderr)
        self.assertFalse((self.project / "gs-pwned.txt").exists())
        self.assertFalse(Path("gs-pwned.txt").exists())

    def test_crlf_line_endings(self):
        self.write_env("OTHER=1\r\nGH_ACC=octo-home\r\n")
        self.assert_switched(self.run_helper())

    # Project resolution

    def test_nested_cwd_uses_project_root(self):
        self.write_env("GH_ACC=octo-home\n")
        nested = self.project / "src" / "deep"
        nested.mkdir(parents=True)
        self.assert_switched(self.run_helper(cwd=nested))

    def test_worktree_uses_its_own_root(self):
        self.write_env("GH_ACC=octo-home\n")
        git(self.project, "commit", "-q", "--allow-empty", "-m", "init")
        worktree = self.tmp / "project-wt"
        git(self.project, "worktree", "add", "-q", str(worktree))
        self.assert_no_acc(self.run_helper(cwd=worktree))
        self.write_env("GH_ACC=octo-home\n", root=worktree)
        self.assert_switched(self.run_helper(cwd=worktree))

    def test_clone_behind_symlink_ignores_outer_workspace(self):
        outer = self.tmp / "workspace"
        (outer / "repositories").mkdir(parents=True)
        git(outer, "init", "-q")
        self.write_env("GH_ACC=octo-work\n", root=outer)
        link = outer / "repositories" / "demo"
        link.symlink_to(self.project)
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper(cwd=link))

    # Explicit targets

    def test_matching_target_switches(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper("--target", "Sentimony/Demo-App"))

    def test_matching_gh_repo_with_host_prefix_switches(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper(env={"GH_REPO": "github.com/sentimony/demo-app"}))

    def test_https_remote_matches(self):
        git(self.project, "remote", "set-url", "origin", "https://github.com/sentimony/demo-app.git")
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper("--target", "sentimony/demo-app"))

    def test_lookalike_remote_host_does_not_match(self):
        self.write_env("GH_ACC=octo-home\n")
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
        self.write_env("GH_ACC=octo-home\n")
        for kwargs in ({"args": ("--target", "other/repo")}, {"env": {"GH_REPO": "other/repo"}}):
            with self.subTest(kwargs):
                result = self.run_helper(*kwargs.get("args", ()), env=kwargs.get("env"))
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "gh-switch: no project config for this target; account unchanged\n")
                self.assertEqual(self.calls(), [])

    # No-switch mode

    def test_no_switch_prints_prefix_and_never_switches(self):
        self.write_env("GH_ACC=octo-home\n")
        for active in ("octo-work", "octo-home"):
            with self.subTest(active):
                self.set_state(active=active, accounts={"octo-work": "success", "octo-home": "success"})
                result = self.run_helper("--no-switch")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, 'gh-switch: prefix the command with GH_TOKEN="$(gh auth token '
                                                '--hostname github.com --user octo-home)"; account unchanged\n')
                self.assertEqual(self.switch_calls(), [])
                self.assertEqual(self.active(), active)

    def test_no_switch_still_checks_login_and_overrides(self):
        self.write_env("GH_ACC=octo-home\n")
        self.set_state(active="octo-work", accounts={"octo-work": "success"})
        self.assertEqual(self.run_helper("--no-switch").returncode, 3)
        self.assertEqual(self.run_helper("--no-switch", env={"GH_TOKEN": SYNTH}).returncode, 4)
        self.assertEqual(self.switch_calls(), [])

    # Overrides and gh state

    def test_token_override_blocks_without_printing_values(self):
        self.write_env("GH_ACC=octo-home\n")
        for name in ("GH_TOKEN", "GITHUB_TOKEN"):
            with self.subTest(name):
                result = self.run_helper(env={name: SYNTH})
                self.assertEqual(result.returncode, 4)
                self.assertIn(name, result.stderr)
                self.assertNotIn(SYNTH, result.stdout + result.stderr)
                self.assertEqual(self.calls(), [])

    def test_empty_token_variable_is_not_an_override(self):
        self.write_env("GH_ACC=octo-home\n")
        self.assert_switched(self.run_helper(env={"GH_TOKEN": ""}))

    def test_missing_account_suggests_login(self):
        self.set_state(active="octo-work", accounts={"octo-work": "success"})
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 3)
        self.assertIn("gh auth login --hostname github.com", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_empty_hosts_suggests_login(self):
        self.set_state(active=None, accounts={})
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_invalid_credentials_of_wanted_account(self):
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "error"})
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 5)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.switch_calls(), [])

    def test_unusable_status(self):
        self.write_env("GH_ACC=octo-home\n")
        for flag in ("status_fatal", "status_garbage"):
            with self.subTest(flag):
                self.set_state(active="octo-work", accounts={"octo-home": "success"}, **{flag: True})
                result = self.run_helper()
                self.assertEqual(result.returncode, 5)
                self.assertEqual(result.stdout, "")
                self.assertEqual(self.switch_calls(), [])

    def test_old_gh_is_rejected(self):
        self.set_state(active="octo-work", accounts={"octo-home": "success"}, version="2.80.0")
        self.write_env("GH_ACC=octo-home\n")
        self.assertEqual(self.run_helper().returncode, 5)
        self.assertEqual(self.switch_calls(), [])

    def test_gh_version_boundary(self):
        self.write_env("GH_ACC=octo-home\n")
        for version, accepted in (("2.80.9", False), ("2.81.0", True), ("2.100.0", True)):
            with self.subTest(version):
                self.log.unlink(missing_ok=True)
                self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "success"},
                               version=version)
                result = self.run_helper()
                if accepted:
                    self.assert_switched(result)
                else:
                    self.assertEqual(result.returncode, 5)
                    self.assertEqual(self.switch_calls(), [])

    def test_missing_gh_is_reported(self):
        self.write_env("GH_ACC=octo-home\n")
        git_only = self.tmp / "git-only"
        git_only.mkdir()
        (git_only / "git").symlink_to(shutil.which("git"))
        result = self.run_helper(path=str(git_only))
        self.assertEqual(result.returncode, 5)
        self.assertIn("gh", result.stderr)

    def test_failed_switch_prints_no_success(self):
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "success"},
                       switch_fails=True)
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")

    def test_unconfirmed_switch_prints_no_success(self):
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "success"},
                       switch_noop=True)
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("->", result.stderr)

    def test_status_failure_after_switch_prints_no_success(self):
        self.set_state(active="octo-work", accounts={"octo-work": "success", "octo-home": "success"},
                       fatal_after_switch=True)
        self.write_env("GH_ACC=octo-home\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("->", result.stderr)


class FetchUserTest(unittest.TestCase):
    def setUp(self):
        FakeGitLab.seen = []
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGitLab)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/v4/user"
        proxies = mock.patch.dict(os.environ, {"no_proxy": "*", "NO_PROXY": "*"})
        proxies.start()
        self.addCleanup(proxies.stop)

    def fetch(self, code, body):
        FakeGitLab.reply = (code, body)
        return gh_switch.fetch_user(self.url, SYNTH)

    def assert_stop(self, code, body):
        with self.assertRaises(gh_switch.Stop) as caught:
            self.fetch(code, body)
        self.assertEqual(caught.exception.code, gh_switch.STATE)
        self.assertNotIn(SYNTH, str(caught.exception))
        return str(caught.exception)

    def test_returns_username_and_sends_token_header(self):
        self.assertEqual(self.fetch(200, {"username": "io-upstars", "id": 7}), "io-upstars")
        self.assertEqual(FakeGitLab.seen, [("/api/v4/user", SYNTH)])

    def test_rejected_token(self):
        self.assertIn("401", self.assert_stop(401, {"message": "401 Unauthorized"}))

    def test_other_status_does_not_echo_body(self):
        self.assertIn("403", self.assert_stop(403, {"message": SYNTH}))

    def test_success_class_status_other_than_200_stops(self):
        self.assertIn("202", self.assert_stop(202, {"username": "io-upstars"}))

    def test_redirect_is_not_followed(self):
        self.assertIn("302", self.assert_stop(302, b""))
        self.assertEqual(len(FakeGitLab.seen), 1)

    def test_unreadable_reply(self):
        for body in (b"not json", {"username": ""}, {"username": "bad name!"}, [1], {}):
            with self.subTest(body=body):
                self.assert_stop(200, body)

    def test_truncated_reply_stops(self):
        self.assert_stop(200, "truncated")

    def test_unreachable_host(self):
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(gh_switch.Stop) as caught:
            gh_switch.fetch_user(self.url, SYNTH)
        self.assertEqual(caught.exception.code, gh_switch.STATE)


class EnsureGitLabTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="evgs-gl-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.project = self.tmp / "project"
        self.project.mkdir()
        git(self.project, "init", "-q")
        git(self.project, "remote", "add", "origin", "git@gitlab.example.test:io/okr.git")
        self.requests = []
        self.reply = "io-upstars"
        fake = mock.patch.object(gh_switch, "fetch_user", self.fake_fetch)
        fake.start()
        self.addCleanup(fake.stop)

    def fake_fetch(self, url, token):
        self.requests.append((url, token))
        if isinstance(self.reply, gh_switch.Stop):
            raise self.reply
        return self.reply

    def write_env(self, text):
        directory = self.project / ".env"
        directory.mkdir(exist_ok=True)
        (directory / ".env").write_text(text, encoding="utf-8")

    def stop(self):
        with self.assertRaises(gh_switch.Stop) as caught:
            gh_switch.ensure_gitlab(self.project)
        message = str(caught.exception)
        for form in secret_forms(GL_SYNTH):
            self.assertNotIn(form, message)
        return caught.exception.code, message

    def test_silent_when_token_belongs_to_gl_acc(self):
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))
        self.assertEqual(self.requests, [("https://gitlab.example.test/api/v4/user", GL_SYNTH)])

    def test_username_case_is_ignored(self):
        self.write_env(f"GL_ACC=IO-Upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))

    def test_token_of_another_account_stops(self):
        self.reply = "someone-else"
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        self.assertEqual(self.stop(), (gh_switch.MISMATCH,
                                       "GITLAB_TOKEN belongs to someone-else, expected io-upstars"))

    def test_host_comes_from_https_and_ssh_remotes(self):
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        for url in ("https://gitlab.example.test/io/okr.git", "ssh://git@gitlab.example.test:2222/io/okr.git"):
            with self.subTest(url=url):
                self.requests.clear()
                git(self.project, "remote", "set-url", "origin", url)
                gh_switch.ensure_gitlab(self.project)
                self.assertEqual(self.requests[0][0], "https://gitlab.example.test/api/v4/user")

    def test_unreadable_remotes_stop_instead_of_skipping(self):
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        real_run = gh_switch.run
        failures = (
            subprocess.TimeoutExpired(["git"], 1),
            OSError("git missing"),
            subprocess.CompletedProcess(["git"], 128, "", "fatal"),
        )
        for failure in failures:
            def fake_run(argv, failure=failure):
                if "remote" not in argv:
                    return real_run(argv)
                if isinstance(failure, BaseException):
                    raise failure
                return failure
            with self.subTest(failure=type(failure).__name__), \
                    mock.patch.object(gh_switch, "run", fake_run):
                self.assertEqual(self.stop(), (gh_switch.STATE, "could not read the Git remotes"))
        self.assertEqual(self.requests, [])

    def test_silent_without_gl_acc_or_gitlab_remote(self):
        self.write_env(f"GITLAB_TOKEN={GL_SYNTH}\n")
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        git(self.project, "remote", "set-url", "origin", "git@github.com:sentimony/demo-app.git")
        for name, url in (("local", "../other"), ("dotted", "backup.example/repo.git"),
                          ("file", "file:///tmp/repo.git"), ("alias", "gitlab-work:io/okr.git")):
            git(self.project, "remote", "add", name, url)
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))
        self.assertEqual(self.requests, [])

    def test_silent_without_env_file(self):
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))
        self.assertEqual(self.requests, [])

    def test_configuration_errors_do_not_echo_values(self):
        cases = {
            "missing token": "GL_ACC=io-upstars\n",
            "empty token": "GL_ACC=io-upstars\nGITLAB_TOKEN=\n",
            "duplicate token": f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\nGITLAB_TOKEN={GL_SYNTH}\n",
            "exported token": f"GL_ACC=io-upstars\nexport GITLAB_TOKEN={GL_SYNTH}\n",
            "spaced token": f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH} trailing\n",
            "single-quoted token": f"GL_ACC=io-upstars\nGITLAB_TOKEN='{GL_SYNTH}'\n",
            "double-quoted token": f'GL_ACC=io-upstars\nGITLAB_TOKEN="{GL_SYNTH}"\n',
            "invalid username": f"GL_ACC=bad name!\nGITLAB_TOKEN={GL_SYNTH}\n",
            "quoted username": f'GL_ACC="io-upstars"\nGITLAB_TOKEN={GL_SYNTH}\n',
            "duplicate username": f"GL_ACC=io-upstars\nGL_ACC=io-other\nGITLAB_TOKEN={GL_SYNTH}\n",
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.write_env(text)
                code, message = self.stop()
                self.assertEqual(code, gh_switch.CONFIG)
                for fragment in ("bad name!", '"io-upstars"', "trailing"):
                    self.assertNotIn(fragment, message)
        self.assertEqual(self.requests, [])

    def test_github_remote_next_to_gitlab_is_not_a_second_host(self):
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        git(self.project, "remote", "add", "mirror", "git@github.com:sentimony/demo-app.git")
        self.assertIsNone(gh_switch.ensure_gitlab(self.project))
        self.assertEqual([url for url, _ in self.requests], ["https://gitlab.example.test/api/v4/user"])

    def test_more_than_one_gitlab_host_stops(self):
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        git(self.project, "remote", "add", "upstream", "git@gitlab.other.test:io/okr.git")
        self.assertEqual(self.stop()[0], gh_switch.CONFIG)
        self.assertEqual(self.requests, [])

    def test_api_failure_is_masked(self):
        self.assertEqual(len(secret_forms(GL_SYNTH)), 6)
        self.reply = gh_switch.Stop(gh_switch.STATE, "echo " + " ".join(sorted(secret_forms(GL_SYNTH))))
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        self.assertEqual(self.stop()[0], gh_switch.STATE)

    def test_main_reports_mismatch_line(self):
        self.reply = "someone-else"
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.dict(os.environ, {"GH_HOST": "", "GH_REPO": ""}):
            code = gh_switch.main(["--cwd", str(self.project), "--gitlab"])
        self.assertEqual(code, 7)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "gh-switch: GITLAB_TOKEN belongs to someone-else, expected io-upstars\n")

    def test_gitlab_mode_ignores_github_state(self):
        self.write_env(f"GH_ACC=octo-home\nGL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        out, err = io.StringIO(), io.StringIO()
        # GH_TOKEN would stop the GitHub branch with exit 4; GitLab mode must not look at it.
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.dict(os.environ, {"GH_TOKEN": "x"}):
            code = gh_switch.main(["--cwd", str(self.project), "--gitlab"])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "", ""))
        self.assertEqual(len(self.requests), 1)

    def test_default_mode_does_not_read_the_gitlab_token(self):
        self.reply = "someone-else"
        self.write_env(f"GL_ACC=io-upstars\nGITLAB_TOKEN={GL_SYNTH}\n")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.dict(os.environ, {"GH_HOST": "", "GH_REPO": ""}):
            code = gh_switch.main(["--cwd", str(self.project)])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "", ""))
        self.assertEqual(self.requests, [])



def skill_section(heading):
    """Return the body of one '## ' section of the skill's SKILL.md."""
    text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    start = text.index("\n## " + heading + "\n")
    end = text.find("\n## ", start + 1)
    return " ".join(text[start:end if end != -1 else len(text)].split())


class SwitchReportContractTest(unittest.TestCase):
    """20261024-2354: a switch is the skill's job, so it is neither warned about nor undone."""

    def test_run_section_forbids_warning_and_switching_back(self):
        body = skill_section("Run the helper")
        self.assertIn("do not warn the user that the account changed for other sessions", body)
        self.assertIn("do not offer, suggest, or run a switch back to the previous account", body)

    def test_security_model_marks_the_shared_switch_as_expected(self):
        body = skill_section("Security Model")
        self.assertIn("This is expected; do not report it beyond the helper's line or offer "
                      "to switch back.", body)


if __name__ == "__main__":
    unittest.main()
