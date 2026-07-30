#!/usr/bin/env python3
"""
Run TypeScript type-checking and summarize compiler errors by code.

Prefers the project's own "typecheck" npm script when present; otherwise runs an
existing local `tsc`/`vue-tsc` binary directly, never a network installer.

Usage:
    python <skill>/scripts/run_typecheck.py --root .
    python <skill>/scripts/run_typecheck.py --root . --project packages/core/tsconfig.json
    python <skill>/scripts/run_typecheck.py --root . --files src/index.ts src/util.ts
    python <skill>/scripts/run_typecheck.py --root . --json
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from local_tools import local_binary


LOCKFILES = [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("package-lock.json", "npm"),
    ("npm-shrinkwrap.json", "npm"),
]

KNOWN_PACKAGE_MANAGERS = {"pnpm", "yarn", "bun", "npm"}

ERROR_RE = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\): error (?P<code>TS\d+): (?P<message>.*)$"
)

TOP_N = 5


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def detect_package_manager(root):
    for name, manager in LOCKFILES:
        if (root / name).exists():
            return manager
    # No lockfile here (e.g. a monorepo sub-package): fall back to the
    # package.json#packageManager (corepack) declaration.
    pkg = load_json(root / "package.json") or {}
    declared = pkg.get("packageManager")
    if isinstance(declared, str):
        name = declared.split("@")[0]
        if name in KNOWN_PACKAGE_MANAGERS:
            return name
    return None


VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def normalize_node_version(value):
    """Normalize a concrete Node version to a comparable three-part tuple."""
    if not isinstance(value, str):
        return None
    match = VERSION_RE.fullmatch(value.strip())
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def project_node_requirements(root):
    """Read supported exact/minimum Node requirements, or None when ambiguous."""
    requirements = []
    try:
        nvmrc = (root / ".nvmrc").read_text(encoding="utf-8").strip()
    except OSError:
        nvmrc = ""
    if nvmrc:
        version = normalize_node_version(nvmrc)
        if version is None:
            return None
        requirements.append(("exact", version))
    pkg = load_json(root / "package.json") or {}
    engines = pkg.get("engines") if isinstance(pkg.get("engines"), dict) else {}
    node_range = engines.get("node")
    if node_range is not None:
        if not isinstance(node_range, str):
            return None
        match = re.fullmatch(r"\s*(>=|=)?\s*(v?\d+\.\d+\.\d+)\s*", node_range)
        if not match:
            return None
        version = normalize_node_version(match.group(2))
        if version is None:
            return None
        operator = "minimum" if match.group(1) == ">=" else "exact"
        requirements.append((operator, version))
    return requirements


def runtime_preflight(root):
    """Return safe runtime diagnostics before starting a typecheck subprocess."""
    requirements = project_node_requirements(root)
    if requirements is None:
        return ["NODE_RUNTIME_UNKNOWN"]
    if not requirements:
        return []
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=False
        )
    except OSError:
        return ["NODE_RUNTIME_UNKNOWN"]
    active = normalize_node_version(result.stdout) if result.returncode == 0 else None
    if active is None:
        return ["NODE_RUNTIME_UNKNOWN"]
    for operator, required in requirements:
        if operator == "minimum" and active < required:
            return ["NODE_RUNTIME_MISMATCH"]
        if operator == "exact" and active != required:
            return ["NODE_RUNTIME_MISMATCH"]
    return []


def make_files_config(root, files, project):
    """Write a temp tsconfig extending the project config but checking only `files`.

    Passing files directly to tsc would bypass tsconfig entirely (strict, paths,
    jsx, lib would all fall back to compiler defaults); extending keeps the
    project's effective flags. Returns the temp file path (caller deletes it).
    """
    config = {"files": files, "include": []}
    base = Path(project) if project else Path("tsconfig.json")
    if (root / base).is_file():
        config["extends"] = "./" + base.as_posix()
    handle = tempfile.NamedTemporaryFile(
        mode="w", dir=str(root), prefix=".tsc-files-", suffix=".json", delete=False
    )
    with handle:
        json.dump(config, handle)
    return Path(handle.name)


def binary_path(root, name):
    return str(local_binary(root, name) or root / "node_modules" / ".bin" / name)


def build_command(root, args, manager, files_config=None):
    pkg = load_json(root / "package.json") or {}
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    deps = {}
    for key in ("dependencies", "devDependencies"):
        if isinstance(pkg.get(key), dict):
            deps.update(pkg[key])
    if not args.project and not args.files:
        for name in ("typecheck", "type-check", "check-types"):
            if name in scripts:
                return [manager or "npm", "run", name], "project script '{}'".format(name)
        # Framework checkers: plain tsc would silently skip .vue/.svelte/.astro files.
        if "nuxt" in deps:
            return [binary_path(root, "nuxi"), "typecheck"], "nuxi typecheck"
        if "astro" in deps:
            return [binary_path(root, "astro"), "check"], "astro check"
        if "svelte" in deps or "@sveltejs/kit" in deps:
            return [binary_path(root, "svelte-check")], "svelte-check"
    command = []
    # vue-tsc is a drop-in tsc replacement that also checks .vue SFCs.
    checker = "vue-tsc" if "vue-tsc" in deps else "tsc"
    command += [binary_path(root, checker), "--noEmit", "--pretty", "false"]
    if files_config is not None:
        command += ["-p", files_config.name]
    elif args.project:
        command += ["-p", args.project]
    return command, "direct {}".format(checker)


def summarize(output):
    errors = []
    for line in output.splitlines():
        match = ERROR_RE.match(line.strip())
        if match:
            errors.append(match.groupdict())
    by_code = Counter(err["code"] for err in errors)
    return errors, by_code


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--project", help="Path to a specific tsconfig (tsc -p)")
    parser.add_argument("--files", nargs="+", help="Check only these files (ignores tsconfig include)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    root = Path(args.root)
    if not (root / "package.json").exists():
        print("Error: no package.json in {}".format(root), file=sys.stderr)
        return 2

    manager = detect_package_manager(root)
    runtime_diagnostics = runtime_preflight(root)
    if "NODE_RUNTIME_MISMATCH" in runtime_diagnostics:
        if args.json:
            print(json.dumps({"diagnostics": runtime_diagnostics, "total_errors": 0, "by_code": {}}, indent=2))
        else:
            print("Diagnostic: NODE_RUNTIME_MISMATCH", file=sys.stderr)
        return 2
    files_config = make_files_config(root, args.files, args.project) if args.files else None
    command, mode = build_command(root, args, manager, files_config)

    if args.files and not args.json:
        print("Warning: checking only the listed files can miss project-wide errors;", file=sys.stderr)
        print("run a full check before concluding the codebase is clean.", file=sys.stderr)

    try:
        result = subprocess.run(
            command, cwd=str(root), capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        if args.json:
            print(json.dumps({
                "diagnostics": runtime_diagnostics + ["TYPECHECK_LOCAL_COMPILER_UNAVAILABLE"],
                "total_errors": 0, "by_code": {},
            }, indent=2))
        else:
            print("Diagnostic: TYPECHECK_LOCAL_COMPILER_UNAVAILABLE", file=sys.stderr)
        return 2
    finally:
        if files_config is not None:
            files_config.unlink(missing_ok=True)

    output = (result.stdout or "") + (result.stderr or "")
    errors, by_code = summarize(output)

    if args.json:
        print(json.dumps({
            "mode": mode,
            "exit_code": result.returncode,
            "total_errors": len(errors),
            "by_code": dict(by_code),
            "diagnostics": runtime_diagnostics + (
                ["TYPECHECK_FAILED_UNPARSEABLE"] if result.returncode and not errors else []
            ),
        }, indent=2))
        return result.returncode

    print("Typecheck mode: {}".format(mode))
    for diagnostic in runtime_diagnostics:
        print("Diagnostic: {}".format(diagnostic))
    if result.returncode == 0 and not errors:
        print("Type check passed.")
        return 0
    if not errors:
        print("Diagnostic: TYPECHECK_FAILED_UNPARSEABLE")
        return result.returncode

    print("Total errors: {}".format(len(errors)))
    print("\nTop error codes:")
    for code, count in by_code.most_common(TOP_N):
        print("  {} x{}".format(code, count))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
