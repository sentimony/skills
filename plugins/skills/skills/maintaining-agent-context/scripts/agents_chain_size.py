#!/usr/bin/env python3
"""Measure every Codex AGENTS.md chain of a repository against a byte budget.

Read-only: walks the tree without following symlinks, reads file sizes, and prints
one line per chain from the root to each directory that holds an instruction file.
Codex includes at most one file per directory (AGENTS.override.md, then AGENTS.md,
then each fallback name) and bounds the project chain by project_doc_max_bytes.

Without --budget the limit is resolved as Codex resolves it, lowest layer first: the
default, /etc/codex/config.toml, the user config.toml in CODEX_HOME (or ~/.codex), the
--profile file <name>.config.toml there, the root's .codex/config.toml when the user
config trusts the root, and /etc/codex/managed_config.toml. Only the keys
project_doc_max_bytes and project_doc_fallback_filenames are read; no other config
value is printed. -c launch flags and MDM preferences are invisible to the script.

A nested folder whose instruction file the root AGENTS.md or CLAUDE.md pulls in with a
bare Claude Code @-import (docs/session-learnings by default, the session-learnings
notes folder, even without one) is no Codex chain: no session starts there, Codex does
not expand @, and Claude Code loads it with the root. Such a folder is printed on its
own line outside the budget instead.

Exit codes: 0 every chain fits, 1 a chain exceeds the budget, 2 invalid input.
"""

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

DEFAULT_BUDGET = 32768
LIMIT_KEY = "project_doc_max_bytes"
FALLBACK_KEY = "project_doc_fallback_filenames"
SYSTEM_CONFIG = Path("/etc/codex/config.toml")
MANAGED_CONFIG = Path("/etc/codex/managed_config.toml")
PRIMARY_NAMES = ("AGENTS.override.md", "AGENTS.md")
SKIPPED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "vendor",
                "dist", "build", ".next", ".nuxt", ".output", "coverage"}
NOTES_DIRS = ("docs/session-learnings",)
ROOT_IMPORTERS = ("AGENTS.md", "CLAUDE.md")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r"`[^`\n]*`")
# Claude Code expands only a bare @path: a trailing punctuation mark or a code span
# leaves the line as plain text.
BARE_IMPORT = re.compile(r"(?:^|(?<=\s))@([^\s`]+)(?=\s|$)", re.MULTILINE)


def instruction_file(directory: Path, fallbacks):
    """Return the file Codex would read in directory, or None."""
    for name in PRIMARY_NAMES + tuple(fallbacks):
        path = directory / name
        # Codex skips empty instruction files.
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def imported_dirs(root: Path, fallbacks=()):
    """Return {relative dir: (kind, file)} of nested folders outside the Codex chains."""
    names = PRIMARY_NAMES + tuple(fallbacks)
    found = {}
    for importer in ROOT_IMPORTERS:
        path = root / importer
        if not path.is_file():
            continue
        text = CODE_SPAN.sub("", FENCE.sub("", path.read_text(encoding="utf-8", errors="replace")))
        for target in BARE_IMPORT.findall(text):
            if target[-1] in ".,;:!?)]":
                continue
            rel = Path(target)
            if rel.is_absolute() or rel.name not in names or rel.parent == Path("."):
                continue
            file = root / rel
            if file.is_file() and file.resolve().is_relative_to(root):
                found[rel.parent.as_posix()] = ("import (Claude Code)", file, "loaded with the root")
    for rel in NOTES_DIRS:
        if rel not in found:
            file = instruction_file(root / rel, fallbacks)
            if file is not None:
                found[rel] = ("notes (session-learnings)", file, "not imported, loaded on demand")
    return found


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


class ConfigError(Exception):
    pass


def load_toml(path: Path):
    """Return the parsed file, or None when it is absent."""
    if not path.is_file():
        return None
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except (tomllib.TOMLDecodeError, OSError):
        # Codex refuses to start on such a file; name it, never its content.
        raise ConfigError("cannot parse %s; Codex will not start with it" % path)


def codex_home() -> Path:
    home = os.environ.get("CODEX_HOME")
    return Path(home) if home else Path.home() / ".codex"


