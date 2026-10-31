# Agent Skills

[![skills.sh](https://skills.sh/b/sentimony/skills)](https://skills.sh/sentimony/skills)

A collection of agent skills for Claude Code, Codex and other AI coding agents.

The local responsibility-boundary links in the `branch-finish` and `review-resolution`
attribution references are pinned to commit `61919613972e63f2c833c1c5ad4744d7c40ad05a`
to preserve their targets before a repository layout change.

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

Or as one plugin, `skills`, from the [sentimony/marketplace](https://github.com/sentimony/marketplace)
marketplace, in Claude Code:

```bash
claude plugin marketplace add sentimony/marketplace
claude plugin install skills@sentimony   # all 28 skills
claude plugin install aw@sentimony       # workflow chain, code review, session learnings, from sentimony/agentic-workflow
```

or in Codex:

```bash
codex plugin marketplace add sentimony/marketplace
codex plugin add skills@sentimony
codex plugin add aw@sentimony
```

Plugin skills are namespaced by their plugin: `/skills:scope-triage`,
`/skills:skill-crafting`. The marketplace pins each plugin to a release tag of its
repository.

### Migrating from 1.58.14

From 1.58.15 all 28 skills are in the one `skills` plugin again: `devflow`, `writing`,
`skill-crafting`, and `echarts` are gone, and this repository no longer hosts a marketplace.
`claude plugin marketplace add sentimony/skills` stops working; the `sentimony` marketplace
now comes from `sentimony/marketplace`. Remove the old plugins and marketplace, then install
`skills@sentimony` from the new one.

In Claude Code, then restart the session:

```bash
claude plugin uninstall devflow@sentimony
claude plugin uninstall writing@sentimony
claude plugin uninstall skill-crafting@sentimony
claude plugin uninstall echarts@sentimony
claude plugin uninstall skills@sentimony
claude plugin marketplace remove sentimony
claude plugin marketplace add sentimony/marketplace
claude plugin install skills@sentimony
```

In Codex:

```bash
codex plugin remove devflow@sentimony
codex plugin remove writing@sentimony
codex plugin remove skill-crafting@sentimony
codex plugin remove echarts@sentimony
codex plugin remove skills@sentimony
codex plugin marketplace remove sentimony
codex plugin marketplace add sentimony/marketplace
codex plugin add skills@sentimony
```

Commands namespaced by the old plugins change prefix: `/devflow:scope-triage` becomes
`/skills:scope-triage`.

### Migrating from 1.58

`/scope-check` no longer runs `scope-triage`. From 1.58.5 it is a standalone skill that
renders a saved spec or plan to an HTML preview; invoke `/scope-triage` directly.

## Skills

All skills ship in the `skills` plugin: `claude plugin install skills@sentimony`.

| Skill | Description |
| --- | --- |
| [scope-triage](plugins/skills/skills/scope-triage/SKILL.md) | Classify request scope before design work, then route to direct implementation, a light spec, or a full design cycle. |
| [scope-check](plugins/skills/skills/scope-check/SKILL.md) | Render a saved spec or plan to an HTML preview link and keep the folder README index current. |
| [plan-crafting](plugins/skills/skills/plan-crafting/SKILL.md) | Turn an approved design or settled requirements into a bite-sized, TDD-oriented implementation plan. |
| [inline-plan-dev](plugins/skills/skills/inline-plan-dev/SKILL.md) | Execute an existing implementation plan inline in the current session, with plan-reality reconciliation, proportional verification, and durable resume. |
| [subagent-plan-dev](plugins/skills/skills/subagent-plan-dev/SKILL.md) | Execute an existing implementation plan through scoped subagents with risk-based dispatch, independent verification, and controlled escalation. |
| [git-worktree-isolation](plugins/skills/skills/git-worktree-isolation/SKILL.md) | Select, detect, or create a safe isolated development workspace with explicit ownership, baseline, and handoff. |
| [parallel-agents](plugins/skills/skills/parallel-agents/SKILL.md) | Prove work units independent, isolate mutable state, and dispatch one bounded parallel wave with reconciled results. |
| [tdd](plugins/skills/skills/tdd/SKILL.md) | Drive behavior changes through valid RED, sufficient GREEN, and evidence-backed refactoring. |
| [cross-review](plugins/skills/skills/cross-review/SKILL.md) | Hand a plan or a finished implementation to the opposite agent CLI and the Antigravity CLI in parallel, or to one named reviewer, for an independent read-only review. |
| [review-request](plugins/skills/skills/review-request/SKILL.md) | Prepare and dispatch independent code review against requirements, exact scope, and the actual diff. |
| [review-resolution](plugins/skills/skills/review-resolution/SKILL.md) | Validate and resolve code-review findings with evidence, explicit dispositions, and proportional re-review decisions. |
| [debugging](plugins/skills/skills/debugging/SKILL.md) | Investigate bugs and unexpected technical behavior with a root-cause-first evidence workflow. |
| [verification-gate](plugins/skills/skills/verification-gate/SKILL.md) | Turn a completion claim into an evidence-backed verdict against the current tree. |
| [branch-finish](plugins/skills/skills/branch-finish/SKILL.md) | Decide, execute and report the integration outcome for verified work, cleaning up only what is provably safe to remove. |
| [prose-crafting](plugins/skills/skills/prose-crafting/SKILL.md) | Edit prose for its reader, purpose, and author's voice while preserving meaning; audit or explain editorial choices without scoring. |
| [dashfix](plugins/skills/skills/dashfix/SKILL.md) | Replace typographic dashes with the plain hyphen in text of any language, keeping the spaces, and audit a project with a per-occurrence catalog. |
| [negafix](plugins/skills/skills/negafix/SKILL.md) | Ban negative parallelism ("it's not just X, it's Y"), audit prose for it, and score it 0-100. |
| [skill-crafting](plugins/skills/skills/skill-crafting/SKILL.md) | Create, improve, evaluate, optimize, split, merge, and retire agent skills with measured trigger boundaries and package-owned evals. |
| [echarts](plugins/skills/skills/echarts/SKILL.md) | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |
| [web-debug](plugins/skills/skills/web-debug/SKILL.md) | Debug and verify local web apps via Playwright. |
| [webapp-debugger](plugins/skills/skills/webapp-debugger/SKILL.md) | Experimental, /webapp-debugger only: debug and verify local web apps via agent-browser. |
| [commit-all](plugins/skills/skills/commit-all/SKILL.md) | Gather the working tree into one commit per repository the session changed, on the current branch or a new one the user picks, when the user asks to commit everything. |
| [gh-switch](plugins/skills/skills/gh-switch/SKILL.md) | Switch the GitHub CLI to the account a project names in .env/.env before gh commands, check that its GitLab token belongs to GL_ACC, and report in one line. |
| [frontend-crafting](plugins/skills/skills/frontend-crafting/SKILL.md) | Build, implement, redesign, review, and refine user-facing interfaces, including implementation-framed frontend changes, with subject-driven design decisions and a verifiable quality gate. |
| [vitest](plugins/skills/skills/vitest/SKILL.md) | Configure, write, debug, run, migrate, and audit Vitest tests for JavaScript/TypeScript projects. |
| [typescript](plugins/skills/skills/typescript/SKILL.md) | Configure tsconfig, diagnose compiler behavior, design type-safe APIs without silencing diagnostics, and audit or migrate TypeScript projects. |
| [maintaining-agent-context](plugins/skills/skills/maintaining-agent-context/SKILL.md) | Create, audit, restructure, and maintain a repository's agent instruction architecture for Claude Code and Codex. |
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
