#!/usr/bin/env python3
"""Decide what environment and which binaries a child process gets.

Shared by inspect_vitest.py and run_vitest.py. Those two scripts otherwise duplicate
their small helpers on purpose, so that each reads top to bottom on its own; this one is
shared because it is the skill's trust boundary between the machine running the helper
and the project being inspected, and two hand-kept copies of a boundary drift. Both
scripts spawn `node` from a project directory, and the runner also spawns a package
script's launcher, so both need the same answer to the same question: which `node` is
that, and whose environment does it see.
"""

import os
import shutil
import subprocess
from pathlib import Path


# Environment names a package manager injects into the scripts it runs. When a helper is
# itself started from a package script - `npm run test:agent`, a pnpm task, a bun script
# - the package manager has already read the repository's package.json and .npmrc and
# reflected them here: npm_config_registry and npm_config_userconfig decide what a later
# `npx` fetches, npm_package_* mirrors package.json, and INIT_CWD/PROJECT_CWD name the
# directory the run started in. Inheriting them would reintroduce by ambient environment
# exactly the redirection the runner's script-body key allowlist rejects.
#
# The direction is deliberately the opposite of that allowlist's. A script body's
# environment prefix is repository data a helper chooses to honor, so only a closed safe
# set may pass; the ambient environment is the user's own and must pass through by
# default, so only what a package manager demonstrably wrote is removed. That is why the
# match is on the lowercase `npm_` spelling package managers write, and not on
# NPM_CONFIG_* or NPM_TOKEN, which are how a user configures npm from their own shell.
#
# NODE_OPTIONS is not removed. An ambient one is the user's choice -
# `--experimental-vm-modules` is a real Vitest configuration - and the one repository
# path that reaches it, `node-options` in a repository .npmrc, is the documented .npmrc
# channel, not a separate one this filter could close.
INJECTED_ENV_PREFIXES = ("npm_",)
INJECTED_ENV_KEYS = frozenset({"INIT_CWD", "PROJECT_CWD", "BERRY_BIN_FOLDER"})


def is_inside(path, root):
    return path == root or root in path.parents


def touches_project(entry, root):
    """True when any component of a PATH entry lies inside the project.

    Testing the resolved target alone is not enough: `project/bin -> ../outside-bin` is a
    symlink the project owns, so the target it names today is not a property of the
    entry: the project can repoint it between this check and the exec. What makes such an
    entry unsafe is that one of its components is project-controlled, so every prefix is
    resolved and tested, not just the whole. Resolving each prefix rather than comparing
    the text also survives a symlinked ancestor above the project (on macOS `/tmp` is
    `/private/tmp`), where a purely lexical comparison against the resolved root matches
    nothing.

    An entry that passes through the project only to leave again with `..` is rejected
    too, which is conservative: `..` from a real directory cannot be repointed. Such a
    PATH entry does not occur in practice, and being wrong in this direction only drops a
    search path.
    """
    path = Path(entry)
    for prefix in (path, *path.parents):
        try:
            resolved = prefix.resolve()
        except OSError:
            return True
        if is_inside(resolved, root):
            return True
    return False


def sanitized_path(root, value):
    """Return PATH with every entry the project itself could write removed.

    Two kinds of entry go: the empty string and any relative entry, both of which mean
    "resolve from the current directory" and so are decided by whatever directory a run
    happens to start in; and any entry that touches the project, which is repository
    content: node_modules/.bin is the ordinary case, and a package manager puts it on
    PATH for every script it runs. Keeping one would let a package.json ship an `npx` or
    a `node` of its own and have a helper execute it under the name of the real one.

    A surviving entry is kept in resolved form, so the directory this returns is the one
    that was checked rather than a name that could be made to mean something else
    afterwards.
    """
    entries = []
    for entry in (value or "").split(os.pathsep):
        if not entry or not os.path.isabs(entry):
            continue
        if touches_project(entry, root):
            continue
        try:
            entries.append(str(Path(entry).resolve()))
        except OSError:
            continue
    return os.pathsep.join(entries)


def build_environment(root, script_env=None):
    """Return the environment a child process gets.

    The caller's environment minus what a package manager injected, with PATH filtered,
    plus any assignments a caller parsed out of an accepted package script. It is built
    for every spawn, not only when a script contributed assignments: the two hazards it
    removes come from the ambient environment, so they are present exactly when the
    script contributed nothing as well.
    """
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(INJECTED_ENV_PREFIXES) and key not in INJECTED_ENV_KEYS
    }
    if "PATH" in environment:
        environment["PATH"] = sanitized_path(root, environment["PATH"])
    environment.update(script_env or {})
    return environment


def which_program(program, path, root):
    """Resolve a program name against an already-filtered PATH, or return None.

    An absolute path is already a decision about which file runs and is returned as is:
    the local Vitest binary is inside the project on purpose.

    Filtering PATH decides which *directories* are searched, which is not yet a decision
    about which file runs: an allowed directory can hold a symlink whose target is back
    inside the project. `npm link` writes exactly that shape into a global bin directory,
    so this is an ordinary state for a machine to be in, not a contrived one. The file the
    lookup landed on is therefore resolved and tested too, and a target inside the project
    reads as no such program rather than as one to run.

    What runs is the path the lookup returned, not its resolved target. Resolving is how
    the file is identified; executing the target instead would change argv[0], and the
    symlink is the indirection a version manager relies on: Volta's shims are symlinks
    to one `volta-shim` binary that picks the tool from the name it was invoked as, so the
    canonical path names no tool at all. It would also buy nothing here: the repository is
    the untrusted party, and a symlink outside the project is not something a repository
    can write or repoint.
    """
    if os.path.isabs(program):
        return program
    found = shutil.which(program, path=path)
    if found is None:
        return None
    try:
        target = Path(found).resolve()
    except OSError:
        return None
    if is_inside(target, root):
        return None
    return found


def resolve_program(command, path, root):
    """Resolve a command's program to an absolute path, or fail with a stated reason.

    subprocess resolves a bare name itself, through the child's PATH at exec time, which
    is the one thing the filtering above cannot reach into. Resolving here means the
    program a caller reports and the program that runs are the same file, and that the
    choice was made against a PATH the project does not appear in.
    """
    resolved = which_program(command[0], path, root)
    if resolved is None:
        raise SystemExit(
            f"Command not found outside the project: {command[0]}. "
            "Install it so it resolves from a directory the project does not control."
        )
    return [resolved, *command[1:]]


def current_node_version(root):
    """Return the active `node -v` string, or None when there is no usable Node.

    The preflight this feeds compares a project's declared Node version against the
    running one, which means running a program named by the project's own environment.
    A project that ships node_modules/.bin/node would otherwise answer the question about
    itself. Resolution and the child environment therefore go through the same filter as
    everything else here, and a `node` that exists only inside the project, or that an
    outside directory merely points at, is treated as no Node at all rather than executed.
    """
    environment = build_environment(root)
    program = which_program("node", environment.get("PATH"), root)
    if program is None:
        return None
    try:
        result = subprocess.run(
            [program, "-v"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
