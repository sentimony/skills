# Runtime capability matrix

Checked on 2026-09-28 against Claude Code 2.1.283 and codex-cli 0.157.1.
"Documented" means the vendor documentation describes the mechanism; "verified" means an
integration test in this skill's eval package observed it. secret-hygiene 1.0.0 ships no
enforcement adapter; every enforcement row is informational.

| Mechanism | Claude Code | Codex | Status in 1.0.0 |
| --- | --- | --- | --- |
| Deny rules for reading env files | `permissions.deny` with `Read(./.env)` or `Read(**/.env)`; covers built-in file tools, recognized Bash file commands (`cat`, `head`, `tail`, `sed`, `tee`) and redirections | No path-based read rule; `prefix_rule()` in a `.rules` file controls which commands run outside the sandbox (`forbidden` blocks), and rules are experimental | documented, not shipped |
| PreToolUse hook with deny | `hookSpecificOutput.permissionDecision: "deny"` or exit code 2; matches `Bash`, `Read`, `Edit`, `Write`, MCP tools | Same JSON shape or exit code 2; matches shell and unified exec (as `Bash`), `apply_patch`, MCP and local function tools | documented, not shipped |
| PostToolUse output rewrite | `updatedToolOutput` replaces what the model sees; the tool has already run and telemetry keeps the original output | Blocking feedback replaces the tool result; `continue: false` stops normal processing; side effects are not undone | documented, not shipped |
| OS sandbox read control | `sandbox.filesystem.denyRead` and `allowRead`, for Bash, PowerShell and Monitor commands and their children | Sandbox mode limits writes to the workspace; no documented per-path read deny | documented, not shipped |
| Sandbox network control | Sandbox network allowlist; new domains prompt for approval | `workspace-write` runs without network by default; `sandbox_workspace_write.network_access = true` enables it | documented |
| Credential-named environment variables in subprocesses | Inherited from the launching shell | `shell_environment_policy.ignore_default_excludes` defaults to `true`, so variables whose names contain `KEY`, `SECRET` or `TOKEN` reach subprocesses unless set to `false` | documented |
| Project instructions file | `CLAUDE.md`, which can import `AGENTS.md` | `AGENTS.md` | documented |

## Known gaps

- Claude Code `Read` and `Edit` deny rules do not apply to commands that read files without
  naming them (`grep -r pattern .`) or to subprocesses that open files themselves, such as a
  Python or Node script. Only the OS sandbox blocks those.
- An OS-level read deny on the env file also blocks a project helper that runs inside the
  same sandbox, so a guard and a helper need an explicit carve-out to coexist.
- Codex `write_stdin` is transport for an existing unified-exec session and does not run
  `PreToolUse` again when it sends input to a command that already passed the hook.
- Codex hosted tools such as `WebSearch` are not covered by tool hooks. The Codex
  documentation calls tool hooks "a useful guardrail, not a complete enforcement boundary".
- A PostToolUse rewrite happens after the command ran: files written, requests sent, and
  telemetry of the original output are not affected.

## Sources

- https://code.claude.com/docs/en/permissions (checked 2026-09-28)
- https://code.claude.com/docs/en/hooks (checked 2026-09-28)
- https://code.claude.com/docs/en/sandboxing (checked 2026-09-28)
- https://learn.chatgpt.com/docs/hooks (checked 2026-09-28)
- https://learn.chatgpt.com/docs/config-file/config-reference (checked 2026-09-28)
- https://learn.chatgpt.com/docs/agent-configuration/rules (checked 2026-09-28)
- https://learn.chatgpt.com/docs/agent-approvals-security (checked 2026-09-28)
