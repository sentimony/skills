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
    "noImplicitOverride",
    "noFallthroughCasesInSwitch",
    "noUnusedLocals",
    "noUnusedParameters",
    "module",
    "moduleResolution",
    "target",
    "composite",
    "incremental",
    "skipLibCheck",
]

IGNORE_PARTS = {"node_modules", "dist", "build", "coverage", ".git", ".next", ".nuxt", ".output", ".svelte-kit", ".astro"}

EXEC_PREFIX = {"pnpm": "pnpm exec", "yarn": "yarn", "bun": "bunx", "npm": "npx"}

# (framework, dependency that identifies it, checker command). Order matters:
# meta-frameworks first, since e.g. a Nuxt project also depends on vue.
FRAMEWORKS = [
    ("nuxt", "nuxt", "nuxi typecheck"),
    ("astro", "astro", "astro check"),
    ("sveltekit", "@sveltejs/kit", "svelte-check"),
    ("svelte", "svelte", "svelte-check"),
    ("vue", "vue", "vue-tsc --noEmit"),
]

# Frameworks whose effective tsconfig is generated (into .nuxt/, .svelte-kit/, ...);
# file-coverage analysis against visible tsconfigs would be misleading there.
GENERATED_CONFIG_FRAMEWORKS = {"nuxt", "astro", "sveltekit", "svelte"}

SOURCE_SUFFIXES = {".ts", ".tsx", ".mts", ".cts", ".vue"}


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
        if manager in EXEC_PREFIX:
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


def _installed_version(root, dep_name):
    """Read the installed version of a node_modules package, or None."""
    installed = load_jsonc(root / "node_modules" / Path(dep_name) / "package.json")
    if installed and installed.get("version"):
        return installed["version"]
    return None


def detect_native_compiler(root, deps):
    """Find a TypeScript 7 native compiler installed alongside the framework's
    TypeScript 6. Side-by-side layouts alias the native compiler under a second
    dependency (commonly `@typescript/native`) resolving to `npm:typescript@^7`,
    so the `typescript` entry can stay on 6.x for vue-tsc/Volar. Returns
    {name, spec, version} for the native entry, or None."""
    for name, spec in deps.items():
        if name == "typescript":
            continue
        if not isinstance(spec, str):
            continue
        # An npm: alias pointing at the real typescript package, or the official
        # @typescript/native alias name.
        aliases_typescript = spec.startswith("npm:typescript@")
        if not (aliases_typescript or name == "@typescript/native"):
            continue
        version = _installed_version(root, name)
        if version is None and not aliases_typescript:
            continue
        entry = {"name": name, "spec": spec, "version": version}
        # Distinguish a native 7 alias from a 6-compat alias
        # (npm:@typescript/typescript6): only report the former as native.
        if version and not version.startswith("7"):
            continue
        if not version and "@7" not in spec and "typescript6" in spec:
            continue
        return entry
    return None


def typecheck_scripts(scripts):
    """Map every `typecheck*` npm script to the tsconfig it targets (from a
    `-p`/`--project` flag), so a multi-compiler audit can see which config each
    compiler path checks. Returns [{name, command, project}]."""
    found = []
    for name, command in scripts.items():
        if not name.startswith("typecheck") or not isinstance(command, str):
            continue
        match = re.search(r"(?:-p|--project)[=\s]+(\S+)", command)
        found.append({
            "name": name,
            "command": command,
            "project": match.group(1) if match else None,
        })
    return found


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
    """Return (chain_labels, merged_compiler_options, references, file_sets) for a tsconfig.

    file_sets holds the effective include/files/exclude lists (nearest config wins,
    matching how tsc inherits them through extends).
    """
    seen = seen if seen is not None else set()
    resolved = path.resolve()
    if resolved in seen:
        return [], {}, [], {}
    seen.add(resolved)
    config = load_jsonc(path)
    if config is None:
        return [relative_label(path, root) + " (unparsable)"], {}, [], {}
    chain = []
    options = {}
    file_sets = {}
    extends = config.get("extends")
    entries = extends if isinstance(extends, list) else ([extends] if extends else [])
    for entry in entries:
        target = resolve_extends_target(entry, path.parent, root)
        if target is None:
            chain.append(entry + " (unresolved)")
            continue
        sub_chain, sub_options, _, sub_file_sets = load_config_chain(target, root, seen)
        chain.extend(sub_chain)
        options.update(sub_options)
        file_sets.update(sub_file_sets)
    chain.append(relative_label(path, root))
    options.update(config.get("compilerOptions", {}) or {})
    for key in ("include", "files", "exclude"):
        if isinstance(config.get(key), list):
            file_sets[key] = config[key]
    references = [
        ref.get("path")
        for ref in config.get("references", []) or []
        if isinstance(ref, dict) and ref.get("path")
    ]
    return chain, options, references, file_sets


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


def detect_framework(deps):
    for framework, marker, checker in FRAMEWORKS:
        if marker in deps:
            return {"name": framework, "checker": checker}
    return None


def recommended_typecheck(manager, scripts, framework):
    for name in ("typecheck", "type-check", "check-types"):
        if name in scripts:
            return "{} run {}".format(manager or "npm", name)
    prefix = EXEC_PREFIX.get(manager or "npm", "npx")
    # Plain tsc silently skips .vue/.svelte/.astro files; use the framework checker.
    if framework:
        return "{} {}".format(prefix, framework["checker"])
    return "{} tsc --noEmit".format(prefix)


