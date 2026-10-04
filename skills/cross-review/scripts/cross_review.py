"""Hand a plan or implementation review to the opposite agent CLI.

This module holds the loop guard and the reviewer command adapters. Every CLI
invocation is an argv list meant for subprocess with shell=False.
"""

import argparse
import fcntl
import json
import os
import re
import shutil
import signal
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
EXIT_INTERRUPTED = 130  # SIGINT or SIGTERM

LOG_SCHEMA_VERSION = 1
ARTIFACTS = ("brief.md", "review.md", "session.txt", "run.log")
USAGE_FILE = "usage.json"
USAGE_SCHEMA_VERSION = 1
# Claude --output-format json lands here first; review.md gets the parsed answer.
CLAUDE_RAW = "claude-output.json"

# USD per 1M tokens (input, cached input, output), standard tier.
# Source: https://developers.openai.com/api/docs/pricing
PRICES_AS_OF = "2026-10-04"
PRICES = {
    "gpt-6.1-sol": (2.00, 0.10, 10.00),
    "gpt-6-sol": (2.00, 0.20, 10.00),
    "gpt-6-astra": (10.00, 1.00, 50.00),
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-5.3-codex": (1.75, 0.175, 14.00),
}

# input includes cached_input and cache_write; output includes reasoning.
TOKEN_KEYS = ("input", "cached_input", "cache_write", "output", "reasoning")
_CODEX_USAGE_FIELDS = (
    ("input", "input_tokens"),
    ("cached_input", "cached_input_tokens"),
    ("cache_write", "cache_write_input_tokens"),
    ("output", "output_tokens"),
    ("reasoning", "reasoning_output_tokens"),
)
_SKILL_PATH_RE = re.compile(r"([A-Za-z0-9._-]+)/SKILL\.md\b")

# Read-only policy for the Claude reviewer: built-ins limited to Read/Grep/Glob,
# no MCP, no skills or slash commands, and no settings files at all. --restricted
# ignores user, project, and local settings and confines file tools to the repo;
# an empty --setting-sources list states the same intent explicitly. Settings from
# the reviewed repository could otherwise add the server-side advisor tool, hooks,
# or environment variables.
_CLAUDE_POLICY = (
    "--permission-mode", "default",
    "--tools", "Read,Grep,Glob",
    "--allowedTools", "Read,Grep,Glob",
    "--disallowedTools", "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--safe-mode",
    "--restricted",
    "--setting-sources", "",
)

# Codex sandbox tokens. exec resume has no -s and would inherit the user's global
# sandbox, so read-only is forced through a config override there.
_CODEX_RUN_SANDBOX = ("-s", "read-only")
_CODEX_RESUME_SANDBOX = ("-c", 'sandbox_mode="read-only"')

_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_UUID_RE = re.compile(r"\A%s\Z" % _UUID)


class _Terminated(BaseException):
    """Raised from the SIGTERM handler so termination unwinds like Ctrl-C."""


def _raise_terminated(signum, frame):
    raise _Terminated()


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


def _validate_common(reviewer: str, model: str, effort: str) -> None:
    if reviewer not in DEFAULTS:
        raise CrossReviewError(EXIT_INVALID_INPUT,
                               "reviewer must be one of: %s" % ", ".join(sorted(DEFAULTS)))
    _require_text("model", model)
    _require_text("effort", effort)
    # effort becomes a TOML string inside Codex -c; reject characters that escape it.
    if reviewer == "codex" and any(ch in effort for ch in '"\\\n\r'):
        raise CrossReviewError(EXIT_INVALID_INPUT, "effort contains invalid characters")
    # An option-like value would be read by the CLI as a flag.
    for name, value in (("model", model), ("effort", effort)):
        if value.startswith("-"):
            raise CrossReviewError(EXIT_INVALID_INPUT,
                                   "%s looks like a command-line option" % name)


def _is_uuid(value) -> bool:
    return isinstance(value, str) and bool(_UUID_RE.match(value))


# Variables that would point git at another repository than the one under review.
_GIT_REDIRECT_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                      "GIT_CEILING_DIRECTORIES", "GIT_INDEX_FILE")


