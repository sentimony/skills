# AGENTS.md

## Mission

This repository is a public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). One directory per skill:
`skills/<name>/` containing `SKILL.md`, `CHANGELOG.md`, `LICENSE`, and optionally
`examples/`, `scripts/`, `references/`. The current skill list lives in
[README.md](README.md).

## Language

Everything in this repository is written in English: documentation, SKILL.md content,
code comments, commit messages, and PR descriptions.

## Conventions

- `name` in SKILL.md frontmatter matches the directory name (letters, digits, hyphens only).
- `description` starts with "You MUST use this when…" and never summarizes the workflow itself.
- `license` is a valid SPDX identifier (e.g. `Apache-2.0`). Attribution/adaptation notes
  belong in reference files, not in frontmatter.
- Versioning: plain semver without prefix (`metadata.version: "1.1.0"` and CHANGELOG.md
  headings); the `v` prefix (e.g. `v1.0.0`) is used only for repository git tags.
- Each skill has a `CHANGELOG.md` in its directory (Keep a Changelog style). It is
  deliberately NOT referenced from SKILL.md so it never enters an agent's context.

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

`uvx snyk-agent-scan@latest scan skills/` runs the same Snyk engine locally (needs
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
| worktree-isolation | `references/attribution.md:10-13` | Secret detection (600/1000) | baseline: upstream commit SHA in four GitHub URLs |
| frontend-crafting | `references/attribution.md:15-19` | Secret detection (600/1000) | baseline: upstream commit SHAs in five GitHub URLs |
| echarts | `examples/vanilla_line.html:15` | Secret detection (600/1000) | baseline: an SRI `integrity` hash, which is a public content digest rather than a credential |

One finding sits outside that mechanism and is tracked separately:

| Skill | Location | Rule | Classification |
| --- | --- | --- | --- |
| review-resolution | `SKILL.md:3,18-19,433-435` | Third party content exposure (300/1000) | baseline: the skill exists to process review findings from PRs and CI, and it treats them as untrusted evidence rather than instructions |

The table was rebuilt from a full pre-flight on 2026-09-13 over the `inline-plan-dev`
branch. Earlier rows came from a 2026-09-07 scan of two skills only, and its text recorded
`echarts` as clean.

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
  and the skill's `CHANGELOG.md` in the same PR.
- Always update the repository-level [CHANGELOG.md](CHANGELOG.md) in the same PR as
  well; every release entry there must exist before the corresponding `vX.Y.Z` tag
  is created.
- When adding, renaming, or removing a skill, also update [skills.sh.json](skills.sh.json)
  so the skill appears in the right group on the skills.sh page.
- In the same PR, also update
  [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) so the Claude Code
  plugin marketplace exposes the skill; keep its plugin groups mirrored with the
  groupings in skills.sh.json.
- Validate before publishing a release: `gh skill publish --dry-run`; publish with
  `gh skill publish --tag vX.Y.Z` (creates the GitHub Release).
- CI validates SKILL.md frontmatter (name == directory, description present, plain
  semver `metadata.version`), compiles Python scripts/examples, checks for hidden/bidi
  Unicode, and runs every `test_*.py` it finds under `skills/`.
- Maintainer tests live beside the code they cover (`skills/<name>/scripts/test_*.py`).
  CI discovers them by filename and runs each as `python <file>` on a bare Python with
  no installed packages, so a module must be runnable standalone (`unittest.main()`)
  and import only the standard library and its own skill's scripts. A test covering an
  `examples/` file belongs in `scripts/` as well: `examples/` is copy-and-edit material
  a user takes into their own project, and a test harness has no place in it.
- The repository is already picked up by skills.sh; no onboarding steps are needed:
  merged changes to `main` are enough for installs via `npx skills add sentimony/skills`.
