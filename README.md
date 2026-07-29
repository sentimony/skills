# Agent Skills

A collection of [agent skills](https://agentskills.io) for Claude Code and other AI coding agents.

## Skills

| Skill | Skill Version | Release | Description |
| --- | --- | --- | --- |
| [web-debug](skills/web-debug/SKILL.md) | 1.2.1 | v1.6.0 | Debug local web apps via Playwright. Script-assisted browser debugging skill. |
| [vitest](skills/vitest/SKILL.md) | 1.0.3 | v1.6.0 | Configure, write, debug, run, and migrate Vitest tests for JavaScript/TypeScript projects. Script-assisted Vitest skill. |
| [typescript](skills/typescript/SKILL.md) | 1.2.2 | v1.6.0 | Configure tsconfig, resolve compiler errors, debug slow type-checking, fix module resolution, and migrate JavaScript or compiler major versions. Script-assisted TypeScript skill. |
| [echarts](skills/echarts/SKILL.md) | 1.0.5 | v1.6.0 | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |
| [scope-triage](skills/scope-triage/SKILL.md) | 1.0.0 | v1.7.0 | Classify request scope before design work, then route to direct implementation, a light spec, or a full design cycle. |
| [plan-crafting](skills/plan-crafting/SKILL.md) | 1.0.0 | v1.7.0 | Turn an approved design or settled requirements into a bite-sized, TDD-oriented implementation plan. |

## Install

```bash
npx skills add sentimony/skills -s web-debug -a codex claude-code -y
npx skills add sentimony/skills -s vitest -a codex claude-code -y
npx skills add sentimony/skills -s typescript -a codex claude-code -y
npx skills add sentimony/skills -s echarts -a codex claude-code -y
npx skills add sentimony/skills -s scope-triage -a codex claude-code -y
npx skills add sentimony/skills -s plan-crafting -a codex claude-code -y
```

`scope-triage` and `plan-crafting` are the two halves of one workflow: scope triage writes an
approved design to `docs/specs/`, plan crafting turns it into a plan in `docs/plans/`.

`scope-triage` is a scope-gated fork of [obra/superpowers](https://github.com/obra/superpowers)
`brainstorming` and is meant to replace it — install one or the other, not both. Installed on its
own it activates on 10/10 design requests and stays out of 10/10 mechanical or read-only ones;
installed alongside upstream `brainstorming`, the upstream skill's broader trigger wins most design
requests and this skill fires on only 2 of 10. `plan-crafting` replaces upstream `writing-plans`
the same way — install one planning skill, not both.

Have fun ;)
