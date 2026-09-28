# Changelog

All notable changes to the `secret-hygiene` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.0] - 2026-09-28

### Added
- Initial release: an advisory procedure for Claude Code and Codex that keeps credential
  values out of transcripts, tool output, logs, commits, and PR texts while the agent still
  uses them; a helper contract, a runtime capability matrix, and a project rule snippet.
