# Attribution and design lineage

This skill is an original synthesis; no text is copied from either source. Two prior
skills shaped its design:

- [`writing-for-agents`](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents)
  by Matt Pocock (MIT). Source of the writing theory: context pointers with trigger
  branches, the two loads (context vs cognitive), the information hierarchy and
  progressive disclosure, completion criteria, leading words, positive phrasing,
  single source of truth, and the environment-as-source-of-truth ("cache") idea.
- [`claude-md-improver`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-md-management/skills/claude-md-improver)
  from Anthropic's official plugins (Apache-2.0). Source of the operational shape:
  discovery scan, verification against the actual codebase, a quality report before
  any edit, diff-style proposals, and explicit user confirmation.

Deliberate departures from `claude-md-improver`: no universal numeric rubric (criteria
differ by file type), the audit covers the whole instruction architecture rather than
CLAUDE.md alone, both Claude Code and Codex surfaces are first-class, and verification
is read-only by design.
