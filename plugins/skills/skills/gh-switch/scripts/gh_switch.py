#!/usr/bin/env python3
"""
Switch the GitHub CLI to the account a project names in .env/.env before a gh operation,
and check that the project's GitLab token belongs to the account it names.

Usage:
    python3 scripts/gh_switch.py [--cwd PATH] [--target OWNER/REPO] [--no-switch]
    python3 scripts/gh_switch.py --gitlab [--cwd PATH]

Reads only the GH_ACC line of <project root>/.env/.env, or with --gitlab only the GL_ACC
and GITLAB_TOKEN lines. Exit codes: 0 proceed, 2 configuration error, 3 login needed,
4 token override, 5 gh, auth state, or GitLab API problem, 6 switch not confirmed,
7 GitLab token of another account. Prints one "gh-switch: <from> -> <to>" line after a
confirmed switch. With --no-switch it checks GH_ACC the same way but never switches, and
prints the per-command token prefix instead.
"""

import argparse
import base64
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "github.com"
MIN_GH = (2, 81, 0)
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}")
GITLAB_USER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,254}")
REMOTE = re.compile(r"^(?:(?:https|ssh|git)://)?(?:[^@/\s]+@)?github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
URL_REMOTE = re.compile(r"^[a-z][a-z0-9+.-]*://(?:[^@/\s]+@)?([^:/\s]+)", re.IGNORECASE)
SCP_REMOTE = re.compile(r"^(?:[^@/:\s]+@)?([^:/\s]+):")
TOKEN_VALUE = re.compile(r"[^\s'\"]+")
OVERRIDES = ("GH_TOKEN", "GITHUB_TOKEN")
CONFIG, LOGIN_NEEDED, OVERRIDE, STATE, UNCONFIRMED, MISMATCH = 2, 3, 4, 5, 6, 7
TIMEOUT = 60
NO_ACC = "gh-switch: no GH_ACC in .env/.env; account unchanged, do not switch by hand"


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


def read_env(root):
    path = root / ".env" / ".env"
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, UnicodeDecodeError):
        raise Stop(CONFIG, ".env/.env exists but cannot be read")


def read_key(text, key, placeholder):
    line_of_key = re.compile(rf"\s*(?:export\s+)?{key}\s*=")
    values = []
    # Lines are data: only the named key's line is inspected, nothing is expanded or executed.
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line_of_key.match(line):
            continue
        if not line.startswith(f"{key}="):
            raise Stop(CONFIG, f"{key} in .env/.env has an unsupported format; use one line {key}={placeholder}")
        values.append(line[len(key) + 1:])
    if len(values) > 1:
        raise Stop(CONFIG, f"{key} is defined more than once in .env/.env")
    return values[0] if values else None