def trusted(user_config, root: Path) -> bool:
    projects = (user_config or {}).get("projects", {})
    for key in (str(root.resolve()), str(root)):
        if key in projects:
            return projects[key].get("trust_level") == "trusted"
    return False


def resolve_limit(root: Path, profile=None):
    """Return (budget, fallbacks, source, notes) of the effective Codex config."""
    budget, fallbacks, source, notes = DEFAULT_BUDGET, [], "default, not set", []
    if tomllib is None:
        notes.append("Python < 3.11 cannot read config.toml; pass --budget")
        return budget, fallbacks, source, notes
    user_path = codex_home() / "config.toml"
    user_config = load_toml(user_path)
    if user_config and "profile" in user_config:
        notes.append("%s sets the legacy 'profile' key, which Codex rejects" % user_path)
    project_path = root / ".codex" / "config.toml"
    layers = [SYSTEM_CONFIG, user_path]
    if profile:
        layers.append(codex_home() / ("%s.config.toml" % profile))
    if project_path.is_file():
        if trusted(user_config, root):
            layers.append(project_path)
        else:
            notes.append("%s ignored: the project is not trusted" % project_path)
    layers.append(MANAGED_CONFIG)
    for path in layers:
        data = user_config if path == user_path else load_toml(path)
        if not data:
            continue
        if LIMIT_KEY in data:
            budget, source = data[LIMIT_KEY], str(path)
        if FALLBACK_KEY in data:
            # A later layer replaces the whole list.
            fallbacks = [n.strip() for n in data[FALLBACK_KEY] if n.strip()]
    if (root / ".codex" / "config.local.toml").is_file():
        notes.append(".codex/config.local.toml is not read by Codex")
    notes.append("-c launch flags and MDM preferences are not visible here")
    return budget, fallbacks, source, notes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", type=Path,
                        help="project root (default: current directory)")
    parser.add_argument("--budget", type=int,
                        help="limit in bytes (default: the effective Codex config, "
                             "else %d)" % DEFAULT_BUDGET)
    parser.add_argument("--profile",
                        help="the Codex --profile name the sessions run with")
    parser.add_argument("--fallback", action="append",
                        help="a project_doc_fallback_filenames entry; repeatable "
                             "(default: from the Codex config)")
    parser.add_argument("--exclude", action="append", default=[],
                        help="path or glob relative to the root to skip; repeatable")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print("not a directory: %s" % args.root, file=sys.stderr)
        return 2
    if args.budget is not None and args.budget <= 0:
        print("budget must be a positive number of bytes", file=sys.stderr)
        return 2
    try:
        budget, fallbacks, source, notes = resolve_limit(root, args.profile)
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 2
    if args.budget is not None:
        budget, source, notes = args.budget, "--budget", []
    if args.fallback is not None:
        fallbacks = args.fallback
    if not isinstance(budget, int) or budget <= 0:
        print("%s in %s must be a positive integer" % (LIMIT_KEY, source), file=sys.stderr)
        return 2
    print("limit %d B (%s)" % (budget, source))
    for note in notes:
        print("note: %s" % note)
    args.budget = budget
    over = 0
    count = 0
    imports = imported_dirs(root, fallbacks)
    excludes = list(args.exclude) + [rel for rel in imports
                                     if not excluded(rel, args.exclude)]
    for rel, total, files in chains(root, fallbacks, excludes):
        count += 1
        status = "OVER" if total > args.budget else "ok"
        over += total > args.budget
        names = " + ".join(f.relative_to(root).as_posix() for f in files)
        print("%-4s %7d B  %s  (%s)" % (status, total, rel, names))
    for rel in sorted(imports):
        if excluded(rel, args.exclude):
            continue
        kind, file, how = imports[rel]
        print("%s: +%d B  %s  (%s, %s, not a Codex chain)"
              % (kind, file.stat().st_size, rel, file.relative_to(root).as_posix(), how))
    if count == 0:
        print("no instruction files found")
    print("budget %d B; %d chain(s), %d over" % (args.budget, count, over))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
