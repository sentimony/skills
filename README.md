# Agent Skills

[![skills.sh](https://skills.sh/b/sentimony/skills)](https://skills.sh/sentimony/skills)

A collection of agent skills for Claude Code, Codex and other AI coding agents.

## Skills

| Skill | Skill Version | Release | Description |
| --- | --- | --- | --- |
| [scope-triage](skills/scope-triage/SKILL.md) | 1.0.3 | v1.10.0 | Classify request scope before design work, then route to direct implementation, a light spec, or a full design cycle. |
| [plan-crafting](skills/plan-crafting/SKILL.md) | 1.1.2 | v1.10.0 | Turn an approved design or settled requirements into a bite-sized, TDD-oriented implementation plan. |
| [vitest](skills/vitest/SKILL.md) | 1.2.1 | v1.10.0 | Configure, write, debug, run, migrate, and audit Vitest tests for JavaScript/TypeScript projects. |
| [typescript](skills/typescript/SKILL.md) | 1.3.2 | v1.10.0 | Configure tsconfig, diagnose compiler behavior, and audit or migrate TypeScript projects. |
| [web-debug](skills/web-debug/SKILL.md) | 1.3.2 | v1.10.0 | Debug and verify local web apps via Playwright. |
| [echarts](skills/echarts/SKILL.md) | 1.1.2 | v1.10.0 | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |
| [dashfix](skills/dashfix/SKILL.md) | 1.1.0 | v1.11.0 | Ban typographic dashes in English text, check their form where a language's orthography requires them, audit a project, and score it 0-100. |
| [negafix](skills/negafix/SKILL.md) | 1.1.0 | v1.11.0 | Ban negative parallelism ("it's not just X, it's Y"), audit prose for it, and score it 0-100. |
| [commit-all](skills/commit-all/SKILL.md) | 1.0.0 | unreleased | Gather the working tree into a single commit on the current branch, on explicit /commit-all invocation only. |

## Install

```bash
# All at once

npx skills add sentimony/skills -a codex claude-code -y

# Or each separately

npx skills add sentimony/skills -s scope-triage -a codex claude-code -y
npx skills add sentimony/skills -s plan-crafting -a codex claude-code -y
npx skills add sentimony/skills -s vitest -a codex claude-code -y
npx skills add sentimony/skills -s typescript -a codex claude-code -y
npx skills add sentimony/skills -s web-debug -a codex claude-code -y
npx skills add sentimony/skills -s echarts -a codex claude-code -y
npx skills add sentimony/skills -s dashfix -a codex claude-code -y
npx skills add sentimony/skills -s negafix -a codex claude-code -y
npx skills add sentimony/skills -s commit-all -a codex claude-code -y
```

Have fun ;)
