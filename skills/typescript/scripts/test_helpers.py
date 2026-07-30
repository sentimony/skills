#!/usr/bin/env python3
"""Regression tests for the helper scripts. Run: python3 test_helpers.py"""

import json
import io
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import inspect_typescript as it
import run_typecheck as rt


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
        self.assertIsNone(info["uncovered_files"])  # generated-config framework

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

    def test_uncovered_files_reported(self):
        root = self.tmp / "coverage"
        make_project(root, {"devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]},
                     files=["src/a.ts", "netlify/functions/handler.ts"])
        self.assertEqual(it.inspect(root)["uncovered_files"],
                         ["netlify/functions/handler.ts"])

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
        native = info["native_compiler"]
        self.assertEqual(native["name"], "@typescript/native")
        self.assertEqual(native["spec"], "npm:typescript@^7.0.2")
        scripts = {s["name"]: s["project"] for s in info["typecheck_scripts"]}
        self.assertEqual(scripts["typecheck:ts7"], "netlify/tsconfig.json")
        self.assertIsNone(scripts["typecheck"])

    def test_compat6_alias_is_not_native(self):
        # npm:@typescript/typescript6 is the TS6 compat API, not a native TS7 compiler.
        root = self.tmp / "compat6"
        make_project(root, {"devDependencies": {
            "typescript": "npm:@typescript/typescript6@^6.0.2",
            "@typescript/native": "npm:typescript@^7.0.2",
        }}, tsconfig={})
        info = it.inspect(root)
        self.assertEqual(info["native_compiler"]["name"], "@typescript/native")

    def test_coverage_complete_when_no_uncovered(self):
        root = self.tmp / "clean"
        make_project(root, {"devDependencies": {"typescript": "5.6.0"}},
                     tsconfig={"include": ["src/**/*.ts"]}, files=["src/a.ts"])
        self.assertEqual(it.inspect(root)["uncovered_files"], [])

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
        original = it.subprocess.run

        def record(argv, **kwargs):
            calls.append(argv)
            return original(argv, **kwargs)

        it.subprocess.run = record
        try:
            it.inspect(root)
        finally:
            it.subprocess.run = original
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


if __name__ == "__main__":
    unittest.main()
