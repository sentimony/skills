#!/usr/bin/env python3
"""
Inspect a project for TypeScript configuration and conventions.

Detects the package manager, TypeScript version, tsconfig files with their
extends chains and effective compiler flags, monorepo markers, linter,
TS runner, package.json module type, and a recommended typecheck command.

Usage:
    python <skill>/scripts/inspect_typescript.py --root .
    python <skill>/scripts/inspect_typescript.py --root ../my-app --json
"""

import argparse
import json
import re
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

MONOREPO_MARKERS = ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"]

LINTER_FILES = [
    ("biome.json", "biome"),
    ("biome.jsonc", "biome"),
    ("eslint.config.js", "eslint"),
    ("eslint.config.mjs", "eslint"),
    ("eslint.config.cjs", "eslint"),
    ("eslint.config.ts", "eslint"),
    (".eslintrc.json", "eslint"),
    (".eslintrc.js", "eslint"),
    (".eslintrc.cjs", "eslint"),
]

KEY_FLAGS = [
    "strict",
    "noImplicitAny",
    "strictNullChecks",
    "noUncheckedIndexedAccess",
    "exactOptionalPropertyTypes",
    "module",
    "moduleResolution",
    "target",
    "composite",
    "incremental",
    "skipLibCheck",
]

IGNORE_PARTS = {"node_modules", "dist", "build", "coverage", ".git", ".next", ".nuxt", ".output"}

EXEC_TSC = {"pnpm": "pnpm exec tsc", "yarn": "yarn tsc", "bun": "bunx tsc", "npm": "npx tsc"}


def strip_jsonc(text):
    """Remove // and /* */ comments and trailing commas from JSONC."""
    out = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    cleaned = "".join(out)
    return re.sub(r",\s*([}\]])", r"\1", cleaned)


def load_jsonc(path):
    try:
        return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def detect_package_manager(root):
    for name, manager in LOCKFILES:
        if (root / name).exists():
            return manager, name
    # No lockfile here (e.g. a monorepo sub-package): fall back to the
    # package.json#packageManager (corepack) declaration.
    pkg = load_jsonc(root / "package.json") or {}
    declared = pkg.get("packageManager")
    if isinstance(declared, str):
        manager = declared.split("@")[0]
        if manager in EXEC_TSC:
            return manager, "package.json#packageManager"
    return None, None


def all_dependencies(pkg):
    merged = {}
    for key in ("dependencies", "devDependencies"):
        value = pkg.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def typescript_version(root, deps):
    installed = load_jsonc(root / "node_modules" / "typescript" / "package.json")
    if installed and installed.get("version"):
        return installed["version"], "installed"
    if "typescript" in deps:
        return deps["typescript"], "declared"
    return None, None


def find_tsconfigs(root, max_depth=3, limit=20):
    found = []
    for path in sorted(root.rglob("tsconfig*.json")):
        rel = path.relative_to(root)
        if any(part in IGNORE_PARTS for part in rel.parts):
            continue
        if len(rel.parts) > max_depth:
            continue
        found.append(path)
        if len(found) >= limit:
            break
    return found


def resolve_extends_target(entry, base_dir, root):
    """Resolve an extends entry to an existing config file, or None."""
    if entry.startswith("."):
        candidates = [base_dir / entry, base_dir / (entry + ".json")]
    else:
        pkg_path = root / "node_modules" / Path(entry)
        candidates = [pkg_path, Path(str(pkg_path) + ".json"), pkg_path / "tsconfig.json"]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def load_config_chain(path, root, seen=None):
    """Return (chain_labels, merged_compiler_options, references) for a tsconfig."""
    seen = seen if seen is not None else set()
    resolved = path.resolve()
    if resolved in seen:
        return [], {}, []
    seen.add(resolved)
    config = load_jsonc(path)
    if config is None:
        return [relative_label(path, root) + " (unparsable)"], {}, []
    chain = []
    options = {}
    extends = config.get("extends")
    entries = extends if isinstance(extends, list) else ([extends] if extends else [])
    for entry in entries:
        target = resolve_extends_target(entry, path.parent, root)
        if target is None:
            chain.append(entry + " (unresolved)")
            continue
        sub_chain, sub_options, _ = load_config_chain(target, root, seen)
        chain.extend(sub_chain)
        options.update(sub_options)
    chain.append(relative_label(path, root))
    options.update(config.get("compilerOptions", {}) or {})
    references = [
        ref.get("path")
        for ref in config.get("references", []) or []
        if isinstance(ref, dict) and ref.get("path")
    ]
    return chain, options, references


