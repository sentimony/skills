# Agent hook enforcement

The `commit-msg` hook in `SKILL.md`, Enforcement, rejects a commit message with a banned
dash while `git commit` runs. Stop the same mistake before the tool call with the bundled
`PreToolUse` guard, `scripts/dashfix-commit-guard`. It is perl with the core `JSON::PP`
module alone, since a `jq` pipeline exits 0 on a machine without `jq` and lets the commit
through in silence. Copy it into the project:

```bash
install -m 755 scripts/dashfix-commit-guard .claude/hooks/dashfix-commit-guard
```

Then add the matcher to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_PROJECT_DIR/.claude/hooks/dashfix-commit-guard\"; [ -f \"$f\" ] || { echo \"dashfix: commit guard missing at $f\" >&2; exit 1; }; perl \"$f\""
          }
        ]
      }
    ]
  }
}
```

A missing script exits 1: Claude Code shows the message and the command still runs, so a
lost copy is visible without blocking every Bash call. Like the `commit-msg` hook, the
guard is a copy: reinstall it after a `dashfix` update.

## What it checks

The guard judges only the commands in the tool call that run `git commit` (`git -C <dir>
commit` included): their own text, which holds the `-m` arguments and a quoted
`"$(cat <<'EOF' ... EOF)"` message, text piped into them, and a heredoc fed to them
(`git commit -F - <<'EOF'`). A literal `\u2014`-style escape there counts as a dash.
Everything else in the same call passes: a replacement script or `sed` before
`&& git commit`, and a heredoc that writes text about dashes into a file. A message file
given with `-F <path>` is left to the `commit-msg` hook, which reads the stored message.

Commands split at unquoted `&&`, `||`, `;`, `&`, and newlines; a pipeline stays one
command. A payload that is not valid JSON falls back to the old whole-text check: any
banned dash anywhere in a call that mentions `git commit` blocks it.

Up to `dashfix` 2.2.2 the hook was a one-line perl matcher over the whole command, which
blocked a dash-cleanup script chained with `&& git commit` and a heredoc that mentioned
`git commit`, and missed `git -C <dir> commit`. `scripts/test_commit_guard.py` keeps
both kinds of case.
