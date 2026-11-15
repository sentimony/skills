# Optional Claude Code hooks

Add these entries to your Claude Code `settings.json`. Replace the example absolute path
with the absolute path to `transfer_context_hooks.py` in your installation.

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "python3 /absolute/path/to/skills/transfer-context/scripts/transfer_context_hooks.py session-start", "timeout": 10}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 /absolute/path/to/skills/transfer-context/scripts/transfer_context_hooks.py user-prompt-submit", "timeout": 10}]}]
  }
}
```

`SessionStart` reads the current worktree's latest checkpoint and prints its path, age,
branch and HEAD, with a reminder to check the state. It does not print the checkpoint body.
`UserPromptSubmit` reads the session ID and transcript path, measures context usage and
adds a reminder to the prompt at the prepare and rotate levels. Refresh uses the prepare
reminder. Each reminder appears once per session and level. The hook creates marker files
under `<store>/reminders/`; the store is selected by the usual transfer-context settings.
Errors are silent and do not block the session. Remove these entries to disable the hooks.
