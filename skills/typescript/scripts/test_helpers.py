#!/usr/bin/env python3
"""Regression tests for the helper scripts. Run: python3 test_helpers.py"""

import json
import io
import os
import pathlib
import sys
import tempfile
import threading
import time
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import inspect_typescript as it
import local_tools
import run_typecheck as rt
import trace_perf as tp


def make_project(root, pkg, tsconfig=None, lockfile=None, files=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    if tsconfig is not None:
        (root / "tsconfig.json").write_text(json.dumps(tsconfig), encoding="utf-8")
    if lockfile:
        (root / lockfile).touch()
    for rel in files or []:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("export const x = 1\n", encoding="utf-8")


def build_command(root):
    args = types.SimpleNamespace(project=None, files=None)
    return rt.build_command(root, args, rt.detect_package_manager(root))


def make_local_compiler(path, listed_files):
    """Create a local test compiler that reports only the supplied paths."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "#!/usr/bin/env python3\n" + "\n".join(
        "print({!r})".format(str(item)) for item in listed_files
    ) + "\n"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def make_nuxt_solution(root):
    """Create a real Nuxt solution layout with local listFilesOnly compilers."""
    make_project(root, {
        "dependencies": {"nuxt": "4.5.1", "vue": "3.5.0"},
        "devDependencies": {"typescript": "6.0.3", "vue-tsc": "3.3.8"},
    }, tsconfig={"references": [
        {"path": "./.nuxt/tsconfig.app.json"},
        {"path": "./.nuxt/tsconfig.server.json"},
        {"path": "./.nuxt/tsconfig.shared.json"},
        {"path": "./.nuxt/tsconfig.node.json"},
    ]}, files=[
        "src/app.ts", "server/api/health.ts", "shared/types.ts", "nuxt.config.ts",
        "tests/unit.test.ts", "vitest.config.ts", "playwright.config.ts",
    ])
    configs = {
        "app": {"strict": True, "noImplicitOverride": True},
        "server": {"strict": True, "noImplicitOverride": False},
        "shared": {"strict": True, "noImplicitOverride": True},
        "node": {"strict": True, "noImplicitOverride": True},
    }
    for name, options in configs.items():
        path = root / ".nuxt" / "tsconfig.{}.json".format(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"compilerOptions": options}), encoding="utf-8")
    make_local_compiler(root / "node_modules/.bin/vue-tsc", [root / "src/app.ts"])
    make_local_compiler(root / "node_modules/.bin/tsc", [
        root / "server/api/health.ts", root / "shared/types.ts", root / "nuxt.config.ts",
    ])


def run_cli(module, argv):
    """Run one helper CLI and return its status plus safe observable output."""
    before = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        sys.argv = argv
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = module.main()
    finally:
        sys.argv = before
    return status, stdout.getvalue(), stderr.getvalue()


class HelperScriptTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_package_manager_declaration_without_lockfile(self):
        root = self.tmp / "nolock"
        make_project(root, {"packageManager": "pnpm@9.0.0",
                            "devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"compilerOptions": {"strict": True}})
        info = it.inspect(root)
        self.assertEqual(info["package_manager"], "pnpm")
        self.assertEqual(info["recommended_typecheck"], "local tsc --noEmit")

    def test_project_typecheck_script_wins(self):
        root = self.tmp / "plain"
        make_project(root, {"scripts": {"typecheck": "tsc --noEmit"},
                            "devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={}, lockfile="yarn.lock")
        self.assertEqual(build_command(root), (["yarn", "run", "typecheck"],
                                               "project script 'typecheck'"))
        self.assertEqual(it.inspect(root)["recommended_typecheck"], "yarn run typecheck")

    def test_vue_fallback_uses_vue_tsc(self):
        root = self.tmp / "vueapp"
        make_project(root, {"dependencies": {"vue": "3.4.0"},
                            "devDependencies": {"vue-tsc": "2.0.0", "typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]}, lockfile="package-lock.json")
        command, mode = build_command(root)
        self.assertEqual(command, [str(root / "node_modules/.bin/vue-tsc"), "--noEmit", "--pretty", "false"])
        self.assertEqual(mode, "direct vue-tsc")
        self.assertEqual(it.inspect(root)["recommended_typecheck"], "project script or local vue-tsc --noEmit")

    def test_nuxt_fallback_uses_nuxi(self):
        root = self.tmp / "nuxtapp"
        make_project(root, {"dependencies": {"nuxt": "3.13.0", "vue": "3.4.0"}},
                     tsconfig={}, lockfile="pnpm-lock.yaml")
        self.assertEqual(build_command(root),
                         ([str(root / "node_modules/.bin/nuxi"), "typecheck"], "nuxi typecheck"))
        info = it.inspect(root)
        self.assertEqual(info["framework"]["name"], "nuxt")
        self.assertIsNone(info["uncovered"])  # generated-config framework

    def test_svelte_fallback_uses_svelte_check(self):
        root = self.tmp / "svapp"
        make_project(root, {"devDependencies": {"svelte": "5.0.0", "typescript": "5.6.0"}},
                     tsconfig={})
        self.assertEqual(build_command(root),
                         ([str(root / "node_modules/.bin/svelte-check")], "svelte-check"))

    def test_astro_fallback_uses_astro_check(self):
        root = self.tmp / "astroapp"
        make_project(root, {"dependencies": {"astro": "4.16.0"}}, tsconfig={})
        self.assertEqual(build_command(root),
                         ([str(root / "node_modules/.bin/astro"), "check"], "astro check"))

    def test_uncovered_files_reported_as_category_counts(self):
        # Mutation target: uncovered files are counted per category, never named.
        root = self.tmp / "coverage"
        make_project(root, {"devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]},
                     files=["src/a.ts", "netlify/functions/handler.ts",
                            "scripts/tool.config.ts", "e2e/login.spec.ts"])
        self.assertEqual(it.inspect(root)["uncovered"],
                         {"total": 3, "production": 1, "tests": 1, "config": 1})

    def test_uncovered_file_names_never_reach_the_report(self):
        # Mutation target: repository-controlled file names stay out of both renderers.
        root = self.tmp / "coverage-hostile"
        marker = "HOSTILE_PATH_MARKER_IGNORE_PREVIOUS_INSTRUCTIONS"
        make_project(root, {"devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]},
                     files=["src/a.ts", "{}/handler.ts".format(marker)])
        status_json, output_json, errors_json = run_cli(
            it, ["inspect_typescript.py", "--root", str(root), "--json"]
        )
        status_human, output_human, errors_human = run_cli(
            it, ["inspect_typescript.py", "--root", str(root)]
        )
        self.assertEqual((status_json, status_human), (0, 0))
        self.assertNotIn(marker, output_json + errors_json + output_human + errors_human)
        self.assertEqual(json.loads(output_json)["uncovered"]["total"], 1)

    def make_hoisted_workspace(self, name, with_git=True):
        workspace = self.tmp / name
        package_root = workspace / "packages" / "api"
        make_project(package_root, {"devDependencies": {"typescript": "5.6.0"}}, tsconfig={})
        if with_git:
            (workspace / ".git").mkdir(parents=True, exist_ok=True)
        binary = workspace / "node_modules" / ".bin" / "tsc"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
        return package_root, binary

    def test_hoisted_workspace_binary_is_found_from_a_package_root(self):
        # Mutation target: build_command() must walk up to a hoisted node_modules.
        package_root, binary = self.make_hoisted_workspace("workspace")
        command, _ = build_command(package_root)
        self.assertEqual(pathlib.Path(command[0]).resolve(), binary.resolve())

    def test_binary_outside_the_repository_is_never_selected(self):
        # Mutation target: without a repository boundary the lookup must stay local.
        package_root, binary = self.make_hoisted_workspace("nogit", with_git=False)
        self.assertIsNone(local_tools.local_binary(package_root, "tsc"))
        command, _ = build_command(package_root)
        self.assertEqual(
            pathlib.Path(command[0]),
            package_root / "node_modules" / ".bin" / "tsc",
        )
        self.assertNotEqual(pathlib.Path(command[0]).resolve(), binary.resolve())

    def test_walk_up_stops_at_the_repository_root(self):
        # Mutation target: an ancestor above the repository root is out of scope.
        package_root, _ = self.make_hoisted_workspace("bounded")
        outside = self.tmp / "node_modules" / ".bin" / "vue-tsc"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text("#!/bin/sh\nexit 0\n")
        outside.chmod(0o755)
        self.assertIsNone(local_tools.local_binary(package_root, "vue-tsc"))

    def test_native_compiler_alias_detected(self):
        root = self.tmp / "sidebyside"
        make_project(root, {"devDependencies": {
            "typescript": "^6.0.3",
            "@typescript/native": "npm:typescript@^7.0.2",
            "vue-tsc": "3.3.7",
        }, "scripts": {
            "typecheck": "vue-tsc --noEmit",
            "typecheck:ts7": "node node_modules/@typescript/native/bin/tsc -p netlify/tsconfig.json",
        }}, tsconfig={})
        info = it.inspect(root)
        self.assertTrue(info["native_compiler"])
        self.assertEqual(info["typecheck_scripts"], [
            {"targets_project": False},
            {"targets_project": True},
        ])

    def test_compat6_alias_is_not_native(self):
        # npm:@typescript/typescript6 is the TS6 compat API, not a native TS7 compiler.
        root = self.tmp / "compat6"
        make_project(root, {"devDependencies": {
            "typescript": "npm:@typescript/typescript6@^6.0.2",
            "@typescript/native": "npm:typescript@^7.0.2",
        }}, tsconfig={})
        info = it.inspect(root)
        self.assertTrue(info["native_compiler"])

    def test_coverage_complete_when_no_uncovered(self):
        root = self.tmp / "clean"
        make_project(root, {"devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]}, files=["src/a.ts"])
        self.assertEqual(it.inspect(root)["uncovered"],
                         {"total": 0, "production": 0, "tests": 0, "config": 0})

    def test_nuxt_solution_reports_program_flags_and_category_counts(self):
        # Mutation target: inspect() must discover generated Nuxt programs and union their files.
        root = self.tmp / "nuxt-solution"
        make_nuxt_solution(root)
        info = it.inspect(root)
        self.assertEqual(set(info["programs"]), {"app", "server", "shared", "node"})
        self.assertEqual(info["coverage"]["production"]["uncovered"], 0)
        self.assertEqual(info["coverage"]["tests"]["uncovered"], 1)
        self.assertEqual(info["coverage"]["config"]["uncovered"], 2)
        self.assertTrue(info["programs"]["app"]["flags"]["strict"])
        self.assertFalse(info["programs"]["server"]["flags"]["noImplicitOverride"])

    def test_nuxt_inspection_uses_only_local_program_argv(self):
        # Mutation target: nuxt_program_info() must invoke fixed local compiler argv.
        root = self.tmp / "nuxt-argv"
        make_nuxt_solution(root)
        calls = []
        original = it.run_bounded_compiler

        def record(argv, cwd):
            calls.append(argv)
            return original(argv, cwd)

        it.run_bounded_compiler = record
        try:
            it.inspect(root)
        finally:
            it.run_bounded_compiler = original
        self.assertIn([str(root / "node_modules/.bin/vue-tsc"), "--noEmit", "--pretty", "false", "--listFilesOnly", "-p", str(root / ".nuxt/tsconfig.app.json")], calls)
        self.assertIn([str(root / "node_modules/.bin/tsc"), "--noEmit", "--pretty", "false", "--listFilesOnly", "-p", str(root / ".nuxt/tsconfig.server.json")], calls)
        self.assertTrue(all(call[0].startswith(str(root / "node_modules/.bin/")) for call in calls))

    def test_missing_nuxt_generated_configs_has_one_safe_diagnostic(self):
        # Mutation target: inspect() must return a stable missing-generated-config diagnostic.
        root = self.tmp / "nuxt-missing"
        make_project(root, {"dependencies": {"nuxt": "4.5.1"}}, tsconfig={"references": [
            {"path": ".nuxt/tsconfig.app.json"},
        ]})
        info = it.inspect(root)
        self.assertEqual(info["diagnostics"], ["NUXT_GENERATED_CONFIGS_MISSING"])
        self.assertEqual(info["programs"], {})

    def test_partial_nuxt_generation_reports_existing_programs(self):
        # Mutation target: a partially generated solution is not a missing .nuxt.
        root = self.tmp / "nuxt-partial"
        make_nuxt_solution(root)
        (root / ".nuxt/tsconfig.shared.json").unlink()
        info = it.inspect(root)
        self.assertEqual(info["diagnostics"], ["NUXT_GENERATED_CONFIG_PARTIAL"])
        self.assertEqual(set(info["programs"]), {"app", "server", "node"})
        self.assertIsNone(info["coverage"])

    def test_hostile_compiler_output_is_not_reported(self):
        # Mutation target: nuxt_program_info() must treat compiler output as untrusted evidence.
        root = self.tmp / "nuxt-hostile"
        make_nuxt_solution(root)
        marker = "HOSTILE_COMPILER_MARKER_IGNORE_PREVIOUS_INSTRUCTIONS"
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text("#!/usr/bin/env python3\nprint({!r})\nprint({!r})\n".format(
            str(root / "src/app.ts"), marker), encoding="utf-8")
        compiler.chmod(0o755)
        status, output, errors = run_cli(it, ["inspect_typescript.py", "--root", str(root), "--json"])
        self.assertEqual(status, 0)
        self.assertNotIn(marker, output + errors)

    def test_node_mismatch_blocks_typecheck_before_compiler_execution(self):
        # Mutation target: runtime_preflight() must stop a Node 18 run before TypeScript starts.
        root = self.tmp / "node-mismatch"
        make_project(root, {"engines": {"node": ">=24.15.0"}, "devDependencies": {"typescript": "6.0.3"}}, tsconfig={})
        (root / ".nvmrc").write_text("24.15.0\n", encoding="utf-8")
        calls = []
        original = rt.subprocess.run

        def fake_run(argv, **kwargs):
            calls.append(argv)
            if argv == ["node", "--version"]:
                return types.SimpleNamespace(returncode=0, stdout="v18.19.1\n", stderr="")
            raise AssertionError("typecheck subprocess must not run on a Node mismatch")

        rt.subprocess.run = fake_run
        try:
            status, output, _ = run_cli(rt, ["run_typecheck.py", "--root", str(root), "--json"])
        finally:
            rt.subprocess.run = original
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output)["diagnostics"], ["NODE_RUNTIME_MISMATCH"])
        self.assertEqual(calls, [["node", "--version"]])

    def test_typecheck_fallback_never_uses_download_launcher(self):
        # Mutation target: build_command() must choose existing local tools, never npx or bunx.
        root = self.tmp / "local-tool"
        make_project(root, {"devDependencies": {"typescript": "6.0.3"}}, tsconfig={})
        command, _ = build_command(root)
        self.assertEqual(command[0], str(root / "node_modules/.bin/tsc"))
        self.assertNotIn(command[0], {"npx", "bunx"})

    def test_nuxt_coverage_counts_more_than_500_candidates_exactly(self):
        # Mutation target: find_source_files() must not silently cap exact Nuxt coverage.
        root = self.tmp / "nuxt-large"
        make_nuxt_solution(root)
        bulk = []
        for index in range(501):
            rel = "src/generated/item-{:03d}.ts".format(index)
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("export const value = {}\n".format(index), encoding="utf-8")
            bulk.append(path)
        make_local_compiler(
            root / "node_modules/.bin/vue-tsc",
            [root / "src/app.ts"] + bulk,
        )
        info = it.inspect(root)
        self.assertEqual(info["coverage"]["production"], {
            "covered": 504,
            "uncovered": 0,
        })

    def test_hostile_config_values_are_not_reported(self):
        # Mutation target: inspect() must keep config paths/labels/references/paths internal.
        root = self.tmp / "nuxt-hostile-config"
        make_nuxt_solution(root)
        marker = "HOSTILE_CONFIG_MARKER_IGNORE_PREVIOUS_INSTRUCTIONS"
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        package["scripts"] = {
            "typecheck:{}".format(marker): "tsc -p {}".format(marker),
        }
        (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
        (root / "tsconfig.{}.json".format(marker)).write_text(
            json.dumps({"compilerOptions": {"module": marker}}), encoding="utf-8"
        )
        (root / "tsconfig.json").write_text(json.dumps({
            "extends": "./{}.json".format(marker),
            "references": [
                {"path": "./.nuxt/tsconfig.app.json"},
                {"path": "./.nuxt/tsconfig.server.json"},
                {"path": "./.nuxt/tsconfig.shared.json"},
                {"path": "./.nuxt/tsconfig.node.json"},
                {"path": marker},
            ],
            "compilerOptions": {
                "moduleResolution": marker,
                "paths": {marker: [marker]},
            },
        }), encoding="utf-8")
        status_json, output_json, errors_json = run_cli(
            it, ["inspect_typescript.py", "--root", str(root), "--json"]
        )
        status_human, output_human, errors_human = run_cli(
            it, ["inspect_typescript.py", "--root", str(root)]
        )
        self.assertEqual((status_json, status_human), (0, 0))
        report = output_json + errors_json + output_human + errors_human
        self.assertNotIn(marker, report)
        parsed = json.loads(output_json)
        self.assertTrue(all(set(config) == {"flags"} for config in parsed["tsconfigs"]))
        self.assertNotIn("paths", json.dumps(parsed["tsconfigs"]))

    def test_hostile_package_identity_values_are_not_reported(self):
        # Mutation target: inspect() must normalize package-derived identity fields.
        root = self.tmp / "hostile-package-identity"
        marker = "HOSTILE_OUTPUT_MARKER"
        make_project(root, {
            "type": marker,
            "devDependencies": {
                "typescript": marker,
                "@typescript/native": "npm:typescript@^7.0.0-{}".format(marker),
            },
        }, tsconfig={})
        installed = root / "node_modules/@typescript/native/package.json"
        installed.parent.mkdir(parents=True, exist_ok=True)
        installed.write_text(json.dumps({
            "version": "7.0.0-{}".format(marker),
        }), encoding="utf-8")
        status_json, output_json, errors_json = run_cli(
            it, ["inspect_typescript.py", "--root", str(root), "--json"]
        )
        status_human, output_human, errors_human = run_cli(
            it, ["inspect_typescript.py", "--root", str(root)]
        )
        self.assertEqual((status_json, status_human), (0, 0))
        self.assertNotIn(
            marker,
            output_json + errors_json + output_human + errors_human,
        )
        parsed = json.loads(output_json)
        self.assertEqual(parsed["typescript_installation"], "declared")
        self.assertIsNone(parsed["typescript_version"])
        self.assertEqual(parsed["module_type"], "other")
        self.assertTrue(parsed["native_compiler"])

    def test_trace_perf_uses_no_download_launcher_or_recommendation(self):
        # Mutation target: trace_perf main() must use local tsc and never recommend npx/bunx.
        root = self.tmp / "trace-local"
        make_project(
            root,
            {"packageManager": "bun@1.2.0", "devDependencies": {"typescript": "6.0.3"}},
            tsconfig={},
            lockfile="bun.lock",
        )
        make_local_compiler(root / "node_modules/.bin/tsc", [])
        calls = []
        original_run = tp.subprocess.run

        def fake_run(argv, **kwargs):
            calls.append(argv)
            return types.SimpleNamespace(
                returncode=0,
                stdout="Files: 10\nTotal time: 0.10s\n",
                stderr="",
            )

        tp.subprocess.run = fake_run
        try:
            status, output, errors = run_cli(
                tp, ["trace_perf.py", "--root", str(root), "--trace"]
            )
        finally:
            tp.subprocess.run = original_run
        self.assertEqual(status, 0)
        self.assertEqual(calls[0][0], str(root / "node_modules/.bin/tsc"))
        self.assertNotIn("npx", output + errors)
        self.assertNotIn("bunx", output + errors)

    def test_trace_perf_missing_compiler_hides_absolute_path(self):
        # Mutation target: trace_perf must keep launcher failures path-free and stable.
        root = self.tmp / "trace-missing-compiler"
        make_project(root, {"devDependencies": {"typescript": "6.0.3"}}, tsconfig={})
        compiler = root / "node_modules/.bin/tsc"
        compiler.parent.mkdir(parents=True, exist_ok=True)
        compiler.touch()
        original_run = tp.subprocess.run

        def missing_compiler(*args, **kwargs):
            raise FileNotFoundError("simulated launcher failure")

        tp.subprocess.run = missing_compiler
        try:
            status, output, errors = run_cli(tp, ["trace_perf.py", "--root", str(root)])
        finally:
            tp.subprocess.run = original_run
        self.assertEqual(status, 2)
        self.assertIn("Diagnostic: TRACE_LOCAL_COMPILER_UNAVAILABLE", errors)
        self.assertNotIn(str(compiler), output + errors)

    def test_unsupported_node_engine_ranges_are_unknown(self):
        # Mutation target: project_node_requirements() must not treat ^/~ as minimum ranges.
        for index, node_range in enumerate(("^24.15.0", "~24.15.0")):
            root = self.tmp / "unsupported-range-{}".format(index)
            make_project(root, {"engines": {"node": node_range}}, tsconfig={})
            self.assertEqual(rt.runtime_preflight(root), ["NODE_RUNTIME_UNKNOWN"])

    def test_malformed_node_versions_are_unknown(self):
        # Mutation target: normalize_node_version() must reject trailing junk via full-match.
        root = self.tmp / "malformed-node"
        make_project(root, {"engines": {"node": ">=24.15.0"}}, tsconfig={})
        original_run = rt.subprocess.run

        def fake_run(argv, **kwargs):
            return types.SimpleNamespace(
                returncode=0,
                stdout="v24.15.0TRAILING_JUNK\n",
                stderr="",
            )

        rt.subprocess.run = fake_run
        try:
            self.assertEqual(rt.runtime_preflight(root), ["NODE_RUNTIME_UNKNOWN"])
        finally:
            rt.subprocess.run = original_run

    def test_missing_nuxt_compilers_keep_programs_and_unavailable_coverage(self):
        # Mutation target: nuxt_program_info() must retain identities and withhold coverage.
        root = self.tmp / "nuxt-missing-compilers"
        make_nuxt_solution(root)
        (root / "node_modules/.bin/vue-tsc").unlink()
        (root / "node_modules/.bin/tsc").unlink()
        info = it.inspect(root)
        self.assertEqual(set(info["programs"]), {"app", "server", "shared", "node"})
        self.assertIsNone(info["coverage"])
        self.assertEqual(info["diagnostics"], ["NUXT_LOCAL_COMPILER_UNAVAILABLE"])
        self.assertTrue(all(program["covered"] is None for program in info["programs"].values()))
        status, output, errors = run_cli(
            it, ["inspect_typescript.py", "--root", str(root)]
        )
        self.assertEqual(status, 0)
        self.assertIn("coverage unavailable", output)
        self.assertNotIn("None file(s)", output + errors)

    def test_failed_nuxt_compiler_keeps_programs_and_hides_output(self):
        # Mutation target: nuxt_program_info() must withhold coverage on nonzero compilers.
        root = self.tmp / "nuxt-failed-compiler"
        make_nuxt_solution(root)
        marker = "HOSTILE_FAILED_COMPILER_MARKER"
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            "print({!r}, file=sys.stderr)\nsys.exit(1)\n".format(marker),
            encoding="utf-8",
        )
        compiler.chmod(0o755)
        info = it.inspect(root)
        self.assertEqual(set(info["programs"]), {"app", "server", "shared", "node"})
        self.assertIsNone(info["coverage"])
        self.assertEqual(info["diagnostics"], ["NUXT_PROGRAM_COMPILER_FAILED"])
        status, output, errors = run_cli(
            it, ["inspect_typescript.py", "--root", str(root), "--json"]
        )
        self.assertEqual(status, 0)
        self.assertNotIn(marker, output + errors)

    def test_oversized_nuxt_compiler_output_is_bounded_and_withholds_coverage(self):
        # Mutation target: capture_output=True can retain arbitrary compiler output.
        root = self.tmp / "nuxt-oversized-output"
        make_nuxt_solution(root)
        marker = "HOSTILE_OVERSIZED_COMPILER_OUTPUT"
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text(
            "#!/usr/bin/env python3\n"
            "print({!r})\n"
            "print('A' * 4096)\n".format(marker),
            encoding="utf-8",
        )
        compiler.chmod(0o755)
        original_limit = it.NUXT_COMPILER_OUTPUT_BYTES
        it.NUXT_COMPILER_OUTPUT_BYTES = 512
        try:
            info = it.inspect(root)
            status, output, errors = run_cli(
                it, ["inspect_typescript.py", "--root", str(root), "--json"]
            )
        finally:
            it.NUXT_COMPILER_OUTPUT_BYTES = original_limit

        self.assertEqual(status, 0)
        self.assertIsNone(info["coverage"])
        self.assertEqual(
            info["diagnostics"], ["NUXT_PROGRAM_COMPILER_OUTPUT_LIMIT"]
        )
        self.assertNotIn(marker, output + errors)
        self.assertNotIn(str(root), output + errors)

    def test_nonterminating_nuxt_compiler_is_killed_reaped_and_reported_safely(self):
        # Mutation target: an unbounded compiler wait can hang inspection forever.
        root = self.tmp / "nuxt-timeout"
        make_nuxt_solution(root)
        pid_file = root / "compiler.pid"
        marker = "HOSTILE_NONTERMINATING_COMPILER_OUTPUT"
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text(
            "#!/usr/bin/env python3\n"
            "import os\n"
            "import time\n"
            "from pathlib import Path\n"
            "Path({!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
            "print({!r}, flush=True)\n"
            "while True:\n"
            "    time.sleep(1)\n".format(str(pid_file), marker),
            encoding="utf-8",
        )
        compiler.chmod(0o755)
        original_timeout = it.NUXT_COMPILER_TIMEOUT_SECONDS
        it.NUXT_COMPILER_TIMEOUT_SECONDS = 0.2
        try:
            started = time.monotonic()
            info = it.inspect(root)
            elapsed = time.monotonic() - started
            status, output, errors = run_cli(
                it, ["inspect_typescript.py", "--root", str(root), "--json"]
            )
        finally:
            it.NUXT_COMPILER_TIMEOUT_SECONDS = original_timeout

        compiler_pid = int(pid_file.read_text(encoding="utf-8"))
        self.assertLess(elapsed, 2)
        self.assertEqual(status, 0)
        self.assertIsNone(info["coverage"])
        self.assertEqual(info["diagnostics"], ["NUXT_PROGRAM_COMPILER_TIMEOUT"])
        self.assertNotIn(marker, output + errors)
        self.assertNotIn(str(root), output + errors)
        with self.assertRaises(ProcessLookupError):
            os.kill(compiler_pid, 0)

    def test_nuxt_compiler_timeout_still_applies_after_output_fds_close(self):
        # Mutation target: a bare wait() after reader EOF can block past the deadline.
        root = self.tmp / "nuxt-closed-output-timeout"
        make_nuxt_solution(root)
        pid_file = root / "closed-output.pid"
        stop_file = root / "stop-compiler"
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text(
            "#!/bin/sh\n"
            "printf '%s' \"$$\" > {!r}\n"
            "exec 1>&-\n"
            "exec 2>&-\n"
            "while [ ! -e {!r} ]; do\n"
            "  sleep 0.01\n"
            "done\n".format(str(pid_file), str(stop_file)),
            encoding="utf-8",
        )
        compiler.chmod(0o755)
        original_timeout = it.NUXT_COMPILER_TIMEOUT_SECONDS
        it.NUXT_COMPILER_TIMEOUT_SECONDS = 1
        result = {}
        failures = []

        def inspect_project():
            try:
                result["info"] = it.inspect(root)
            except BaseException as error:
                failures.append(error)

        worker = threading.Thread(target=inspect_project)
        started = time.monotonic()
        compiler_pid = None
        completed_within_deadline = False
        try:
            worker.start()
            ready_deadline = time.monotonic() + 2
            while not pid_file.exists() and time.monotonic() < ready_deadline:
                time.sleep(0.01)
            if pid_file.exists():
                compiler_pid = int(pid_file.read_text(encoding="utf-8"))
            worker.join(2)
            completed_within_deadline = not worker.is_alive()
        finally:
            if worker.is_alive():
                stop_file.touch()
            worker.join(2)
            it.NUXT_COMPILER_TIMEOUT_SECONDS = original_timeout
        elapsed = time.monotonic() - started

        self.assertIsNotNone(compiler_pid, "fake compiler did not signal readiness")
        self.assertTrue(completed_within_deadline)
        self.assertFalse(worker.is_alive())
        self.assertFalse(failures)
        self.assertLess(elapsed, 3)
        info = result["info"]
        self.assertIsNone(info["coverage"])
        self.assertEqual(info["diagnostics"], ["NUXT_PROGRAM_COMPILER_TIMEOUT"])
        rendered = json.dumps(info)
        self.assertNotIn(str(root), rendered)
        with self.assertRaises(ProcessLookupError):
            os.kill(compiler_pid, 0)

    def test_overlong_nuxt_compiler_line_withholds_coverage(self):
        # Mutation target: processing an unbounded output line as a candidate path.
        root = self.tmp / "nuxt-line-limit"
        make_nuxt_solution(root)
        compiler = root / "node_modules/.bin/vue-tsc"
        compiler.write_text(
            "#!/usr/bin/env python3\nprint('A' * 512)\n",
            encoding="utf-8",
        )
        compiler.chmod(0o755)
        original_limit = it.NUXT_COMPILER_LINE_BYTES
        it.NUXT_COMPILER_LINE_BYTES = 128
        try:
            info = it.inspect(root)
        finally:
            it.NUXT_COMPILER_LINE_BYTES = original_limit

        self.assertIsNone(info["coverage"])
        self.assertEqual(
            info["diagnostics"], ["NUXT_PROGRAM_COMPILER_LINE_LIMIT"]
        )


if __name__ == "__main__":
    unittest.main()
