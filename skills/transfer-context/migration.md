# Migrating from context-transfer

`context-transfer` was renamed to `transfer-context` in 0.0.5 (plugin `cross-agent` 0.0.6); since `skills` 0.0.112 the skill ships in the `skills` plugin.
Checkpoints are not rewritten: the store, the environment variable and the marker keep
their original names, so existing checkpoints resume unchanged.

## What changed

| Before | After |
| --- | --- |
| skill `context-transfer` | skill `transfer-context` |
| `/context-transfer`, `$context-transfer` | `/transfer-context`, `$transfer-context` |
| `scripts/context_transfer.py` | `scripts/transfer_context.py` |
| `scripts/context_transfer_hooks.py` | `scripts/transfer_context_hooks.py` |

## What stays the same

1. The default store `~/.sentimony/cross-agent/context-transfer/<slug>/`.
2. The legacy stores `<git common dir>/context-transfer/` and `docs/context-transfer/`.
3. The `CONTEXT_TRANSFER_DIR` variable and the `--store` option.
4. The `<!-- context-transfer:resume-check -->` marker in resume prompts.

Checkpoints saved before the rename pass `resume-check` without conversion. A resume prompt
written by an older version names `/context-transfer`; run `/transfer-context resume <id>`
instead.

## Steps

1. Remove the old skill with the host's supported operation: a plugin update, or
   `npx skills remove context-transfer`.
2. Install `transfer-context` from the `skills` plugin, or with
   `npx skills add sentimony/skills -s transfer-context -a codex claude-code -y`.
3. For a symlink installation, replace the links with the ones in
   [installation](install.md); delete the dangling `context-transfer` links.
4. If you enabled the Claude Code hooks, edit `settings.json`: the path ends in
   `skills/transfer-context/scripts/transfer_context_hooks.py`. The old path no longer
   exists, and hook errors are silent, so reminders stop without a message.
5. Update any shell alias, script or note that calls `scripts/context_transfer.py`.
6. Run `/transfer-context resume` in a project with a checkpoint to confirm that the
   existing store is found.

Do not move the store to a `transfer-context` directory: the skill reads only the names
above, so a moved store is treated as empty.
