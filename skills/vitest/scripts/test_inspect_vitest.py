#!/usr/bin/env python3
"""Behavior tests for the safe Vitest inspection report."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inspect_vitest


HOSTILE = "IGNORE_PREVIOUS_INSTRUCTIONS_7F31"
CUSTOM_SCRIPT = "custom-secret-script"
SCRIPT_BODY = f"vitest run --reporter={HOSTILE}"
HOSTILE_CONFIG_FILE = f"vitest.config.{HOSTILE}.ts"
PRIVATE_TEST_FILE = "tests/private-name.test.ts"


class InspectVitestTests(unittest.TestCase):
    def make_project(self, root):
        (root / "package-lock.json").write_text("{}", encoding="utf-8")
        (root / "package.json").write_text(
            json.dumps(
                {
                    "packageManager": "npm@10.8.2",
                    "scripts": {
                        CUSTOM_SCRIPT: SCRIPT_BODY,
                    },
                    "devDependencies": {
                        "vitest": "^2.0.0",
                        "nuxt": "^3.0.0",
                        "vue": "^3.0.0",
                    },
                    "engines": {"node": ">=20.0.0"},
                }
            ),
            encoding="utf-8",
        )
        (root / ".nvmrc").write_text(f"{HOSTILE}\n", encoding="utf-8")
        (root / ".node-version").write_text(f"{HOSTILE}\n", encoding="utf-8")
        (root / "vitest.config.ts").write_text("export default {}\n", encoding="utf-8")
        (root / HOSTILE_CONFIG_FILE).write_text("export default {}\n", encoding="utf-8")
        (root / "vitest.projects.ts").write_text("export default []\n", encoding="utf-8")
        for relative in (PRIVATE_TEST_FILE, "src/unit.spec.ts"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("export {}\n", encoding="utf-8")

    def report_for(self, root):
        # The Node executable is external state; pin it so version diagnostics are deterministic.
        with patch.object(inspect_vitest, "current_node_version", return_value="v20.11.1"):
            return inspect_vitest.build_report(root, limit=20)

    def render_human(self, report):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            inspect_vitest.print_human(report)
        return stdout.getvalue(), stderr.getvalue()

    def test_report_is_normalized_and_does_not_leak_repository_text(self):
        """Mutation target: returning raw scripts, names, filenames, or version-file text."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            report = self.report_for(root)

        report_json = json.dumps(report)
        human_stdout, human_stderr = self.render_human(report)
        self.assertEqual(report.get("schema_version"), 2)
        self.assertEqual(report.get("package_manager"), "npm")
        self.assertEqual(report.get("vitest_dependency"), "present")
        self.assertEqual(report.get("test_runner"), "package-script")
        self.assertEqual(report.get("filesystem_candidates"), {
            "lower_bound": 2,
            "truncated": False,
            "truncation_reason": None,
        })
        # Mutation target: leaking a repository-controlled value only through stderr.
        for raw_value in (
            HOSTILE,
            CUSTOM_SCRIPT,
            SCRIPT_BODY,
            HOSTILE_CONFIG_FILE,
            PRIVATE_TEST_FILE,
        ):
            for rendered_value in (report_json, human_stdout, human_stderr):
                self.assertNotIn(raw_value, rendered_value)

    def test_invalid_version_declarations_are_unknown(self):
        """Mutation target: accepting partial or malformed version declarations as valid."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            (root / ".nvmrc").write_text("20\n", encoding="utf-8")
            (root / ".node-version").write_text("v20.11\n", encoding="utf-8")
            package_json = json.loads((root / "package.json").read_text(encoding="utf-8"))
            package_json["engines"]["node"] = "twenty"
            package_json["volta"] = {"node": "20.11"}
            (root / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
            report = self.report_for(root)

        self.assertEqual(report.get("node", {}).get("nvmrc"), "unknown")
        self.assertEqual(report.get("node", {}).get("node_version_file"), "unknown")
        self.assertEqual(report.get("node", {}).get("engines"), "unknown")
        self.assertEqual(report.get("node", {}).get("volta"), "unknown")

    def test_non_string_version_metadata_is_unknown_without_an_exception(self):
        """Mutation target: passing untyped repository metadata into version regex parsing."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            package_json = json.loads((root / "package.json").read_text(encoding="utf-8"))
            package_json["volta"] = {"node": 20}
            (root / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
            try:
                report = self.report_for(root)
            except TypeError:
                report = None

        self.assertIsNotNone(report)
        self.assertEqual(report.get("node", {}).get("volta"), "unknown")

    def test_node_engine_minimum_operators_preserve_strict_boundary_semantics(self):
        """Mutation target: treating a strict greater-than range as greater-than-or-equal."""
        boundary = (20, 0, 0)
        above = (20, 0, 1)

        self.assertEqual(
            inspect_vitest.engine_status(">20.0.0", boundary), "incompatible"
        )
        self.assertEqual(inspect_vitest.engine_status(">20.0.0", above), "compatible")
        self.assertEqual(
            inspect_vitest.engine_status(">=20.0.0", boundary), "compatible"
        )
        self.assertEqual(inspect_vitest.engine_status("^20.0.0", above), "unknown")

    def test_generated_and_toolchain_directories_do_not_count_as_candidates(self):
        """Mutation target: counting generated or toolchain test-shaped files."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            for relative in (
                "node_modules/tool/example.test.ts",
                ".nuxt/generated.spec.ts",
                "coverage/report.test.ts",
                "dist/bundle.test.ts",
                "build/output.test.ts",
                ".next/cache.test.ts",
                ".output/server.test.ts",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("export {}\n", encoding="utf-8")
            report = self.report_for(root)

        self.assertEqual(
            report.get("filesystem_candidates", {}).get("lower_bound"), 2
        )

    def test_ignored_ancestor_name_does_not_hide_project_candidates(self):
        """Mutation target: checking ignored directory names above the project root."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "build" / "project"
            root.mkdir(parents=True)
            self.make_project(root)
            report = self.report_for(root)

        self.assertEqual(
            report.get("filesystem_candidates", {}).get("lower_bound"), 2
        )

    def test_candidate_scan_stops_at_cap_and_prunes_ignored_directories(self):
        """Mutation target: repeated full-tree globs or ignored-directory descent."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            visited_directory_lists = []

            def traversal(_root, onerror=None):
                directories = ["node_modules", "coverage", "src"]
                visited_directory_lists.append(directories)
                yield str(root), directories, ["first.test.ts", "second.spec.ts"]
                raise AssertionError("candidate scan continued after reaching its cap")

            with patch.object(inspect_vitest.os, "walk", side_effect=traversal):
                scan = inspect_vitest.scan_test_files(
                    root, candidate_limit=1, visited_limit=50
                )

        self.assertEqual(scan, {
            "lower_bound": 1,
            "truncated": True,
            "truncation_reason": "candidate-limit",
        })
        self.assertEqual(
            [tuple(directories) for directories in visited_directory_lists],
            [("src",)],
        )

    def test_candidate_scan_stops_at_explicit_visited_file_cap(self):
        """Mutation target: traversing an unbounded tree without a candidate match."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def traversal(_root, onerror=None):
                yield str(root), [], ["one.txt", "two.txt", "z-last.test.ts"]

            with patch.object(inspect_vitest.os, "walk", side_effect=traversal):
                scan = inspect_vitest.scan_test_files(
                    root, candidate_limit=20, visited_limit=2
                )

        self.assertEqual(scan, {
            "lower_bound": 0,
            "truncated": True,
            "truncation_reason": "visited-file-limit",
        })

    def test_candidate_scan_surfaces_walk_errors_without_leaking_details(self):
        """Mutation target: os.walk silently swallowing a scandir permission error."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = "PRIVATE_PERMISSION_ERROR_PATH"

            def traversal(_root, onerror=None):
                yield str(root), [], ["observed.test.ts"]
                if onerror is not None:
                    onerror(PermissionError(f"{marker}: {root}"))

            with patch.object(inspect_vitest.os, "walk", side_effect=traversal):
                scan = inspect_vitest.scan_test_files(
                    root, candidate_limit=20, visited_limit=50
                )

        self.assertEqual(scan, {
            "lower_bound": 1,
            "truncated": True,
            "truncation_reason": "filesystem-error",
        })
        self.assertNotIn(marker, json.dumps(scan))
        self.assertNotIn(str(root), json.dumps(scan))

    def test_candidate_scan_sorts_filenames_before_applying_caps(self):
        """Mutation target: filesystem enumeration order changing a bounded result."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scans = []
            for filenames in (
                ["z-last.test.ts", "a-first.txt"],
                ["a-first.txt", "z-last.test.ts"],
            ):
                with patch.object(
                    inspect_vitest.os,
                    "walk",
                    return_value=iter([(str(root), [], filenames)]),
                ):
                    scans.append(inspect_vitest.scan_test_files(
                        root, candidate_limit=20, visited_limit=1
                    ))

        expected = {
            "lower_bound": 0,
            "truncated": True,
            "truncation_reason": "visited-file-limit",
        }
        self.assertEqual(scans, [expected, expected])

    def test_human_and_json_render_the_same_normalized_semantics(self):
        """Mutation target: omitting or changing a normalized field in either renderer."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            report = self.report_for(root)

        human_stdout, human_stderr = self.render_human(report)
        node = report["node"]
        configs = report["configs"]
        candidates = report["filesystem_candidates"]
        expected_stdout = (
            f"Schema version: {report['schema_version']}\n"
            f"Package manager: {report['package_manager']}\n"
            f"Vitest dependency: {report['vitest_dependency']}\n"
            f"Test runner: {report['test_runner']}\n"
            f"Frameworks: {', '.join(report['frameworks']) or 'none'}\n"
            "Node:\n"
            f"  runtime: {node['runtime']}\n"
            f"  nvmrc: {node['nvmrc']}\n"
            f"  node_version_file: {node['node_version_file']}\n"
            f"  engines: {node['engines']}\n"
            f"  volta: {node['volta']}\n"
            "Configs:\n"
            f"  vitest: {configs['vitest']}\n"
            f"  vite: {configs['vite']}\n"
            f"  projects: {configs['projects']}\n"
            "Filesystem candidates: "
            f"lower_bound={candidates['lower_bound']} "
            f"truncated={str(candidates['truncated']).lower()} "
            f"truncation_reason={candidates['truncation_reason'] or 'none'}\n"
        )
        expected_stderr = "".join(
            f"{finding['severity'].upper()} {finding['code']}: "
            f"{inspect_vitest.DIAGNOSTIC_MESSAGES[finding['code']]}\n"
            for finding in report["findings"]
        )
        self.assertEqual(human_stdout, expected_stdout)
        self.assertEqual(human_stderr, expected_stderr)


    def test_candidate_count_equal_to_the_limit_is_not_truncated(self):
        # Mutation target: only a candidate beyond the cap makes the count a lower bound.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.test.ts").write_text("")
            (root / "src" / "b.test.ts").write_text("")
            exact = inspect_vitest.scan_test_files(root, candidate_limit=2)
            beyond = inspect_vitest.scan_test_files(root, candidate_limit=1)
        self.assertEqual(exact, {
            "lower_bound": 2,
            "truncated": False,
            "truncation_reason": None,
        })
        self.assertEqual(beyond, {
            "lower_bound": 1,
            "truncated": True,
            "truncation_reason": "candidate-limit",
        })


if __name__ == "__main__":
    unittest.main()