def relative_label(path, root):
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def effective_flags(options):
    flags = {key: options.get(key) for key in KEY_FLAGS}
    if options.get("strict"):
        for key in ("noImplicitAny", "strictNullChecks"):
            if key not in options:
                flags[key] = True
    paths = options.get("paths")
    flags["paths"] = sorted(paths.keys()) if isinstance(paths, dict) and paths else None
    return flags


def detect_monorepo(root, pkg):
    markers = [name for name in MONOREPO_MARKERS if (root / name).exists()]
    if pkg.get("workspaces"):
        markers.append("package.json workspaces")
    return markers


def detect_linter(root):
    for name, linter in LINTER_FILES:
        if (root / name).exists():
            return {"name": linter, "config": name}
    return None


def detect_runner(deps):
    for runner in ("tsx", "ts-node"):
        if runner in deps:
            return runner
    return None


def recommended_typecheck(manager, scripts):
    for name in ("typecheck", "type-check", "check-types"):
        if name in scripts:
            return "{} run {}".format(manager or "npm", name)
    return EXEC_TSC.get(manager or "npm", "npx tsc") + " --noEmit"


def inspect(root):
    pkg = load_jsonc(root / "package.json") or {}
    deps = all_dependencies(pkg)
    manager, lockfile = detect_package_manager(root)
    ts_version, ts_source = typescript_version(root, deps)
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}

    tsconfigs = []
    for path in find_tsconfigs(root):
        chain, options, references = load_config_chain(path, root)
        tsconfigs.append({
            "path": relative_label(path, root),
            "extends_chain": chain,
            "references": references,
            "flags": effective_flags(options),
        })

    return {
        "package_manager": manager,
        "lockfile": lockfile,
        "typescript_version": ts_version,
        "typescript_source": ts_source,
        "module_type": pkg.get("type", "commonjs"),
        "runner": detect_runner(deps),
        "linter": detect_linter(root),
        "monorepo_markers": detect_monorepo(root, pkg),
        "tsconfigs": tsconfigs,
        "recommended_typecheck": recommended_typecheck(manager, scripts),
    }


def print_human(info):
    manager = info["package_manager"] or "unknown"
    if info["lockfile"]:
        manager += " ({})".format(info["lockfile"])
    print("Package manager: {}".format(manager))
    if info["typescript_version"]:
        print("TypeScript: {} ({})".format(info["typescript_version"], info["typescript_source"]))
    else:
        print("TypeScript: not found in dependencies or node_modules")
    print("Module type: {}".format(info["module_type"]))
    print("Runner: {}".format(info["runner"] or "none detected"))
    if info["linter"]:
        print("Linter: {} ({})".format(info["linter"]["name"], info["linter"]["config"]))
    else:
        print("Linter: none detected")
    print("Monorepo: {}".format(", ".join(info["monorepo_markers"]) or "no"))
    for config in info["tsconfigs"]:
        print()
        print(config["path"])
        if len(config["extends_chain"]) > 1:
            print("  extends chain: {}".format(" -> ".join(config["extends_chain"])))
        if config["references"]:
            print("  references: {}".format(", ".join(config["references"])))
        flags = config["flags"]
        set_flags = {k: v for k, v in flags.items() if v is not None}
        print("  effective flags: {}".format(
            ", ".join("{}={}".format(k, json.dumps(v)) for k, v in set_flags.items()) or "none set"
        ))
    print()
    print("Recommended typecheck: {}".format(info["recommended_typecheck"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", default=".", help="Project root to inspect")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print("Error: root directory not found: {}".format(root), file=sys.stderr)
        return 2
    if not (root / "package.json").exists():
        print("Error: no package.json in {}; not a JavaScript project root".format(root), file=sys.stderr)
        return 2

    info = inspect(root)
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print_human(info)

    if not info["typescript_version"] and not info["tsconfigs"]:
        print("\nTypeScript is not set up in this project.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