def _git_line(repo: Path, *args: str) -> Optional[str]:
    """Return the first stdout line of a git command in repo, or None on any failure."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT_VARS}
    try:
        proc = subprocess.run(["git", "-C", str(repo)] + list(args),
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, env=env, check=False)
    except OSError:
        return None
    lines = os.fsdecode(proc.stdout).splitlines()
    if proc.returncode != 0 or not lines or not lines[0].strip():
        return None
    return lines[0]


def _on_disk_path(path: Path) -> Optional[str]:
    """Return the path as the file system spells it (case on macOS), if available."""
    if not hasattr(fcntl, "F_GETPATH"):
        return None
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return None
    try:
        raw = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))
    except OSError:
        return None
    finally:
        os.close(fd)
    return os.fsdecode(raw.split(b"\0", 1)[0]) or None


def _find_dot_git(repo: Path) -> Optional[Path]:
    for directory in [repo] + list(repo.parents):
        candidate = directory / ".git"
        if os.path.lexists(candidate):
            return candidate
    return None


def _parse_dot_git(dot_git: Path):
    """Return (toplevel, common_dir) from a .git entry without running git, else None."""
    top = dot_git.parent
    if dot_git.is_dir():
        return top, dot_git.resolve()
    try:
        text = dot_git.read_text("utf-8").strip()
    except (OSError, ValueError):
        return None
    if not text.startswith("gitdir:"):
        return None
    git_dir = (top / text[len("gitdir:"):].strip()).resolve()
    common = git_dir
    try:
        pointer = (git_dir / "commondir").read_text("utf-8").strip()
    except FileNotFoundError:
        pointer = ""
    except (OSError, ValueError):
        return None
    if pointer:
        common = (git_dir / pointer).resolve()
    return top, common


def codex_untrusted_paths(repo: Path) -> list:
    """Paths whose Codex project config must not load.

    A trusted path, or a worktree of a trusted repository, would otherwise load
    .codex/config.toml from the reviewed repository. The set holds the resolved
    repo and its on-disk spelling, the worktree root, the Git common directory's
    parent (the main worktree root for a normal repository), and the common
    directory itself when it is not named .git (bare or separate layouts). Paths
    come from git and from parsing .git directly; a .git entry that yields no
    path at all fails closed.
    """
    repo = Path(repo).resolve()
    paths = [str(repo)]
    on_disk = _on_disk_path(repo)
    if on_disk:
        paths.append(on_disk)

    found = []
    top = _git_line(repo, "rev-parse", "--show-toplevel")
    common = _git_line(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        # Git before 2.31 has no --path-format; a relative answer is relative to repo.
        common = _git_line(repo, "rev-parse", "--git-common-dir")
        common = str(repo / common) if common else None
    if top:
        found.append((Path(top).resolve(), None))
    if common:
        found.append((None, Path(common).resolve()))

    dot_git = _find_dot_git(repo)
    parsed = _parse_dot_git(dot_git) if dot_git is not None else None
    if parsed:
        found.append(parsed)
    if dot_git is not None and not found:
        raise CrossReviewError(
            EXIT_INVALID_INPUT,
            "cannot determine the Git layout of %s (%s is unreadable); refusing to run "
            "the Codex reviewer without marking it untrusted" % (repo, dot_git))

    for top_path, common_path in found:
        if top_path is not None:
            paths.append(str(top_path))
        if common_path is not None:
            paths.append(str(common_path.parent))
            if common_path.name != ".git":
                paths.append(str(common_path))
    return list(dict.fromkeys(paths))


def _codex_untrusted_override(paths) -> str:
    """Build the -c value that marks every path as an untrusted Codex project."""
    entries = []
    for path in paths:
        if any(ord(ch) < 0x20 or ch == "\x7f" or 0xD800 <= ord(ch) <= 0xDFFF
               for ch in path):
            raise CrossReviewError(EXIT_INVALID_INPUT,
                                   "repository path contains control characters "
                                   "or undecodable bytes")
        # json.dumps yields a valid TOML basic string for a path without control
        # characters; ensure_ascii=False keeps non-BMP characters out of surrogate escapes.
        entries.append('%s={trust_level="untrusted"}' % json.dumps(path, ensure_ascii=False))
    if not entries:
        raise CrossReviewError(EXIT_INVALID_INPUT, "no repository path to mark untrusted")
    return "projects={%s}" % ", ".join(entries)


def build_run_command(reviewer: str, repo: Path, run_dir: Path,
                      model: str, effort: str, session_id: str,
                      untrusted=None) -> list:
    """Build the argv for a fresh review run.

    Codex reads the brief from stdin ("-") and writes the final message to
    run_dir/review.md. Claude reads the brief from stdin, runs with cwd=repo,
    and uses the runner-generated session_id. untrusted lists the paths forced to an
    untrusted Codex project; None computes them from repo.
    """
    _validate_common(reviewer, model, effort)
    if not Path(repo).is_dir():
        raise CrossReviewError(EXIT_INVALID_INPUT, "repo is not a directory: %s" % repo)

    if reviewer == "codex":
        if untrusted is None:
            untrusted = codex_untrusted_paths(repo)
        return (["codex", "exec"] + list(_CODEX_RUN_SANDBOX)
                + ["-m", model, "-c", 'model_reasoning_effort="%s"' % effort,
                   "-c", _codex_untrusted_override(untrusted),
                   "-C", str(repo), "-o", str(Path(run_dir) / "review.md"), "-"])

    if not _is_uuid(session_id):
        raise CrossReviewError(EXIT_INVALID_INPUT, "session_id must be a UUID")
    return (["claude", "-p", "--model", model, "--effort", effort]
            + list(_CLAUDE_POLICY)
            + ["--session-id", session_id])


def build_resume_command(reviewer: str, repo: Path, run_dir: Path,
                         model: str, effort: str, session_id: str,
                         untrusted=None) -> list:
    """Build the argv for a follow-up in an existing reviewer session.

    The caller runs it with cwd=repo. Codex resume has no -s/-C flags and would
    inherit a permissive sandbox, so read-only is forced through -c sandbox_mode.
    Never uses --last: the session is always the explicit UUID. untrusted works as
    in build_run_command.
    """
    _validate_common(reviewer, model, effort)
    if not _is_uuid(session_id):
        raise CrossReviewError(EXIT_NO_SESSION, "session id is missing or not a UUID")

    if reviewer == "codex":
        if untrusted is None:
            untrusted = codex_untrusted_paths(repo)
        return (["codex", "exec", "resume", "-m", model,
                 "-c", 'model_reasoning_effort="%s"' % effort]
                + list(_CODEX_RESUME_SANDBOX)
                + ["-c", _codex_untrusted_override(untrusted)]
                + ["-o", str(Path(run_dir) / "review.md"), session_id, "-"])

    return (["claude", "-p", "--model", model, "--effort", effort]
            + list(_CLAUDE_POLICY)
            + ["--resume", session_id])


def _count(mapping, key) -> int:
    """Read a count already checked by _valid_counts; absent or null means 0."""
    value = mapping.get(key)
    return 0 if value is None else value


def _valid_counts(mapping, required, optional) -> bool:
    """True when every required count is present and every present count is valid.

    A valid count is a non-negative int. An optional count may be absent or null,
    but a present malformed value makes the whole record unknown instead of 0.
    """
    def ok(value):
        return type(value) is int and value >= 0

    return (isinstance(mapping, dict)
            and all(ok(mapping.get(key)) for key in required)
            and all(mapping.get(key) is None or ok(mapping[key]) for key in optional))


def _zero_tokens() -> dict:
    return {key: 0 for key in TOKEN_KEYS}


def parse_codex_events(log: str) -> dict:
    """Read the codex --json event stream mixed into run.log.

    Lines that are not JSON objects (stderr diagnostics, the runner header) are
    skipped. Only the first thread.started sets the session, so an id that shows up
    later cannot replace it; message text is JSON-escaped inside one line and never
    forms an event. Skills are the directory names of SKILL.md files that a shell
    command touched. tokens is None when no turn.completed carried usage, or when
    one of them lacked valid input/output counts or held a malformed optional count;
    usage_error then says why.
    """
    session, seen_thread, tokens, turns, skills = None, False, _zero_tokens(), 0, set()
    usage_error = None
    for line in (log or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "thread.started" and not seen_thread:
            seen_thread = True
            thread = event.get("thread_id")
            session = thread if _is_uuid(thread) else None
        elif kind == "turn.completed":
            usage = event.get("usage")
            # input and output are required; cache and reasoning counts may be absent.
            if not _valid_counts(usage, ("input_tokens", "output_tokens"),
                                 ("cached_input_tokens", "cache_write_input_tokens",
                                  "reasoning_output_tokens")):
                usage_error = "turn.completed with missing or invalid token counts"
                continue
            turns += 1
            for key, field in _CODEX_USAGE_FIELDS:
                tokens[key] += _count(usage, field)
        elif kind == "item.completed" and isinstance(event.get("item"), dict):
            item = event["item"]
            if item.get("type") == "command_execution":
                skills.update(_SKILL_PATH_RE.findall(str(item.get("command", ""))))
    return {"session": session,
            "tokens": tokens if turns and usage_error is None else None,
            "skills": sorted(skills), "usage_error": usage_error}


def parse_codex_session(log: str) -> Optional[str]:
    """Return the session id of the first thread.started event, else None."""
    return parse_codex_events(log)["session"]


def codex_cost(model: str, tokens: Mapping[str, int]) -> Optional[float]:
    """Approximate USD for a Codex run from PRICES; None for a model not in the table.

    input already includes cached tokens and output already includes reasoning
    tokens, so neither subset is added again.
    """
    price = PRICES.get(model)
    if price is None:
        return None
    input_price, cached_price, output_price = price
    uncached = max(tokens["input"] - tokens["cached_input"], 0)
    total = (uncached * input_price + tokens["cached_input"] * cached_price
             + tokens["output"] * output_price) / 1_000_000
    return round(total, 4)


def parse_claude_output(raw: str):
    """Split claude --output-format json into (review text, usage), or (None, None).

    usage is {"tokens": dict or None, "cost_usd": float or None}. A failure while
    reading the metrics never costs the review text: usage then holds two Nones.
    """
    try:
        payload = json.loads(raw)
    except (ValueError, RecursionError):
        return None, None
    if not isinstance(payload, dict) or not isinstance(payload.get("result"), str):
        return None, None
    try:
        usage = _claude_usage(payload)
    except Exception:  # metrics must never fail a review
        usage = {"tokens": None, "cost_usd": None}
    return payload["result"], usage


def _claude_usage(payload: dict) -> dict:
    """Sum every model in modelUsage; cost is the CLI-reported total_cost_usd at list price."""
    tokens = None
    models = payload.get("modelUsage")
    if isinstance(models, dict) and models:
        tokens = _zero_tokens()
        for entry in models.values():
            # inputTokens and outputTokens are required; cache and thinking may be absent.
            if not _valid_counts(entry, ("inputTokens", "outputTokens"),
                                 ("cacheReadInputTokens", "cacheCreationInputTokens",
                                  "thinkingTokens")):
                tokens = None
                break
            cached = _count(entry, "cacheReadInputTokens")
            written = _count(entry, "cacheCreationInputTokens")
            tokens["input"] += _count(entry, "inputTokens") + cached + written
            tokens["cached_input"] += cached
            tokens["cache_write"] += written
            tokens["output"] += _count(entry, "outputTokens")
            tokens["reasoning"] += _count(entry, "thinkingTokens")
    cost = payload.get("total_cost_usd")
    # The range check also rejects NaN and Infinity, which json.loads accepts.
    if type(cost) not in (int, float) or not 0 <= cost < float("inf"):
        cost = None
    return {"tokens": tokens, "cost_usd": None if cost is None else round(cost, 4)}


def _valid_total(total) -> bool:
    if not isinstance(total, dict):
        return False
    tokens, cost = total.get("tokens"), total.get("cost_usd")
    return (isinstance(tokens, dict)
            and all(type(tokens.get(key)) is int and tokens[key] >= 0 for key in TOKEN_KEYS)
            and (cost is None or (type(cost) in (int, float) and cost >= 0))
            and type(total.get("runs")) is int and total["runs"] >= 1
            and type(total.get("complete")) is bool)


def _session_total(tokens, cost_usd, previous_run, previous) -> dict:
    complete = tokens is not None and cost_usd is not None
    total_tokens = dict(tokens) if tokens is not None else _zero_tokens()
    total_cost, runs = cost_usd, 1
    if previous_run is not None:
        prior = previous.get("session_total") if isinstance(previous, dict) else None
        if _valid_total(prior):
            for key in TOKEN_KEYS:
                total_tokens[key] += prior["tokens"][key]
            if prior["cost_usd"] is not None:
                total_cost = (total_cost or 0.0) + prior["cost_usd"]
            runs += prior["runs"]
            complete = complete and prior["complete"]
        else:
            complete = False
    return {"tokens": total_tokens,
            "cost_usd": None if total_cost is None else round(total_cost, 4),
            "runs": runs, "complete": complete}


def build_usage(reviewer: str, model: str, effort: str, tokens, cost_usd, skills,
                previous_run=None, previous=None) -> dict:
    """Assemble the usage.json record of one run.

    cost_usd is the CLI-reported cost and is used for claude only; the codex cost
    comes from PRICES. previous is the parsed usage.json of previous_run, or None
    when it is missing or unreadable, which marks the session total incomplete.
    """
    if reviewer == "codex":
        cost_usd = codex_cost(model, tokens) if tokens is not None else None
        basis = "price-table" if cost_usd is not None else "unknown"
        skills, note = sorted(skills), "detected from SKILL.md reads"
    else:
        basis = "cli-list" if cost_usd is not None else "unknown"
        skills, note = [], "disabled by policy"
    return {
        "schema_version": USAGE_SCHEMA_VERSION,
        "reviewer": reviewer,
        "model": model,
        "effort": effort,
        "skills": skills,
        "skills_note": note,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "cost_basis": basis,
        "prices_as_of": PRICES_AS_OF if basis == "price-table" else None,
        "previous_run": None if previous_run is None else str(previous_run),
        "session_total": _session_total(tokens, cost_usd, previous_run, previous),
    }


def format_usage_line(usage: Mapping) -> str:
    """One ASCII summary line for stdout; missing data reads as unknown."""
    skills = ",".join(usage.get("skills") or []) or "none"
    if usage.get("reviewer") == "claude":
        skills += " (disabled by policy)"
    parts = ["usage:", str(usage.get("reviewer")), str(usage.get("model")),
             "effort=%s" % usage.get("effort"), "skills=%s" % skills]
    tokens = usage.get("tokens")
    if isinstance(tokens, dict):
        parts.append("tokens in=%d (cached %d) out=%d (reasoning %d)" % (
            tokens["input"], tokens["cached_input"], tokens["output"], tokens["reasoning"]))
    else:
        parts.append("tokens unknown")
    cost = usage.get("cost_usd")
    if cost is None:
        parts.append("cost unknown")
    elif usage.get("cost_basis") == "price-table":
        parts.append("cost~$%.2f (price table %s)" % (cost, usage.get("prices_as_of")))
    else:
        parts.append("cost~$%.2f (claude cli list price)" % cost)
    total = usage.get("session_total")
    if usage.get("previous_run") and isinstance(total, dict):
        if total.get("cost_usd") is None:
            text = "session cost unknown over %d runs" % total.get("runs", 0)
        else:
            text = "session~$%.2f over %d runs" % (total["cost_usd"], total.get("runs", 0))
        if not total.get("complete"):
            text += " (incomplete)"
        parts.append(text)
    # model and effort may hold any non-option text; keep stdout printable in a C locale.
    return " ".join(parts).encode("ascii", "replace").decode("ascii")



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
        pass  # An existing root is validated below, never repaired.
    else:
        # mkdir mode is filtered by umask; set it explicitly before verifying.
        os.chmod(root, 0o700)
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


FOLLOW_UP_PREAMBLE = """\
This is a follow-up in the same cross-review session. The original constraints still apply:
- Stay read-only: inspect and report only; do not edit files, commit, or run commands that change state.
- Do not delegate: no other agents, CLIs, or reviewer skills.
- Keep the previous review target and requirements. If the requirements, base, or file set
  changed, say so instead of reusing the earlier verdict; that needs a fresh run.

