#!/usr/bin/env python3
"""
Switch the GitHub CLI to the account a project names in .env/.env before a gh operation,
and check that the project's GitLab token belongs to the account it names.

Usage:
    python3 scripts/gh_switch.py [--cwd PATH] [--target OWNER/REPO] [--no-switch]
    python3 scripts/gh_switch.py --gitlab [--cwd PATH]

Reads only the GH_ACC line of <project root>/.env/.env, or with --gitlab only the GL_ACC
and GITLAB_TOKEN lines. Without GH_ACC it adds the line to a gitignored .env/.env when the
account is unambiguous: the one remote owner that is a logged-in login, or the GH_ACC every
sibling clone of the same owner names. Exit codes: 0 proceed, 2 configuration error, 3 login needed,
4 token override, 5 gh, auth state, or GitLab API problem, 6 switch not confirmed,
7 GitLab token of another account. Prints one "gh-switch: <from> -> <to>" line after a
confirmed switch. With --no-switch it checks GH_ACC the same way but never switches, and
prints the per-command token prefix instead.
"""

import argparse
import base64
import fcntl
import http.client
import json
import os
import re
import stat
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
REMOTE = re.compile(r"^((?:(?:https|ssh|git)://)?)(?:[^@/\s]+@)?([^:/\s]+)[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
URL_REMOTE = re.compile(r"^[a-z][a-z0-9+.-]*://(?:[^@/\s]+@)?([^:/\s]+)", re.IGNORECASE)
SCP_REMOTE = re.compile(r"^(?:[^@/:\s]+@)?([^:/\s]+):")
TOKEN_VALUE = re.compile(r"[^\s'\"]+")
OVERRIDES = ("GH_TOKEN", "GITHUB_TOKEN")
CONFIG, LOGIN_NEEDED, OVERRIDE, STATE, UNCONFIRMED, MISMATCH = 2, 3, 4, 5, 6, 7
TIMEOUT = 60
NO_ACC = "gh-switch: no GH_ACC for this project in accounts.md; account unchanged, do not switch by hand"


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


def resolve_ssh_host(host, cache={}):
    """Return the real hostname an SSH config alias resolves to, or None.

    Runs `ssh -G <host>` as an argument list without a shell: it prints the effective
    configuration and opens no connection. Any failure yields None (host not trusted).
    """
    if host in cache:
        return cache[host]
    name = None
    if not host.startswith("-"):
        try:
            done = run(["ssh", "-G", host])
            if done.returncode == 0:
                for line in done.stdout.splitlines():
                    parts = line.split()
                    if len(parts) == 2 and parts[0].lower() == "hostname":
                        name = parts[1].lower()
                        break
        except (OSError, subprocess.TimeoutExpired):
            name = None
    cache[host] = name
    return name


def is_github_host(scheme, host):
    if host.lower() == HOST:
        return True
    if scheme.startswith(("http://", "https://")):
        return False
    return resolve_ssh_host(host) == HOST


def project_repos(root):
    repos = set()
    try:
        lines = run(["git", "-C", str(root), "remote", "-v"]).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return repos
    for line in lines:
        parts = line.split()
        match = REMOTE.match(parts[1]) if len(parts) > 1 else None
        if match and is_github_host(match.group(1), match.group(2)):
            repos.add(f"{match.group(3)}/{match.group(4)}".lower())
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


ACC_VARS = ("GH_ACC", "GL_ACC")
TABLE_DIR = (".sentimony", "skills", "gh-switch")


def accounts_path(environ):
    home = environ.get("HOME", "")
    if not home or not os.path.isabs(home) or not os.path.isdir(home):
        raise Stop(CONFIG, "HOME is not usable, so accounts.md cannot be located; no fallback path is used")
    return Path(home).joinpath(*TABLE_DIR, "accounts.md")


def main_checkout(root):
    done = run(["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if done.returncode != 0:
        raise Stop(STATE, "could not read the Git common directory")
    common = Path(os.path.realpath(done.stdout.strip()))
    return common.parent if common.name == ".git" else common


def parse_table(text):
    rows, seen = [], {}
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r").strip()
        if not line or line.startswith("#"):
            continue

        def bad(why):
            return Stop(CONFIG, f"accounts.md line {number} is invalid: {why}")

        if "|" not in line:
            raise bad("expected '<path>/ | <VAR>=<value>'")
        path, _, assign = (part.strip() for part in line.partition("|"))
        if not path.startswith("/") or not path.endswith("/"):
            raise bad("the path must be absolute with a trailing slash")
        var, _, value = assign.partition("=")
        if var not in ACC_VARS:
            raise bad("unknown variable")
        pattern = LOGIN if var == "GH_ACC" else GITLAB_USER
        if not value or not pattern.fullmatch(value):
            raise bad("empty or malformed value")
        if (path, var) in seen:
            raise bad(f"duplicate row for the same path and variable (line {seen[(path, var)]})")
        seen[(path, var)] = number
        rows.append((number, path, var, value))
    return rows


def lookup(rows, main, var):
    wanted = str(main).rstrip("/") + "/"
    return next((value for _, path, name, value in rows if path == wanted and name == var), None)


def read_table(environ):
    path = accounts_path(environ)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Stop(CONFIG, "accounts.md is a symlink or not a regular file")
    try:
        return parse_table(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError):
        raise Stop(CONFIG, "accounts.md exists but cannot be read")


def read_login(root, environ):
    return lookup(read_table(environ), main_checkout(root), "GH_ACC")


LEGACY_HINT = ("gh-switch: {var} is in .env/.env but not in accounts.md; account unchanged. Ask the user to "
               "confirm the import, then run: gh_switch.py --migrate --yes")


def legacy_acc(root, var):
    text = read_env(main_checkout(root))
    return None if text is None else read_key(text, var, "<login>")


def has_legacy(root, var):
    # A duplicate or unsupported line still means the key exists; migration reports the defect.
    try:
        return legacy_acc(root, var) is not None
    except Stop:
        return True


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


def owners_of(repos):
    return {repo.split("/")[0] for repo in repos}


def sibling_logins(root, owners, environ):
    logins = set()
    rows = read_table(environ)
    try:
        siblings = [path for path in root.parent.iterdir() if path != root and (path / ".git").exists()]
    except OSError:
        return logins
    for sibling in siblings:
        if not owners & owners_of(project_repos(sibling)):
            continue
        try:
            login = lookup(rows, main_checkout(sibling), "GH_ACC")
        except Stop:
            continue
        if login:
            logins.add(login.lower())
    return logins


def infer_login(root, owners, entries, environ):
    usable = {str(entry.get("login", "")).lower(): entry["login"] for entry in entries
              if entry.get("state") == "success" and entry.get("login")}
    found = owners & usable.keys()
    if not found:
        # Organization repositories: only an account every sibling clone of the owner agrees on.
        found = sibling_logins(root, owners, environ)
        if not found <= usable.keys():
            return None
    return usable[found.pop()] if len(found) == 1 else None


def format_row(main, var, value):
    return f"{main}/ | {var}={value}"


def private_dir(environ):
    """Create or verify ~/.sentimony/skills/gh-switch component by component; refuse unsafe ones."""
    target = accounts_path(environ).parent
    current = Path(environ["HOME"])
    for name in target.relative_to(current).parts:
        current = current / name
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            os.mkdir(current, 0o700)
            info = os.lstat(current)
        except OSError:
            raise Stop(CONFIG, "the accounts.md directory cannot be inspected")
        if not stat.S_ISDIR(info.st_mode):
            raise Stop(CONFIG, f"{name} in the accounts.md path is a symlink or not a directory")
        if info.st_uid != os.getuid():
            raise Stop(CONFIG, f"{name} in the accounts.md path belongs to another user")
        if info.st_mode & 0o077:
            os.chmod(current, 0o700)
    return target


def append_row(environ, main, var, value):
    """Add '<main>/ | VAR=value' unless it is there; True when written. Atomic and exclusive."""
    row = format_row(main, var, value)
    parse_table(row)
    try:
        directory = private_dir(environ)
        table = directory / "accounts.md"
        lock = os.open(directory / "accounts.md.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError:
        raise Stop(CONFIG, "accounts.md storage cannot be prepared")
    try:
        os.fchmod(lock, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        text = ""
        try:
            handle = os.open(table, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            handle = None
        except OSError:
            raise Stop(CONFIG, "accounts.md is a symlink or cannot be opened")
        if handle is not None:
            with os.fdopen(handle, "rb") as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                    raise Stop(CONFIG, "accounts.md is not a regular file of the current user")
                try:
                    text = source.read().decode("utf-8")
                except UnicodeDecodeError:
                    raise Stop(CONFIG, "accounts.md exists but cannot be read")
        current = lookup(parse_table(text), main, var)
        if current == value:
            return False
        if current is not None:
            raise Stop(CONFIG, f"accounts.md already has {var}={current} for this project; {var}={value} not written")
        newline = "\r\n" if "\r\n" in text else "\n"
        if text and not text.endswith("\n"):
            text += newline
        data = (text + row + newline).encode("utf-8")
        temp = directory / f".accounts.md.{os.getpid()}.tmp"
        try:
            descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, table)
            folder = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
        except OSError:
            temp.unlink(missing_ok=True)
            raise Stop(CONFIG, "accounts.md could not be written")
        return True
    finally:
        os.close(lock)


def adopt_login(root, main, owners, environ):
    if any(environ.get(name) for name in OVERRIDES):
        return None
    try:
        check_gh_version()
        login = infer_login(root, owners, accounts(), environ)
    except Stop:
        return None
    if login:
        append_row(environ, main, "GH_ACC", login)
    return login or None


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
    login = read_login(root, environ)
    if login is not None:
        return select(login, environ, switch)
    if not repos:
        return None
    if has_legacy(root, "GH_ACC"):
        return LEGACY_HINT.format(var="GH_ACC")
    main = main_checkout(root)
    login = adopt_login(root, main, owners_of({normalize_target(target)} if target else repos), environ)
    if login is None:
        # Silence here used to read as "account matches", and agents then switched by hand.
        return NO_ACC
    message = select(login, environ, switch)
    tail = message[len("gh-switch: "):] if message else "account already active"
    return f"gh-switch: added to accounts.md: {format_row(main, 'GH_ACC', login)}; {tail}"


def select(login, environ, switch):
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


def ensure_gitlab(cwd, environ):
    root = project_root(cwd)
    if root is None:
        return None
    hosts = gitlab_hosts(root)
    if not hosts:
        return None
    login = lookup(read_table(environ), main_checkout(root), "GL_ACC")
    if login is None:
        message = "no GL_ACC row for this project in accounts.md; the helper does not write GL_ACC itself"
        if has_legacy(root, "GL_ACC"):
            message += ". " + LEGACY_HINT.format(var="GL_ACC")[len("gh-switch: "):]
        raise Stop(CONFIG, message)
    text = read_env(root)
    if len(hosts) > 1:
        raise Stop(CONFIG, "remotes point to more than one non-GitHub host; GL_ACC cannot pick one")
    token = None if text is None else read_key(text, "GITLAB_TOKEN", "<token>")
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
            ensure_gitlab(args.cwd, os.environ)
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
