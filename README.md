# Agent Skills

A collection of [agent skills](https://agentskills.io) for Claude Code and other AI coding agents.

## Skills

| Skill | Skill Version | Release | Description |
| --- | --- | --- | --- |
| [scope-triage](skills/scope-triage/SKILL.md) | 1.0.1 | v1.9.0 | Classify request scope before design work, then route to direct implementation, a light spec, or a full design cycle. |
| [plan-crafting](skills/plan-crafting/SKILL.md) | 1.1.1 | v1.9.0 | Turn an approved design or settled requirements into a bite-sized, TDD-oriented implementation plan. |
| [vitest](skills/vitest/SKILL.md) | 1.2.0 | v1.9.0 | Configure, write, debug, run, migrate, and audit Vitest tests for JavaScript/TypeScript projects. |
| [typescript](skills/typescript/SKILL.md) | 1.3.1 | v1.9.0 | Configure tsconfig, diagnose compiler behavior, and audit or migrate TypeScript projects. |
| [web-debug](skills/web-debug/SKILL.md) | 1.3.1 | v1.9.0 | Debug and verify local web apps via Playwright. |
| [echarts](skills/echarts/SKILL.md) | 1.1.1 | v1.9.0 | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |

## Install

```bash
npx skills add sentimony/skills -s scope-triage -a codex claude-code -y
npx skills add sentimony/skills -s plan-crafting -a codex claude-code -y
npx skills add sentimony/skills -s vitest -a codex claude-code -y
npx skills add sentimony/skills -s typescript -a codex claude-code -y
npx skills add sentimony/skills -s web-debug -a codex claude-code -y
npx skills add sentimony/skills -s echarts -a codex claude-code -y
```

`scope-triage` and `plan-crafting` are the two halves of one workflow: scope triage
writes an approved design to `docs/specs/`, then plan crafting turns it into a plan in
`docs/plans/`.

`scope-triage` is a scope-gated fork of [obra/superpowers](https://github.com/obra/superpowers)
`brainstorming` and is meant to replace it — install one or the other, not both. Installed on its
own it activates on 10/10 design requests and stays out of 10/10 mechanical or read-only ones;
installed alongside upstream `brainstorming`, the upstream skill's broader trigger wins most design
requests and this skill fires on only 2 of 10. `plan-crafting` replaces upstream
`writing-plans` the same way — install one planning skill, not both.

Have fun ;)
