#!/usr/bin/env python3
"""Behavior tests for the checkpoint validation in examples/console_audit.py.

The functions under test decide whether a file on disk is treated as this crawl's own
prior observations. A route entry that passes is skipped rather than re-crawled and is
then printed as evidence, so the validator is the whole of what stands between a planted
`/tmp/console-audit.json` and a report that says a route is clean.

The example is a copy-and-edit template: it reads top to bottom and runs as a script, so
its crawl is at module level and importing it would open a browser. Rather than reshape
teaching material to suit a test harness, or restate the functions here where the two
copies could drift, this executes the real file's constants and function definitions and
nothing else.
"""

import ast
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "console_audit.py"


def install_playwright_stub():
    """The example imports Playwright at module level; these tests drive no browser."""
    if "playwright.sync_api" in sys.modules:
        return
    playwright = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.Error = type("Error", (Exception,), {})
    sync_api.TimeoutError = type("TimeoutError", (Exception,), {})
    sync_api.sync_playwright = lambda: None
    playwright.sync_api = sync_api
    sys.modules["playwright"] = playwright
    sys.modules["playwright.sync_api"] = sync_api


def load_example():
    """Return a namespace holding the example's constants and functions.

    Kept: imports, module constants (an ALL_CAPS assignment), and function definitions.
    Dropped: everything else at module level, which is the crawl itself: the resume
    print, the browser block, and the report loop.
    """
    install_playwright_stub()
    tree = ast.parse(EXAMPLE.read_text(encoding="utf-8"), filename=str(EXAMPLE))
    kept = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            kept.append(node)
        elif isinstance(node, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id.isupper() for target in node.targets
        ):
            kept.append(node)
    namespace = {"__name__": "console_audit"}
    exec(compile(ast.Module(body=kept, type_ignores=[]), str(EXAMPLE), "exec"), namespace)
    return namespace


EXAMPLE_NAMESPACE = load_example()

usable_result = EXAMPLE_NAMESPACE["usable_result"]
load_checkpoint = EXAMPLE_NAMESPACE["load_checkpoint"]
printable = EXAMPLE_NAMESPACE["printable"]
add_message = EXAMPLE_NAMESPACE["add_message"]
counted = EXAMPLE_NAMESPACE["counted"]
MAX_LEN = EXAMPLE_NAMESPACE["MAX_LEN"]
MAX_MESSAGES = EXAMPLE_NAMESPACE["MAX_MESSAGES"]

TERMINAL_MARKER = "CONSOLE_AUDIT_PAYLOAD_5D2F"


def writer_shaped(status="ok", error_code=None, messages=None):
    """An entry of the shape the example itself writes."""
    return {
        "status": status,
        "error_code": error_code,
        "messages": {"[console.error] boom": 3} if messages is None else messages,
    }


