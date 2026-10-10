# Codex loading mechanics

Read this in Phase 1 when Codex is in scope. Facts reflect the OpenAI Codex
agent-configuration documentation as of mid-2026, and the size budget is checked
against the Codex source at `rust-v0.160.0`; if the tooling looks newer, spot-check
against https://learn.chatgpt.com/docs/agent-configuration/agents-md and the Codex
configuration reference before relying on a detail. (The generic https://agents.md
spec describes the file format, not Codex loading behavior.)

## AGENTS.md discovery

Codex builds the instruction chain **once at session start**: global guidance from
the Codex home directory (`~/.codex` unless `CODEX_HOME` overrides it), then project
files from the project root down to the session's working directory, concatenated in
that order; the file closest to the working directory takes precedence on conflict,
and explicit user prompts override all files. Nothing loads on demand later - a
nested `AGENTS.md` outside the start-directory chain is simply not in the session.
The project root is located by walking up for marker files (configurable via
`project_root_markers`). Within each project directory Codex includes **at most one**
instruction file, checked in order: `AGENTS.override.md`, then `AGENTS.md`, then any
filename configured in `project_doc_fallback_filenames` (fallbacks apply to project
directories, not the home scope) - so an override file silently masks its sibling
`AGENTS.md`, and a repo can route Codex to a custom filename entirely. Check the
Codex config for these settings during discovery: user-level
`$CODEX_HOME/config.toml` (default `~/.codex/config.toml`), plus project-scoped
`.codex/config.toml` overrides - loaded only when the project is trusted. A project
marked `trust_level = "untrusted"` skips its `.codex/` layers and every project
`AGENTS.md`; only the global file loads. A project with no `[projects]` entry still
loads its files. Empty files are skipped.

## Size budget

`project_doc_max_bytes` (32 KiB by default; a config can change it, see below) bounds
only the project chain from the root to the working directory. The global
`AGENTS.md` in the Codex home is read without a size limit and does not count against
the budget, so measure the deepest project chain alone. At the boundary Codex does
not drop the file that overflows: it truncates it by bytes mid-text, possibly inside
a sentence or a multi-byte character, and reads no further files. The only signal is
a warning in the Codex log; the user sees no error. The lost text is the tail of the
deepest, most specific file, so total size is an audit finding.

## Effective size limit

Read the limit the session actually runs with instead of assuming the default:

1. Check whether `CODEX_HOME` is set, without printing any other environment value;
   the user-level config is `$CODEX_HOME/config.toml`, or `~/.codex/config.toml`
   when it is not set.
2. From that file, and from the project `.codex/config.toml` when the project is
   trusted, read only the `project_doc_max_bytes` and
   `project_doc_fallback_filenames` keys. Never print the rest of a config file: it
   can hold MCP server tokens and private paths. Layers override in this order, later
   wins: the default, the user-level config (an active profile in it wins over its
   top level), the project `.codex/config.toml` (trusted projects only), then a
   `-c project_doc_max_bytes=...` launch flag. System and enterprise configs sit below
   the user level, legacy managed configs above all of these; the agent usually cannot
   see them, so the value without them is a best estimate - say so in the map. Codex
   reads no `.codex/config.local.toml`: a limit set there changes nothing, so report
   such a file as a finding.
3. If a config file does not parse (a duplicated table such as `[features]`, a
   value of the wrong type), Codex refuses to start with `failed to load bootstrap
   configuration`, so no limit from it applies. Report the broken file as a finding
   and name the key or table, not its values.
4. Record the effective value and the layer it came from in the surface map, one line
   per chain:
   `AGENTS.md chain: 9755 B; limit 65536 B (~/.codex/config.toml)`, or
   `limit 32768 B (default, not set)`.

Which value governs depends on who else runs Codex on the repository. In a shared
repository, colleagues and CI run with the default unless the project
`.codex/config.toml` changes it, so the governing limit is the lower of the default
and the project value. A larger user-level value goes into the map as a note ("fits
on this machine up to 65536 B"), not as the limit. Treat the repository as personal,
and let the user-level value govern, only when the user says so or a project
instruction file already declares the repository personal; state that choice in the
report rather than inferring it from remotes or commit authors. A declaration names
the source of the limit, not its number ("personal repository: the Codex limit is
`project_doc_max_bytes` from `~/.codex/config.toml`"), so it stays true when the
config changes; a repository size test with its own number stays a separate budget.

When the chain fits the local limit but exceeds the default, report it as a finding
of its own: on every machine with the default limit Codex truncates the chain with no
visible error. When the chain fits both, the map line is enough. A budget the
repository writes for itself (a size test, a line in `AGENTS.md`) is a separate
number: compare it with the governing limit and report a mismatch, but never take it
for the platform limit.

## No conditional rules

Codex has no glob- or frontmatter-based conditional loading; directory nesting is the
only scoping mechanism. Content that Claude Code would put in a path-scoped rule can
only reach Codex as a nested `AGENTS.md` in the relevant directory or as a pointer the
agent follows by hand.

When both agents are in scope, also read
[claude-code-loading.md](claude-code-loading.md) - its closing table classifies every
surface of a mixed repository.
