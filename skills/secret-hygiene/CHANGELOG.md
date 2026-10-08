# Changelog

All notable changes to the `secret-hygiene` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.2] - 2026-10-08

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.

## [1.0.1] - 2026-10-01

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.0] - 2026-09-28

### Added
- Initial release: an advisory procedure for Claude Code and Codex that keeps credential
  values out of transcripts, tool output, logs, commits, and PR texts while the agent still
  uses them; a helper contract, a runtime capability matrix, and a project rule snippet.
