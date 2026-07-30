#!/usr/bin/env python3
"""
Locate project-local tool binaries without leaving the project.

Shared by the TypeScript helper scripts: every one of them must run an existing
local compiler and never a binary from an unrelated directory.
"""

from pathlib import Path


def repository_boundary(root):
    """Return the repository root that bounds a lookup, or None when unknown."""
    resolved = Path(root).resolve()
    for directory in [resolved, *resolved.parents]:
        if (directory / ".git").exists():
            return directory
    return None


def local_binary(root, name):
    """Return an existing local binary from this project, or None.

    Workspace installs hoist binaries to the workspace root, so a package-level
    --root has to look upwards. The walk stops at the repository root, and without
    a repository boundary it does not walk at all: an arbitrary ancestor directory
    is not part of the project and its binaries are not trusted.
    """
    root = Path(root)
    direct = root / "node_modules" / ".bin" / name
    if direct.is_file():
        return direct
    boundary = repository_boundary(root)
    if boundary is None or boundary == root.resolve():
        return None
    for directory in root.resolve().parents:
        candidate = directory / "node_modules" / ".bin" / name
        if candidate.is_file():
            return candidate
        if directory == boundary:
            break
    return None
