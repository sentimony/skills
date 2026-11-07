---
name: maintaining-agent-context
description: Inform users that maintaining-agent-context has been renamed to agent-instructions and show how to install the replacement. Use when a user invokes maintaining-agent-context or asks about its new name.
---

# maintaining-agent-context has moved

`maintaining-agent-context` was renamed to `agent-instructions`. Install the replacement with:

```bash
npx skills add sentimony/skills -s agent-instructions -a codex claude-code -y
```
