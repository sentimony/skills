#!/usr/bin/env python3
"""Inspect a JavaScript/TypeScript project for safe Vitest setup signals.

Usage:
    python <skill>/scripts/inspect_vitest.py --root .
    python <skill>/scripts/inspect_vitest.py --root ../my-app --json
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

VITEST_CONFIG_FILES = [
    "vitest.config.ts", "vitest.config.mts", "vitest.config.cts",
    "vitest.config.js", "vitest.config.mjs", "vitest.config.cjs",
]
VITE_CONFIG_FILES = [
    "vite.config.ts", "vite.config.mts", "vite.config.cts",
    "vite.config.js", "vite.config.mjs", "vite.config.cjs",
]
PROJECT_FILES = [
    "vitest.workspace.ts", "vitest.workspace.mts", "vitest.workspace.js",
    "vitest.workspace.mjs", "vitest.workspace.cjs", "vitest.projects.ts",
    "vitest.projects.mts", "vitest.projects.js", "vitest.projects.mjs",
    "vitest.projects.cjs", "vitest.projects.json",
]
TEST_GLOBS = [
    "**/*.test.ts", "**/*.test.tsx", "**/*.test.mts", "**/*.test.cts",
    "**/*.test.js", "**/*.test.jsx", "**/*.test.mjs", "**/*.test.cjs",
    "**/*.spec.ts", "**/*.spec.tsx", "**/*.spec.mts", "**/*.spec.cts",
    "**/*.spec.js", "**/*.spec.jsx", "**/*.spec.mjs", "**/*.spec.cjs",
]
IGNORE_PARTS = {
    "node_modules", "dist", "build", "coverage", ".git", ".next", ".nuxt", ".output",
}
FRAMEWORK_DEPENDENCIES = {
    "nuxt": "nuxt",
    "next": "next",
    "vue": "vue",
    "react": "react",
    "svelte": "svelte",
    "pinia": "pinia",
    "jsdom": "jsdom",
    "happy-dom": "happy-dom",
}
DIAGNOSTIC_MESSAGES = {
    "PACKAGE_JSON_MISSING": "package.json is unavailable.",
    "VITEST_DEPENDENCY_ABSENT": "Vitest is not declared as a dependency.",
    "NODE_RUNTIME_UNAVAILABLE": "The active Node runtime is unavailable or not a strict semantic version.",
    "NODE_NVMRC_INVALID": "The .nvmrc version declaration is invalid.",
    "NODE_NVMRC_MISMATCH": "The active Node runtime does not match .nvmrc.",
    "NODE_VERSION_FILE_INVALID": "The .node-version declaration is invalid.",
    "NODE_VERSION_FILE_MISMATCH": "The active Node runtime does not match .node-version.",
    "NODE_ENGINES_UNKNOWN": "The engines.node declaration is not a supported strict version or minimum range.",
    "NODE_ENGINES_INCOMPATIBLE": "The active Node runtime is incompatible with engines.node.",
    "NODE_VOLTA_UNKNOWN": "The volta.node declaration is not a strict semantic version.",
    "NODE_VOLTA_MISMATCH": "The active Node runtime does not match volta.node.",
    "DOM_ENVIRONMENT_MISSING": "Component framework detected without jsdom or happy-dom.",
    "CONFIG_ABSENT": "No known Vitest or Vite config is present.",
}


def parse_strict_version(value):
    """Return a semantic version tuple only for complete x.y.z values."""
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*v?(\d+)\.(\d+)\.(\d+)\s*", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def read_optional_text(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def current_node_version():
    try:
        result = subprocess.run(
            ["node", "-v"], check=False, capture_output=True, text=True
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def package_manager_field(package_json):
    value = package_json.get("packageManager") if package_json else None
    if not isinstance(value, str):
        return None
    manager = value.split("@", 1)[0]
    return manager if manager in {"npm", "pnpm", "yarn", "bun"} else None


def detect_package_manager(root, package_json=None):
    managers = []
    for filename, manager in LOCKFILES:
        if (root / filename).exists() and manager not in managers:
            managers.append(manager)
    if len(managers) == 1:
        return managers[0]
    declared = package_manager_field(package_json)
    if declared:
        return declared
    return managers[0] if managers else "npm"


def has_dep(package_json, name):
    if not package_json:
        return False
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        dependencies = package_json.get(section)
        if isinstance(dependencies, dict) and name in dependencies:
            return True
    return False


def detect_frameworks(package_json):
    return sorted(
        label for label, dependency in FRAMEWORK_DEPENDENCIES.items()
        if has_dep(package_json, dependency)
    )


def scripts_mapping(package_json):
    scripts = package_json.get("scripts") if package_json else None
    return scripts if isinstance(scripts, dict) else {}


def detect_likely_test_script(scripts):
    """Classify script availability without returning a repository-controlled name."""
    preferred = ("test:unit", "test:vitest", "vitest", "test")
    for name in preferred:
        value = scripts.get(name)
        if isinstance(value, str) and "vitest" in value.lower():
            return True
    return any(isinstance(value, str) and "vitest" in value.lower() for value in scripts.values())


def version_file_status(value, current):
    if value is None:
        return "absent"
    if not isinstance(value, str):
        return "unknown"
    parsed = parse_strict_version(value)
    if not parsed:
        # A token unrelated to a version is an invalid declaration; partial versions are unknown.
        return "unknown" if re.fullmatch(r"\s*v?\d+(?:\.\d+){0,2}\s*", value) else "invalid"
    if current is None:
        return "unknown"
    return "match" if parsed == current else "mismatch"


def engine_status(value, current):
    if value is None:
        return "absent"
    if not isinstance(value, str):
        return "unknown"
    exact = parse_strict_version(value)
    minimum = re.fullmatch(r"\s*(>=|>)\s*v?(\d+)\.(\d+)\.(\d+)\s*", value)
    if not exact and not minimum:
        return "unknown"
    if current is None:
        return "unknown"
    if exact:
        return "compatible" if current == exact else "incompatible"
    minimum_version = tuple(int(part) for part in minimum.groups()[1:])
    return "compatible" if current >= minimum_version else "incompatible"


def inspect_node(root, package_json):
    current = parse_strict_version(current_node_version())
    engines = package_json.get("engines") if package_json else None
    volta = package_json.get("volta") if package_json else None
    engine_value = engines.get("node") if isinstance(engines, dict) else None
    volta_value = volta.get("node") if isinstance(volta, dict) else None
    return {
        "runtime": "valid" if current else "unknown",
        "nvmrc": version_file_status(read_optional_text(root / ".nvmrc"), current),
        "node_version_file": version_file_status(read_optional_text(root / ".node-version"), current),
        "engines": engine_status(engine_value, current),
        "volta": version_file_status(volta_value, current),
    }


def find_test_file_count(root):
    files = set()
    try:
        for pattern in TEST_GLOBS:
            for path in root.glob(pattern):
                if not any(part in IGNORE_PARTS for part in path.relative_to(root).parts):
                    files.add(path)
    except OSError:
        return 0
    return len(files)


def config_count(root, names):
    return sum((root / name).is_file() for name in names)


def findings_for(package_json, frameworks, node, configs):
    findings = []

    def add(code, severity):
        findings.append({"code": code, "severity": severity})

    if package_json is None:
        add("PACKAGE_JSON_MISSING", "warning")
    elif not has_dep(package_json, "vitest"):
        add("VITEST_DEPENDENCY_ABSENT", "warning")
    if node["runtime"] == "unknown":
        add("NODE_RUNTIME_UNAVAILABLE", "warning")
    for status, invalid_code, mismatch_code in (
        (node["nvmrc"], "NODE_NVMRC_INVALID", "NODE_NVMRC_MISMATCH"),
        (node["node_version_file"], "NODE_VERSION_FILE_INVALID", "NODE_VERSION_FILE_MISMATCH"),
        (node["volta"], "NODE_VOLTA_UNKNOWN", "NODE_VOLTA_MISMATCH"),
    ):
        if status == "invalid":
            add(invalid_code, "warning")
        elif status == "mismatch":
            add(mismatch_code, "warning")
    if node["engines"] == "unknown":
        add("NODE_ENGINES_UNKNOWN", "warning")
    elif node["engines"] == "incompatible":
        add("NODE_ENGINES_INCOMPATIBLE", "warning")
    if ("react" in frameworks or "vue" in frameworks) and not ({"jsdom", "happy-dom"} & set(frameworks)):
        add("DOM_ENVIRONMENT_MISSING", "warning")
    if not configs["vitest"] and not configs["vite"]:
        add("CONFIG_ABSENT", "info")
    return findings


def build_report(root, limit):
    """Build the stable report schema without copying repository-controlled strings."""
    package_json = read_json(root / "package.json")
    scripts = scripts_mapping(package_json)
    frameworks = detect_frameworks(package_json)
    configs = {
        "vitest": config_count(root, VITEST_CONFIG_FILES),
        "vite": config_count(root, VITE_CONFIG_FILES),
        "projects": config_count(root, PROJECT_FILES),
    }
    node = inspect_node(root, package_json)
    total = find_test_file_count(root)
    reported = min(total, max(0, limit))
    test_runner = "package-script" if detect_likely_test_script(scripts) else (
        "local-binary" if (root / "node_modules" / ".bin" / "vitest").is_file() else "unavailable"
    )
    return {
        "schema_version": 1,
        "package_manager": detect_package_manager(root, package_json),
        "vitest_dependency": "present" if has_dep(package_json, "vitest") else "absent",
        "test_runner": test_runner,
        "frameworks": frameworks,
        "node": node,
        "configs": configs,
        "filesystem_candidates": {
            "total": total,
            "reported": reported,
            "truncated": total > reported,
        },
        "findings": findings_for(package_json, frameworks, node, configs),
    }


def print_human(report):
    """Print normalized report fields to stdout and stable diagnostics to stderr."""
    print(f"Schema version: {report['schema_version']}")
    print(f"Package manager: {report['package_manager']}")
    print(f"Vitest dependency: {report['vitest_dependency']}")
    print(f"Test runner: {report['test_runner']}")
    print(f"Frameworks: {', '.join(report['frameworks']) or 'none'}")
    print("Node:")
    for key in ("runtime", "nvmrc", "node_version_file", "engines", "volta"):
        print(f"  {key}: {report['node'][key]}")
    print("Configs:")
    for key in ("vitest", "vite", "projects"):
        print(f"  {key}: {report['configs'][key]}")
    candidates = report["filesystem_candidates"]
    print(
        "Filesystem candidates: "
        f"total={candidates['total']} reported={candidates['reported']} truncated={str(candidates['truncated']).lower()}"
    )
    for finding in report["findings"]:
        message = DIAGNOSTIC_MESSAGES[finding["code"]]
        print(f"{finding['severity'].upper()} {finding['code']}: {message}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Inspect a project for normalized Vitest setup signals")
    parser.add_argument("--root", default=".", help="Project root to inspect (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--limit", type=int, default=20, help="Maximum filesystem candidates to report")
    args = parser.parse_args()

    try:
        root = Path(args.root).expanduser().resolve()
        available = root.exists() and root.is_dir()
    except OSError:
        available = False
    if not available:
        raise SystemExit("Requested project directory is unavailable.")

    report = build_report(root, args.limit)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
