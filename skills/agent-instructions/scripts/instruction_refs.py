#!/usr/bin/env python3
"""Check the paths and commands that repository instruction files mention.

Read-only: reads instruction files (AGENTS.md, AGENTS.override.md, CLAUDE.md,
.claude/CLAUDE.md, .claude/rules/**/*.md), package.json and Makefile files, and asks git
for the file list and the ignore rules. It never runs a project command.

For every backtick span (and every command line in a fenced block) it checks:

* a path: relative to the instruction file's folder, then to the repo root, then by
  suffix among the repo files; one suffix match is ok, several are `ambiguous`;
* `pnpm|npm|yarn run <x>` against `scripts` of the nearest package.json, `make <x>`
  against the targets of the nearest Makefile.

Things that look like paths but are not repo files are reported as `skipped (<class>)`
instead of `broken`: route, external repo, gitignored, generated, pattern, url, home,
absolute, workspace filter. Exit codes: 0 no broken reference, 1 at least one broken,
2 invalid input.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIPPED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "vendor",
                "dist", "build", ".next", ".nuxt", ".output", "coverage"}
GENERATED = SKIPPED_DIRS | {".turbo", ".cache", "out", "tmp"}
INSTRUCTION_NAMES = ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md")
FILE_EXTENSIONS = {
    "md", "json", "ts", "tsx", "js", "jsx", "mjs", "cjs", "py", "sh", "yml", "yaml",
    "toml", "txt", "css", "scss", "html", "vue", "lock", "env", "cfg", "ini", "xml",
    "svg", "sql", "go", "rs", "rb", "php", "java", "mdc", "csv", "png", "jpg", "pdf"}
SPAN = re.compile(r"`([^`\n]+)`")
PACKAGE_RUN = re.compile(
    r"^\s*\$?\s*(pnpm|npm|yarn)\s+((?:-\S+\s+(?:(?!run\b)[^-\s]\S*\s+)?)*)"
    r"run(?:-script)?\s+([^\s&|;]+)")
MAKE_RUN = re.compile(r"^\s*\$?\s*make\s+(.*)")
PATTERN_CHARS = re.compile(r"[*?{}\[\]<>$%=|;&()\"']")
OWNER_REPO = re.compile(r"^[\w.-]+/[\w.-]+$")
TARGET = re.compile(r"^([A-Za-z0-9_.%/-]+(?:\s+[A-Za-z0-9_.%/-]+)*)\s*:(?![:=])", re.MULTILINE)


def git(root, *args, stdin=None):
    """Run a read-only git command; return stdout, or None when git cannot answer."""
    try:
        done = subprocess.run(["git", "-C", str(root), *args], input=stdin,
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode in (0, 1) else None


def repo_files(root):
    listing = git(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if listing:
        return sorted(set(line for line in listing.splitlines() if line))
    found = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIPPED_DIRS]
        found += [(Path(current) / f).relative_to(root).as_posix() for f in files]
    return sorted(found)


def excluded(rel, excludes):
    return any(rel == e or rel.startswith(e + "/") for e in excludes)


def instruction_files(root, excludes):
    found = []
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        kept = []
        for d in sorted(dirs):
            rel = (here / d).relative_to(root).as_posix()
            if d in SKIPPED_DIRS or excluded(rel, excludes) or os.path.lexists(here / d / ".git"):
                continue
            kept.append(d)
        dirs[:] = kept
        rel_dir = here.relative_to(root).as_posix()
        in_claude = here.name == ".claude" and here.parent == root
        in_rules = rel_dir == ".claude/rules" or rel_dir.startswith(".claude/rules/")
        for name in sorted(files):
            if name in INSTRUCTION_NAMES or (in_claude and name == "CLAUDE.md") \
                    or (in_rules and name.endswith(".md")):
                found.append(here / name)
    return found


def spans(path):
    """Yield (line number, text, in_fence) for backtick spans and fenced lines."""
    fence = None
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        marker = re.match(r"^\s*(```|~~~)", line)
        if marker:
            fence = None if fence == marker.group(1) else (fence or marker.group(1))
            continue
        if fence:
            yield number, line.strip(), True
        else:
            for match in SPAN.finditer(line):
                yield number, match.group(1).strip(), False


def candidate(text):
    """Return a path string when the span reads as a single path, else None."""
    if not text or " " in text or text.startswith("-"):
        return None
    cleaned = re.sub(r"#.*$", "", text)
    cleaned = re.sub(r":\d+(?::\d+)?$", "", cleaned).rstrip(",.;")
    if not cleaned.strip("/"):
        return None
    if "/" in cleaned:
        return cleaned
    ext = cleaned.rsplit(".", 1)[-1] if "." in cleaned.strip(".") else ""
    return cleaned if ext in FILE_EXTENSIONS else None


class Index:
    def __init__(self, root, files):
        self.root = root
        self.files = files
        self.file_set = set(files)
        self.dirs = set()
        for rel in files:
            parts = rel.split("/")
            for depth in range(1, len(parts)):
                self.dirs.add("/".join(parts[:depth]))

    def exists(self, rel):
        return rel in self.dirs or rel in self.file_set or (self.root / rel).exists()

    def suffix_matches(self, rel):
        tail = "/" + rel
        hits = [f for f in self.files if f == rel or f.endswith(tail)]
        hits += [d for d in self.dirs if d == rel or d.endswith(tail)]
        return sorted(set(hits))


def classify_path(text, folder_rel, index):
    """Return (status, detail) for one path candidate."""
    root = index.root
    if "://" in text or re.match(r"^[\w.-]+@[\w.-]+:", text):
        return "skipped", "url"
    if text.startswith("@") and len(text) > 1:
        text = text[1:]
    if text.startswith("~"):
        return "skipped", "home"
    if PATTERN_CHARS.search(text):
        return "skipped", "pattern"
    path = text.rstrip("/")
    if path.startswith("/"):
        inner = path.lstrip("/")
        if inner and index.exists(inner):
            return "ok", None
        if Path(path).exists():
            return "skipped", "absolute"
        return "skipped", "route"
    path = os.path.normpath(path).replace("\\", "/")
    for base in (folder_rel, ""):
        joined = os.path.normpath(os.path.join(base, path)).replace("\\", "/")
        if not joined.startswith("..") and index.exists(joined):
            return "ok", None
    hits = index.suffix_matches(path)
    if len(hits) == 1:
        return "ok", None
    if len(hits) > 1:
        return "ambiguous", ", ".join(hits[:4]) + (" ..." if len(hits) > 4 else "")
    first = path.split("/")[0]
    if first in GENERATED:
        return "skipped", "generated"
    if git_ignored(root, path):
        return "skipped", "gitignored"
    if OWNER_REPO.match(path) and first not in index.dirs and "." not in path.rsplit("/", 1)[-1]:
        return "skipped", "external repo"
    return "broken", "no such path"


def git_ignored(root, path):
    try:
        done = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--", path],
                              capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def nearest(root, folder, name):
    """Return the nearest file called name from folder up to the root, or None."""
    current = folder
    while True:
        file = current / name
        if file.is_file():
            return file
        if current == root or root not in current.parents:
            return None
        current = current.parent


def check_package_script(root, folder, script):
    package = nearest(root, folder, "package.json")
    if package is None:
        return "broken", "no package.json up to the root"
    try:
        scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
    except (ValueError, OSError):
        return "broken", "cannot parse %s" % package.relative_to(root).as_posix()
    if script in scripts:
        return "ok", None
    return "broken", "no script %r in %s" % (script, package.relative_to(root).as_posix())


def check_make_target(root, folder, rest):
    words = [w for w in rest.split() if not w.startswith("-") and "=" not in w]
    if not words:
        return "ok", None
    target = words[0]
    if PATTERN_CHARS.search(target):
        return "skipped", "pattern"
    makefile = None
    for name in ("Makefile", "makefile", "GNUmakefile"):
        makefile = nearest(root, folder, name)
        if makefile:
            break
    if makefile is None:
        return "broken", "no Makefile up to the root"
    text = makefile.read_text(encoding="utf-8", errors="replace")
    names = set()
    for match in TARGET.finditer(text):
        names.update(match.group(1).split())
    if target in names:
        return "ok", None
    if re.search(r"^-?include\s", text, re.MULTILINE):
        return "skipped", "included makefile"
    return "broken", "no target %r in %s" % (target, makefile.relative_to(root).as_posix())


def check_span(text, in_fence, folder, index):
    """Return (status, detail), or None when the span is neither a path nor a command."""
    root = index.root
    package = PACKAGE_RUN.match(text)
    if package:
        if package.group(2).strip():
            return "skipped", "workspace filter"
        if PATTERN_CHARS.search(package.group(3)):
            return "skipped", "pattern"
        return check_package_script(root, folder, package.group(3))
    make = MAKE_RUN.match(text)
    if make:
        return check_make_target(root, folder, make.group(1))
    if in_fence:
        return None
    path = candidate(text)
    if path is None:
        return None
    return classify_path(path, folder.relative_to(root).as_posix(), index)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="repository root")
    parser.add_argument("--exclude", action="append", default=[],
                        help="path relative to the root to skip; repeatable")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print("not a directory: %s" % args.root, file=sys.stderr)
        return 2
    excludes = [e.rstrip("/") for e in args.exclude]
    index = Index(root, repo_files(root))
    counts = Counter()
    lines = []
    files = instruction_files(root, excludes)
    for file in files:
        rel_file = file.relative_to(root).as_posix()
        for number, text, in_fence in spans(file):
            result = check_span(text, in_fence, file.parent, index)
            if result is None:
                continue
            status, detail = result
            key = "skipped (%s)" % detail if status == "skipped" else status
            counts[key] += 1
            if status != "ok":
                lines.append("%s %s:%d  `%s`%s" % (
                    key, rel_file, number, text,
                    "  - %s" % detail if status != "skipped" and detail else ""))
    for line in sorted(lines, key=lambda l: (not l.startswith("broken"),
                                             not l.startswith("ambiguous"))):
        print(line)
    total = sum(counts.values())
    summary = ", ".join("%s %d" % (k, counts[k]) for k in sorted(counts))
    print("%d instruction file(s); checked %d reference(s)%s"
          % (len(files), total, ": " + summary if summary else ""))
    return 1 if counts["broken"] else 0


if __name__ == "__main__":
    sys.exit(main())
