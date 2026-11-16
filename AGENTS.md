# AGENTS.md

A public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). Each skill is a directory
`skills/<name>/` in the one `skills` plugin, with `SKILL.md` and optional
`references/`, `scripts/`, `examples/`. The branch, PR, publish, and test workflow lives in
[CONTRIBUTING.md](CONTRIBUTING.md); read it before changing anything in this repository.

## Skills

| Skill | Use when |
| --- | --- |
| `scope-triage` | a request needs design decisions before code |
| `plan-craft` | an approved design needs a multi-step implementation plan |
| `worktree-isolation` | deciding whether work needs an isolated workspace or worktree |
| `implement` | executing a plan in the current session |
| `subagents-implement` | executing a plan through coordinated subagents |
| `parallel-agents` | several units of work might run concurrently through agents |
| `tdd` | implementing testable behavior changes, test first |
| `debug` | investigating bugs, failures, flaky or unexpected behavior |
| `request-review` | an implementation needs an independent review against its requirements and diff |
| `cross-review` | a plan or implementation needs review by other agent CLIs (by default the opposite of Codex and Claude Code, plus Antigravity) |
| `received-review` | review findings or PR comments need validation before any fix |
| `verify-gate` | work is about to be called done, fixed, or mergeable |
| `finalize` | verified work is ready to merge, push, open a PR, or discard |
| `md-preview` | a saved Markdown/JSON/YAML/TOML/CSV/text file needs an HTML preview and README index entry |
| `prose-craft` | drafting or editing English or Ukrainian prose |
| `dashfix` | writing prose or auditing typographic dashes |
| `negafix` | writing prose or auditing "it's not just X, it's Y" constructions |
| `skill-crafting` | designing, creating, evaluating, or retiring agent skills |
| `echarts` | building or debugging Apache ECharts charts |
| `frontend-craft` | building or reviewing user-facing interfaces |
| `playwright-debug` | testing or debugging a local web app with Playwright |
| `vitest` | configuring, writing, or debugging Vitest tests |
| `typescript` | compiler errors, tsconfig, typing, and module resolution problems |
| `maintain-agents-md` | creating or auditing AGENTS.md, CLAUDE.md, and other agent instructions |
| `secret-hygiene` | using credentials from env files or config with real services |
| `gh-switch` | a project-scoped `gh` command is about to run on github.com, or a GitLab API call in a project with a GitLab remote |
| `commit-all` | the user asks to commit all current changes without a message |
| `agent-browser-debug` | slash-only: testing or debugging a local web app with agent-browser |
| `session-learnings` | session pitfalls or corrections should reach future agents, or accumulated notes need triage |
| `transfer-context` | saving, resuming or checking a checkpoint to hand work to a new session |

The `description` in each `SKILL.md` is the authoritative trigger; this table is a map.

## Renaming and the skills.sh catalog

1. Renaming a released skill moves `skills/<old>/` to `skills/<new>/` like a directory rename:
   no file of the old skill remains. Its files change only in the name and its mentions; the
   version continues with a patch bump, and the CHANGELOG entry names the old name. The old
   name goes to the last `Deprecated` group of `skills.sh.json`. Content changes go in a
   separate PR and version.
1. `skills.sh.json` lists every skill skills.sh knows for this repository: a name missing
   from it shows on the skills.sh page under an unwanted `Other skills` heading. Any change
   that adds, renames, moves out or removes a skill updates the file in the same PR. A skill
   under `skills/` goes to the `Skills` group, both its `skills` list and the parentheses of
   its description, in README order. A name with no files left goes to the last `Deprecated`
   group, and that group's description records it in two pairs of parentheses, entries
   separated by ` · `: renamed skills as `old → new` (`cr-receive → cr-received`), skills
   moved to another repository as `skill → owner/repo` (`cross-cr → sentimony/cross-agent`).
   A name renamed twice maps to its current name.

## Improving a skill

1. A plan or spec that improves one of this repository's skills contains a `skill-tuning` task
   for that skill. The task checks the frontmatter and the body length, and compares a changed
   `description` before and after and against trigger cases. A `description` that grew in the
   plan is a review finding, not a detail.

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
npx -y skl-x sln <clone>/skills -a codex claude-code -y
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
