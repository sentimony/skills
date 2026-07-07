# Agent Skills

A collection of [agent skills](https://agentskills.io) for Claude Code and other AI coding agents.

## Skills

| Skill | Version | Description |
| --- | --- | --- |
| [web-debug](skills/web-debug/SKILL.md) | 1.1.1 | Debug local web apps via Playwright. Script-assisted browser debugging skill. |
| [vitest](skills/vitest/SKILL.md) | 1.0.1 | Configure, write, debug, run, and migrate Vitest tests for JavaScript/TypeScript projects. Script-assisted Vitest skill. |
| [typescript](skills/typescript/SKILL.md) | 1.0.1 | Configure tsconfig, resolve compiler errors, debug slow type-checking, fix module resolution, migrate JS to TS. Script-assisted TypeScript skill. |
| [echarts](skills/echarts/SKILL.md) | 1.0.1 | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |

## Install

```bash
npx skills add sentimony/skills -s web-debug -a codex claude-code -y
npx skills add sentimony/skills -s vitest -a codex claude-code -y
npx skills add sentimony/skills -s typescript -a codex claude-code -y
npx skills add sentimony/skills -s echarts -a codex claude-code -y
```

Have fun ;)
