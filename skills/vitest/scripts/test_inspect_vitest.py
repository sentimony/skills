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


class InspectVitestTests(unittest.TestCase):
    def make_project(self, root):
        (root / "package-lock.json").write_text("{}", encoding="utf-8")
        (root / "package.json").write_text(
            json.dumps(
                {
                    "packageManager": "npm@10.8.2",
                    "scripts": {
                        "custom-secret-script": f"vitest run --reporter={HOSTILE}",
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
        (root / ".nvmrc").write_text("20.11.1\n", encoding="utf-8")
        (root / ".node-version").write_text(f"{HOSTILE}\n", encoding="utf-8")
        (root / "vitest.config.ts").write_text("export default {}\n", encoding="utf-8")
        (root / f"vitest.config.{HOSTILE}.ts").write_text("export default {}\n", encoding="utf-8")
        (root / "vitest.projects.ts").write_text("export default []\n", encoding="utf-8")
        for relative in ("tests/private-name.test.ts", "src/unit.spec.ts"):
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
        self.assertEqual(report.get("schema_version"), 1)
        self.assertEqual(report.get("package_manager"), "npm")
        self.assertEqual(report.get("vitest_dependency"), "present")
        self.assertEqual(report.get("test_runner"), "package-script")
        self.assertEqual(report.get("filesystem_candidates", {}).get("total"), 2)
        self.assertNotIn(HOSTILE, report_json)
        self.assertNotIn("custom-secret-script", report_json)
        self.assertNotIn("tests/private-name.test.ts", report_json)
        self.assertNotIn(HOSTILE, human_stdout)
        self.assertNotIn(HOSTILE, human_stderr)
        self.assertNotIn("custom-secret-script", human_stdout)
        self.assertNotIn("tests/private-name.test.ts", human_stdout)

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

        self.assertEqual(report.get("filesystem_candidates", {}).get("total"), 2)

    def test_human_and_json_render_the_same_normalized_semantics(self):
        """Mutation target: renderer-specific fields or raw values in either output mode."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            report = self.report_for(root)

        human_stdout, human_stderr = self.render_human(report)
        for value in (
            report.get("package_manager"),
            report.get("vitest_dependency"),
            report.get("test_runner"),
            report.get("node", {}).get("runtime"),
            report.get("node", {}).get("nvmrc"),
            report.get("node", {}).get("node_version_file"),
            report.get("node", {}).get("engines"),
            report.get("node", {}).get("volta"),
        ):
            self.assertIsNotNone(value)
            self.assertIn(value, human_stdout)
        self.assertNotIn(HOSTILE, human_stderr)


if __name__ == "__main__":
    unittest.main()
