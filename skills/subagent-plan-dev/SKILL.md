---
name: subagent-plan-dev
description: Inform users that subagent-plan-dev has been renamed to plan-orchestration and show how to install the replacement. Use when a user invokes subagent-plan-dev or asks about its new name.
---

# subagent-plan-dev has moved

`subagent-plan-dev` was renamed to `plan-orchestration`. Install the replacement with:

```bash
npx skills add sentimony/skills -s plan-orchestration -a codex claude-code -y
```
