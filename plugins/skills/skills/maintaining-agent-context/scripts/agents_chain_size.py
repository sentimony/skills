#!/usr/bin/env python3
"""Measure every Codex AGENTS.md chain of a repository against a byte budget.

Read-only: walks the tree without following symlinks, reads file sizes, and prints
one line per chain from the root to each directory that holds an instruction file.
Codex includes at most one file per directory (AGENTS.override.md, then AGENTS.md,
then each fallback name) and bounds the project chain by project_doc_max_bytes.

Exit codes: 0 every chain fits, 1 a chain exceeds the budget, 2 invalid input.
"""

import argparse
import fnmatch
import os
import sys
from pathlib import Path

DEFAULT_BUDGET = 32768
PRIMARY_NAMES = ("AGENTS.override.md", "AGENTS.md")
SKIPPED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "vendor",
                "dist", "build", ".next", ".nuxt", ".output", "coverage"}


def instruction_file(directory: Path, fallbacks):
    """Return the file Codex would read in directory, or None."""
    for name in PRIMARY_NAMES + tuple(fallbacks):
        path = directory / name
        # Codex skips empty instruction files.
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def excluded(rel: str, patterns) -> bool:
    return any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/")
               or fnmatch.fnmatch(rel, p) for p in patterns)


def chains(root: Path, fallbacks=(), excludes=()):
    """Yield (relative dir, total bytes, files) for each directory with a file."""
    picked = {}
    for current, dirs, _files in os.walk(root, followlinks=False):
        current_path = Path(current)
        rel = current_path.relative_to(root).as_posix()
        dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS and not excluded(
            (current_path / d).relative_to(root).as_posix(), excludes))
        found = instruction_file(current_path, fallbacks)
        if found is not None:
            picked[rel] = found
    for rel in sorted(picked):
        parts = [] if rel == "." else rel.split("/")
        files = []
        for depth in range(len(parts) + 1):
            key = "/".join(parts[:depth]) or "."
            if key in picked:
                files.append(picked[key])
        yield rel, sum(f.stat().st_size for f in files), files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", type=Path,
                        help="project root (default: current directory)")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                        help="limit in bytes (default: %d)" % DEFAULT_BUDGET)
    parser.add_argument("--fallback", action="append", default=[],
                        help="a project_doc_fallback_filenames entry; repeatable")
    parser.add_argument("--exclude", action="append", default=[],
                        help="path or glob relative to the root to skip; repeatable")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print("not a directory: %s" % args.root, file=sys.stderr)
        return 2
    if args.budget <= 0:
        print("budget must be a positive number of bytes", file=sys.stderr)
        return 2
    over = 0
    count = 0
    for rel, total, files in chains(root, args.fallback, args.exclude):
        count += 1
        status = "OVER" if total > args.budget else "ok"
        over += total > args.budget
        names = " + ".join(f.relative_to(root).as_posix() for f in files)
        print("%-4s %7d B  %s  (%s)" % (status, total, rel, names))
    if count == 0:
        print("no instruction files found")
    print("budget %d B; %d chain(s), %d over" % (args.budget, count, over))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
