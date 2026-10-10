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
    "It's not just a formatter, it enforces the commit message style.",
    "This is not a retry helper but a resilience layer.",
    "More than just a cache, it is the product.",
    "Це не просто скрипт, це філософія.",
    "це не про швидкість",
]
DETERMINISTIC_MISSES = [
    "The worker does not retry on 429 responses.",
    "The logger writes structured JSON instead of plain text lines.",
    "The migration script commits changes in a single transaction.",
    # Word-boundary regression: PATTERN's Ukrainian tail is `це не про(?![^\W\d_])`,
    # so a letter right after "про" must not match.
    "це не пропорційна відповідь",
]

CROSS_HITS = [
    "This does not mean the queue is optional. It means the queue is the safety net.",
    "The goal isn't uptime.\nThe goal is shipping without babysitting the deploy.",
    "It's not a feature. It's a philosophy.",
    "This isn't a cache. This is a database.",
    "It is not a mirror. It is a cache.",
    "This does not mean the queue\nis optional. It means the queue is the safety net.",
    "The goal isn't shaving a few seconds off the startup path that nobody notices\nduring a demo anyway. The goal is booting reliably every time.",
]
CROSS_MISSES = [
    "It is fast. It is also cheap.",
    "This does not retry. The caller does.",
    "The worker does not requeue on 4xx responses; the dispatcher decides whether to requeue.",
    "It's not just cheap; it costs a fraction of the previous vendor's license.",
]

RATHER_HITS = [
    "We ship a framework rather than just a library.",
    "Rather than a library, we ship a framework.",
]
RATHER_MISSES = ["I would rather ship on Monday."]

OBJECTION_HITS = [
    "To be clear, I'm not proposing to skip code review.",
    "Don't get me wrong, this isn't about firing the intern.",
    "Some might say the cache hides bugs, but every miss is logged.",
]
OBJECTION_MISSES = [
    "I am not on call this week.",
    "This is about the retry loop.",
]

TAIL_HITS = [
    "Retries stop after three attempts, no exceptions.",
    "Logs stream directly to stdout, no filtering.",
]
TAIL_MISSES = [
    "There is, no doubt, a cost to this.",
    "We accept no arguments.",
    "Run it with --no-cache to skip the cache.",
]

# UA_CONTRAST: `\bне X, а Y` split across a comma.
UA_CONTRAST_HITS = [
    "Мова не про терміни, а про межі відповідальності",
    "імпорт читає не тільки CSV, а й JSON",
]
UA_CONTRAST_MISSES = [
    "Скрипт не падає на порожньому вводі.",
]
# Known false positive: an imperative "не X, а Y" with no genuine contrast claim.
# UA_CONTRAST still fires on it; documented here instead of narrowing the regex
# in SKILL.md, per the plan for this task.
UA_CONTRAST_KNOWN_FALSE_POSITIVES = [
    "не запускай, а якщо запустив - зупини",
]

# UA_SPLIT: "Це не X. Це Y." split across a sentence boundary.
UA_SPLIT_HITS = [
    "Це не черга. Це журнал подій.",
]
UA_SPLIT_MISSES = [
    "Це не працює без ключа. Потрібен токен.",
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

    def test_ua_contrast(self):
        self.check("UA_CONTRAST", UA_CONTRAST_HITS, UA_CONTRAST_MISSES)
        pattern = compile_variable("UA_CONTRAST")
        for text in UA_CONTRAST_KNOWN_FALSE_POSITIVES:
            with self.subTest(name="UA_CONTRAST known false positive", text=text):
                self.assertIsNotNone(
                    pattern.search(text),
                    f"documented false positive stopped matching, re-check SKILL.md: {text!r}",
                )

    def test_ua_split(self):
        self.check("UA_SPLIT", UA_SPLIT_HITS, UA_SPLIT_MISSES)

    def test_variables_present(self):
        for name in ("UA_CONTRAST", "UA_SPLIT"):
            with self.subTest(name=name):
                value = read_variable(name)
                self.assertTrue(value.startswith("(?i)"), f"{name} should carry its own (?i): {value!r}")


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
