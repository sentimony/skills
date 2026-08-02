#!/usr/bin/env python3
"""
Inspect a project for TypeScript configuration and conventions.

Detects the package manager, TypeScript installation source and version,
per-config effective compiler flags, monorepo markers, linter, TS runner,
package.json module type, and a recommended typecheck command.

Usage:
    python <skill>/scripts/inspect_typescript.py --root .
    python <skill>/scripts/inspect_typescript.py --root ../my-app --json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from local_tools import is_executable, local_binary


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

BOOLEAN_FLAGS = set(KEY_FLAGS) - {"module", "moduleResolution", "target"}

FLAG_ENUMS = {
    "module": {
        "none", "commonjs", "amd", "umd", "system", "es6", "es2015", "es2020",
        "es2022", "esnext", "node16", "node18", "node20", "nodenext", "preserve",
    },
    "moduleResolution": {
        "classic", "node", "node10", "node16", "nodenext", "bundler",
    },
    "target": {
        "es3", "es5", "es6", "es2015", "es2016", "es2017", "es2018", "es2019",
        "es2020", "es2021", "es2022", "es2023", "es2024", "esnext",
    },
}

IGNORE_PARTS = {"node_modules", "dist", "build", "coverage", ".git", ".next", ".nuxt", ".output", ".svelte-kit", ".astro"}

KNOWN_PACKAGE_MANAGERS = {"pnpm", "yarn", "bun", "npm"}

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

NUXT_PROGRAMS = {
    ".nuxt/tsconfig.app.json": ("app", "vue-tsc"),
    ".nuxt/tsconfig.server.json": ("server", "tsc"),
    ".nuxt/tsconfig.shared.json": ("shared", "tsc"),
    ".nuxt/tsconfig.node.json": ("node", "tsc"),
}

NUXT_COMPILER_OUTPUT_BYTES = 1024 * 1024
NUXT_COMPILER_LINE_BYTES = 4096
NUXT_COMPILER_TIMEOUT_SECONDS = 10
NUXT_COMPILER_TERMINATE_SECONDS = 1


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
        if manager in KNOWN_PACKAGE_MANAGERS:
            return manager, "package.json#packageManager"
    return None, None


def all_dependencies(pkg):
    merged = {}
    for key in ("dependencies", "devDependencies"):
        value = pkg.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def normalized_version(value):
    """Return a version or range only when it matches a strict known format.

    Repository-controlled text never reaches the report: anything outside
    `x.y.z` with an optional range operator becomes None, prereleases included —
    their free-text identifier would otherwise be a channel of its own.
    """
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\^|~|>=|<=|>|<)?\s*v?(\d+\.\d+\.\d+)\s*", value)
    if not match:
        return None
    return (match.group(1) or "") + match.group(2)


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
    `-p`/`--project` flag), exposing only whether a project target exists."""
    found = []
    for name, command in scripts.items():
        if not name.startswith("typecheck") or not isinstance(command, str):
            continue
        match = re.search(r"(?:-p|--project)[=\s]+(\S+)", command)
        found.append({"targets_project": match is not None})
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
    raw_flags = {key: options.get(key) for key in KEY_FLAGS}
    if options.get("strict") is True:
        for key in ("noImplicitAny", "strictNullChecks"):
            if key not in options:
                raw_flags[key] = True
    flags = {}
    for key, value in raw_flags.items():
        if key in BOOLEAN_FLAGS:
            flags[key] = value if isinstance(value, bool) else None
            continue
        if value is None:
            flags[key] = None
            continue
        normalized = value.lower() if isinstance(value, str) else ""
        flags[key] = normalized if normalized in FLAG_ENUMS[key] else "other"
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
    # Plain tsc silently skips .vue/.svelte/.astro files; use the framework checker.
    if framework:
        return "project script or local {}".format(framework["checker"])
    return "local tsc --noEmit"


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


def find_source_files(root, limit=None):
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
        if limit is not None and len(found) >= limit:
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