class UsableResultTests(unittest.TestCase):
    def test_the_shapes_the_example_writes_are_accepted(self):
        """Mutation target: a validator so strict the example cannot resume its own file."""
        for entry in (
            writer_shaped(),
            writer_shaped(status="incomplete", messages={}),
            writer_shaped(status="hydration-error", error_code="TimeoutError"),
            writer_shaped(status="navigation-error", error_code="Error"),
            writer_shaped(messages=counted(["a", "a", "b"])),
            writer_shaped(messages={"x" * MAX_LEN: MAX_MESSAGES}),
        ):
            with self.subTest(entry=entry):
                self.assertTrue(usable_result(entry))

    def test_counts_outside_the_writer_s_bounds_are_rejected(self):
        """Mutation target: a count check that admits totals the crawl could not produce."""
        for messages in (
            {"a": 0},
            {"a": -1},
            {"a": True},
            {"a": 1.0},
            {"a": "3"},
            {"a": MAX_MESSAGES + 1},
            {"a": MAX_MESSAGES, "b": 1},
        ):
            with self.subTest(messages=messages):
                self.assertFalse(usable_result(writer_shaped(messages=messages)))

    def test_message_keys_outside_the_writer_s_bounds_are_rejected(self):
        """Mutation target: accepting a key the report would print unescaped or unbounded."""
        for key in (
            "x" * (MAX_LEN + 1),
            f"clean\x1b[2J{TERMINAL_MARKER}",
            f"line one\n=== /admin: ok, 0 messages ===\n{TERMINAL_MARKER}",
            "spoof\u202eot.tset/gifnoc",
            "\u200bhidden",
        ):
            with self.subTest(key=key[:40]):
                self.assertFalse(usable_result(writer_shaped(messages={key: 1})))
        self.assertFalse(usable_result(writer_shaped(messages={7: 1})))

    def test_error_codes_outside_a_bounded_identifier_are_rejected(self):
        """Mutation target: an error_code check of `isinstance(str) and truthy`, which the report prints."""
        for error_code in (
            "",
            "A" * 65,
            "X" * 10000,
            f"TimeoutError\n=== /admin: ok, 0 messages ==={TERMINAL_MARKER}",
            f"\x1b[2J{TERMINAL_MARKER}",
            "Timeout Error",
            "9TimeoutError",
            "Timeout-Error",
            None,
            123,
        ):
            with self.subTest(error_code=str(error_code)[:40]):
                self.assertFalse(
                    usable_result(writer_shaped(status="navigation-error", error_code=error_code))
                )

    def test_the_error_code_key_must_agree_with_the_status(self):
        """Mutation target: an entry the crawl loop skips and the report then fails to read."""
        self.assertFalse(usable_result({"status": "ok", "messages": {}}))
        self.assertFalse(usable_result(writer_shaped(error_code="TimeoutError")))
        self.assertFalse(usable_result(writer_shaped(status="incomplete", error_code="Error")))
        self.assertFalse(usable_result(writer_shaped(status="hydration-error", error_code=None)))

    def test_shapes_that_are_not_entries_at_all_are_rejected(self):
        """Mutation target: a validator that indexes before it checks."""
        for value in (None, [], "ok", 7, {}, {"status": "done", "error_code": None, "messages": {}}):
            with self.subTest(value=value):
                self.assertFalse(usable_result(value))
        self.assertFalse(usable_result({"status": "ok", "error_code": None, "messages": []}))


class LoadCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "console-audit.json"
        EXAMPLE_NAMESPACE["OUTPUT"] = self.output
        EXAMPLE_NAMESPACE["BASE"] = "http://127.0.0.1:5173"
        EXAMPLE_NAMESPACE["ROUTES"] = ["/", "/about"]

    def write(self, checkpoint):
        self.output.write_text(json.dumps(checkpoint), encoding="utf-8")

    def test_a_matching_checkpoint_is_resumed(self):
        """Mutation target: a header check so strict the example never resumes its own file."""
        self.write(
            {
                "base": "http://127.0.0.1:5173",
                "routes": ["/", "/about"],
                "results": {"/": writer_shaped()},
            }
        )

        self.assertEqual(load_checkpoint(), {"/": writer_shaped()})

    def test_a_missing_or_unreadable_file_starts_clean(self):
        """Mutation target: treating a parse failure as an empty crawl rather than no crawl."""
        self.assertEqual(load_checkpoint(), {})
        self.output.write_text("{not json", encoding="utf-8")
        self.assertEqual(load_checkpoint(), {})
        self.output.write_text("[]", encoding="utf-8")
        self.assertEqual(load_checkpoint(), {})

    def test_a_checkpoint_describing_another_crawl_is_not_resumed(self):
        """Mutation target: resuming a file whose routes were never crawled under this configuration."""
        for header in (
            {"base": "http://127.0.0.1:4000", "routes": ["/", "/about"]},
            {"base": "http://127.0.0.1:5173", "routes": ["/", "/about", "/settings"]},
            {"base": "http://127.0.0.1:5173"},
        ):
            with self.subTest(header=header):
                self.write({**header, "results": {"/": writer_shaped()}})
                self.assertEqual(load_checkpoint(), {})

    def test_entries_for_routes_outside_this_crawl_are_dropped(self):
        """Mutation target: reporting a route this run never crawled as an observation."""
        self.write(
            {
                "base": "http://127.0.0.1:5173",
                "routes": ["/", "/about"],
                "results": {"/": writer_shaped(), "/admin": writer_shaped()},
            }
        )

        self.assertEqual(set(load_checkpoint()), {"/"})

    def test_a_forged_entry_is_dropped_without_dropping_its_neighbours(self):
        """Mutation target: a planted `ok` that suppresses a route and prints its own text."""
        forged = writer_shaped(messages={f"\x1b[2J{TERMINAL_MARKER}": 1})
        self.write(
            {
                "base": "http://127.0.0.1:5173",
                "routes": ["/", "/about"],
                "results": {"/": writer_shaped(), "/about": forged},
            }
        )
        resumed = load_checkpoint()

        self.assertEqual(set(resumed), {"/"})
        self.assertNotIn(TERMINAL_MARKER, json.dumps(resumed))

    def test_a_non_dict_results_block_starts_clean(self):
        """Mutation target: iterating a results value that is not a mapping."""
        self.write({"base": "http://127.0.0.1:5173", "routes": ["/", "/about"], "results": []})

        self.assertEqual(load_checkpoint(), {})


