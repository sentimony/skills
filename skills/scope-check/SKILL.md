---
name: scope-check
description: Inform users that scope-check has been renamed to doc-preview and show how to install the replacement. Use when a user invokes scope-check or asks about its new name.
---

# Scope Check has moved

`scope-check` was renamed to `doc-preview`. Install the replacement with:

```bash
npx skills add sentimony/skills -s doc-preview -a codex claude-code -y
```

When invoked, explain the rename and show this command. The user decides whether to run
it. Use `doc-preview` for subsequent document previews when it is available.
