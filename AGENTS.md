# AGENTS.md

## Mission

This repository is a public collection of agent skills, published on
[skills.sh](https://skills.sh/sentimony/skills). One directory per skill:
`skills/<name>/SKILL.md`. The current skill list lives in [README.md](README.md).

## Language

Everything in this repository is written in English: documentation, SKILL.md content,
code comments, commit messages, and PR descriptions.

## Conventions

- `name` in SKILL.md frontmatter matches the directory name (letters, digits, hyphens only).
- `description` is third-person, "Use when…" style, and never summarizes the workflow itself.
- `license` is a valid SPDX identifier (e.g. `Apache-2.0`). Attribution/adaptation notes
  belong in reference files, not in frontmatter.
- Versioning: plain semver without prefix (`metadata.version: "1.1.0"` and CHANGELOG.md
  headings); the `v` prefix (e.g. `v1.0.0`) is used only for repository git tags.
- Each skill has a `CHANGELOG.md` in its directory (Keep a Changelog style). It is
  deliberately NOT referenced from SKILL.md so it never enters an agent's context.

## Workflow

- Develop in feature branches, never directly in `main`.
- Merge pull requests via squash merge only.
- When adding, renaming, or substantially updating a skill, update [README.md](README.md)
  and the skill's `CHANGELOG.md` in the same PR.
- Validate before publishing a release: `gh skill publish --dry-run`.
- The repository is already picked up by skills.sh; no onboarding steps are needed —
  merged changes to `main` are enough for installs via `npx skills add sentimony/skills`.
