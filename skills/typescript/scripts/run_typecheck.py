#!/usr/bin/env python3
"""
Run TypeScript type-checking through the project's package manager and
summarize compiler errors by code and by file.

Prefers the project's own "typecheck" npm script when present; otherwise
runs `tsc --noEmit` via the detected package manager.

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


LOCKFILES = [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("package-lock.json", "npm"),
    ("npm-shrinkwrap.json", "npm"),
]

EXEC_PREFIX = {
    "pnpm": ["pnpm", "exec"],
    "yarn": ["yarn"],
    "bun": ["bunx"],
    "npm": ["npx"],
}

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
        if name in EXEC_PREFIX:
            return name
    return None


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


def build_command(root, args, manager, files_config=None):
    pkg = load_json(root / "package.json") or {}
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    if not args.project and not args.files:
        for name in ("typecheck", "type-check", "check-types"):
            if name in scripts:
                return [manager or "npm", "run", name], "project script '{}'".format(name)
    command = list(EXEC_PREFIX.get(manager or "npm", ["npx"]))
    command += ["tsc", "--noEmit", "--pretty", "false"]
    if files_config is not None:
        command += ["-p", files_config.name]
    elif args.project:
        command += ["-p", args.project]
    return command, "direct tsc"


def summarize(output):
    errors = []
    for line in output.splitlines():
        match = ERROR_RE.match(line.strip())
        if match:
            errors.append(match.groupdict())
    by_code = Counter(err["code"] for err in errors)
    by_file = Counter(err["file"] for err in errors)
    return errors, by_code, by_file


def first_message_for(code, errors):
    for err in errors:
        if err["code"] == code:
            return err["message"]
    return ""


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
        print("Error: command not found: {}".format(command[0]), file=sys.stderr)
        return 2
    finally:
        if files_config is not None:
            files_config.unlink(missing_ok=True)

    output = (result.stdout or "") + (result.stderr or "")
    errors, by_code, by_file = summarize(output)

    if args.json:
        print(json.dumps({
            "command": " ".join(command),
            "mode": mode,
            "exit_code": result.returncode,
            "total_errors": len(errors),
            "by_code": dict(by_code),
            "by_file": dict(by_file),
            "errors": errors,
        }, indent=2))
        return result.returncode

    print("Command: {} ({})".format(" ".join(command), mode))
    if result.returncode == 0 and not errors:
        print("Type check passed.")
        return 0
    if not errors:
        # Non-zero exit but nothing matched the error pattern: show raw output.
        print(output.strip())
        return result.returncode

    print("Total errors: {}".format(len(errors)))
    print("\nTop error codes:")
    for code, count in by_code.most_common(TOP_N):
        print("  {} x{}  e.g. {}".format(code, count, first_message_for(code, errors)[:100]))
    print("\nTop files:")
    for name, count in by_file.most_common(TOP_N):
        print("  {} ({} errors)".format(name, count))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