def glob_to_regex(pattern):
    """Translate a tsconfig include/exclude glob to a regex (approximate)."""
    pattern = pattern.replace("\\", "/").lstrip("./")
    last = pattern.rsplit("/", 1)[-1]
    if "*" not in pattern and "?" not in pattern and "." not in last:
        pattern = pattern.rstrip("/") + "/**/*"
    out = []
    i = 0
    while i < len(pattern):
        if pattern[i : i + 2] == "**":
            out.append(".*")
            i += 2
            if i < len(pattern) and pattern[i] == "/":
                i += 1
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def find_source_files(root, limit=500):
    found = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORE_PARTS or part.startswith(".") for part in rel.parts[:-1]):
            continue
        if path.name.endswith(".d.ts"):
            continue
        found.append(rel.as_posix())
        if len(found) >= limit:
            break
    return found


def uncovered_source_files(root, tsconfigs, source_files):
    """Source files not matched by any tsconfig's files/include (approximate)."""
    matchers = []
    for config in tsconfigs:
        config_dir = (root / config["path"]).parent.resolve()
        try:
            base = config_dir.relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        base = "" if base == "." else base + "/"
        file_sets = config.get("file_sets", {})
        explicit = {
            (base + f.lstrip("./")).replace("//", "/") for f in file_sets.get("files", [])
        }
        include = file_sets.get("include")
        if include is None and "files" not in file_sets:
            include = ["**/*"]
        includes = [glob_to_regex(p) for p in include or []]
        excludes = [glob_to_regex(p) for p in file_sets.get("exclude", [])]
        matchers.append((base, explicit, includes, excludes))
    uncovered = []
    for rel in source_files:
        covered = False
        for base, explicit, includes, excludes in matchers:
            if rel in explicit:
                covered = True
                break
            if base and not rel.startswith(base):
                continue
            local = rel[len(base):]
            if any(rx.match(local) for rx in includes) and not any(
                rx.match(local) for rx in excludes
            ):
                covered = True
                break
        if not covered:
            uncovered.append(rel)
    return uncovered


def inspect(root):
    pkg = load_jsonc(root / "package.json") or {}
    deps = all_dependencies(pkg)
    manager, lockfile = detect_package_manager(root)
    ts_version, ts_source = typescript_version(root, deps)
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    framework = detect_framework(deps)
    native_compiler = detect_native_compiler(root, deps)
    typecheck_cmds = typecheck_scripts(scripts)

    tsconfigs = []
    for path in find_tsconfigs(root):
        chain, options, references, file_sets = load_config_chain(path, root)
        tsconfigs.append({
            "path": relative_label(path, root),
            "extends_chain": chain,
            "references": references,
            "flags": effective_flags(options),
            "file_sets": file_sets,
        })

    if framework and framework["name"] in GENERATED_CONFIG_FRAMEWORKS:
        uncovered = None  # governed by the framework's generated tsconfig
    else:
        uncovered = uncovered_source_files(root, tsconfigs, find_source_files(root))

    return {
        "package_manager": manager,
        "lockfile": lockfile,
        "typescript_version": ts_version,
        "typescript_source": ts_source,
        "module_type": pkg.get("type", "commonjs"),
        "native_compiler": native_compiler,
        "typecheck_scripts": typecheck_cmds,
        "runner": detect_runner(deps),
        "linter": detect_linter(root),
        "framework": framework,
        "monorepo_markers": detect_monorepo(root, pkg),
        "tsconfigs": tsconfigs,
        "uncovered_files": uncovered,
        "recommended_typecheck": recommended_typecheck(manager, scripts, framework),
    }


def print_human(info):
    manager = info["package_manager"] or "unknown"
    if info["lockfile"]:
        manager += " ({})".format(info["lockfile"])
    print("Package manager: {}".format(manager))
    native = info.get("native_compiler")
    if info["typescript_version"]:
        label = "Framework compiler API" if native else "TypeScript"
        print("{}: {} ({})".format(label, info["typescript_version"], info["typescript_source"]))
    else:
        print("TypeScript: not found in dependencies or node_modules")
    if native:
        version = native["version"] or native["spec"]
        installed = "installed" if native["version"] else "declared"
        print("Native compiler: {}@{} ({})".format(native["name"], version, installed))
    print("Module type: {}".format(info["module_type"]))
    print("Runner: {}".format(info["runner"] or "none detected"))
    if info["linter"]:
        print("Linter: {} ({})".format(info["linter"]["name"], info["linter"]["config"]))
    else:
        print("Linter: none detected")
    if info["framework"]:
        print("Framework: {} (typecheck via {}; plain tsc skips component files)".format(
            info["framework"]["name"], info["framework"]["checker"]
        ))
    print("Monorepo: {}".format(", ".join(info["monorepo_markers"]) or "no"))
    typecheck_cmds = info.get("typecheck_scripts") or []
    if native and typecheck_cmds:
        print("Compiler paths (audit each separately):")
        for cmd in typecheck_cmds:
            target = cmd["project"] or "default tsconfig"
            print("  npm run {} -> {}".format(cmd["name"], target))
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
    if info["uncovered_files"]:
        print()
        print("Coverage: {} uncovered TypeScript/Vue file(s) (never type-checked, approximate):".format(
            len(info["uncovered_files"])
        ))
        for rel in info["uncovered_files"][:15]:
            print("  {}".format(rel))
        if len(info["uncovered_files"]) > 15:
            print("  ... and {} more".format(len(info["uncovered_files"]) - 15))
    elif info["uncovered_files"] == []:
        print()
        print("Coverage: complete")
        print("Uncovered TypeScript/Vue files: 0")
    elif info["uncovered_files"] is None and info["framework"]:
        print()
        print("File coverage: governed by {}'s generated tsconfig; not analyzed".format(
            info["framework"]["name"]
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
