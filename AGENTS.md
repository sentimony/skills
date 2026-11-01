# AGENTS.md

A public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). Each skill is a directory
`plugins/skills/skills/<name>/` in the one `skills` plugin, with `SKILL.md` and optional `references/`, `scripts/`,
`examples/`. The branch, PR, publish, and test workflow lives in
[CONTRIBUTING.md](CONTRIBUTING.md); read it before changing anything in this repository.

## Skills

| Skill | Use when |
| --- | --- |
| `scope-triage` | a request needs design decisions before code |
| `plan-crafting` | an approved design needs a multi-step implementation plan |
| `git-worktree-isolation` | deciding whether work needs an isolated workspace or worktree |
| `inline-plan-dev` | executing a plan in the current session |
| `subagent-plan-dev` | executing a plan through coordinated subagents |
| `parallel-agents` | several units of work might run concurrently through agents |
| `tdd` | implementing testable behavior changes, test first |
| `debugging` | investigating bugs, failures, flaky or unexpected behavior |
| `review-request` | an implementation needs an independent review against its requirements and diff |
| `cross-review` | a plan or implementation needs review by other agent CLIs (by default the opposite of Codex and Claude Code, plus Antigravity) |
| `review-resolution` | review findings or PR comments need validation before any fix |
| `verification-gate` | work is about to be called done, fixed, or mergeable |
| `branch-finish` | verified work is ready to merge, push, open a PR, or discard |
| `scope-check` | a spec or plan was saved or edited and needs an HTML preview and README index entry |
| `prose-crafting` | drafting or editing English or Ukrainian prose |
| `dashfix` | writing prose or auditing typographic dashes |
| `negafix` | writing prose or auditing "it's not just X, it's Y" constructions |
| `skill-crafting` | designing, creating, evaluating, or retiring agent skills |
| `echarts` | building or debugging Apache ECharts charts |
| `frontend-crafting` | building or reviewing user-facing interfaces |
| `web-debug` | testing or debugging a local web app with Playwright |
| `vitest` | configuring, writing, or debugging Vitest tests |
| `typescript` | compiler errors, tsconfig, typing, and module resolution problems |
| `maintaining-agent-context` | creating or auditing AGENTS.md, CLAUDE.md, and other agent instructions |
| `secret-hygiene` | using credentials from env files or config with real services |
| `gh-switch` | a project-scoped `gh` command is about to run on github.com, or a GitLab API call in a project with `GL_ACC` |
| `commit-all` | the user asks to commit all current changes without a message |
| `webapp-debugger` | slash-only: testing or debugging a local web app with agent-browser |

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
npx -y skl-x sln <clone>/plugins/skills/skills -a codex claude-code -y
```

As a Claude Code plugin from [sentimony/marketplace](https://github.com/sentimony/marketplace):

```bash
claude plugin marketplace add sentimony/marketplace
claude plugin install skills@sentimony
```

As a Codex plugin:

```bash
codex plugin marketplace add sentimony/marketplace
codex plugin add skills@sentimony
```

All skills ship in the `skills` plugin; this repository hosts no marketplace. After a release,
`sentimony/marketplace` bumps the `skills` entry `ref` to the new `vX.Y.Z` tag. Plugin skills are
namespaced by their plugin: `/skills:scope-triage`.

## ADR

1. Before an architectural change, read relevant current decisions (`docs/adr`), the [ADR policy](docs/adr-adoption/policy.md), and [template](docs/adr-adoption/templates/adr.md); show conflicts to the owner and record important approved choices under that policy.
