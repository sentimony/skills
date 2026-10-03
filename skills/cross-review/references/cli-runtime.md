# CLI Runtime

How the host launches the runner, what the runner executes, and how to read its exit
codes. Everything here was observed with `codex-cli 0.160.0` and Claude Code `2.1.288`;
items marked UNASSESSED were not observed.

## Runner interface

Call the runner by the absolute path of `scripts/cross_review.py` inside the installed
`cross-review` skill directory, never from a source clone:

    python3 <skill-dir>/scripts/cross_review.py run --reviewer codex|claude \
      --repo <repo-root> --brief <brief-file> [--model <id>] [--effort <level>]

    python3 <skill-dir>/scripts/cross_review.py resume --run-dir <previous-run-dir> \
      --prompt "<follow-up>"

The runner reads the brief as UTF-8, starts the reviewer with `cwd` set to the repository,
passes the brief on stdin, and sets no timeout. It refuses to start when
`CROSS_REVIEW_DEPTH` is present in its environment, even empty, and sets
`CROSS_REVIEW_DEPTH=1` for the reviewer process.

Defaults: Codex `gpt-6.1-sol` with effort `low`; Claude `claude-opus-5-5` with effort
`medium`. Both are always passed explicitly, so the reviewer's global configuration does
not override them. `--model` and `--effort` replace the defaults; resume reuses the values
of the previous run.

## Artifacts

Each `run` or `resume` creates a new private directory
`<system temp>/cross-review/<YYYYMMDD-HHMMSS>[-N]/` (mode 0700, files 0600). The runner
refuses a `cross-review` parent that is a symlink, belongs to another user, or is
accessible to others.

| File | Content |
| --- | --- |
| `brief.md` | the brief as sent; for resume, the wrapped follow-up prompt |
| `review.md` | the reviewer's final answer |
| `session.txt` | reviewer session UUID, empty when Codex printed none |
| `run.log` | first line JSON metadata, then CLI diagnostics |

The `run.log` header holds `schema_version`, `reviewer`, `mode` (always `unspecified`),
absolute `repo`, `model`, `effort`, `cli_version`, and `resumed_from` on resume. It never
holds environment variables or credentials. Resume trusts only a header and session that
pass validation.

Codex: stdout and stderr go to `run.log`; the final answer comes from `-o`; the session
UUID is parsed from the `session id: <uuid>` line on stderr. Claude: stdout is
`review.md`, stderr goes to `run.log`; the runner generates the session UUID.

## Production commands

The runner builds these argv lists and runs them without a shell. Values in angle brackets
are filled from the run. Each argument is shown as one argv token: the double quotes in the
Codex `-c` values are part of the token, because they make the value a TOML string. Typed
into a shell, those quotes would be stripped, which is one reason to call the runner rather
than these commands.

Codex run:

    codex exec -s read-only -m gpt-6.1-sol -c model_reasoning_effort="low" \
      -C <repo> -o <run-dir>/review.md -