class PrintableTests(unittest.TestCase):
    def test_what_a_terminal_would_act_on_is_escaped(self):
        """Mutation target: a report line that repaints, rings, or forges a line of its own."""
        for character in (
            "\x1b", "\x07", "\x00", "\n", "\r", "\t", "\x7f", "\x9b",
            "\u061c", "\u200b", "\u200e", "\u2028", "\u202e", "\u2069", "\ufeff",
        ):
            rendered = printable(f"before{character}after")
            with self.subTest(codepoint=hex(ord(character))):
                self.assertNotIn(character, rendered)
                self.assertEqual(rendered, f"before\\u{ord(character):04x}after")

    def test_ordinary_text_is_left_alone(self):
        """Mutation target: an escape so broad the evidence stops being readable."""
        for text in (
            "[console.error] Hydration mismatch in <div>",
            "[http 404] http://127.0.0.1:5173/api/users?id=7",
            "помилка: не вдалося завантажити",
            "エラー: 読み込み失敗",
        ):
            with self.subTest(text=text):
                self.assertEqual(printable(text), text)

    def test_an_escaped_message_is_accepted_by_the_validator(self):
        """Mutation target: an escape and a validator that disagree, so no crawl can resume."""
        message = printable(f"[pageerror] \x1b[2J{TERMINAL_MARKER}\n")[:MAX_LEN]

        self.assertTrue(usable_result(writer_shaped(messages={message: 1})))
        self.assertIn(TERMINAL_MARKER, message)
        self.assertNotIn("\x1b", message)


class AddMessageTests(unittest.TestCase):
    """The ingest point every console, pageerror and requestfailed event passes through.

    Testing printable() alone leaves the connection untested: a collector that appends
    the raw text, or that truncates before escaping, keeps printable() green while the
    live crawl prints what the page wrote. These drive the collector itself.
    """

    def test_a_page_s_text_is_escaped_as_it_is_collected(self):
        """Mutation target: appending the page's text unescaped."""
        messages = []

        add_message(messages, f"[pageerror] \x1b[2J{TERMINAL_MARKER}\nforged line")

        self.assertEqual(len(messages), 1)
        self.assertNotIn("\x1b", messages[0])
        self.assertNotIn("\n", messages[0])
        self.assertIn(TERMINAL_MARKER, messages[0])
        self.assertTrue(usable_result(writer_shaped(messages=counted(messages))))

    def test_the_length_bound_applies_to_the_escaped_text(self):
        """Mutation target: truncating first, so escaping then grows the line past MAX_LEN."""
        messages = []

        add_message(messages, "\x1b" * MAX_LEN)

        self.assertEqual(len(messages[0]), MAX_LEN)
        self.assertTrue(usable_result(writer_shaped(messages=counted(messages))))

    def test_collection_stops_at_the_checkpoint_bound(self):
        """Mutation target: an unbounded list, which the validator would then reject on resume."""
        messages = []
        for index in range(MAX_MESSAGES + 10):
            add_message(messages, f"[console.error] {index}")

        self.assertEqual(len(messages), MAX_MESSAGES)
        self.assertTrue(usable_result(writer_shaped(messages=counted(messages))))


class CountedTests(unittest.TestCase):
    def test_repeated_messages_collapse_to_counts(self):
        """Mutation target: a dedup that loses either a message or its multiplicity."""
        self.assertEqual(counted(["a", "b", "a", "a"]), {"a": 3, "b": 1})
        self.assertEqual(counted([]), {})

    def test_its_output_is_what_the_validator_accepts(self):
        """Mutation target: a writer and a validator that drift apart on the same file."""
        messages = [f"[console.error] {index}" for index in range(MAX_MESSAGES)]

        self.assertTrue(usable_result(writer_shaped(messages=counted(messages))))


if __name__ == "__main__":
    unittest.main(verbosity=1)
