# Installation

Install the skill separately in Claude Code or Codex by linking its source directory into
the project's skill directory. Replace the source with the absolute path to this checkout:

```sh
mkdir -p .claude/skills .agents/skills
ln -s /absolute/path/to/skills/transfer-context .claude/skills/transfer-context
ln -s /absolute/path/to/skills/transfer-context .agents/skills/transfer-context
```

The skill stands alone. Delegated sessions are captured only when a `cross-agent` skill is
installed as its sibling (`skills/cross-agent/`); a plugin install of `skills` has no
sibling, so the checkpoint records why they were not captured.

Claude Code can use the optional [hook settings](hooks.md). Codex uses the skill manually;
this package provides no Codex hooks. A checkpoint's resume prompt includes
manual checks for a session where the skill is unavailable.