def relative_to_root(line, root, root_prefixes):
    """Return the root-relative posix path, or raise ValueError when outside.

    Compiler output is untrusted text, so this stays a string operation. A
    relative line is joined to the root rather than dropped: tsc prints absolute
    paths, but a relative one would otherwise silently lower the coverage count.
    """
    path = Path(os.path.normpath(line))
    if not path.is_absolute():
        return Path(os.path.normpath(str(root / path))).relative_to(
            Path(os.path.normpath(str(root.absolute())))
        ).as_posix()
    for prefix in root_prefixes:
        try:
            return path.relative_to(prefix).as_posix()
        except ValueError:
            continue
    raise ValueError("path outside the project root")


def classify_source_file(rel):
    """Return a stable audit category without exposing the file name."""
    path = Path(rel)
    name = path.name
    if any(part in {"test", "tests", "__tests__"} for part in path.parts) or re.search(
        r"\.(test|spec)\.[cm]?[jt]sx?$", name
    ):
        return "tests"
    if name == "nuxt.config.ts" or ".config." in name:
        return "config"
    return "production"


def uncovered_summary(uncovered):
    """Normalize uncovered files into counts per stable audit category.

    File names are repository-controlled text and never reach the report; the
    audit needs how much is uncovered and of what kind, not which paths.
    """
    summary = {"total": len(uncovered), "production": 0, "tests": 0, "config": 0}
    for rel in uncovered:
        summary[classify_source_file(rel)] += 1
    return summary


