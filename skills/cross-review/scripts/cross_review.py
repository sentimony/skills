"""Hand a plan or implementation review to the opposite agent CLI.

This module holds the loop guard and the reviewer command adapters. Every CLI
invocation is an argv list meant for subprocess with shell=False.
"""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Mapping, Optional

DEPTH_VAR = "CROSS_REVIEW_DEPTH"

# Explicit model and effort per reviewer so the reviewer's global config never wins.
DEFAULTS = {
    "codex": ("gpt-6.1-sol", "low"),
    "claude": ("claude-opus-5-5", "medium"),
}

EXIT_OK = 0
EXIT_INVALID_INPUT = 2
EXIT_NESTED = 20
EXIT_MISSING_CLI = 21
EXIT_REVIEWER_FAILED = 22
EXIT_EMPTY_RESULT = 23
EXIT_NO_SESSION = 24
EXIT_INTERRUPTED = 130

LOG_SCHEMA_VERSION = 1
ARTIFACTS = ("brief.md", "review.md", "session.txt", "run.log")

# Read-only policy for the Claude reviewer: built-ins limited to Read/Grep/Glob,
# no MCP, no skills or slash commands, no user settings (removes server-side advisor).
_CLAUDE_POLICY = (
    "--permission-mode", "default",
    "--tools", "Read,Grep,Glob",
    "--allowedTools", "Read,Grep,Glob",
    "--disallowedTools", "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--safe-mode",
    "--setting-sources", "project",
)

_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_UUID_RE = re.compile(r"\A%s\Z" % _UUID)
_SESSION_RE = re.compile(r"session id:\s*(%s)\s*$" % _UUID, re.MULTILINE)


