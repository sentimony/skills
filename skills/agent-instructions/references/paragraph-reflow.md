# Paragraph reflow

Read this when the audit finds paragraphs of `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*.md`
or the files they import with a line past the target width, or an unfilled line inside a
paragraph. Files grow by sessions appending or patching a fragment and wrapping only that
fragment; the result is a short line mid-paragraph next to an overlong neighbour, which
reads badly in a diff and an editor.

## Check

1. Measure width in characters, not bytes: Python `len(line)`. `awk length` on macOS
   counts bytes, so Cyrillic text looks twice as long.
2. Prose only: skip fenced code, tables, headings, link-only lines and the `@path` line.
3. Target width is taken from the file: the width most of its paragraphs are already
   wrapped to (typically 90-100); with none, 100. Ask the user only when the file has two
   clear widths.
4. Report each offending paragraph: file, first line, line count. A line over the width
   because of one indivisible token (URL, path, code span) is not a finding.

## Fix

Reflow the whole paragraph, never one line:

1. Fill lines to the target width; sentence ends do not force a break.
2. A code span is never split across lines (`textwrap` with `break_on_hyphens=False`,
   `break_long_words=False`, spaces inside backticks protected before wrapping); a URL or
   a path is never cut.
3. A list item keeps its marker and wraps with the continuation indented under the item
   text; nesting is kept.
4. Code blocks, tables, headings, link lines and `@path` lines stay byte for byte; blank
   lines between paragraphs and items do not change.

## Verify

1. `git diff --word-diff` shows no changed word or character, only line breaks; any other
   change means the reflow altered content, so revert and redo it.
2. Codex budget does not grow: a break replaces a space and back, so the chain size is
   the same within a few bytes. Show the size before and after
   (`scripts/agents_chain_size.py`).
3. A reflow with that proof changes no meaning, so it may be applied without a separate
   approval when the invocation allows applying line-break-only edits; otherwise it is a
   Phase 5 item like any other.

## Scope

1. The audit proposes the whole file in one commit with no other change, so `git blame`
   and review see a clean reflow. Edit mode reflows only the paragraphs it changes itself.
2. Global user files (`~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`) only on an explicit
   request, like every edit outside the repository.