def stop_and_reap(process):
    """Stop a compiler process and always collect its exit status."""
    if process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass
    try:
        process.wait(timeout=NUXT_COMPILER_TERMINATE_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except OSError:
        pass
    process.wait()


def run_bounded_compiler(argv, cwd):
    """Run fixed compiler argv with bounded output, duration, and cleanup."""
    try:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError:
        return "unavailable", None, b""

    captured = bytearray()
    output_limit_reached = threading.Event()
    reader_failed = []

    def read_output():
        try:
            while True:
                chunk = process.stdout.read(8192)
                if not chunk:
                    return
                remaining = NUXT_COMPILER_OUTPUT_BYTES - len(captured)
                if len(chunk) > remaining:
                    captured.extend(chunk[:max(0, remaining)])
                    output_limit_reached.set()
                    return
                captured.extend(chunk)
        except (OSError, ValueError):
            reader_failed.append(True)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    deadline = time.monotonic() + NUXT_COMPILER_TIMEOUT_SECONDS
    boundary = None
    while reader.is_alive():
        if output_limit_reached.is_set():
            boundary = "output-limit"
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            boundary = "timeout"
            break
        reader.join(min(0.02, remaining))

    if boundary is None and output_limit_reached.is_set():
        boundary = "output-limit"

    returncode = None
    if boundary is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            boundary = "timeout"
        else:
            try:
                returncode = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                boundary = "timeout"

    if boundary is not None:
        stop_and_reap(process)
        if process.stdout is not None:
            process.stdout.close()
        reader.join(NUXT_COMPILER_TERMINATE_SECONDS)
        return boundary, process.returncode, b""

    if process.stdout is not None:
        process.stdout.close()
    if reader_failed:
        return "failed", returncode, b""
    return "completed", returncode, bytes(captured)


def nuxt_program_info(root):
    """Inspect Nuxt's generated programs using local compilers only.

    Compiler output is untrusted evidence. Paths are normalized and used only for
    internal set membership; the returned structure deliberately contains counts.
    """
    if not any((root / config).is_file() for config in NUXT_PROGRAMS):
        return {}, None, ["NUXT_GENERATED_CONFIGS_MISSING"]

    candidates = set(find_source_files(root))
    # Both spellings of the root: a symlinked temp or home directory makes the
    # resolved and the plain absolute prefix differ.
    root_prefixes = {root.resolve(), Path(os.path.normpath(str(root.absolute())))}
    covered = set()
    programs = {}
    diagnostics = []
    coverage_available = True
    for config_label, (name, compiler_name) in NUXT_PROGRAMS.items():
        config_path = root / config_label
        if not config_path.is_file():
            # Report the programs that exist; a partial solution is still evidence.
            diagnostics.append("NUXT_GENERATED_CONFIG_PARTIAL")
            coverage_available = False
            continue
        binary = local_binary(root, compiler_name) or root / "node_modules" / ".bin" / compiler_name
        _, options, _, _ = load_config_chain(config_path, root)
        programs[name] = {
            "flags": effective_flags(options),
            "covered": None,
        }
        if not is_executable(binary):
            diagnostics.append("NUXT_LOCAL_COMPILER_UNAVAILABLE")
            coverage_available = False
            continue
        status, returncode, output = run_bounded_compiler(
            [
                str(binary), "--noEmit", "--pretty", "false",
                "--listFilesOnly", "-p", str(config_path),
            ],
            root,
        )
        if status == "unavailable":
            diagnostics.append("NUXT_LOCAL_COMPILER_UNAVAILABLE")
            coverage_available = False
            continue
        if status == "output-limit":
            diagnostics.append("NUXT_PROGRAM_COMPILER_OUTPUT_LIMIT")
            coverage_available = False
            continue
        if status == "timeout":
            diagnostics.append("NUXT_PROGRAM_COMPILER_TIMEOUT")
            coverage_available = False
            continue
        if status != "completed" or returncode != 0:
            diagnostics.append("NUXT_PROGRAM_COMPILER_FAILED")
            coverage_available = False
            continue
        listed = set()
        line_limit_reached = False
        for raw_line in output.splitlines():
            if len(raw_line) > NUXT_COMPILER_LINE_BYTES:
                line_limit_reached = True
                break
            try:
                line = raw_line.decode("utf-8", errors="replace").strip()
                # normpath keeps this a pure string operation: compiler-controlled
                # paths must never trigger a filesystem lookup.
                rel = relative_to_root(line, root, root_prefixes)
            except (OSError, ValueError):
                continue
            if rel in candidates:
                listed.add(rel)
        if line_limit_reached:
            diagnostics.append("NUXT_PROGRAM_COMPILER_LINE_LIMIT")
            coverage_available = False
            continue
        covered.update(listed)
        programs[name]["covered"] = len(listed)

    if not coverage_available:
        return programs, None, sorted(set(diagnostics))
    coverage = {}
    for category in ("production", "tests", "config"):
        category_files = {path for path in candidates if classify_source_file(path) == category}
        coverage[category] = {
            "covered": len(category_files & covered),
            "uncovered": len(category_files - covered),
        }
    return programs, coverage, sorted(set(diagnostics))


def normalized_reference(reference):
    """Normalize only the optional leading ./ without changing hidden directories."""
    return reference[2:] if reference.startswith("./") else reference


def inspect(root):
    pkg = load_jsonc(root / "package.json") or {}
    deps = all_dependencies(pkg)
    manager, lockfile = detect_package_manager(root)
    ts_version, ts_source = typescript_version(root, deps)
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    framework = detect_framework(deps)
    native_compiler_details = detect_native_compiler(root, deps)
    typecheck_cmds = typecheck_scripts(scripts)

    tsconfig_details = []
    for path in find_tsconfigs(root):
        chain, options, references, file_sets = load_config_chain(path, root)
        tsconfig_details.append({
            "path": relative_label(path, root),
            "extends_chain": chain,
            "references": references,
            "flags": effective_flags(options),
            "file_sets": file_sets,
        })
    tsconfigs = [{"flags": config["flags"]} for config in tsconfig_details]

    programs = {}
    coverage = None
    diagnostics = []
    nuxt_solution = framework and framework["name"] == "nuxt" and any(
        normalized_reference(ref) in NUXT_PROGRAMS
        for config in tsconfig_details for ref in config["references"]
    )
    if nuxt_solution:
        programs, coverage, diagnostics = nuxt_program_info(root)
        uncovered = None
    elif framework and framework["name"] in GENERATED_CONFIG_FRAMEWORKS:
        uncovered = None  # governed by the framework's generated tsconfig
    else:
        uncovered = uncovered_summary(
            uncovered_source_files(root, tsconfig_details, find_source_files(root))
        )

    return {
        "package_manager": manager,
        "lockfile": lockfile,
        "typescript_installation": ts_source if ts_version else None,
        "typescript_version": normalized_version(ts_version),
        "module_type": (
            pkg.get("type")
            if pkg.get("type") in {"module", "commonjs"}
            else ("commonjs" if "type" not in pkg else "other")
        ),
        "native_compiler": native_compiler_details is not None,
        "typecheck_scripts": typecheck_cmds,
        "runner": detect_runner(deps),
        "linter": detect_linter(root),
        "framework": framework,
        "monorepo_markers": detect_monorepo(root, pkg),
        "tsconfigs": tsconfigs,
        "programs": programs,
        "coverage": coverage,
        "diagnostics": diagnostics,
        "uncovered": uncovered,
        "recommended_typecheck": recommended_typecheck(manager, scripts, framework),
    }


def print_human(info):
    manager = info["package_manager"] or "unknown"
    if info["lockfile"]:
        manager += " ({})".format(info["lockfile"])
    print("Package manager: {}".format(manager))
    native = info.get("native_compiler")
    if info["typescript_installation"]:
        label = "Framework compiler API" if native else "TypeScript"
        print("{}: {} ({})".format(
            label,
            info["typescript_version"] or "unknown",
            info["typescript_installation"],
        ))
    else:
        print("TypeScript: not found in dependencies or node_modules")
    if native:
        print("Native compiler: detected")
    print("Module type: {}".format(info["module_type"]))
    print("TypeScript runner: {}".format(info["runner"] or "none detected"))
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
        for index, cmd in enumerate(typecheck_cmds, start=1):
            target = "explicit config" if cmd["targets_project"] else "default config"
            print("  typecheck script {} -> {}".format(index, target))
    for index, config in enumerate(info["tsconfigs"], start=1):
        print()
        print("TypeScript config {}".format(index))
        flags = config["flags"]
        set_flags = {k: v for k, v in flags.items() if v is not None}
        print("  effective flags: {}".format(
            ", ".join("{}={}".format(k, json.dumps(v)) for k, v in set_flags.items()) or "none set"
        ))
    if info.get("programs"):
        print()
        print("Nuxt generated programs:")
        if info.get("coverage"):
            print("  Per-program counts overlap; use aggregate coverage below for gaps.")
        for name in ("app", "server", "shared", "node"):
            program = info["programs"].get(name)
            if not program:
                continue
            flags = {key: value for key, value in program["flags"].items() if value is not None}
            coverage_label = (
                "{} file(s)".format(program["covered"])
                if program["covered"] is not None else "coverage unavailable"
            )
            print("  {}: {}; flags: {}".format(
                name, coverage_label,
                ", ".join("{}={}".format(key, json.dumps(value)) for key, value in flags.items()) or "none set",
            ))
    if info.get("coverage"):
        print()
        print("Nuxt coverage counts:")
        for category in ("production", "tests", "config"):
            counts = info["coverage"][category]
            print("  {}: {} covered, {} uncovered".format(
                category, counts["covered"], counts["uncovered"]
            ))
    for diagnostic in info.get("diagnostics", []):
        if diagnostic == "NUXT_GENERATED_CONFIGS_MISSING":
            print("Diagnostic: NUXT_GENERATED_CONFIGS_MISSING (run the project's prepare command, then inspect again)")
        elif diagnostic == "NUXT_GENERATED_CONFIG_PARTIAL":
            print("Diagnostic: NUXT_GENERATED_CONFIG_PARTIAL (prepare ran, but this Nuxt version does not generate every program; audit the ones reported)")
        else:
            print("Diagnostic: {}".format(diagnostic))
    uncovered = info["uncovered"]
    if uncovered and uncovered["total"]:
        print()
        print("Coverage: {} uncovered TypeScript/Vue file(s) (never type-checked, approximate)".format(
            uncovered["total"]
        ))
        for category in ("production", "tests", "config"):
            print("  {}: {}".format(category, uncovered[category]))
    elif uncovered:
        print()
        print("Coverage: complete")
        print("Uncovered TypeScript/Vue files: 0")
    elif uncovered is None and info["framework"] and not info.get("coverage"):
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

    if not info["typescript_installation"] and not info["tsconfigs"]:
        print("\nTypeScript is not set up in this project.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
