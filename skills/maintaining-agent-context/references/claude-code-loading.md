# Claude Code loading mechanics

Read this in Phase 1 when Claude Code is in scope. Facts reflect the Claude Code
memory documentation as of mid-2026; if the tooling looks newer, spot-check against
https://code.claude.com/docs/en/memory before relying on a detail.

## Memory files and load order

Concatenated (not overridden), in this order: managed org policy, then user-level
`~/.claude/CLAUDE.md`, then `CLAUDE.md` files from filesystem root down to the working
directory, and at each level `CLAUDE.local.md` appended after `CLAUDE.md`. Recognized
project locations: `./CLAUDE.md`, `./.claude/CLAUDE.md`, `./CLAUDE.local.md`
(personal, gitignored). `.claude.md` and `.claude.local.md` (leading-dot forms) are
not real mechanisms - flag them as dead files. `CLAUDE.local.md` is current, not
deprecated, but exists only in the worktree where it was created.

What actually loads can be narrower than this map: the `claudeMdExcludes` setting
glob-excludes files (managed policy files cannot be excluded), and the CLI can
restrict setting sources (`--setting-sources user,project,local`), override settings
for one session (`--settings <file-or-json>`, which can change `claudeMdExcludes`
itself), skip memory discovery entirely (`--bare`), or disable all customizations
including every CLAUDE.md (`--safe-mode`; managed settings still apply there, but
managed CLAUDE.md does not load). An import that resolves outside the working
directory needs one-time user approval before it loads; imports from user-scope files
(`~/.claude/CLAUDE.md`, `~/.claude/rules/`) are exempt, except in Cowork desktop
sessions, which skip user-scope imports that resolve outside the session's working
directory. Treat the map as the default and `/context` as ground truth for a given
session.

## Nested files in monorepos

At launch, Claude Code loads `CLAUDE.md`/`CLAUDE.local.md` from the working directory
and every ancestor. A subdirectory's `CLAUDE.md` (e.g. `packages/web/CLAUDE.md`) loads
on demand, when the agent reads files in that directory - so classify nested files as
conditional, not always-loaded.

## `.claude/rules/`

`.md` files under `.claude/rules/` (recursive) with a `paths:` glob list in YAML
frontmatter load only when the agent reads a matching file:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
```

A rule file **without** `paths:` frontmatter loads at launch, same as
`.claude/CLAUDE.md` - always-loaded content, assess it as such. `paths` is the only
loading-control field; there is no regex or other condition syntax. User-level
`~/.claude/rules/` load before project rules. Symlinked rule files are supported.

## Imports

`@path/to/file` in a memory file inlines the target at launch (relative paths resolve
against the importing file's location). Maximum depth 4 hops. Import syntax inside
backticks or code fences is ignored. An imported file is therefore always-loaded
content, whatever its name - an `AGENTS.md` reached via `@AGENTS.md` has the same cost
as inline text.

## AGENTS.md interop

Claude Code does not read `AGENTS.md` natively. Live interop: a `@AGENTS.md` import
line in `CLAUDE.md`, or a symlink `CLAUDE.md -> AGENTS.md`. Either makes one file the
single source of truth for both agents - the preferred target structure when Codex and
Claude Code share a repo. A `CLAUDE.md` whose body duplicates `AGENTS.md` as text is a
copy that will drift; recommend converting it to an import or symlink. The same move
works for nested files in a monorepo: a package-level
`CLAUDE.md -> AGENTS.md` symlink gives Claude Code on-demand access to a nested
`AGENTS.md` it would otherwise never load.

## Verifying what actually loads

The `/context` command lists loaded memory files for a session; suggest it to the user
as ground truth when the loading map is in doubt.

## Classifying mixed repositories

Use this table only when both agents are in scope; the Codex column relies on
[codex-loading.md](codex-loading.md).

| Surface | Claude Code | Codex |
| --- | --- | --- |
| Root `AGENTS.md` | Only via import/symlink from `CLAUDE.md` | Always (unless masked by `AGENTS.override.md`) |
| `AGENTS.override.md` (home or any directory) | Ignored | Always for that directory, masking its `AGENTS.md` |
| Root `CLAUDE.md` / `.claude/CLAUDE.md` | Always | Ignored |
| `CLAUDE.local.md` | Always (this machine, this worktree) | Ignored |
| `~/.claude/CLAUDE.md` | Always (all projects) | Ignored |
| `.claude/rules/*.md` with `paths:` | Conditional on glob match | Ignored |
| `.claude/rules/*.md` without `paths:` | Always | Ignored |
| Nested `AGENTS.md` | No (unless imported) | If the session starts inside that subtree (chain is fixed at start) |
| Nested `CLAUDE.md` | On demand, when reading that directory | Ignored |
| Docs linked by pointer text | On demand, if the pointer fires | On demand, if the pointer fires |

When both agents are in use, rules that must bind both belong in the shared source of
truth (usually `AGENTS.md` plus a thin `CLAUDE.md` importing it); Claude-only
mechanics (rules globs, imports, local files) stay on the Claude side.
