# AGENTS.md

A public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). Each skill is a directory
`plugins/<plugin>/skills/<name>/` with `SKILL.md` and optional `references/`, `scripts/`,
`examples/`. The branch, PR, publish, and test workflow lives in
[CONTRIBUTING.md](CONTRIBUTING.md); read it before changing anything in this repository.

## Skills

| Plugin | Skill | Use when |
| --- | --- | --- |
| `devflow` | `scope-triage` | a request needs design decisions before code |
| `devflow` | `plan-crafting` | an approved design needs a multi-step implementation plan |
| `devflow` | `git-worktree-isolation` | deciding whether work needs an isolated workspace or worktree |
| `devflow` | `inline-plan-dev` | executing a plan in the current session |
| `devflow` | `subagent-plan-dev` | executing a plan through coordinated subagents |
| `devflow` | `parallel-agents` | several units of work might run concurrently through agents |
| `devflow` | `tdd` | implementing testable behavior changes, test first |
| `devflow` | `debugging` | investigating bugs, failures, flaky or unexpected behavior |
| `devflow` | `review-request` | an implementation needs an independent review against its requirements and diff |
| `devflow` | `cross-review` | a plan or implementation needs review by the other agent CLI (Codex, Claude Code, or Antigravity on request) |
| `devflow` | `review-resolution` | review findings or PR comments need validation before any fix |
| `devflow` | `verification-gate` | work is about to be called done, fixed, or mergeable |
| `devflow` | `branch-finish` | verified work is ready to merge, push, open a PR, or discard |
| `devflow` | `scope-check` | slash-only wrapper: `/scope-check` runs `scope-triage` |
| `writing` | `prose-crafting` | drafting or editing English or Ukrainian prose |
| `writing` | `dashfix` | writing prose or auditing typographic dashes |
| `writing` | `negafix` | writing prose or auditing "it's not just X, it's Y" constructions |
| `skill-crafting` | `skill-crafting` | designing, creating, evaluating, or retiring agent skills |
| `echarts` | `echarts` | building or debugging Apache ECharts charts |
| `skills` | `frontend-crafting` | building or reviewing user-facing interfaces |
| `skills` | `web-debug` | testing or debugging a local web app with Playwright |
| `skills` | `vitest` | configuring, writing, or debugging Vitest tests |
| `skills` | `typescript` | compiler errors, tsconfig, typing, and module resolution problems |
| `skills` | `maintaining-agent-context` | creating or auditing AGENTS.md, CLAUDE.md, and other agent instructions |
| `skills` | `secret-hygiene` | using credentials from env files or config with real services |
| `skills` | `gh-switch` | a project-scoped `gh` command is about to run on github.com |
| `skills` | `commit-all` | the user asks to commit all current changes without a message |
| `skills` | `webapp-debugger` | slash-only wrapper: `/webapp-debugger` runs `debugging` |

The `description` in each `SKILL.md` is the authoritative trigger; this table is a map.

## Install

With [skills](https://skills.sh) (all skills, or pick with `-s`):

```bash
npx skills add sentimony/skills -a codex claude-code -y
npx skills add sentimony/skills -s tdd cross-review -a codex claude-code -y
```

With [skl-x](https://www.npmjs.com/package/skl-x), the same arguments plus a summary
table, or symlinks from a local clone so edits apply without reinstalling:

```bash
npx -y skl-x add sentimony/skills -s tdd cross-review -a codex claude-code -y
npx -y skl-x sln <clone>/plugins/devflow/skills -a codex claude-code -y
```

As Claude Code plugins:

```bash
claude plugin marketplace add sentimony/skills
claude plugin install devflow@sentimony
```

As Codex plugins:

```bash
codex plugin marketplace add sentimony/skills
codex plugin add devflow@sentimony
```

The other plugins are `writing`, `skill-crafting`, `echarts`, and `skills`. Plugin skills
are namespaced by their plugin: `/devflow:scope-triage`.
