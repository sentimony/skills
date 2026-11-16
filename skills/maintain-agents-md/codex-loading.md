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

Read the limit the session actually runs with instead of assuming the default.
`scripts/agents_chain_size.py` without `--budget` performs steps 1-3 and prints the
value with its source; pass `--profile <name>` when sessions run with one.

1. The user-level config is `$CODEX_HOME/config.toml`, or `~/.codex/config.toml` when
   `CODEX_HOME` is not set.
2. Read only the `project_doc_max_bytes` and `project_doc_fallback_filenames` keys.
   Never print the rest of a config file: it can hold MCP server tokens and private
   paths. Layers override in this order, later wins, and a later fallback list replaces
   an earlier one whole (observed in Codex CLI 0.162.1): the default (32768, no
   fallbacks), `/etc/codex/config.toml`, enterprise cloud config, the user-level
   config, the `--profile <name>` file `$CODEX_HOME/<name>.config.toml`, every
   `.codex/config.toml` from the project root down to the working directory (nearest
   wins; each applies only when trusted, by the exact directory, then the project root,
   then the Git trust root, in the user config's `[projects."<path>"]`), `-c` launch
   flags, then `/etc/codex/managed_config.toml` and the macOS MDM preference. A legacy
   `profile = "<name>"` key in `config.toml` makes Codex refuse to start, and the old
   `[profiles.<name>]` table cannot set these keys. The script reads the root's project
   config only and cannot see cloud, `-c`, or MDM layers, so its value is a best
   estimate - say so in the map. Codex reads no `.codex/config.local.toml`: a limit
   set there changes nothing, so report such a file as a finding.
3. If a config file does not parse (a duplicated table such as `[features]`, a
   value of the wrong type), Codex refuses to start with `failed to load bootstrap
   configuration`, so no limit from it applies. Report the broken file as a finding
   and name the key or table, not its values.
4. Record the effective value and the layer it came from in the surface map, one line
   per chain:
   `AGENTS.md chain: 9755 B; limit 65536 B (~/.codex/config.toml)`, or
   `limit 32768 B (default, not set)`.

Three numbers are kept apart in the report, each with its source and reason:

1. The **effective limit** of a trusted project: what the script prints, from the layers
   above. A project `.codex/config.toml` that git tracks reaches everyone who trusts the
   project, so its value governs, higher or lower than the default. Without a tracked
   project value the default governs in a shared repository. A project config that is
   gitignored or untracked (the script prints a note) guarantees nothing for the team:
   say it becomes shared once committed.
2. The **compatibility budget**: the default (32768 B), what a machine without the project
   layer runs with. When a tracked project config raises the limit, a chain over the
   default is a note, not a finding, and not a finding when the root file already records
   the decision. Name the condition that would still truncate it: the project is not
   trusted, the config was not received, or another layer overrides it. Codex does not
   open an untrusted project's `AGENTS.md` at all, so "project opened, `.codex/` skipped"
   is not a scenario.
3. The **internal target margin**: a number the repository set for itself (a size test, a
   line in `AGENTS.md`). Compare it with the effective limit, report a mismatch, and
   re-examine an old margin when the config changes. Never invent a new margin, and never
   take it for the platform limit.

A larger user-level value goes into the map as a note ("fits on this machine up to 65536
B"), not as the limit, unless the repository is personal. Treat it as personal, and let
the user-level value govern, only when the user says so or a project instruction file
already declares the repository personal; state that choice in the report rather than
inferring it from remotes or commit authors. When the user-level value is larger than
the default, no file declares the repository personal, and no tracked project config
sets the limit, do not wait for the user to notice: name both limits in the Phase 4
report with the assumption taken ("shared repository, 32768 B"), and add to Phase 5 an
option "declare the repository personal" with the ready line for the root `AGENTS.md`.
When the chain fits both limits, that option is one item in the Phase 5 list, not a step
that blocks the audit. A declaration names the source of the limit, not its number
("personal repository: the Codex limit is `project_doc_max_bytes` from
`~/.codex/config.toml`"), so it stays true when the config changes.

When the chain fits the effective limit but exceeds the compatibility budget, report it
by the rule of number 2: a finding only when no tracked project config explains the
higher limit, otherwise a note. When the chain fits both, the map line is enough.

## No conditional rules

Codex has no glob- or frontmatter-based conditional loading; directory nesting is the
only scoping mechanism. Content that Claude Code would put in a path-scoped rule can
only reach Codex as a nested `AGENTS.md` in the relevant directory or as a pointer the
agent follows by hand.

When both agents are in scope, also read
[claude-code-loading.md](claude-code-loading.md) - its closing table classifies every
surface of a mixed repository.
