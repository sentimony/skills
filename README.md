# Agent Skills

[![skills.sh](https://skills.sh/b/sentimony/skills)](https://skills.sh/sentimony/skills)

A collection of agent skills for Claude Code, Codex and other AI coding agents.

Version: `v0.0.105`

## Plugins

| Plugin | Version | Skills |
| --- | --- | --- |
| [skills](.) | 0.0.105 | scope-triage, doc-preview, plan-crafting, plan-execution, plan-orchestration, worktree-isolation, parallel-agents, tdd, cross-review, review-request, review-resolution, debugging, verification-gate, branch-finish, prose-crafting, dashfix, negafix, skill-crafting, echarts, web-debug, webapp-debugger, commit-all, gh-switch, frontend-crafting, vitest, typescript, agent-instructions, secret-hygiene |

The local responsibility-boundary links in the `branch-finish` and `review-resolution`
attribution references are pinned to commit `61919613972e63f2c833c1c5ad4744d7c40ad05a`
to preserve their targets before a repository layout change.

The repository root is the plugin root, with one shared `skills/` directory.
Since `v0.0.103` the three manifests (`.claude-plugin/`, `.codex-plugin/`,
`.antigravity-plugin/` `plugin.json`) are back, in the standard layout. In Claude Code
2.1.322 a `git-subdir` marketplace source with `path: "."` installs only the repository's
top-level files, so the marketplace pins the plugin with a `url` source. Codex reads its
manifest with the `interface`; Antigravity reads its own.

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
npx skills add sentimony/skills -s agent-instructions -a codex claude-code -y
npx skills add sentimony/skills -s frontend-crafting -a codex claude-code -y
npx skills add sentimony/skills -s tdd -a codex claude-code -y
npx skills add sentimony/skills -s debugging -a codex claude-code -y
npx skills add sentimony/skills -s review-request -a codex claude-code -y
npx skills add sentimony/skills -s cross-review -a codex claude-code -y
npx skills add sentimony/skills -s review-resolution -a codex claude-code -y
npx skills add sentimony/skills -s verification-gate -a codex claude-code -y
npx skills add sentimony/skills -s worktree-isolation -a codex claude-code -y
npx skills add sentimony/skills -s parallel-agents -a codex claude-code -y
npx skills add sentimony/skills -s plan-execution -a codex claude-code -y
npx skills add sentimony/skills -s plan-orchestration -a codex claude-code -y
npx skills add sentimony/skills -s branch-finish -a codex claude-code -y
npx skills add sentimony/skills -s skill-crafting -a codex claude-code -y
npx skills add sentimony/skills -s secret-hygiene -a codex claude-code -y
npx skills add sentimony/skills -s gh-switch -a codex claude-code -y
npx skills add sentimony/skills -s doc-preview -a codex claude-code -y
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

### Migrating from 0.0.93

From 0.0.94 all 28 skills are in the one `skills` plugin again: `devflow`, `writing`,
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

### Migrating to the renamed skills

0.0.102 renames five skills: `scope-check` to `doc-preview`, `git-worktree-isolation` to
`worktree-isolation`, `maintaining-agent-context` to `agent-instructions`, `inline-plan-dev`
to `plan-execution`, and `subagent-plan-dev` to `plan-orchestration`. Only the names and
their mentions changed. No files remain under the old names: remove the old skills and
install the new ones, or update the plugin. The `plan-orchestration` state root is now
`~/.sentimony/skills/plan-orchestration/`; resume still finds a run under
`~/.sentimony/skills/subagent-plan-dev/`, and plans that record an old name in
`Execution mode` keep working.

### Migrating from 0.0.83

From 0.0.84 through 0.0.99, `/scope-check` was a standalone preview skill and no longer
ran `scope-triage`. For current previews use `doc-preview`; invoke `scope-triage`
directly for design work.

## Skills

All skills ship in the `skills` plugin: `claude plugin install skills@sentimony`.

| Skill | Version | Description |
| --- | --- | --- |
| [scope-triage](skills/scope-triage/SKILL.md) | 0.0.17 | Classify request scope, guide design and approval, and preview a saved spec with its next step. |
| [doc-preview](skills/doc-preview/SKILL.md) | 0.0.9 | Preview a saved Markdown, JSON, YAML, TOML, CSV or text file in HTML with navigation, and keep the folder README index current. |
| [plan-crafting](skills/plan-crafting/SKILL.md) | 0.0.25 | Turn settled requirements into a TDD-oriented implementation plan and preview it with its next step. |
| [plan-execution](skills/plan-execution/SKILL.md) | 0.0.19 | Execute an implementation plan inline with plan-reality reconciliation, proportional verification, and durable resume; preserve task checkboxes, mode, and preview handoff state. |
| [plan-orchestration](skills/plan-orchestration/SKILL.md) | 0.0.20 | Execute an implementation plan through scoped subagents with risk-based dispatch, independent verification, and controlled escalation; preserve task checkboxes, mode, and preview handoff state. |
| [worktree-isolation](skills/worktree-isolation/SKILL.md) | 0.0.14 | Select, detect, or create a safe isolated development workspace with explicit ownership, baseline, and handoff. |
| [parallel-agents](skills/parallel-agents/SKILL.md) | 0.0.14 | Prove work units independent, isolate mutable state, and dispatch one bounded parallel wave with reconciled results. |
| [tdd](skills/tdd/SKILL.md) | 0.0.16 | Drive behavior changes through valid RED, sufficient GREEN, and evidence-backed refactoring. |
| [cross-review](skills/cross-review/SKILL.md) | 0.0.15 | Hand a plan or a finished implementation to the opposite agent CLI and the Antigravity CLI in parallel, or to one named reviewer, for an independent read-only review. |
| [review-request](skills/review-request/SKILL.md) | 0.0.14 | Prepare and dispatch independent code review against requirements, exact scope, and the actual diff. |
| [review-resolution](skills/review-resolution/SKILL.md) | 0.0.17 | Validate and resolve code-review findings with evidence, explicit dispositions, and proportional re-review decisions. |
| [debugging](skills/debugging/SKILL.md) | 0.0.20 | Investigate bugs and unexpected technical behavior with a root-cause-first evidence workflow. |
| [verification-gate](skills/verification-gate/SKILL.md) | 0.0.14 | Turn a completion claim into an evidence-backed verdict against the current tree. |
| [branch-finish](skills/branch-finish/SKILL.md) | 0.0.20 | Decide, execute and report the integration outcome for verified work, cleaning up only what is provably safe to remove. |
| [prose-crafting](skills/prose-crafting/SKILL.md) | 0.0.11 | Edit prose for its reader, purpose, and author's voice while preserving meaning; audit or explain editorial choices without scoring. |
| [dashfix](skills/dashfix/SKILL.md) | 0.0.19 | Replace typographic dashes with the plain hyphen in text of any language, keeping the spaces, and audit a project with a per-occurrence catalog. |
| [negafix](skills/negafix/SKILL.md) | 0.0.15 | Ban negative parallelism ("it's not just X, it's Y"), audit prose for it, and score it 0-100. |
| [skill-crafting](skills/skill-crafting/SKILL.md) | 0.0.12 | Create, improve, evaluate, optimize, split, merge, and retire agent skills with measured trigger boundaries and package-owned evals. |
| [echarts](skills/echarts/SKILL.md) | 0.0.19 | Build, audit, style, debug, and optimize Apache ECharts visualizations in vanilla JS, React, or Vue. |
| [web-debug](skills/web-debug/SKILL.md) | 0.0.16 | Debug and verify local web apps via Playwright. |
| [webapp-debugger](skills/webapp-debugger/SKILL.md) | 0.0.7 | Experimental, /webapp-debugger only: debug and verify local web apps via agent-browser. |
| [commit-all](skills/commit-all/SKILL.md) | 0.0.16 | Gather the working tree into one commit per repository the session changed, on the current branch or a new one the user picks, when the user asks to commit everything. |
| [gh-switch](skills/gh-switch/SKILL.md) | 0.0.11 | Switch the GitHub CLI to the account a project names in ~/.sentimony/skills/gh-switch/accounts.md before gh commands, check that its GitLab token belongs to the project's GL_ACC row, and report in one line. |
| [frontend-crafting](skills/frontend-crafting/SKILL.md) | 0.0.14 | Build, implement, redesign, review, and refine user-facing interfaces, including implementation-framed frontend changes, with subject-driven design decisions and a verifiable quality gate. |
| [vitest](skills/vitest/SKILL.md) | 0.0.17 | Configure, write, debug, run, migrate, and audit Vitest tests for JavaScript/TypeScript projects. |
| [typescript](skills/typescript/SKILL.md) | 0.0.22 | Configure tsconfig, diagnose compiler behavior, design type-safe APIs without silencing diagnostics, and audit or migrate TypeScript projects. |
| [agent-instructions](skills/agent-instructions/SKILL.md) | 0.0.21 | Create, audit, restructure, and maintain a repository's agent instruction architecture for Claude Code and Codex. |
| [secret-hygiene](skills/secret-hygiene/SKILL.md) | 0.0.7 | Use credentials for real work while keeping their values out of transcripts, logs, commits, and PR texts. |

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
`skill-crafting`, `tdd`, `debugging`, `web-debug`, `worktree-isolation`, `parallel-agents`,
`frontend-crafting`, `vitest`, `typescript`, `echarts`.

Have fun ;)
