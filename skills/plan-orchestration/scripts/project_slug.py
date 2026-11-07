#!/usr/bin/env python3
"""Print the plan-orchestration state root for a project (nothing is created).

The slug algorithm is the same as slug() in context-transfer; every skill carries its own copy.
"""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


class StateError(Exception):
    """The state root cannot be determined safely; there is no fallback location."""


def project_key(cwd):
    if not os.path.isdir(cwd):
        raise StateError("the working directory does not exist")
    try:
        done = subprocess.run(["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                              capture_output=True, text=True, env=dict({k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, LC_ALL="C"))
    except OSError:
        raise StateError("git cannot be run")
    if done.returncode != 0:
        # Only a plain directory may fall back to itself; any other failure must not pick a new key.
        here = Path(os.path.realpath(cwd))
        if "not a git repository" in done.stderr and not any(os.path.lexists(d / ".git") for d in (here, *here.parents)):
            return here
        raise StateError("git failed to read the repository")
    common = Path(os.path.realpath(done.stdout.rstrip("\n")))
    return common.parent if common.name == ".git" else common


def slug(path):
    resolved = str(Path(path).resolve())
    digest = hashlib.sha256(os.fsencode(resolved)).hexdigest()[:12]
    name, size = "", 0
    for char in Path(resolved).name or "root":
        size += len(os.fsencode(char))
        if size > 64:
            break
        name += char
    return name + "-" + digest


def state_root(cwd, home=None):
    text = os.fspath(home) if home is not None else os.environ.get("HOME", "")
    if not text or not os.path.isabs(text) or not os.path.isdir(text):
        raise StateError("HOME is not usable; the state root has no fallback location")
    base = Path(text)
    key = project_key(cwd)
    inside = Path(os.path.realpath(text))
    if key in (inside, *inside.parents) or Path(os.path.realpath(cwd)) in (inside, *inside.parents):
        raise StateError("HOME lies inside the project; the state would be repository-local")
    return base / ".sentimony" / "skills" / "plan-orchestration" / slug(key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=os.getcwd())
    try:
        print(state_root(parser.parse_args().cwd))
    except StateError as error:
        print(f"project_slug: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
