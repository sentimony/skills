#!/usr/bin/env python3
"""
Inspect a JavaScript/TypeScript project for Vitest conventions.

Usage:
    python <skill>/scripts/inspect_vitest.py --root .
    python <skill>/scripts/inspect_vitest.py --root ../my-app --json
"""

import argparse
import json
from pathlib import Path


LOCKFILES = [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("package-lock.json", "npm"),
    ("npm-shrinkwrap.json", "npm"),
]

CONFIG_FILES = [
    "vitest.config.ts",
    "vitest.config.mts",
    "vitest.config.cts",
    "vitest.config.js",
    "vitest.config.mjs",
    "vitest.config.cjs",
    "vite.config.ts",
    "vite.config.mts",
    "vite.config.cts",
    "vite.config.js",
    "vite.config.mjs",
    "vite.config.cjs",
]

PROJECT_FILES = [
    "vitest.workspace.ts",
    "vitest.workspace.mts",
    "vitest.workspace.js",
    "vitest.workspace.mjs",
    "vitest.workspace.cjs",
    "vitest.projects.ts",
    "vitest.projects.mts",
    "vitest.projects.js",
    "vitest.projects.mjs",
    "vitest.projects.cjs",
    "vitest.projects.json",
]

TEST_GLOBS = [
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.test.mts",
    "**/*.test.cts",
    "**/*.test.js",
    "**/*.test.jsx",
    "**/*.test.mjs",
    "**/*.test.cjs",
    "**/*.spec.ts",
    "**/*.spec.tsx",
    "**/*.spec.mts",
    "**/*.spec.cts",
    "**/*.spec.js",
    "**/*.spec.jsx",
    "**/*.spec.mjs",
    "**/*.spec.cjs",
]

IGNORE_PARTS = {"node_modules", "dist", "build", "coverage", ".git", ".next", ".nuxt", ".output"}


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def package_manager_field(package_json):
    value = package_json.get("packageManager") if package_json else None
    if not isinstance(value, str):
        return None
    manager = value.split("@", 1)[0]
    return manager if manager in {"npm", "pnpm", "yarn", "bun"} else None


def detect_package_manager(root, package_json=None):
    lockfile_managers = []
    for filename, manager in LOCKFILES:
        if (root / filename).exists() and manager not in lockfile_managers:
            lockfile_managers.append(manager)
    if len(lockfile_managers) == 1:
        return lockfile_managers[0]

    declared_manager = package_manager_field(package_json)
    if declared_manager:
        return declared_manager
    if lockfile_managers:
        return lockfile_managers[0]
    return "npm"


def package_command(root, manager, script_name=None):
    if script_name:
        if manager == "npm":
            return f"npm run {script_name} --"
        if manager == "yarn":
            return f"yarn {script_name}"
        if manager == "pnpm":
            return f"pnpm {script_name}"
        if manager == "bun":
            return f"bun run {script_name}"

    local_vitest = root / "node_modules" / ".bin" / "vitest"
    if local_vitest.exists():
        return f"{local_vitest} run"
    return "No suitable command found; add a Vitest package script or install Vitest locally."


def has_dep(package_json, name):
    if not package_json:
        return False
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        if name in package_json.get(section, {}):
            return True
    return False


def detect_frameworks(package_json):
    checks = {
        "vitest": "vitest",
        "vite": "vite",
        "nuxt": "nuxt",
        "next": "next",
        "vue": "vue",
        "react": "react",
        "svelte": "svelte",
        "jsdom": "jsdom",
        "happy-dom": "happy-dom",
        "@nuxt/test-utils": "@nuxt/test-utils",
        "@testing-library/react": "@testing-library/react",
        "@testing-library/jest-dom": "@testing-library/jest-dom",
        "@vitest/coverage-v8": "@vitest/coverage-v8",
        "@vitest/coverage-istanbul": "@vitest/coverage-istanbul",
        "@vue/test-utils": "@vue/test-utils",
    }
    return sorted(label for label, dep in checks.items() if has_dep(package_json, dep))


def find_test_files(root, limit):
    files = []
    for pattern in TEST_GLOBS:
        for path in root.glob(pattern):
            if any(part in IGNORE_PARTS for part in path.parts):
                continue
            files.append(path)
    unique = sorted(set(files))
    return [str(path.relative_to(root)) for path in unique[:limit]], len(unique)


def detect_likely_test_script(scripts):
    if not scripts:
        return None
    for name in ("test:unit", "test:vitest", "vitest", "test"):
        value = scripts.get(name)
        if value and "vitest" in value:
            return name
    for name, value in scripts.items():
        if "vitest" in value:
            return name
    return None


def build_report(root, limit):
    package_json_path = root / "package.json"
    package_json = read_json(package_json_path)
    scripts = package_json.get("scripts", {}) if package_json else {}
    manager = detect_package_manager(root, package_json)
    test_script = detect_likely_test_script(scripts)
    test_files, total_tests = find_test_files(root, limit)
    config_files = [name for name in CONFIG_FILES if (root / name).exists()]
    project_files = [name for name in PROJECT_FILES if (root / name).exists()]
    frameworks = detect_frameworks(package_json)

    warnings = []
    notes = []
    if not package_json:
        warnings.append("No package.json found.")
    if package_json and not has_dep(package_json, "vitest"):
        warnings.append("Vitest is not listed in package dependencies.")
    if "react" in frameworks and not any(env in frameworks for env in ("jsdom", "happy-dom")):
        warnings.append("React component tests usually need jsdom or happy-dom.")
    if "vue" in frameworks and not any(env in frameworks for env in ("jsdom", "happy-dom")):
        warnings.append("Vue component tests usually need jsdom or happy-dom.")
    if not config_files:
        notes.append("No Vitest/Vite config file found; this is fine for simple Node tests, but DOM, aliases, setup files, coverage, or projects may need config.")

    return {
        "root": str(root),
        "package_manager": manager,
        "package_manager_field": package_json.get("packageManager") if package_json else None,
        "frameworks": frameworks,
        "vitest_scripts": {name: value for name, value in scripts.items() if "vitest" in value},
        "likely_test_script": test_script,
        "suggested_run_command": package_command(root, manager, test_script),
        "config_files": config_files,
        "project_files": project_files,
        "test_files_sample": test_files,
        "test_files_total": total_tests,
        "notes": notes,
        "warnings": warnings,
    }


def print_human(report):
    print(f"Root: {report['root']}")
    print(f"Package manager: {report['package_manager']}")
    print(f"Framework hints: {', '.join(report['frameworks']) or 'none'}")
    print(f"Suggested run command: {report['suggested_run_command']}")

    print("\nVitest scripts:")
    if report["vitest_scripts"]:
        for name, value in report["vitest_scripts"].items():
            marker = " (likely)" if name == report["likely_test_script"] else ""
            print(f"  - {name}{marker}: {value}")
    else:
        print("  - none")

    print("\nConfig files:")
    for name in report["config_files"] or ["none"]:
        print(f"  - {name}")

    print("\nWorkspace/project files:")
    for name in report["project_files"] or ["none"]:
        print(f"  - {name}")

    print(f"\nTest files: {report['test_files_total']}")
    for path in report["test_files_sample"]:
        print(f"  - {path}")

    if report["notes"]:
        print("\nNotes:")
        for note in report["notes"]:
            print(f"  - {note}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main():
    parser = argparse.ArgumentParser(description="Inspect a project for Vitest setup and conventions")
    parser.add_argument("--root", default=".", help="Project root to inspect (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--limit", type=int, default=20, help="Maximum test files to list (default: 20)")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Root is not a directory: {root}")

    report = build_report(root, args.limit)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
