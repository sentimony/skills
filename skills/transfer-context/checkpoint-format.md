# Checkpoint format

A checkpoint is Markdown with a JSON object between `---` front matter lines. Write a
UTF-8 draft with only the model-owned fields `task`, `verification`, `continuation`,
`artifacts` and optional `source.model`. `write` supplies all other fields and rejects
script-owned fields in a draft. Artifact paths are relative to the project root and must
exist when writing; describe missing paths in `Missing information` instead. Each
`artifacts` entry is a path string, not an object; describe its role in the body.

The model owns `task.objective`, `task.status` (`in-progress`, `blocked`, `awaiting-user`,
`done`), `task.next_action`, `verification.status` (`verified`, `partial`, `unverified`),
`verification.evidence` entries (`claim`, `check`, `result`), and the lists
`continuation.recommended_skills`, `continuation.blockers`, and
`continuation.pending_decisions`. It also owns `artifacts` and optional `source.model`.

The script owns `schema_version`, `transfer_id`, `created_at`, `previous_transfer_id`,
`source.agent`, `source.session_id`, `source.context`, `project`, and
`delegated_sessions`. Project facts include root, worktree, Git common directory, remote,
branch, HEAD, dirty and untracked paths, content digests, linked worktrees, and local
default-branch and origin ref values. The default branch comes only from local
`refs/remotes/origin/HEAD`; unavailable values are null. A bare repository entry in the
worktree list has null `head` and `branch`. These refs reflect the last local
update and do not establish current server state. Old checkpoints remain valid; resume
reports missing or unavailable facts in `unverified`. When `resume-check` runs from
another worktree of the same repository, its result has `resumed_from_other_worktree` (the
checkpoint's worktree path, else null) and compares the checkpoint with that worktree;
when that worktree is gone or no longer belongs to the repository, `drift` has a single
`worktree-removed` entry and `unverified` lists `artifacts`. Delegated sessions contain
session identity, task, family, model, effort, CLI session, state and liveness, or a
`not_captured` reason. Source context records occupancy, window, percent, basis and
threshold mode. Unknown values are null.

Use the following section order. Keep empty sections as `None.`. `write` appends a
self-contained block with the checkpoint's absolute path and manual Git checks to the
resume prompt.

```markdown
---
{
  "task": {"objective": "Finish the parser", "status": "in-progress", "next_action": "Inspect the failing case"},
  "verification": {"status": "partial", "evidence": [{"claim": "Parser handles empty input", "check": "python3 -m unittest", "result": "passed"}]},
  "continuation": {"recommended_skills": [], "blockers": [], "pending_decisions": []},
  "artifacts": ["docs/plans/parser.md"],
  "source": {"model": "example"}
}
---
## Resume prompt
Continue the parser work after checking the current project state.
## Objective and acceptance
Handle empty and malformed input.
## Authority and prohibitions
No deployment authorized.
## State
The empty input case passes.
## Decisions
None.
## Running now
None.
## Pending user decisions
None.
## Failed approaches
None.
## Verification
The recorded unit test passed in this session.
## Next actions
Inspect the failing case.
## Missing information
None.
```

By default the store is `~/.sentimony/cross-agent/context-transfer/<slug>/`, outside the
project tree: nothing is added to the project, `.gitignore` or `.git/info/exclude`,
and a checkpoint survives a reboot. For a Git repository the slug is built from the
main checkout (the parent of the common Git directory), so every worktree shares one
store and resumes from any of them; outside Git it is built from the working
directory. A store with checkpoints there always wins. A legacy store is used only
while it has none: `<git common dir>/context-transfer/`, then `docs/context-transfer/`
of the main checkout. A bare or non-standard common directory uses its own slug.
`--store` overrides `CONTEXT_TRANSFER_DIR`, which overrides the default. Do not point
either at an OS temporary directory such as `/tmp`: a reboot clears it and the
checkpoints are lost, and `facts --json` reports `store_warning` for a store under
one. Keep it under `~/.sentimony/cross-agent/<skill>/<project>/`. Each checkpoint is
`<transfer_id>.md`; `latest-<worktree slug>` points to the latest one. A slug is the
realpath basename (or `root` for `/`) cut to at most 64 bytes on a character boundary,
followed by `-` and the first 12 hex digits of the SHA-256 digest of the
filesystem-encoded realpath. Optional `config.json` holds thresholds and
`window_tokens`; hooks use `reminders/`.

`write --auto` accepts a draft with only `Objective`, `Decisions`, `Failed approaches`
and `Pending user decisions` and fills the other sections from facts or `None recorded.`;
`write` also prints `resume_command_terminal` and `resume_command_terminal_codex`
(`cd <root> && claude '/transfer-context resume <id>'` and
`codex '$transfer-context resume <id>'`, single-quoted so the shell leaves `$` alone).
`list` prints the store's checkpoints, `prune --keep <n> [--all]` removes older ones and
never runs implicitly. Run `validate <path>` to check a completed checkpoint. Missing
artifacts are warnings on validation and errors on write. `--budget` sets the body
character warning threshold (default 12000). The script rejects known secret patterns;
review all material for other secrets before writing.
