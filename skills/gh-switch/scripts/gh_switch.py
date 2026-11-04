#!/usr/bin/env python3
"""
Switch the GitHub CLI to the account a project names in accounts.md before a gh operation,
and check that the project's GitLab token belongs to the account it names.

Usage:
    python3 scripts/gh_switch.py [--cwd PATH] [--target OWNER/REPO] [--no-switch]
    python3 scripts/gh_switch.py --gitlab [--cwd PATH]
    python3 scripts/gh_switch.py --migrate [--yes] [--cwd PATH]

The mapping lives in ~/.sentimony/skills/gh-switch/accounts.md, one row per project and
variable: "<main checkout>/ | GH_ACC=<login>" or "... | GL_ACC=<user>". Without a GH_ACC row
the helper appends one (atomically, under a lock) when the account is unambiguous: the one
remote owner that is a logged-in login, or the GH_ACC every sibling clone of the same owner
has in the table. GITLAB_TOKEN stays in the project's .env/.env. --migrate lists (and with
--yes writes) the old GH_ACC and GL_ACC lines of .env/.env as rows. Exit codes: 0 proceed,
2 configuration error, 3 login needed, 4 token override, 5 gh, auth state, or GitLab API
problem, 6 switch not confirmed, 7 GitLab token of another account. Prints one
"gh-switch: <from> -> <to>" line after a confirmed switch. With --no-switch it checks GH_ACC
the same way but never switches, and prints the per-command token prefix instead.
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
    common = Path(os.path.realpath(done.stdout.rstrip("\n")))
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
    folder = open_private_dir(environ, create=False)
    if folder is None:
        return []
    try:
        try:
            handle = os.open("accounts.md", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
        except FileNotFoundError:
            return []
        except OSError:
            raise Stop(CONFIG, "accounts.md is a symlink or cannot be opened")
        info = os.fstat(handle)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            os.close(handle)
            raise Stop(CONFIG, "accounts.md is not a regular file of the current user")
        with os.fdopen(handle, "rb") as source:
            try:
                return parse_table(source.read().decode("utf-8"))
            except (OSError, UnicodeDecodeError):
                raise Stop(CONFIG, "accounts.md exists but cannot be read")
    finally:
        os.close(folder)


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


def open_private_dir(environ, create=True):
    """Return an fd of ~/.sentimony/skills/gh-switch, verified one component at a time.

    Each step uses the parent's fd and O_NOFOLLOW, so a component swapped for a symlink after
    the check cannot redirect later operations. Without create, a missing component gives None.
    """
    home = Path(accounts_path(environ).parents[len(TABLE_DIR)])
    try:
        descriptor = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        raise Stop(CONFIG, "HOME is not usable, so accounts.md cannot be located; no fallback path is used")
    try:
        for name in TABLE_DIR:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                except OSError:
                    raise Stop(CONFIG, f"{name} in the accounts.md path cannot be created")
            try:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            except FileNotFoundError:
                if create:
                    raise Stop(CONFIG, f"{name} in the accounts.md path cannot be opened")
                os.close(descriptor)
                return None
            except OSError:
                raise Stop(CONFIG, f"{name} in the accounts.md path is a symlink or not a directory")
            os.close(descriptor)
            descriptor = child
            info = os.fstat(descriptor)
            if info.st_uid != os.getuid():
                raise Stop(CONFIG, f"{name} in the accounts.md path belongs to another user")
            if create and info.st_mode & 0o077:
                os.fchmod(descriptor, 0o700)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def own_regular(descriptor, what):
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        raise Stop(CONFIG, f"{what} is not a private regular file of the current user")
    if info.st_mode & 0o177:
        os.fchmod(descriptor, 0o600)


def acquire_lock(folder):
    """Open accounts.md.lock and hold LOCK_EX on the inode the name still points to."""
    for _ in range(20):
        try:
            lock = os.open("accounts.md.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600,
                           dir_fd=folder)
        except FileNotFoundError:
            continue  # macOS reports a spurious ENOENT when several processes create the file at once
        except OSError:
            raise Stop(CONFIG, "accounts.md.lock cannot be opened")
        try:
            own_regular(lock, "accounts.md.lock")
            fcntl.flock(lock, fcntl.LOCK_EX)
            named = os.stat("accounts.md.lock", dir_fd=folder, follow_symlinks=False)
            held = os.fstat(lock)
            if (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino):
                return lock
        except FileNotFoundError:
            pass
        except BaseException:
            os.close(lock)
            raise
        os.close(lock)
    raise Stop(CONFIG, "accounts.md.lock keeps changing; try again")


def append_rows(environ, main, items):
    """Add '<main>/ | VAR=value' for every (var, value) not yet there, all or none, in one atomic write.

    Returns one bool per item: True when written, False when the same row already existed.
    """
    rows = [(var, value, format_row(main, var, value)) for var, value in items]
    for _, _, row in rows:
        parse_table(row)
    folder = open_private_dir(environ)
    lock = None
    try:
        lock = acquire_lock(folder)
        text = ""
        try:
            handle = os.open("accounts.md", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
        except FileNotFoundError:
            handle = None
        except OSError:
            raise Stop(CONFIG, "accounts.md is a symlink or cannot be opened")
        if handle is not None:
            try:
                own_regular(handle, "accounts.md")
            except BaseException:
                os.close(handle)
                raise
            with os.fdopen(handle, "rb") as source:
                try:
                    text = source.read().decode("utf-8")
                except UnicodeDecodeError:
                    raise Stop(CONFIG, "accounts.md exists but cannot be read")
        parsed = parse_table(text)
        written, pending = [], []
        for var, value, row in rows:
            current = lookup(parsed, main, var)
            if current is not None and current != value:
                raise Stop(CONFIG, f"accounts.md already has {var}={current} for this project; {var}={value} "
                                   "not written, nothing was written")
            written.append(current is None)
            if current is None:
                pending.append(row)
        if not pending:
            return written
        newline = "\r\n" if "\r\n" in text else "\n"
        if text and not text.endswith("\n"):
            text += newline
        temp = f".accounts.md.{os.getpid()}.{os.urandom(4).hex()}.tmp"
        created = False
        try:
            descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=folder)
            created = True
            with os.fdopen(descriptor, "wb") as out:
                out.write((text + "".join(row + newline for row in pending)).encode("utf-8"))
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, "accounts.md", src_dir_fd=folder, dst_dir_fd=folder)
            created = False
            os.fsync(folder)
        except OSError:
            raise Stop(CONFIG, "accounts.md could not be written")
        finally:
            if created:
                os.unlink(temp, dir_fd=folder)
        return written
    finally:
        if lock is not None:
            os.close(lock)
        os.close(folder)


def append_row(environ, main, var, value):
    return append_rows(environ, main, [(var, value)])[0]


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


def migrate(cwd, environ, confirmed):
    root = project_root(cwd)
    if root is None:
        raise Stop(CONFIG, "not a Git project; nothing to migrate")
    main = main_checkout(root)
    found = []
    for var in ACC_VARS:
        value = legacy_acc(root, var)
        if value is None:
            continue
        try:
            parse_table(format_row(main, var, value))
        except Stop:
            raise Stop(CONFIG, f"{var} in .env/.env is empty or malformed; nothing imported") from None
        found.append((var, value))
    if not found:
        return ["gh-switch: nothing to migrate"]
    rows = read_table(environ)
    for var, value in found:
        current = lookup(rows, main, var)
        if current is not None and current != value:
            raise Stop(CONFIG, f"accounts.md already has {var}={current} for this project, .env/.env has "
                               f"{value}; nothing imported")
    if not confirmed:
        return [f"gh-switch: would add: {format_row(main, var, value)}" for var, value in found]
    written = append_rows(environ, main, found)
    return [f"gh-switch: {'added to' if new else 'already in'} accounts.md: {format_row(main, var, value)}"
            for (var, value), new in zip(found, written)]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Select the gh account named by GH_ACC, or with --gitlab check the "
                                                 "GitLab token owner against GL_ACC, in the project's .env/.env.")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--target", help="OWNER/REPO the gh command addresses explicitly (--repo)")
    parser.add_argument("--no-switch", action="store_true",
                        help="check GH_ACC without gh auth switch and print the per-command token prefix")
    parser.add_argument("--gitlab", action="store_true",
                        help="check that GITLAB_TOKEN belongs to GL_ACC instead of selecting the gh account")
    parser.add_argument("--migrate", action="store_true",
                        help="import GH_ACC and GL_ACC from .env/.env into accounts.md (lists unless --yes)")
    parser.add_argument("--yes", action="store_true", help="with --migrate: write the rows after the user confirmed")
    args = parser.parse_args(argv)
    if args.yes and not args.migrate:
        parser.error("--yes needs --migrate")
    if args.migrate and (args.gitlab or args.target or args.no_switch):
        parser.error("--migrate cannot be combined with --gitlab, --target or --no-switch")
    try:
        if args.migrate:
            for line in migrate(args.cwd, os.environ, args.yes):
                print(line)
        elif args.gitlab:
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
