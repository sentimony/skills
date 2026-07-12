#!/usr/bin/env python3
"""Regression tests for the helper scripts. Run: python3 test_helpers.py"""

import json
import sys
import tempfile
import types
import unittest
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
        self.assertEqual(info["recommended_typecheck"], "pnpm exec tsc --noEmit")

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
        self.assertEqual(command, ["npx", "vue-tsc", "--noEmit", "--pretty", "false"])
        self.assertEqual(mode, "direct vue-tsc")
        self.assertEqual(it.inspect(root)["recommended_typecheck"], "npx vue-tsc --noEmit")

    def test_nuxt_fallback_uses_nuxi(self):
        root = self.tmp / "nuxtapp"
        make_project(root, {"dependencies": {"nuxt": "3.13.0", "vue": "3.4.0"}},
                     tsconfig={}, lockfile="pnpm-lock.yaml")
        self.assertEqual(build_command(root),
                         (["pnpm", "exec", "nuxi", "typecheck"], "nuxi typecheck"))
        info = it.inspect(root)
        self.assertEqual(info["framework"]["name"], "nuxt")
        self.assertIsNone(info["uncovered_files"])  # generated-config framework

    def test_svelte_fallback_uses_svelte_check(self):
        root = self.tmp / "svapp"
        make_project(root, {"devDependencies": {"svelte": "5.0.0", "typescript": "5.6.0"}},
                     tsconfig={})
        self.assertEqual(build_command(root), (["npx", "svelte-check"], "svelte-check"))

    def test_astro_fallback_uses_astro_check(self):
        root = self.tmp / "astroapp"
        make_project(root, {"dependencies": {"astro": "4.16.0"}}, tsconfig={})
        self.assertEqual(build_command(root), (["npx", "astro", "check"], "astro check"))

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


if __name__ == "__main__":
    unittest.main()
