# Agent Skills

[![skills.sh](https://skills.sh/b/sentimony/skills)](https://skills.sh/sentimony/skills)

A collection of agent skills for Claude Code, Codex and other AI coding agents.

## Install

```bash
# All at once

npx skills add sentimony/skills -a codex claude-code -y

# Or each separately

npx skills add sentimony/skills -s web-debug -a codex claude-code -y
npx skills add sentimony/skills -s vitest -a codex claude-code -y
npx skills add sentimony/skills -s typescript -a codex claude-code -y
npx skills add sentimony/skills -s echarts -a codex claude-code -y
npx skills add sentimony/skills -s scope-triage -a codex claude-code -y
npx skills add sentimony/skills -s plan-crafting -a codex claude-code -y
npx skills add sentimony/skills -s dashfix -a codex claude-code -y
npx skills add sentimony/skills -s negafix -a codex claude-code -y
npx skills add sentimony/skills -s prose-crafting -a codex claude-code -y
npx skills add sentimony/skills -s commit-all -a codex claude-code -y
npx skills add sentimony/skills -s maintaining-agent-context -a codex claude-code -y
npx skills add sentimony/skills -s frontend-crafting -a codex claude-code -y
npx skills add sentimony/skills -s tdd -a codex claude-code -y
npx skills add sentimony/skills -s debugging -a codex claude-code -y
npx skills add sentimony/skills -s review-request -a codex claude-code -y
npx skills add sentimony/skills -s cross-review -a codex claude-code -y
npx skills add sentimony/skills -s review-resolution -a codex claude-code -y
npx skills add sentimony/skills -s verification-gate -a codex claude-code -y
npx skills add sentimony/skills -s git-worktree-isolation -a codex claude-code -y
npx skills add sentimony/skills -s parallel-agents -a codex claude-code -y
npx skills add sentimony/skills -s inline-plan-dev -a codex claude-code -y
npx skills add sentimony/skills -s subagent-plan-dev -a codex claude-code -y
npx skills add sentimony/skills -s branch-finish -a codex claude-code -y
npx skills add sentimony/skills -s skill-crafting -a codex claude-code -y
npx skills add sentimony/skills -s secret-hygiene -a codex claude-code -y
npx skills add sentimony/skills -s gh-switch -a codex claude-code -y
npx skills add sentimony/skills -s scope-check -a codex claude-code -y
npx skills add sentimony/skills -s webapp-debugger -a codex claude-code -y
```

Or as plugins, in Claude Code:

```bash
claude plugin marketplace add sentimony/skills
claude plugin install devflow@sentimony         # scope, plan, build, review, verify, finish
claude plugin install writing@sentimony         # prose editing, dashes, negative parallelism
claude plugin install skill-crafting@sentimony  # create and evaluate agent skills
claude plugin install echarts@sentimony         # Apache ECharts visualizations
claude plugin install skills@sentimony          # frontend, Vitest, TypeScript, agent context, secrets, browser debugging, git helpers
```

or in Codex:

```bash
codex plugin marketplace add sentimony/skills
codex plugin add devflow@sentimony
codex plugin add writing@sentimony
codex plugin add skill-crafting@sentimony
codex plugin add echarts@sentimony
codex plugin add skills@sentimony
```

Plugin skills are namespaced by their plugin: `/devflow:scope-triage`,
`/skill-crafting:skill-crafting`.

### Migrating from 1.55

Up to 1.55.1, `skills@sentimony` carried all 28 skills. From 1.56.0 it carries nine; the
other 19 moved to `devflow`, `writing`, `skill-crafting`, and `echarts`. Updating
`skills@sentimony` alone removes them, so install the plugins whose skills you use.

In Claude Code, then restart the session:

```bash
claude plugin marketplace update sentimony
claude plugin update skills@sentimony
claude plugin install devflow@sentimony
claude plugin install writing@sentimony
claude plugin install skill-crafting@sentimony
claude plugin install echarts@sentimony
```

In Codex:

```bash
codex plugin marketplace upgrade sentimony
codex plugin add devflow@sentimony
codex plugin add writing@sentimony
codex plugin add skill-crafting@sentimony
codex plugin add echarts@sentimony
```

## Skills

### devflow

Development workflow skills: scope triage, planning, plan execution inline or through subagents, test-driven development, root-cause debugging, code review, verification, and branch finishing.

`claude plugin install devflow@sentimony`

| Skill | Description |
| --- | --- |
| [scope-triage](plugins/devflow/skills/scope-triage/SKILL.md) | Classify request scope before design work, then route to direct implementation, a light spec, or a full design cycle. |
| [scope-check](plugins/devflow/skills/scope-check/SKILL.md) | Experimental: run scope-triage on explicit /scope-check invocation only. |
| [plan-crafting](plugins/devflow/skills/plan-crafting/SKILL.md) | Turn an approved design or settled requirements into a bite-sized, TDD-oriented implementation plan. |
| [inline-plan-dev](plugins/devflow/skills/inline-plan-dev/SKILL.md) | Execute an existing implementation plan inline in the current session, with plan-reality reconciliation, proportional verification, and durable resume. |
| [subagent-plan-dev](plugins/devflow/skills/subagent-plan-dev/SKILL.md) | Execute an existing implementation plan through scoped subagents with risk-based dispatch, independent verification, and controlled escalation. |
| [git-worktree-isolation](plugins/devflow/skills/git-worktree-isolation/SKILL.md) | Select, detect, or create a safe isolated development workspace with explicit ownership, baseline, and handoff. |
| [parallel-agents](plugins/devflow/skills/parallel-agents/SKILL.md) | Prove work units independent, isolate mutable state, and dispatch one bounded parallel wave with reconciled results. |
| [tdd](plugins/devflow/skills/tdd/SKILL.md) | Drive behavior changes through valid RED, sufficient GREEN, and evidence-backed refactoring. |
| [cross-review](plugins/devflow/skills/cross-review/SKILL.md) | Hand a plan or a finished implementation to the opposite agent CLI for an independent read-only review. |
| [review-request](plugins/devflow/skills/review-request/SKILL.md) | Prepare and dispatch independent code review against requirements, exact scope, and the actual diff. |
| [review-resolution](plugins/devflow/skills/review-resolution/SKILL.md) | Validate and resolve code-review findings with evidence, explicit dispositions, and proportional re-review decisions. |
| [debugging](plugins/devflow/skills/debugging/SKILL.md) | Investigate bugs and unexpected technical behavior with a root-cause-first evidence workflow. |
| [verification-gate](plugins/devflow/skills/verification-gate/SKILL.md) | Turn a completion claim into an evidence-backed verdict against the current tree. |
| [branch-finish](plugins/devflow/skills/branch-finish/SKILL.md) | Decide, execute and report the integration outcome for verified work, cleaning up only what is provably safe to remove. |

### writing

Writing skills: edit prose for its reader, purpose, and author's voice, replace typographic dashes with the plain hyphen, and ban negative parallelism.

`claude plugin install writing@sentimony`

| Skill | Description |
| --- | --- |
| [prose-crafting](plugins/writing/skills/prose-crafting/SKILL.md) | Edit prose for its reader, purpose, and author's voice while preserving meaning; audit or explain editorial choices without scoring. |
| [dashfix](plugins/writing/skills/dashfix/SKILL.md) | Replace typographic dashes with the plain hyphen in text of any language, keeping the spaces, and audit a project with a per-occurrence catalog. |
| [negafix](plugins/writing/skills/negafix/SKILL.md) | Ban negative parallelism ("it's not just X, it's Y"), audit prose for it, and score it 0-100. |

### skill-crafting

Create, improve, evaluate, and optimize agent skills with measured trigger boundaries and package-owned evals.

`claude plugin install skill-crafting@sentimony`

| Skill | Description |
| --- | --- |
| [skill-crafting](plugins/skill-crafting/skills/skill-crafting/SKILL.md) | Create, improve, evaluate, and optimize agent skills with measured trigger boundaries and package-owned evals. |

### echarts

Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue.

`claude plugin install echarts@sentimony`

| Skill | Description |
| --- | --- |
| [echarts](plugins/echarts/skills/echarts/SKILL.md) | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |

### skills

General agent skills: frontend design, Vitest, TypeScript, agent context maintenance, secret hygiene, browser debugging, GitHub account switching, and committing the working tree.

`claude plugin install skills@sentimony`

| Skill | Description |
| --- | --- |
| [web-debug](plugins/skills/skills/web-debug/SKILL.md) | Debug and verify local web apps via Playwright. |
| [webapp-debugger](plugins/skills/skills/webapp-debugger/SKILL.md) | Experimental: run debugging on explicit /webapp-debugger invocation only. |
| [commit-all](plugins/skills/skills/commit-all/SKILL.md) | Gather the working tree into one commit per repository the session changed, on the current branch or a new one the user picks, when the user asks to commit everything. |
| [gh-switch](plugins/skills/skills/gh-switch/SKILL.md) | Switch the GitHub CLI to the account a project names in .env/.env before gh commands, and report the switch in one line. |
| [frontend-crafting](plugins/skills/skills/frontend-crafting/SKILL.md) | Create, redesign, review, and polish user interfaces with subject-driven design decisions and a verifiable quality gate. |
| [vitest](plugins/skills/skills/vitest/SKILL.md) | Configure, write, debug, run, migrate, and audit Vitest tests for JavaScript/TypeScript projects. |
| [typescript](plugins/skills/skills/typescript/SKILL.md) | Configure tsconfig, diagnose compiler behavior, and audit or migrate TypeScript projects. |
| [maintaining-agent-context](plugins/skills/skills/maintaining-agent-context/SKILL.md) | Audit, restructure, and maintain a repository's agent instruction architecture for Claude Code and Codex. |
| [secret-hygiene](plugins/skills/skills/secret-hygiene/SKILL.md) | Use credentials for real work while keeping their values out of transcripts, logs, commits, and PR texts. |

## Development Workflow

`scope-triage` is the development entry point. It classifies the request and picks the
minimum appropriate process, so a one-line configuration change and a new subsystem do not
receive the same ceremony.

```text
                         scope-triage
                              │
               ┌──────────────┼──────────────┐
               │              │              │
            Route A        Route B        Route C
         direct work     light spec      full design
               │              │              │
               │         direct work     plan-crafting
               │              │              │
               │              │        ┌─────┴─────┐
               │              │        │           │
               │              │   inline-plan   subagent-plan
               │              │      -dev           -dev
               └──────────────┴────────┬───────────┘
                                      │
                               implementation
                                      │
                         behavior change → tdd
                                      │
                 review-request (when warranted)
                                      │
             review-resolution (when findings exist)
                                      │
                              verification-gate
                                      │
               branch-finish (when lifecycle exists)
                                      │
                                   complete
```

When work fails unexpectedly, the diagnostic path runs alongside the main flow and returns
to whatever workflow discovered the failure.

```text
any development stage
        │
        ▼
     debugging
        │
        ├── browser evidence needed
        │          │
        │      web-debug
        │          │
        └──────────┘
        │
     root cause
        │
        ├── material redesign needed → scope-triage
        │
        ├── behavior correction → tdd
        │
        ▼
       fix
        │
        ▼
return to calling workflow
```

Four properties of this workflow are worth stating explicitly.

- **`tdd` is used within implementation, whenever behavior changes.** It is a micro-cycle
  inside a task rather than a sequential phase that follows implementation. Both execution
  modes and direct implementation invoke it at the moment a behavior change is written.
- **Review is proportional; verification is authoritative.** `review-request` is invoked
  when the change warrants independent eyes, and `review-resolution` validates findings
  before anything is changed in response. A review verdict stands separate from completion:
  `verification-gate` owns the authoritative pass or fail against the current tree.
- **The diagnostic path has three distinct owners.** `debugging` owns causal investigation,
  `web-debug` supplies browser and runtime evidence when the symptom lives in a page, and
  `tdd` drives the regression behavior once the cause is known. The fix then returns to the
  workflow that discovered the failure.
- **The workflow is composable rather than mandatory-linear.** Every step after `scope-triage` is
  reached on a condition. Route A terminates in implementation with proportional
  verification, and `branch-finish` runs only when a branch or workspace lifecycle exists.

Conditional capabilities, invoked when the work calls for them rather than in sequence:
`skill-crafting`, `tdd`, `debugging`, `web-debug`, `git-worktree-isolation`, `parallel-agents`,
`frontend-crafting`, `vitest`, `typescript`, `echarts`.

Have fun ;)
