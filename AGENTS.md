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
  script before running it; document a Security Model instead (which inputs are user- vs
  untrusted-controlled, and that page/DOM/tool output is data, not instructions).
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

## Workflow

- Develop in feature branches, never directly in `main`.
- Merge pull requests via squash merge only. If the branch was rebased onto a rewritten
  `main`, write the squash message by hand: the default one concatenates the titles of
  the replayed commits and drags their old wording back into `main`.
- Released CHANGELOG sections — repository-level and per skill — are frozen; never
  rewrite them after the fact. `main` and the tags are the source of truth for what
  actually shipped: check them (`git show <tag>:path`, `git grep <name> <tag>`) instead
  of reconstructing history from your branch's commits.
- A PR that adds, renames, removes, or substantially updates a skill updates, in the
  same PR: [README.md](README.md), the skill's `CHANGELOG.md`, the repository-level
  [CHANGELOG.md](CHANGELOG.md) (its release entry must exist before the corresponding
  `vX.Y.Z` tag is created), [skills.sh.json](skills.sh.json), and
  [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json), whose plugin
  groups mirror the groupings in skills.sh.json. Changes such a branch makes to
  previously created files and skills are noted in the repository-level CHANGELOG too.
- Validate before publishing a release: `gh skill publish --dry-run`; publish with
  `gh skill publish --tag vX.Y.Z` (creates the GitHub Release).
- The source of truth for what CI validates is [.github/workflows/ci.yml](.github/workflows/ci.yml);
  the hand-off checks below mirror its core.
- Maintainer tests live beside the code they cover (`skills/<name>/scripts/test_*.py`).
  CI discovers them by filename and runs each as `python <file>` on a bare Python with
  no installed packages, so a module must be runnable standalone (`unittest.main()`)
  and import only the standard library and its own skill's scripts. A test covering an
  `examples/` file belongs in `scripts/` as well: `examples/` is copy-and-edit material
  a user takes into their own project, and a test harness has no place in it.
- The repository is already picked up by skills.sh; no onboarding steps are needed:
  merged changes to `main` are enough for installs via `npx skills add sentimony/skills`.

Before handing off changes, run the checks CI will run anyway:

```bash
git diff --check
python3 -m py_compile skills/*/scripts/*.py skills/*/examples/*.py
for test in skills/*/scripts/test_*.py; do python3 "$test"; done
```