Codex resume (with `cwd` set to the repository from the previous run's header):

    codex exec resume -m gpt-6.1-sol -c model_reasoning_effort="low" \
      -c sandbox_mode="read-only" -o <run-dir>/review.md <session-uuid> -

Claude run:

    claude -p --model claude-opus-5-5 --effort medium --permission-mode default \
      --tools "Read,Grep,Glob" --allowedTools "Read,Grep,Glob" \
      --disallowedTools "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*" \
      --strict-mcp-config --disable-slash-commands --safe-mode \
      --restricted --setting-sources "" --session-id <session-uuid>

Claude resume: the same command with `--resume <session-uuid>` in place of
`--session-id <session-uuid>`.

What each safety flag does:

| Flag | Purpose |
| --- | --- |
| `-s read-only` | Codex sandbox forbids writes for the run |
| `-c sandbox_mode="read-only"` | `exec resume` has no `-s` and otherwise inherits the user's global sandbox, which can be `danger-full-access` |
| `-o <run-dir>/review.md` | keeps only the final answer, separate from progress output |
| `-` | brief or follow-up arrives on stdin |
| `--tools "Read,Grep,Glob"` | the only built-in tools loaded into the Claude session |
| `--allowedTools "Read,Grep,Glob"` | pre-approves those tools so the headless run never waits on a prompt |
| `--disallowedTools ...` | denies write, shell, delegation, skill, and MCP tools even if a setting enables them |
| `--permission-mode default` | overrides a permissive default mode from settings |
| `--strict-mcp-config` | loads no MCP servers from any configuration |
| `--disable-slash-commands` | disables skills and slash commands |
| `--safe-mode` | disables customizations such as project hooks while keeping authentication |
| `--restricted` | ignores user, project, and local settings files and keeps file tools inside the repository; the host embeds any needed file from outside it in the brief |
| `--setting-sources ""` | an empty source list: no settings file is loaded, the same intent stated explicitly |
| `--session-id` / `--resume` | fixes the session for resume; resume never uses `--last` |

Settings files matter because the reviewed repository's `.claude/settings.json` is
untrusted. Loaded as a project source, it enabled the server-side `advisor` tool through
`advisorModel` and injected its `env` values into the reviewer's environment, overriding
`CROSS_REVIEW_DEPTH`. With this policy neither happened.

Observed effect of the Claude policy: the initial tool inventory is `Glob`, `Grep`, `Read`
with no MCP servers, skills, slash commands, or `advisor`, also in a repository whose
`.claude/settings.json` sets `advisorModel` and `env`, allows `Bash(*)`, `Write`, and
`Edit`, and defines `SessionStart` and `PreToolUse` hooks; those hooks did not run, and a
read of a file outside the repository was refused. Authentication through the CLI login
keeps working. Codex resume logged `sandbox: read-only`.

UNASSESSED: Claude authentication through an `apiKeyHelper`, which lives in a settings
file this policy does not load.

UNASSESSED: MCP servers and plugins configured in the Codex reviewer's
`~/.codex/config.toml`; the Codex commands do not disable them.

## Launch from the host

A review can run for more than ten minutes. Wait for the runner's actual exit; a job that
is still running has produced no review.

### Claude Code host (reviewer: Codex)

Run the runner with the Bash tool and `run_in_background: true`, then read the output
after the completion notification. A 660-second background job completed with its exit
code and output.

Fallback when background execution is unavailable: start the runner detached with stdin
from `/dev/null`, output redirected to a file, and a wrapper that writes the exit code to a
marker file, all inside a private directory from `mktemp -d`. Treat only the exit marker
as completion; a live PID proves nothing.

### Codex host (reviewer: Claude)

Run the runner as one `exec_command` call with
`sandbox_permissions: "require_escalated"` and a justification such as "Allow
cross-review to run the Claude CLI, which needs its login credentials and the Claude API".
Do not try the command inside the sandbox first: under `workspace-write` the Claude CLI
reported `Not logged in` there, with or without network access. Allowing network access
alone does not help; the Claude CLI needs the escalated run to reach its login.

If the approval policy is `never` or the escalation is denied, cross-review is unavailable:
report the reason and apply the fallback.

Start with an early yield, keep the returned process session, and poll with `write_stdin`
until the call reports `exit_code`. This is costly in tokens: thirteen 60-second polls used
about 259k input tokens, mostly cached.

UNASSESSED: escalation behavior in the interactive Codex TUI and under approval policies
other than `never`; only `codex exec` was observed as a host.

## Exit codes

| Code | Meaning | Agent action |
| --- | --- | --- |
| 0 | `review.md` holds a non-empty answer | check completeness, then hand off to `review-resolution` |
| 2 | invalid input: unknown reviewer, empty model or effort, missing repository, missing or non-UTF-8 brief, empty prompt, unsafe run root, or a failure to create the run root | fix the invocation once; otherwise report unavailable |
| 20 | `CROSS_REVIEW_DEPTH` is set: this process is already a reviewer | perform the review yourself; never retry delegation |
| 21 | reviewer CLI not found or not executable | report unavailable and apply the fallback |
| 22 | reviewer exited non-zero, or a runtime I/O failure after the run directory exists | report unavailable with the cause from `run.log`; partial output is no review |
| 23 | reviewer exited 0 with an empty or whitespace-only answer | report unavailable and apply the fallback |
| 24 | resume impossible: previous run directory missing or unsafe, header invalid or of an unknown schema, or no valid session UUID | start a fresh `run` with a full brief if the follow-up is still needed |
| 130 | interrupted by SIGINT or SIGTERM; the runner stops the reviewer CLI | no review; partial artifacts stay for diagnosis |

Whenever a run directory exists, the runner prints it and its artifact paths, also on
failure. Exit code 0 shows that an answer exists; whether it covers the target is the
completeness check in `SKILL.md`.
