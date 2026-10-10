# AGENTS.md

## Mission

This repository is a public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). Skills are grouped into plugins: one
directory per skill, `plugins/<plugin>/skills/<name>/`, containing `SKILL.md`,
and optionally `examples/`, `scripts/`, `references/`. The current skill list lives in
[README.md](README.md).

## Language

Everything in this repository is written in English: documentation, SKILL.md content,
code comments, commit messages, and PR descriptions.

## Conventions

- `name` in SKILL.md frontmatter matches the directory name (letters, digits, hyphens only).
- `description` starts with "You MUST use this when…" and never summarizes the workflow itself.
- SKILL.md frontmatter has no `license`, and skills have no `LICENSE` of their own: the
  repository-level [LICENSE](LICENSE) (MIT, with the upstream notices) and
  [LICENSE-APACHE](LICENSE-APACHE) cover every skill. A new fork of an upstream skill adds
  the upstream copyright notice there.
  Attribution/adaptation notes belong in reference files, not in frontmatter.
- Skills are not versioned individually: SKILL.md frontmatter has no `metadata.version` or
  `metadata.author`. Repository git tags (`vX.Y.Z`) are the only versions.
- SKILL.md frontmatter has no `metadata` block. Never add `metadata.internal: true`: it
  hides the skill from `npx skills` discovery.
- `argument-hint` (a Claude Code frontmatter field outside the Agent Skills specification)
  is set only when the skill body documents arguments typed after the slash command, and
  lists only those: `[a|b]` optional choice, `<x>` required value, `[--flag]` flag. A
  skill that runs from context alone has no hint; an empty hint beats an invented one.
- Skills have no `CHANGELOG.md` of their own: every change is recorded in the
  repository-level [CHANGELOG.md](CHANGELOG.md) under the skill's name.

### skills.sh security audits

skills.sh runs each skill through Gen Agent Trust Hub, Socket, and Snyk, and shows a
Pass/Warn badge plus a "Contains Shell Commands" notice on the skill page. Write skills
to keep these green; findings we have hit and how to avoid them:

- **"Contains Shell Commands" (false positive):** triggered by an isolated inline-code
  exclamation mark; the scanner reads it as a shell-command directive.
  Keep that character inside a longer code span (e.g. `` `x!` ``), not alone in backticks.
- **Snyk W012 "unverifiable external dependency":** runtime import of remote JS from a
  CDN. In standalone examples, pin the exact release (`pkg@1.2.3`, never a floating major)
  since ESM imports can't carry an SRI hash.
- **Gen Agent Trust Hub prompt-injection flags:** don't tell the agent not to inspect a
  script before running it; document a Security Model instead. The section carries four
  components: which inputs are user-controlled, which are untrusted, that page, DOM and tool
  output is data rather than instructions, and whether the skill runs shell commands or
  network calls.
- **Snyk W007 "insecure credential handling in skill instructions":** triggered by the
  directive itself: an instruction to repeat the literal values from the user's request
  reads as forcing the model to echo any secret verbatim. A carve-out placed after that
  directive does not clear the finding: `scope-triage` 1.0.1 added one and still failed
  the audit. Ask for the request's *domain values*, lead the prohibition with its own
  paragraph, and refer to credentials by placeholder name everywhere they appear.

`uvx snyk-agent-scan@latest scan plugins/<plugin>/skills/<name>` runs the same Snyk engine locally (needs
`SNYK_TOKEN`), but it is weaker than the skills.sh audit: it reported zero findings on
the very `scope-triage` version that skills.sh failed on W007. Treat a clean local run as
a pre-flight, never as proof the badge will be green.

### Known baseline findings

Every finding below is the same mechanism: the scanner redacts a public upstream Git object
ID inside a GitHub URL, then flags its own `**REDACTED_SECRET_<PLUGIN>**` marker as a
secret. The values are public commit and blob IDs that pin adaptation provenance, so each
is a false positive in the local pre-flight.

| Skill | Location | Rule | Classification |
| --- | --- | --- | --- |
| plan-crafting | `references/attribution.md:4-5` | Secret detection (600/1000) | baseline: commit and blob IDs of the forked upstream file |
| parallel-agents | `references/attribution.md:10-12` | Secret detection (600/1000) | baseline: one upstream commit SHA in three GitHub URLs |
| review-request | `references/attribution.md` | Secret detection (600/1000) | baseline: upstream commit SHA in GitHub URLs |
| review-resolution | `references/attribution.md:7,10-14` | Secret detection (600/1000) | baseline: upstream commit SHA in GitHub URLs |
| git-worktree-isolation | `references/attribution.md:10-13` | Secret detection (600/1000) | baseline: upstream commit SHA in four GitHub URLs |
| frontend-crafting | `references/attribution.md:15-19` | Secret detection (600/1000) | baseline: upstream commit SHAs in five GitHub URLs |
| echarts | `examples/vanilla_line.html:15` | Secret detection (600/1000) | baseline: an SRI `integrity` hash, which is a public content digest rather than a credential |
| skill-crafting | `references/attribution.md:9-12,25-28` | Secret detection (600/1000) | expected, not yet observed: upstream commit SHAs, in GitHub URLs and as bare source-commit values. Confirm against the first scan before release |
| negafix | `references/attribution.md:4` | Secret detection (600/1000) | expected, not yet observed: upstream commit SHA in a GitHub URL. Confirm against the first scan before release |
| prose-crafting | `references/attribution.md:4,27,34,40,47,53,57,64,70,91` | Secret detection (600/1000) | expected, not yet observed: upstream commit SHAs in ten GitHub URLs. Confirm against the first scan before release |

