# Codex loading mechanics

Read this in Phase 1 when Codex is in scope. Facts reflect the OpenAI Codex
agent-configuration documentation as of mid-2026; if the tooling looks newer,
spot-check against https://developers.openai.com/codex/agent-configuration/agents-md
and the Codex configuration reference before relying on a detail. (The generic
https://agents.md spec describes the file format, not Codex loading behavior.)

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
`.codex/config.toml` overrides - loaded only when the project is trusted; untrusted
projects skip `.codex/` layers entirely. Empty files are skipped, and
collection stops once combined size reaches `project_doc_max_bytes` (default
32 KiB) - oversized instruction trees get silently truncated, so total size is an
audit finding.

## No conditional rules

Codex has no glob- or frontmatter-based conditional loading; directory nesting is the
only scoping mechanism. Content that Claude Code would put in a path-scoped rule can
only reach Codex as a nested `AGENTS.md` in the relevant directory or as a pointer the
agent follows by hand.

When both agents are in scope, also read
[claude-code-loading.md](claude-code-loading.md) - its closing table classifies every
surface of a mixed repository.