Follow-up request:
"""


def _follow_up_brief(prompt: str) -> str:
    return FOLLOW_UP_PREAMBLE + prompt.rstrip("\n") + "\n"


def _read_private_file(path: Path, limit: int) -> bytes:
    """Read a run artifact only if it is a regular file we own (no symlinks)."""
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
            raise OSError("not a regular file owned by the current user")
        return os.read(fd, limit)
    finally:
        os.close(fd)


def _load_previous_run(run_dir: Path):
    """Return (metadata, session_id) of a finished run, or raise code 24."""
    def unavailable(reason):
        return CrossReviewError(EXIT_NO_SESSION,
                                "cannot resume %s: %s" % (run_dir, reason))

    try:
        _ensure_private_dir(run_dir)
    except FileNotFoundError:
        raise unavailable("run directory does not exist")
    except (CrossReviewError, OSError) as exc:
        raise unavailable(getattr(exc, "message", str(exc)))

    try:
        first = _read_private_file(run_dir / "run.log", 1 << 16).split(b"\n", 1)[0]
        meta = json.loads(first.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise unavailable("run.log header unreadable (%s)" % exc)
    if not isinstance(meta, dict):
        raise unavailable("run.log header is not a JSON object")
    version = meta.get("schema_version")
    if type(version) is not int or version != LOG_SCHEMA_VERSION:
        raise unavailable("unsupported schema_version %r" % (version,))
    for key in ("reviewer", "repo", "model", "effort"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise unavailable("header field %r is missing or invalid" % key)
    if meta["reviewer"] not in DEFAULTS:
        raise unavailable("unknown reviewer %r" % meta["reviewer"])
    for key in ("model", "effort"):
        # An option-like value would be read by the CLI as a flag.
        if meta[key].startswith("-"):
            raise unavailable("header field %r looks like a command-line option" % key)
    if not os.path.isabs(meta["repo"]) or not Path(meta["repo"]).is_dir():
        raise unavailable("repo %r is not an existing absolute directory" % meta["repo"])

    try:
        session = _read_private_file(run_dir / "session.txt", 4096).decode("utf-8").strip()
    except (OSError, ValueError) as exc:
        raise unavailable("session.txt unreadable (%s)" % exc)
    if not _is_uuid(session):
        raise unavailable("session.txt has no valid session id")
    return meta, session


def _require_cli(reviewer: str) -> str:
    executable = shutil.which(reviewer)
    if executable is None:
        raise CrossReviewError(EXIT_MISSING_CLI, "%s CLI not found on PATH" % reviewer)
    return executable


def _execute(reviewer: str, repo: Path, model: str, effort: str, brief_data: bytes,
             env: Mapping[str, str], build, session_id: Optional[str],
             extra_header: Optional[dict] = None) -> Path:
    """Create a run directory, spawn the reviewer, and settle its artifacts.

    build(run_dir) returns the argv. session_id is what session.txt records unless
    Codex prints a newer id. Unexpected OSError: environment (run root) -> 2,
    runtime after the run directory exists -> 22.
    """
    executable = _require_cli(reviewer)
    child_env = reviewer_environment(env)
    try:
        run_dir = _create_run_dir()
    except OSError as exc:
        raise CrossReviewError(EXIT_INVALID_INPUT, "cannot create run directory: %s" % exc)
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
        header.update(extra_header or {})
        os.write(fds["run.log"], (json.dumps(header) + "\n").encode("utf-8"))

        argv = build(run_dir)
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
            printed = parse_codex_session(paths["run.log"].read_text("utf-8", "replace"))
            session_id = printed or session_id
        if session_id:
            os.write(fds["session.txt"], (session_id + "\n").encode("utf-8"))
        else:
            _log(fds["run.log"], "session id not found; resume unavailable")

        for name in ARTIFACTS:
            if os.path.lexists(paths[name]):
                try:
                    _tighten(paths[name])
                except CrossReviewError as exc:
                    # Logged so run.log alone explains the exit code after a clean CLI status.
                    _log(fds["run.log"], exc.message)
                    raise

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
    except (KeyboardInterrupt, _Terminated):
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        _try_log(fds, "interrupted; partial artifacts kept")
        raise CrossReviewError(EXIT_INTERRUPTED, "interrupted", run_dir)
    except CrossReviewError as exc:
        exc.run_dir = exc.run_dir or run_dir
        raise
    except OSError as exc:
        _try_log(fds, "runtime error: %s" % exc)
        raise CrossReviewError(EXIT_REVIEWER_FAILED, "runtime error: %s" % exc, run_dir)
    finally:
        for fd in fds.values():
            os.close(fd)


def _try_log(fds: dict, line: str) -> None:
    if "run.log" in fds:
        try:
            _log(fds["run.log"], line)
        except OSError:
            pass


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
    # Validate everything (including argv) before touching the filesystem: inputs,
    # then the CLI lookup, then the Codex trust paths, and only then the run directory.
    build_run_command(reviewer, repo, Path("/"), model, effort, session_id or "",
                      untrusted=[str(repo)])
    brief_data = _read_brief(brief)
    _require_cli(reviewer)
    untrusted = codex_untrusted_paths(repo) if reviewer == "codex" else None
    build_run_command(reviewer, repo, Path("/"), model, effort, session_id or "",
                      untrusted=untrusted)
    return _execute(
        reviewer, repo, model, effort, brief_data, env,
        lambda run_dir: build_run_command(reviewer, repo, run_dir, model, effort, session_id,
                                          untrusted=untrusted),
        session_id)


def resume_review(run_dir: Path, prompt: str, env: Mapping[str, str]) -> Path:
    """Send a follow-up to the session of a previous run; return the new run directory.

    Reviewer, repo, model, and effort come from the validated run.log header and the
    session from session.txt. The previous run directory is only read.
    """
    ensure_not_nested(env)
    if not isinstance(prompt, str) or not prompt.strip():
        raise CrossReviewError(EXIT_INVALID_INPUT, "prompt must be non-empty")
    previous = Path(run_dir).absolute()
    meta, session = _load_previous_run(previous)
    reviewer, model, effort = meta["reviewer"], meta["model"], meta["effort"]
    repo = Path(meta["repo"])
    try:
        build_resume_command(reviewer, repo, Path("/"), model, effort, session,
                             untrusted=[str(repo.resolve())])
    except CrossReviewError as exc:
        raise CrossReviewError(EXIT_NO_SESSION, "cannot resume %s: %s" % (previous, exc.message))
    brief_data = _follow_up_brief(prompt).encode("utf-8")
    _require_cli(reviewer)
    untrusted = codex_untrusted_paths(repo) if reviewer == "codex" else None
    build_resume_command(reviewer, repo, Path("/"), model, effort, session,
                         untrusted=untrusted)
    return _execute(
        reviewer, repo, model, effort, brief_data, env,
        lambda new_dir: build_resume_command(reviewer, repo, new_dir, model, effort, session,
                                             untrusted=untrusted),
        session, {"resumed_from": str(previous)})


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
    # SIGTERM stops the reviewer and keeps partial artifacts, like Ctrl-C.
    try:
        previous_sigterm = signal.signal(signal.SIGTERM, _raise_terminated)
    except ValueError:  # not the main thread; keep the default handler
        return _main(argv, env)
    try:
        return _main(argv, env)
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)


def _main(argv, env) -> int:
    try:
        # The loop guard runs before argument parsing, CLI lookup, metadata, and run-dir.
        ensure_not_nested(env)
        parser = _Parser(prog="cross_review.py")
        sub = parser.add_subparsers(dest="command", required=True)
        run = sub.add_parser("run", help="start a fresh review")
        run.add_argument("--reviewer", required=True)
        run.add_argument("--repo", required=True, type=Path)
        run.add_argument("--brief", required=True, type=Path)
        run.add_argument("--model")
        run.add_argument("--effort")
        resume = sub.add_parser("resume", help="ask a follow-up in the same session")
        resume.add_argument("--run-dir", required=True, type=Path)
        resume.add_argument("--prompt", required=True)
        args = parser.parse_args(argv)
        if args.command == "run":
            run_dir = run_review(args.reviewer, args.repo, args.brief, args.model,
                                 args.effort, env)
        else:
            run_dir = resume_review(args.run_dir, args.prompt, env)
    except CrossReviewError as exc:
        if exc.run_dir is not None:
            _print_run(exc.run_dir)
        print("cross-review: %s" % exc.message, file=sys.stderr)
        return exc.code
    except OSError as exc:
        # Backstop: no traceback for unexpected runtime I/O failures.
        print("cross-review: runtime error: %s" % exc, file=sys.stderr)
        return EXIT_REVIEWER_FAILED
    except (KeyboardInterrupt, _Terminated):
        print("cross-review: interrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    _print_run(run_dir)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
