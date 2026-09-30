#!/usr/bin/env python3
"""
Switch the GitHub CLI to the account a project names in .env/.env before a gh operation.

Usage:
    python3 scripts/gh_switch.py [--cwd PATH] [--target OWNER/REPO]

Reads only the GH_ACC line of <project root>/.env/.env. Exit codes: 0 proceed,
2 configuration error, 3 login needed, 4 token override, 5 gh or auth state problem,
6 switch not confirmed. Prints one "gh-switch: <from> -> <to>" line after a confirmed switch.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOST = "github.com"
MIN_GH = (2, 81, 0)
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}")
KEY_LINE = re.compile(r"\s*(?:export\s+)?GH_ACC\s*=")
REMOTE = re.compile(r"^(?:(?:https|ssh|git)://)?(?:[^@/\s]+@)?github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
OVERRIDES = ("GH_TOKEN", "GITHUB_TOKEN")
CONFIG, LOGIN_NEEDED, OVERRIDE, STATE, UNCONFIRMED = 2, 3, 4, 5, 6
TIMEOUT = 60


class Stop(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def run(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT)


def project_root(cwd):
    try:
        done = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"])
    except (OSError, subprocess.TimeoutExpired):
        return None
    return Path(done.stdout.strip()) if done.returncode == 0 else None


def project_repos(root):
    repos = set()
    try:
        lines = run(["git", "-C", str(root), "remote", "-v"]).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return repos
    for line in lines:
        parts = line.split()
        match = REMOTE.match(parts[1]) if len(parts) > 1 else None
        if match:
            repos.add(f"{match.group(1)}/{match.group(2)}".lower())
    return repos


def normalize_target(value):
    target = value.strip().lower()
    for prefix in ("https://github.com/", "github.com/"):
        if target.startswith(prefix):
            target = target[len(prefix):]
    if target.endswith(".git"):
        target = target[:-4]
    return target.strip("/")


def read_login(root):
    path = root / ".env" / ".env"
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, UnicodeDecodeError):
        raise Stop(CONFIG, ".env/.env exists but cannot be read")
    values = []
    # Lines are data: only the GH_ACC line is inspected, nothing is expanded or executed.
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not KEY_LINE.match(line):
            continue
        if not line.startswith("GH_ACC="):
            raise Stop(CONFIG, "GH_ACC in .env/.env has an unsupported format; use one line GH_ACC=<login>")
        values.append(line[len("GH_ACC="):])
    if not values:
        return None
    if len(values) > 1:
        raise Stop(CONFIG, "GH_ACC is defined more than once in .env/.env")
    if not LOGIN.fullmatch(values[0]):
        raise Stop(CONFIG, "GH_ACC in .env/.env is empty or not a valid GitHub login")
    return values[0]


def check_gh_version():
    try:
        done = run(["gh", "--version"])
    except OSError:
        raise Stop(STATE, "gh is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise Stop(STATE, "gh --version timed out")
    match = re.search(r"gh version (\d+)\.(\d+)\.(\d+)", done.stdout)
    if done.returncode != 0 or not match:
        raise Stop(STATE, "cannot read the gh version")
    if tuple(int(part) for part in match.groups()) < MIN_GH:
        raise Stop(STATE, "gh 2.81.0 or newer is required")


def accounts():
    try:
        done = run(["gh", "auth", "status", "--hostname", HOST, "--json", "hosts"])
    except (OSError, subprocess.TimeoutExpired):
        raise Stop(STATE, "gh auth status could not be run; check the gh installation and configuration")
    if done.returncode != 0:
        raise Stop(STATE, "gh auth status failed; check the gh installation and configuration")
    try:
        entries = (json.loads(done.stdout).get("hosts") or {}).get(HOST) or []
    except (ValueError, AttributeError):
        raise Stop(STATE, "gh auth status returned unreadable output")
    if not isinstance(entries, list):
        raise Stop(STATE, "gh auth status returned unreadable output")
    return [entry for entry in entries if isinstance(entry, dict)]


def find(entries, login):
    return next((entry for entry in entries if str(entry.get("login", "")).lower() == login.lower()), None)


def ensure(cwd, target, environ):
    root = project_root(cwd)
    if root is None:
        return None
    host = environ.get("GH_HOST", "")
    if host and host.lower() != HOST:
        return None
    target = target or environ.get("GH_REPO", "")
    if target and normalize_target(target) not in project_repos(root):
        return "gh-switch: no project config for this target; account unchanged"
    login = read_login(root)
    if login is None:
        return None
    for name in OVERRIDES:
        if environ.get(name):
            raise Stop(OVERRIDE, f"{name} is set and overrides the stored gh accounts; unset it or confirm "
                                 "that the current credentials should be used. Account unchanged")
    check_gh_version()
    entries = accounts()
    wanted = find(entries, login)
    if wanted is None:
        raise Stop(LOGIN_NEEDED, f"account {login} is not logged in on {HOST}; the user can run: "
                                 f"gh auth login --hostname {HOST}")
    if wanted.get("state") != "success":
        raise Stop(STATE, f"stored credentials for {login} are not valid; the user can re-authenticate with "
                          f"gh auth login --hostname {HOST}")
    if wanted.get("active"):
        return None
    previous = next((entry.get("login") for entry in entries if entry.get("active")), None)
    try:
        switched = run(["gh", "auth", "switch", "--hostname", HOST, "--user", wanted["login"]])
    except (OSError, subprocess.TimeoutExpired):
        raise Stop(UNCONFIRMED, f"switch to {wanted['login']} could not be confirmed")
    if switched.returncode != 0:
        raise Stop(UNCONFIRMED, f"gh auth switch to {wanted['login']} failed; account not changed")
    try:
        after = find(accounts(), login)
    except Stop:
        after = None
    if not after or not after.get("active") or after.get("state") != "success":
        raise Stop(UNCONFIRMED, f"switch to {wanted['login']} could not be confirmed")
    return f"gh-switch: {previous or 'none'} -> {wanted['login']}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Select the gh account named by GH_ACC in the project's .env/.env.")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--target", help="OWNER/REPO the gh command addresses explicitly (--repo)")
    args = parser.parse_args(argv)
    try:
        message = ensure(args.cwd, args.target, os.environ)
    except Stop as stop:
        print(f"gh-switch: {stop}", file=sys.stderr)
        return stop.code
    if message:
        print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
