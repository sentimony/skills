#!/usr/bin/env python3
"""Print the subagent-plan-dev state root for a project (nothing is created).

The slug algorithm is the same as slug() in context-transfer; every skill carries its own copy.
"""

import argparse
import hashlib
import os
import subprocess
from pathlib import Path


def project_key(cwd):
    done = subprocess.run(["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return Path(os.path.realpath(cwd))
    common = Path(os.path.realpath(done.stdout.strip()))
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
    base = Path(home) if home is not None else Path.home()
    return base / ".sentimony" / "skills" / "subagent-plan-dev" / slug(project_key(cwd))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=os.getcwd())
    print(state_root(parser.parse_args().cwd))


if __name__ == "__main__":
    main()
