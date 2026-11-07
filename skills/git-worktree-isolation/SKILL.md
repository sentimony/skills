---
name: git-worktree-isolation
description: Inform users that git-worktree-isolation has been renamed to worktree-isolation and show how to install the replacement. Use when a user invokes git-worktree-isolation or asks about its new name.
---

# Git Worktree Isolation has moved

`git-worktree-isolation` was renamed to `worktree-isolation`. Install the replacement with:

```bash
npx skills add sentimony/skills -s worktree-isolation -a codex claude-code -y
```

When invoked, explain the rename and show this command. The user decides whether to run
it. Use `worktree-isolation` for subsequent workspace isolation when it is available.