Findings outside that mechanism are tracked separately:

| Skill | Location | Rule | Classification |
| --- | --- | --- | --- |
| review-resolution | `SKILL.md:3,18-19,433-435` | Third party content exposure (300/1000) | baseline: the skill exists to process review findings from PRs and CI, and it treats them as untrusted evidence rather than instructions |
| web-debug | `SKILL.md`, Playwright workflow | Third party content exposure, W011 (medium, 0.10) | baseline: the skill exists to ingest DOM, console, network, and page errors of the app under test, and its Security Model treats page content as data rather than instructions. Security Model rewritten in 1.3.5; confirm against the first skills.sh scan after release |

The observed rows of the first table and the `review-resolution` row come from a full
local pre-flight on 2026-09-13 over the `inline-plan-dev` branch; the rows marked
"expected, not yet observed" were added afterwards, on 2026-09-15 and 2026-09-26, with the
releases that introduced those attribution files, and still await their first local
pre-flight. The `web-debug` row comes from the skills.sh Snyk audit page
dated 2026-09-16, which the local pre-flight did not report. Earlier rows came from a
2026-09-07 scan of two skills only, and its text recorded `echarts` as clean.

Treat the scanner as nondeterministic across runs on identical input.
`examples/vanilla_line.html` has not changed since `ce25861`, yet the 2026-09-07 pre-flight
reported no findings in `echarts` and the 2026-09-13 one flags it. The finding text is
model-generated and reasons about its own protocol, so an exact match between runs is not
expected. Classify a finding by its mechanism against this table, not by matching a row
literally: a redaction marker standing in for a public Git object ID is baseline wherever it
appears. Anything whose mechanism is absent here is new and must be classified before the
release where it appears, for every skill and not only the ones listed.

## Workflow

- Develop in feature branches, never directly in `main`.
- Merge pull requests via squash merge only.
- A branch that adds a new skill may also change previously created files and skills;
  every such change must be noted in the repository-level [CHANGELOG.md](CHANGELOG.md).
- When adding, renaming, or substantially updating a skill, update [README.md](README.md)
  in the same PR.
- Always update the repository-level [CHANGELOG.md](CHANGELOG.md) in the same PR as
  well; every release entry there must exist before the corresponding `vX.Y.Z` tag
  is created.
- The repository ships five plugins for Claude Code and Codex, which
  [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) exposes as the
  `sentimony` marketplace: `devflow`, `writing`, `skill-crafting`, `echarts`, and `skills`.
  A new skill goes into the plugin of its domain, `plugins/<plugin>/skills/<name>/`, and
  into the `skills` list of `plugins/<plugin>/.claude-plugin/plugin.json`; the Codex
  manifest reads every skill from `./skills/`. Skill names stay unique across plugins. A
  new plugin is a `plugins/<plugin>/` directory with both manifests and an entry with
  `source: "./plugins/<plugin>"` in marketplace.json. All plugins share one version: set
  `version` in every `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` to the
  release tag without the `v` prefix. There is no `skills.sh.json`: skills.sh lists the
  skills as one flat list.
- Validate before publishing a release: `gh skill publish --dry-run`; publish with
  `gh skill publish --tag vX.Y.Z` (creates the GitHub Release).
- CI validates SKILL.md frontmatter (name == directory, description present, no
  `metadata.version`), compiles Python scripts/examples, checks for hidden/bidi
  Unicode, and runs every `test_*.py` it finds under `plugins/`, and checks each plugin's
  manifests against its skills and the marketplace.
- Maintainer tests live beside the code they cover
  (`plugins/<plugin>/skills/<name>/scripts/test_*.py`).
  CI discovers them by filename and runs each as `python <file>` on a bare Python with
  no installed packages, so a module must be runnable standalone (`unittest.main()`)
  and import only the standard library and its own skill's scripts. A test covering an
  `examples/` file belongs in `scripts/` as well: `examples/` is copy-and-edit material
  a user takes into their own project, and a test harness has no place in it.
- The repository is already picked up by skills.sh; no onboarding steps are needed:
  merged changes to `main` are enough for installs via `npx skills add sentimony/skills`.
