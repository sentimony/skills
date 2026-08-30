---
name: commit-all
description: User-invoked via /commit-all only. Gathers the working tree into a single commit on the current branch, no push.
metadata:
  author: Ihor Orlovskyi
  version: "1.1.0"
disable-model-invocation: true
license: MIT
---

# Commit All

Collect every change on the current branch into one commit with a generated message.
No push, no `--amend`, no new branches, no history rewriting: the skill produces exactly
one commit on the branch the user is already on, or stops to ask. The explicit
invocation is the approval: on a feature branch a normal run analyzes the tree, shows
the plan, and commits in the same turn without asking again.

Only the user triggers this skill: never activate it from a description of finished
work, and never invoke it from another skill. When the user supplies their own commit
message, commit directly without this skill.

Arguments: `/commit-all` commits; `/commit-all dry-run` prints the file list and the
generated message without committing.

## Workflow

1. **Survey the tree.** Run `git status --short`, `git diff`, `git diff --staged`, and
   `git log --oneline -10` for the branch's message conventions. A clean tree ends the
   run with "no changes to commit" and nothing else.
2. **Check the branch.** On `main` or `master`, stop and ask whether to commit there or
   create a branch first; never commit to a default branch silently.
3. **Separate the session's changes from pre-existing ones.** Compare the tree against
   the `git status` from the start of the conversation, when available. The split feeds
   the message's thematic groups and helps spot suspicious files; it is never a reason
   to pause. An explicit `/commit-all` already covers the whole tree, pre-existing
   changes included.
4. **Screen untracked files.** Skip anything `.gitignore` should have covered, one-off
   scripts, and files that may hold secrets; ask about them instead of staging blindly.
5. **Generate the message.** One imperative summary line up to ~72 characters. Reuse a
   prefix convention (`feat(scope):`, `fix:`) only when `git log` shows one; never
   impose your own. Add a body only when the diff spans several unrelated groups: 2-4
   short bullets, one per group, no per-file listing. Write the message in English. No
   co-author or agent attribution unless the repository's conventions require it.
6. **Show before committing.** Print the file list and the generated message as a
   progress update, then continue to the commit in the same turn. Only `dry-run` stops
   here. The remaining stop conditions are step 2 (default branch), step 4 (suspicious
   untracked files), and arguments whose intended scope cannot be determined safely
   (explicit paths or partial-commit requests that do not match the tree).
7. **Commit.** One commit on the current branch. Afterwards show `git log -1 --stat`
   (or a short excerpt). Do not push.

## Mechanics

- Pass the message via `git commit -F -` with a heredoc, never `-m` with escaping.
- Argument order matters: `git commit -F - -- <paths>`; putting `-F` after the pathspec
  breaks.
- zsh does not word-split an unquoted variable, so `git diff -- $PATHS` silently matches
  nothing; keep path lists in a file or a shell array.
- For a partial commit use `git commit -F - -- <paths>` so already-staged index entries
  (renames in particular) survive untouched.
- Never pass `--no-verify`; a failing pre-commit hook is a result to report, not an
  obstacle.
- Force push and history rewriting are out of scope for this skill under any wording.

## Amend

When the previous commit was made by this same session and is not pushed, offer
`--amend` in one sentence; run it only after the user agrees. Never offer it for a
pushed or foreign commit.
