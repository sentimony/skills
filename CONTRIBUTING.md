# Contributing

The skill catalog and install instructions live in [AGENTS.md](AGENTS.md) and
[README.md](README.md).

## Workflow

1. Develop in feature branches, never directly in `main`. Merge pull requests via squash
   merge only.
1. Update [README.md](README.md) and the repository-level [CHANGELOG.md](CHANGELOG.md) in
   the same PR; every release entry in CHANGELOG.md must exist before the corresponding
   `vX.Y.Z` tag is created.
1. A change to a skill bumps `metadata.version` in its SKILL.md (patch only: every
   change, including new behavior and breaking changes, bumps the patch number; the
   repository tag also moves by patch only) and adds
   an entry `## [x.y.z] - YYYY-MM-DD - [A.B.C]` to the skill's own `CHANGELOG.md`, where
   `A.B.C` is the repository release. Every skill keeps its `LICENSE` and SPDX `license`
   field; a fork keeps the upstream license text and notice verbatim.
1. A new skill goes into the "Skills" group of [skills.sh.json](skills.sh.json) and into the
   matching list in that group's description; CI fails on an ungrouped skill, which
   skills.sh would show below the groups.
1. Every skill lives in the root `skills/<name>/` directory of the one `skills` plugin.
   Hosts discover that directory by default; keep explicit additional skill paths out
   of the Claude Code and Antigravity manifests to avoid duplicate discovery.
   Root `plugin.json` and the three platform manifests carry the release version
   without the `v`. The Codex compatibility manifest retains its complete interface
   settings; the portable manifest supplies the shared identity.
   The marketplace lives in [sentimony/marketplace](https://github.com/sentimony/marketplace),
   not here: after a release tag, bump the `ref` of its `skills` entry there.
1. Validate before publishing a release: `gh skill publish --dry-run`; publish with
   `gh skill publish --tag vX.Y.Z` (creates the GitHub Release).

## Tests

1. Maintainer tests live beside the code they cover
   (`skills/<name>/scripts/test_*.py`).
   CI discovers them by filename and runs each as `python <file>` on a bare Python with
   no installed packages, so a module must be runnable standalone (`unittest.main()`)
   and import only the standard library and its own skill's scripts. A test covering an
   `examples/` file belongs in `scripts/` as well: `examples/` is copy-and-edit material
   a user takes into their own project, and a test harness has no place in it.

1. Root package checks live in `scripts/check_plugin_layout.py` and
   `scripts/test_plugin_layout.py`. Run the checker normally for current metadata, or
   use `--baseline <full-pre-move-commit-SHA>` for a one-time byte/type/mode migration
   comparison. Default CI permits future skill changes.