def read_login(root):
    text = read_env(root)
    login = None if text is None else read_key(text, "GH_ACC", "<login>")
    if login is None:
        return None
    if not LOGIN.fullmatch(login):
        raise Stop(CONFIG, "GH_ACC in .env/.env is empty or not a valid GitHub login")
    return login


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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_user(url, token):
    request = urllib.request.Request(url, headers={"PRIVATE-TOKEN": token, "Accept": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise Stop(STATE, f"GitLab API returned {response.status}")
            body = response.read(65536)
    except urllib.error.HTTPError as error:
        error.close()
        if 300 <= error.code < 400:
            raise Stop(STATE, f"GitLab API redirected ({error.code}); the token was not sent further")
        if error.code == 401:
            raise Stop(STATE, "GitLab API rejected GITLAB_TOKEN (401); check or renew the token")
        raise Stop(STATE, f"GitLab API returned {error.code}")
    except (OSError, ValueError, http.client.HTTPException):
        raise Stop(STATE, "GitLab API could not be reached")
    try:
        user = json.loads(body).get("username")
    except (ValueError, AttributeError):
        user = None
    if not isinstance(user, str) or not GITLAB_USER.fullmatch(user):
        raise Stop(STATE, "GitLab API returned an unreadable user")
    return user


def ensure(cwd, target, environ, switch=True):
    root = project_root(cwd)
    if root is None:
        return None
    host = environ.get("GH_HOST", "")
    if host and host.lower() != HOST:
        return None
    repos = project_repos(root)
    target = target or environ.get("GH_REPO", "")
    if target and normalize_target(target) not in repos:
        return "gh-switch: no project config for this target; account unchanged"
    login = read_login(root)
    if login is None:
        # Silence here used to read as "account matches", and agents then switched by hand.
        return NO_ACC if repos else None
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
    if not switch:
        # Another session can switch the shared account at any time, so the prefix is
        # printed even when the wanted account is active now.
        return (f'gh-switch: prefix the command with GH_TOKEN="$(gh auth token --hostname {HOST} '
                f'--user {wanted["login"]})"; account unchanged')
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


def gitlab_hosts(root):
    hosts = set()
    # Unlike the gh branch, a failed read must not look like "no GitLab remote": that would
    # skip the token check silently.
    try:
        done = run(["git", "-C", str(root), "remote", "-v"])
    except (OSError, subprocess.TimeoutExpired):
        done = None
    if done is None or done.returncode != 0:
        raise Stop(STATE, "could not read the Git remotes")
    for line in done.stdout.splitlines():
        parts = line.split()
        url = parts[1] if len(parts) > 1 else ""
        # Git reads "host:path" as SCP-like only when no slash precedes the colon; anything else
        # without a scheme is a local path. A host without a dot is an SSH alias or a local name.
        match = URL_REMOTE.match(url) or SCP_REMOTE.match(url)
        host = match.group(1).lower() if match else ""
        if "." in host and host != HOST:
            hosts.add(host)
    return hosts


def mask(text, token):
    forms = {token, urllib.parse.quote(token, safe="")}
    for encode in (base64.b64encode, base64.urlsafe_b64encode):
        encoded = encode(token.encode("utf-8")).decode("ascii")
        forms |= {encoded, encoded.rstrip("=")}
    for form in sorted(forms, key=len, reverse=True):
        text = text.replace(form, "***")
    return text


def ensure_gitlab(cwd):
    root = project_root(cwd)
    text = None if root is None else read_env(root)
    login = None if text is None else read_key(text, "GL_ACC", "<username>")
    if login is None:
        return None
    if not GITLAB_USER.fullmatch(login):
        raise Stop(CONFIG, "GL_ACC in .env/.env is empty or not a valid GitLab username")
    hosts = gitlab_hosts(root)
    if not hosts:
        return None
    if len(hosts) > 1:
        raise Stop(CONFIG, "remotes point to more than one non-GitHub host; GL_ACC cannot pick one")
    token = read_key(text, "GITLAB_TOKEN", "<token>")
    if not token or not TOKEN_VALUE.fullmatch(token):
        raise Stop(CONFIG, "GITLAB_TOKEN in .env/.env is missing, empty, or malformed")
    try:
        user = fetch_user(f"https://{hosts.pop()}/api/v4/user", token)
    except Stop as stop:
        raise Stop(stop.code, mask(str(stop), token)) from None
    if user.lower() != login.lower():
        raise Stop(MISMATCH, mask(f"GITLAB_TOKEN belongs to {user}, expected {login}", token))
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Select the gh account named by GH_ACC, or with --gitlab check the "
                                                 "GitLab token owner against GL_ACC, in the project's .env/.env.")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--target", help="OWNER/REPO the gh command addresses explicitly (--repo)")
    parser.add_argument("--no-switch", action="store_true",
                        help="check GH_ACC without gh auth switch and print the per-command token prefix")
    parser.add_argument("--gitlab", action="store_true",
                        help="check that GITLAB_TOKEN belongs to GL_ACC instead of selecting the gh account")
    args = parser.parse_args(argv)
    try:
        if args.gitlab:
            ensure_gitlab(args.cwd)
        else:
            message = ensure(args.cwd, args.target, os.environ, switch=not args.no_switch)
            if message:
                print(message)
    except Stop as stop:
        print(f"gh-switch: {stop}", file=sys.stderr)
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
