# Agent Skills

[![skills.sh](https://skills.sh/b/sentimony/skills)](https://skills.sh/sentimony/skills)

A collection of agent skills for Claude Code, Codex and other AI coding agents.

## Install

```bash
# All at once
npx skills add sentimony/skills -a codex claude-code -y
# Or each separately
npx skills add sentimony/skills -s scope-triage -a codex claude-code -y
```

```bash
claude plugin marketplace add sentimony/marketplace
claude plugin install skills@sentimony
```

```bash
codex plugin marketplace add sentimony/marketplace
codex plugin add skills@sentimony
```

For Antigravity, install from the repository URL; the `/tree/<tag>` form pins a release:

```bash
agy plugin install https://github.com/sentimony/skills/tree/v0.0.114
```

## Skills

| # | Skill | Description |
| --- | --- | --- |
| 1 | `scope-triage` <sup>[0.0.21](skills/scope-triage/SKILL.md)</sup> | Classify a request and settle design before code. |
| 2 | `doc-preview` <sup>[0.0.12](skills/doc-preview/SKILL.md)</sup> | Preview saved Markdown, JSON, YAML, TOML, CSV or text files as HTML. |
| 3 | `plan-craft` <sup>[0.0.30](skills/plan-craft/SKILL.md)</sup> | Turn settled requirements into an implementation plan. |
| 4 | `implement` <sup>[0.0.23](skills/implement/SKILL.md)</sup> | Execute a plan task by task in the current session. |
| 5 | `subagents-implement` <sup>[0.0.26](skills/subagents-implement/SKILL.md)</sup> | Execute a plan through coordinated subagents. |
| 6 | `worktree-isolation` <sup>[0.0.17](skills/worktree-isolation/SKILL.md)</sup> | Pick the safest workspace: in place or a Git worktree. |
| 7 | `parallel-agents` <sup>[0.0.19](skills/parallel-agents/SKILL.md)</sup> | Run independent units of work concurrently through agents. |
| 8 | `tdd` <sup>[0.0.19](skills/tdd/SKILL.md)</sup> | Red-green-refactor development with meaningful failing tests first. |
| 9 | `cross-review` <sup>[0.0.19](skills/cross-review/SKILL.md)</sup> | Second-opinion review by other agent CLIs. |
| 10 | `request-review` <sup>[0.0.16](skills/request-review/SKILL.md)</sup> | Independent review of a change against its requirements and diff. |
| 11 | `received-review` <sup>[0.0.20](skills/received-review/SKILL.md)</sup> | Verify review findings before any fix. |
| 12 | `debug` <sup>[0.0.23](skills/debug/SKILL.md)</sup> | Root-cause-first investigation of unexpected behavior. |
| 13 | `verify-gate` <sup>[0.0.16](skills/verify-gate/SKILL.md)</sup> | Evidence-backed pass or fail verdict on a completion claim. |
| 14 | `finalize` <sup>[0.0.23](skills/finalize/SKILL.md)</sup> | Merge, push, open a PR or clean up verified work. |
| 15 | `prose-craft` <sup>[0.0.13](skills/prose-craft/SKILL.md)</sup> | Edit prose to fit its reader. |
| 16 | `dashfix` <sup>[0.0.20](skills/dashfix/SKILL.md)</sup> | Replace typographic dashes with the plain hyphen. |
| 17 | `negafix` <sup>[0.0.17](skills/negafix/SKILL.md)</sup> | Ban "it's not just X, it's Y" constructions. |
| 18 | `skill-crafting` <sup>[0.0.15](skills/skill-crafting/SKILL.md)</sup> | Create, evaluate and retire agent skills. |
| 19 | `echarts` <sup>[0.0.22](skills/echarts/SKILL.md)</sup> | Build and debug Apache ECharts charts. |
| 20 | `playwright-debug` <sup>[0.0.20](skills/playwright-debug/SKILL.md)</sup> | Test and debug local web apps with Playwright. |
| 21 | `agent-browser-debug` <sup>[0.0.11](skills/agent-browser-debug/SKILL.md)</sup> | Slash-only: debug local web apps with agent-browser. |
| 22 | `commit-all` <sup>[0.0.20](skills/commit-all/SKILL.md)</sup> | Slash-only: commit all current changes without a message. |
| 23 | `gh-switch` <sup>[0.0.14](skills/gh-switch/SKILL.md)</sup> | Keep the active GitHub account matching the project. |
| 24 | `frontend-craft` <sup>[0.0.17](skills/frontend-craft/SKILL.md)</sup> | Design and build user-facing interfaces. |
| 25 | `vitest` <sup>[0.0.19](skills/vitest/SKILL.md)</sup> | Configure, write and debug Vitest tests. |
| 26 | `typescript` <sup>[0.0.24](skills/typescript/SKILL.md)</sup> | Fix compiler errors, tsconfig and typing problems. |
| 27 | `maintain-agents-md` <sup>[0.0.26](skills/maintain-agents-md/SKILL.md)</sup> | Create and audit AGENTS.md, CLAUDE.md and agent instructions. |
| 28 | `secret-hygiene` <sup>[0.0.9](skills/secret-hygiene/SKILL.md)</sup> | Keep credential values out of agent output. |
| 29 | `session-learnings` <sup>[0.0.18](skills/session-learnings/SKILL.md)</sup> | Record session learnings for future agents. |
| 30 | `transfer-context` <sup>[0.0.13](skills/transfer-context/SKILL.md)</sup> | Save and resume work across agent sessions. |

## Agentic Workflow

```text
scope-triage -> plan-craft -> implement | subagents-implement -> request-review -> received-review -> verify-gate -> finalize
```

Have fun ;)
