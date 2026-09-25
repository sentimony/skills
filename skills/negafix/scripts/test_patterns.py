#!/usr/bin/env python3
"""Keep the negafix regexes in SKILL.md and the commit hook honest.

Runs on bare Python; CI executes it as `python test_patterns.py`.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
HOOK = SKILL_DIR / "scripts" / "commit-msg"


def read_variable(name: str) -> str:
    """Return the regex assigned to NAME in the first `NAME=...` line of SKILL.md."""
    for line in SKILL_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            value = line[len(name) + 1:]
            if value[0] in "\"'" and value[-1] == value[0]:
                value = value[1:-1]
            return value
    raise AssertionError(f"{name}= not found in {SKILL_MD}")


def compile_variable(name: str) -> re.Pattern:
    # Only PATTERN runs as `rg -i`; the other variables carry their own `(?i)`.
    flags = re.IGNORECASE if name == "PATTERN" else 0
    return re.compile(read_variable(name), flags | re.MULTILINE)


DETERMINISTIC_HITS = [
    "It's not just a linter, it enforces the release checklist.",
    "This is not a retry helper but a resilience layer.",
    "More than just a cache, it is the product.",
    "Це не просто скрипт, це філософія.",
]
DETERMINISTIC_MISSES = [
    "The function does not retry on 5xx responses.",
    "The parser reads bytes rather than characters.",
    "Configuration comes directly from the schema, no guessing.",
]

CROSS_HITS = [
    "This does not mean the cache is optional. It means the cache is the whole product.",
    "The goal isn't speed.\nThe goal is being blazing fast on every run.",
    "It's not a feature. It's a philosophy.",
    "This isn't a cache. This is a database.",
    "It is not a proxy. It is a resolver.",
    "This does not mean the cache\nis optional. It means the cache is the whole product.",
    "The goal isn't shaving a few milliseconds off the cold path that nobody measures\nin production anyway. The goal is being fast where it counts.",
]
CROSS_MISSES = [
    "It is fast. It is also cheap.",
    "This does not retry. The caller does.",
    "The client does not retry on 5xx responses; the caller decides whether to retry.",
    "It's not just fast; it responds in under 20 ms at p99.",
]

RATHER_HITS = [
    "We ship a platform rather than just a tool.",
    "Rather than a tool, we ship a platform.",
]
RATHER_MISSES = ["I would rather ship on Monday."]

OBJECTION_HITS = [
    "To be clear, I'm not proposing to hide outages.",
    "Don't get me wrong, this isn't about replacing the ORM.",
    "Some might say the loop hides outages, but every retry is logged.",
]
OBJECTION_MISSES = [
    "I am not on call this week.",
    "This is about the retry loop.",
]

TAIL_HITS = [
    "Configuration comes directly from the schema, no guessing.",
    "The build runs on the host toolchain, no Docker required.",
]
TAIL_MISSES = [
    "There is, no doubt, a cost to this.",
    "We accept no arguments.",
    "Run it with --no-cache to skip the cache.",
]


class VariableTests(unittest.TestCase):
    def check(self, name, hits, misses):
        pattern = compile_variable(name)
        for text in hits:
            with self.subTest(name=name, text=text):
                self.assertIsNotNone(pattern.search(text), f"{name} should match: {text!r}")
        for text in misses:
            with self.subTest(name=name, text=text):
                self.assertIsNone(pattern.search(text), f"{name} should not match: {text!r}")

    def test_deterministic(self):
        self.check("PATTERN", DETERMINISTIC_HITS, DETERMINISTIC_MISSES)

    def test_cross(self):
        self.check("CROSS", CROSS_HITS, CROSS_MISSES)

    def test_rather(self):
        self.check("RATHER", RATHER_HITS, RATHER_MISSES)

    def test_objection(self):
        self.check("OBJECTION", OBJECTION_HITS, OBJECTION_MISSES)

    def test_tail(self):
        self.check("TAIL", TAIL_HITS, TAIL_MISSES)


@unittest.skipUnless(shutil.which("perl"), "perl is not installed")
class HookTests(unittest.TestCase):
    """The hook must agree with PATTERN on every deterministic sample."""

    def run_hook(self, message: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write(message + "\n")
            path = handle.name
        try:
            # A C locale proves the hook decodes UTF-8 itself (-CSD) instead of relying
            # on the caller's locale.
            env = os.environ.copy()
            env.update(LC_ALL="C", LANG="C")
            result = subprocess.run(
                ["sh", str(HOOK), path], capture_output=True, text=True, check=False,
                env=env,
            )
        finally:
            os.unlink(path)
        self.assertEqual(result.returncode, 0, "the hook must never block")
        return result.stderr

    def test_hook_warns_on_hits(self):
        for text in DETERMINISTIC_HITS:
            with self.subTest(text=text):
                self.assertIn("negafix:", self.run_hook(text))

    def test_hook_silent_on_misses(self):
        for text in DETERMINISTIC_MISSES:
            with self.subTest(text=text):
                self.assertEqual("", self.run_hook(text))


if __name__ == "__main__":
    unittest.main()
