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
import re
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


def parse_version(value):
    if not value:
        return None
    match = re.search(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(value))
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def is_exact_version(value):
    return bool(re.fullmatch(r"\s*v?\d+\.\d+\.\d+\s*", str(value or "")))


def matches_version_prefix(current, expected):
    return current[: len(expected)] == expected


def read_optional_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def current_node_version():
    try:
        result = subprocess.run(
            ["node", "-v"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


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


DIRECT_SCRIPT_PATTERN = re.compile(
    # Optional environment prefix: one or more KEY=value pairs, with or without
    # cross-env. The value class is shell-inert on purpose: it excludes whitespace,
    # quotes, parentheses, braces, brackets, glob characters and every character
    # that could start a command, a substitution or a redirection. Equals signs are
    # allowed inside the value so NODE_OPTIONS=--max-old-space-size=4096 still counts.
    r"(?:(?:cross-env[ \t]+)?(?:[A-Za-z_][A-Za-z0-9_]*=[A-Za-z0-9_.:/@,+=-]*[ \t]+)+)?"
    # Optional launcher. Only launchers that take the binary name as their next
    # argument are accepted; the sole npx flag allowed is --no-install, because
    # flags such as -c or -p change what npx actually executes.
    r"(?:npx[ \t]+(?:--no-install[ \t]+)?|npm[ \t]+exec[ \t]+"
    r"|pnpm[ \t]+(?:exec[ \t]+)?|yarn[ \t]+|bunx[ \t]+|bun[ \t]+)?"
    # Vitest plus its arguments. The excluded characters are the ones that chain a
    # command (semicolon, ampersand, pipe, carriage return, newline), redirect
    # streams, or substitute output (backtick, dollar sign).
    r"vitest(?:[ \t]+[^&;|<>`$\n\r]*)?"
)


def is_direct_vitest_script(body):
    """A script body is direct when it only invokes Vitest.

    Package scripts are untrusted repository data: auto-selecting one means running
    whatever else it chains. Anything with shell chaining, redirection, substitution,
    or a second binary is not auto-run.

    Every separator in the pattern is explicit horizontal whitespace, and the match
    is a fullmatch over the stripped body, so a newline can never enter the command
    line: in sh a bare newline separates commands exactly like a semicolon.
    """
    return bool(DIRECT_SCRIPT_PATTERN.fullmatch(str(body or "").strip()))


def find_script(package_json, requested, watch=False):
    """Return (script_name, skipped_indirect).

    skipped_indirect is True only when auto-selection found no direct script but
    did skip at least one indirect candidate, so the caller can explain the fallback.
    """
    scripts = package_json.get("scripts", {})
    if requested:
        if requested not in scripts:
            raise SystemExit(f"Script not found in package.json: {requested}")
        return requested, False

    skipped_indirect = False

    if watch:
        watch_names = ("test:watch", "vitest:watch", "watch:test", "watch")
        for name in watch_names:
            value = scripts.get(name)
            if value and "vitest" in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if "vitest" in value and "watch" in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if "vitest" in value and "run" not in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
    else:
        for name in ("test:unit", "test:vitest", "vitest", "test"):
            if name in scripts and "vitest" in scripts[name]:
                if not is_direct_vitest_script(scripts[name]):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if "vitest" in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False

    return None, skipped_indirect


def check_node_version(root, package_json):
    current = current_node_version()
    current_version = parse_version(current)
    blockers = []
    warnings = []

    engines = package_json.get("engines", {}) if package_json else {}
    volta = package_json.get("volta", {}) if package_json else {}
    exact_hints = {
        ".nvmrc": read_optional_text(root / ".nvmrc"),
        ".node-version": read_optional_text(root / ".node-version"),
        "package.json volta.node": volta.get("node") if isinstance(volta, dict) else None,
    }

    if not current:
        if any(exact_hints.values()) or (isinstance(engines, dict) and engines.get("node")):
            blockers.append("Project declares a Node version, but `node -v` is not available.")
        return blockers, warnings

    for source, expected in exact_hints.items():
        expected_version = parse_version(expected)
        if is_exact_version(expected) and current_version and expected_version and current_version != expected_version:
            blockers.append(
                f"Project expects Node {expected} from {source}, but current Node is {current}."
            )

    engines_node = engines.get("node") if isinstance(engines, dict) else None
    engine_version = parse_version(engines_node)
    if current_version and engine_version and isinstance(engines_node, str):
        if engines_node.strip().startswith((">=", ">")) and current_version < engine_version:
            warnings.append(
                f"package.json engines.node is {engines_node}, but current Node is {current}."
            )
        elif re.fullmatch(r"\s*v?\d+(?:\.\d+){0,2}\s*", engines_node) and not matches_version_prefix(current_version, engine_version):
            warnings.append(
                f"package.json engines.node is {engines_node}, but current Node is {current}."
            )

    return blockers, warnings


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
    parser.add_argument("--skip-node-check", action="store_true", help="Skip project Node version preflight")
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
    if not args.skip_node_check:
        blockers, warnings = check_node_version(root, package_json)
        for warning in warnings:
            print(f"Warning: {warning}")
        if blockers:
            for blocker in blockers:
                print(blocker)
            print("Switch to the project Node version before running Vitest, for example with nvm/fnm/Volta/mise/asdf.")
            print("Use --skip-node-check to bypass this check.")
            sys.exit(1)

    manager = args.manager or detect_package_manager(root, package_json)
    script_name, skipped_indirect = find_script(package_json, args.script, watch=args.watch)
    if args.script:
        requested_body = package_json.get("scripts", {}).get(args.script)
        if not is_direct_vitest_script(requested_body):
            print(
                "Warning: SCRIPT_NOT_DIRECT (explicit --script runs a package script "
                "that does more than invoke Vitest)"
            )
    command = build_command(root, manager, script_name, vitest_args, watch=args.watch)
    # Printed only after build_command confirmed the local binary exists, so the note
    # never promises a fallback that is about to fail.
    if skipped_indirect:
        print(
            "Note: SCRIPT_NOT_DIRECT; using node_modules/.bin/vitest. "
            "Pass --script <name> to run the package script instead."
        )

    print(f"Root: {root}")
    print(f"Command: {' '.join(command)}")
    if args.dry_run:
        return

    result = subprocess.run(command, cwd=root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
