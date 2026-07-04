#!/usr/bin/env python3
"""
Run Vitest through the package manager detected from lockfiles or package.json.

Usage:
    python <skill>/scripts/run_vitest.py --root .
    python <skill>/scripts/run_vitest.py --root . -- tests/example.test.ts
    python <skill>/scripts/run_vitest.py --root . --coverage -- tests/example.test.ts
    python <skill>/scripts/run_vitest.py --root . --test-name "formats currency"

Arguments after "--" are passed directly to Vitest.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


LOCKFILES = [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("package-lock.json", "npm"),
    ("npm-shrinkwrap.json", "npm"),
]


def read_package_json(root):
    path = root / "package.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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


def find_script(package_json, requested, watch=False):
    scripts = package_json.get("scripts", {})
    if requested:
        if requested not in scripts:
            raise SystemExit(f"Script not found in package.json: {requested}")
        return requested
    if watch:
        watch_names = ("test:watch", "vitest:watch", "watch:test", "watch")
        for name in watch_names:
            value = scripts.get(name)
            if value and "vitest" in value:
                return name
        for name, value in scripts.items():
            if "vitest" in value and "watch" in value:
                return name
        for name, value in scripts.items():
            if "vitest" in value and "run" not in value:
                return name
        return None
    for name in ("test:unit", "test:vitest", "vitest", "test"):
        if name in scripts and "vitest" in scripts[name]:
            return name
    for name, value in scripts.items():
        if "vitest" in value:
            return name
    return None


def build_command(root, manager, script_name, vitest_args, watch=False):
    if script_name:
        if manager == "npm":
            return ["npm", "run", script_name, "--", *vitest_args]
        if manager == "yarn":
            return ["yarn", script_name, *vitest_args]
        if manager == "pnpm":
            return ["pnpm", script_name, *vitest_args]
        if manager == "bun":
            return ["bun", "run", script_name, *vitest_args]

    local_vitest = root / "node_modules" / ".bin" / "vitest"
    if not local_vitest.exists():
        raise SystemExit(
            "No suitable Vitest command found. Add a package.json script that runs Vitest "
            "or install Vitest locally so node_modules/.bin/vitest exists."
        )

    return [str(local_vitest), "watch" if watch else "run", *vitest_args]


def main():
    parser = argparse.ArgumentParser(description="Run Vitest with package-manager detection")
    parser.add_argument("--root", default=".", help="Project root (default: current directory)")
    parser.add_argument("--manager", choices=["npm", "pnpm", "yarn", "bun"], help="Override package manager")
    parser.add_argument("--script", help="Package.json script to run instead of auto-detecting")
    parser.add_argument("--coverage", action="store_true", help="Add --coverage")
    parser.add_argument("--watch", action="store_true", help="Use watch mode")
    parser.add_argument("--test-name", help="Filter tests by name pattern")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it")
    parser.add_argument("vitest_args", nargs=argparse.REMAINDER, help="Arguments after -- are passed to Vitest")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Root is not a directory: {root}")

    vitest_args = list(args.vitest_args)
    if vitest_args and vitest_args[0] == "--":
        vitest_args = vitest_args[1:]
    if args.coverage:
        vitest_args.insert(0, "--coverage")
    if args.test_name:
        vitest_args = ["--testNamePattern", args.test_name, *vitest_args]

    package_json = read_package_json(root)
    manager = args.manager or detect_package_manager(root, package_json)
    script_name = find_script(package_json, args.script, watch=args.watch)
    command = build_command(root, manager, script_name, vitest_args, watch=args.watch)

    print(f"Root: {root}")
    print(f"Command: {' '.join(command)}")
    if args.dry_run:
        return

    result = subprocess.run(command, cwd=root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