class CrossReviewError(Exception):
    """Error that maps to a specific process exit code."""

    def __init__(self, code: int, message: str, run_dir: Optional[Path] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        # Set once a run directory exists, so callers can still find partial artifacts.
        self.run_dir = run_dir


def ensure_not_nested(env: Mapping[str, str]) -> None:
    """Refuse to run inside a reviewer process; an empty value still counts."""
    if DEPTH_VAR in env:
        raise CrossReviewError(
            EXIT_NESTED,
            "You are already the cross-reviewer; do the review yourself "
            "instead of delegating it again.",
        )


def reviewer_environment(env: Mapping[str, str]) -> dict:
    """Return a copy of env for the reviewer child with the depth marker set."""
    child = dict(env)
    child[DEPTH_VAR] = "1"
    return child


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CrossReviewError(EXIT_INVALID_INPUT, "%s must be a non-empty string" % name)


def build_run_command(reviewer: str, repo: Path, run_dir: Path,
                      model: str, effort: str, session_id: str) -> list:
    """Build the argv for a fresh review run.

    Codex reads the brief from stdin ("-") and writes the final message to
    run_dir/review.md. Claude reads the brief from stdin, runs with cwd=repo,
    and uses the runner-generated session_id.
    """
    if reviewer not in DEFAULTS:
        raise CrossReviewError(EXIT_INVALID_INPUT,
                               "reviewer must be one of: %s" % ", ".join(sorted(DEFAULTS)))
    _require_text("model", model)
    _require_text("effort", effort)
    if not Path(repo).is_dir():
        raise CrossReviewError(EXIT_INVALID_INPUT, "repo is not a directory: %s" % repo)

    if reviewer == "codex":
        # effort becomes a TOML string inside -c; reject characters that escape it.
        if any(ch in effort for ch in '"\\\n\r'):
            raise CrossReviewError(EXIT_INVALID_INPUT, "effort contains invalid characters")
        return [
            "codex", "exec", "-s", "read-only", "-m", model,
            "-c", 'model_reasoning_effort="%s"' % effort,
            "-C", str(repo), "-o", str(Path(run_dir) / "review.md"), "-",
        ]

    if not isinstance(session_id, str) or not _UUID_RE.match(session_id):
        raise CrossReviewError(EXIT_INVALID_INPUT, "session_id must be a UUID")
    return (["claude", "-p", "--model", model, "--effort", effort]
            + list(_CLAUDE_POLICY)
            + ["--session-id", session_id])


def parse_codex_session(log: str) -> Optional[str]:
    """Return the first valid UUID printed as 'session id: <uuid>', else None."""
    match = _SESSION_RE.search(log or "")
    return match.group(1) if match else None


def _timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _ensure_private_dir(path: Path) -> None:
    """Accept only a real directory owned by us with mode 0700."""
    st = os.lstat(path)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise CrossReviewError(EXIT_INVALID_INPUT, "unsafe run root (not a real directory): %s" % path)
    if st.st_uid != os.getuid():
        raise CrossReviewError(EXIT_INVALID_INPUT, "unsafe run root (foreign owner): %s" % path)
    if stat.S_IMODE(st.st_mode) != 0o700:
        raise CrossReviewError(EXIT_INVALID_INPUT,
                               "unsafe run root (mode %o, expected 700): %s"
                               % (stat.S_IMODE(st.st_mode), path))


def _runs_root() -> Path:
    root = Path(tempfile.gettempdir()).absolute() / "cross-review"
    try:
        os.mkdir(root, 0o700)
    except FileExistsError:
        pass
    _ensure_private_dir(root)
    return root


def _create_run_dir() -> Path:
    root = _runs_root()
    base = _timestamp()
    for counter in range(1000):
        candidate = root / (base if counter == 0 else "%s-%d" % (base, counter))
        try:
            os.mkdir(candidate, 0o700)
        except FileExistsError:
            continue
        # mkdir mode is filtered by umask; set it explicitly and re-verify.
        os.chmod(candidate, 0o700)
        _ensure_private_dir(candidate)
        return candidate
    raise CrossReviewError(EXIT_INVALID_INPUT, "too many runs for timestamp %s" % base)


def _create_private_file(path: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    os.fchmod(fd, 0o600)
    return fd


def _read_brief(brief: Path) -> bytes:
    try:
        data = Path(brief).read_bytes()
    except OSError as exc:
        raise CrossReviewError(EXIT_INVALID_INPUT, "cannot read brief %s: %s" % (brief, exc))
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise CrossReviewError(EXIT_INVALID_INPUT, "brief is not valid UTF-8: %s" % brief)
    return data


def _cli_version(executable: str, env: Mapping[str, str]) -> str:
    try:
        proc = subprocess.run([executable, "--version"], stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=dict(env), check=False)
    except OSError:
        return "unknown"
    lines = proc.stdout.decode("utf-8", "replace").strip().splitlines()
    return lines[0].strip() if proc.returncode == 0 and lines else "unknown"


def _tighten(path: Path) -> None:
    """Re-check an artifact after the reviewer ran; the CLI may have replaced it."""
    st = os.lstat(path)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise CrossReviewError(EXIT_REVIEWER_FAILED, "unsafe artifact after run: %s" % path)
    if stat.S_IMODE(st.st_mode) != 0o600:
        os.chmod(path, 0o600)


def _log(log_fd: int, line: str) -> None:
    os.write(log_fd, ("cross-review: %s\n" % line).encode("utf-8"))


def run_review(reviewer: str, repo: Path, brief: Path, model: Optional[str],
               effort: Optional[str], env: Mapping[str, str]) -> Path:
    """Run one review and return the absolute run directory.

    Raises CrossReviewError with an exit code; run_dir is attached once it exists.
    """
    ensure_not_nested(env)
    if reviewer not in DEFAULTS:
        raise CrossReviewError(EXIT_INVALID_INPUT,
                               "reviewer must be one of: %s" % ", ".join(sorted(DEFAULTS)))
    default_model, default_effort = DEFAULTS[reviewer]
    model = default_model if model is None else model
    effort = default_effort if effort is None else effort
    repo = Path(repo).resolve()
    session_id = str(uuid.uuid4()) if reviewer == "claude" else None
    # Validate everything (including argv) before touching the filesystem.
    build_run_command(reviewer, repo, Path("/"), model, effort, session_id or "")
    brief_data = _read_brief(brief)

    executable = shutil.which(reviewer)
    if executable is None:
        raise CrossReviewError(EXIT_MISSING_CLI, "%s CLI not found on PATH" % reviewer)

    child_env = reviewer_environment(env)
    run_dir = _create_run_dir()
    paths = {name: run_dir / name for name in ARTIFACTS}
    fds = {}
    proc = None
    try:
        for name in ARTIFACTS:
            fds[name] = _create_private_file(paths[name])
        os.write(fds["brief.md"], brief_data)
        header = {
            "schema_version": LOG_SCHEMA_VERSION,
            "reviewer": reviewer,
            "mode": "unspecified",
            "repo": str(repo),
            "model": model,
            "effort": effort,
            "cli_version": _cli_version(executable, child_env),
        }
        os.write(fds["run.log"], (json.dumps(header) + "\n").encode("utf-8"))

        argv = build_run_command(reviewer, repo, run_dir, model, effort, session_id)
        stdout_fd = fds["run.log"] if reviewer == "codex" else fds["review.md"]
        with open(paths["brief.md"], "rb") as stdin:
            try:
                proc = subprocess.Popen(argv, stdin=stdin, stdout=stdout_fd,
                                        stderr=fds["run.log"], cwd=str(repo),
                                        env=child_env, shell=False, umask=0o077)
            except (FileNotFoundError, PermissionError) as exc:
                _log(fds["run.log"], "spawn failed: %s" % exc)
                raise CrossReviewError(EXIT_MISSING_CLI,
                                       "%s CLI could not be started: %s" % (reviewer, exc),
                                       run_dir)
            returncode = proc.wait()
        _log(fds["run.log"], "exit status %d" % returncode)

        if reviewer == "codex":
            session_id = parse_codex_session(paths["run.log"].read_text("utf-8", "replace"))
        if session_id:
            os.write(fds["session.txt"], (session_id + "\n").encode("utf-8"))
        else:
            _log(fds["run.log"], "session id not found; resume unavailable")

        for name in ARTIFACTS:
            if os.path.lexists(paths[name]):
                _tighten(paths[name])

        if returncode != 0:
            raise CrossReviewError(EXIT_REVIEWER_FAILED,
                                   "%s exited with status %d" % (reviewer, returncode), run_dir)
        try:
            review = paths["review.md"].read_text("utf-8", "replace")
        except FileNotFoundError:
            review = ""
        if not review.strip():
            raise CrossReviewError(EXIT_EMPTY_RESULT, "%s returned an empty review" % reviewer,
                                   run_dir)
        return run_dir
    except KeyboardInterrupt:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        if "run.log" in fds:
            _log(fds["run.log"], "interrupted; partial artifacts kept")
        raise CrossReviewError(EXIT_INTERRUPTED, "interrupted", run_dir)
    except CrossReviewError as exc:
        exc.run_dir = exc.run_dir or run_dir
        raise
    finally:
        for fd in fds.values():
            os.close(fd)


def _print_run(run_dir: Path) -> None:
    print("run_dir: %s" % run_dir)
    for name in ARTIFACTS:
        print("%s: %s" % (name, run_dir / name))
    sys.stdout.flush()


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CrossReviewError(EXIT_INVALID_INPUT, message)


def main(argv=None) -> int:
    env = os.environ
    try:
        # The loop guard runs before argument parsing, CLI lookup, and run-dir creation.
        ensure_not_nested(env)
        parser = _Parser(prog="cross_review.py")
        sub = parser.add_subparsers(dest="command", required=True)
        run = sub.add_parser("run", help="start a fresh review")
        run.add_argument("--reviewer", required=True)
        run.add_argument("--repo", required=True, type=Path)
        run.add_argument("--brief", required=True, type=Path)
        run.add_argument("--model")
        run.add_argument("--effort")
        args = parser.parse_args(argv)
        run_dir = run_review(args.reviewer, args.repo, args.brief, args.model,
                             args.effort, env)
    except CrossReviewError as exc:
        if exc.run_dir is not None:
            _print_run(exc.run_dir)
        print("cross-review: %s" % exc.message, file=sys.stderr)
        return exc.code
    except KeyboardInterrupt:
        print("cross-review: interrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    _print_run(run_dir)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
