# Changelog

All notable changes to this skill will be documented in this file.

Entries before 0.0.12 were written in the `sentimony/cross-agent` repository; later entries end
with the `sentimony/skills` release that shipped the version.

## [0.0.13] - 2026-11-15 - [0.0.113]

1. A single threshold mode: tokens decide the level (defaults 100000, 125000 and 150000 whether or not the window is known), and `percent` is informational when the window is known. A percentage flag or config value stays accepted: it is converted to tokens against a known window and replaced by the default token level when the window is unknown. `threshold_mode` is now always `tokens`; checkpoints that recorded `absolute` or `percentage` still validate. `hooks.md` needed no change: the hook acts only on the level names, and its tests pass unchanged.

## [0.0.12] - 2026-11-15 - [0.0.112]

1. Moved from the `cross-agent` plugin (`sentimony/cross-agent` v0.0.11, skill 0.0.11) to the `skills` plugin; the tree is otherwise unchanged except the points below. The default store keeps its `~/.sentimony/cross-agent/context-transfer/` path so existing checkpoints resume.
2. The delegated-session launcher is still looked up next to the skill (`../cross-agent/scripts/cross_agent.py`); `SKILL.md` and `install.md` no longer promise it in the same plugin, and a missing launcher records `not_captured: cross-agent launcher not installed next to this skill` (covered by a test).
3. Three test files gained `unittest.main()` so CI, which runs each file with `python <file>`, actually executes them.
4. Changelog headings use the `## [x.y.z]` form that CI checks.

## [0.0.11] - 2026-11-14

1. Add `migrate [--dry-run]` (legacy stores to the default store, validated copies, legacy
   left untouched); the `store` line names the command and warns about skipped legacy files.

## [0.0.10] - 2026-11-13

1. Move the five reference files from `references/` next to `SKILL.md` and update the links;
   no content change (request `20261111-2225`). `scripts/` stays.

## [0.0.9] - 2026-11-13

1. Rewrite the `description` as a thesis followed by "Use when ..." with fewer tokens; no
   behavior change (requests `20261009-2359`, `20261111-2220`).

## [0.0.8] - 2026-11-12

1. `resume-check` compares a checkpoint with the worktree where it was written when it runs
   from another worktree of the same repository. The result has `resumed_from_other_worktree`;
   the change of place is not drift. A removed worktree gives one `worktree-removed` entry
   (`20261110-2223`).

## [0.0.7] - 2026-11-10

1. Warn through `store_warning` in `facts --json` when the store lies under a temporary
   directory (`20261104-0624`).
2. Lighten the surface (`20261106-1735`): `argument-hint` is `[save | resume [<path|id>] | check]`;
   `write --auto` completes a draft with four sections; `write` prints
   `resume_command_terminal` and `resume_command_terminal_codex`; the usage check moves to
   `references/usage-check.md`; `list`, `validate` and `prune` are described in the
   checkpoint format reference.

## [0.0.6] - 2026-11-10

1. Add `references/migration.md`: what changed in the rename from `context-transfer`, what
   stays, and the steps for installed hooks and links.

## [0.0.5] - 2026-11-07

1. Rename `context-transfer` to `transfer-context`; invoke `/transfer-context` (`$transfer-context` in Codex)
   and run `scripts/transfer_context.py`. Only the name and its mentions changed. The store
   `~/.sentimony/cross-agent/context-transfer/`, `CONTEXT_TRANSFER_DIR` and the
   `context-transfer:resume-check` marker keep their names.

## [0.0.4] - 2026-11-07

1. Warn against pointing `--store` or `CONTEXT_TRANSFER_DIR` at a temporary
   directory such as `/tmp` (`20261104-0624`).

## [0.0.3] - 2026-11-05

1. Capture linked worktrees and local refs, and report drift and unverified facts.

## [0.0.2] - 2026-11-04

1. Document default context usage thresholds and overrides.

## [0.0.1] - 2026-11-04

1. Initial version.
