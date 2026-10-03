"""Hand a plan or implementation review to the opposite agent CLI.

This module holds the loop guard and the reviewer command adapters. Every CLI
invocation is an argv list meant for subprocess with shell=False.
"""

import re
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

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


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
