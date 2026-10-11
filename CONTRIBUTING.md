# Contributing

The skill catalog and install instructions live in [AGENTS.md](AGENTS.md) and
[README.md](README.md).

## Workflow

- Develop in feature branches, never directly in `main`. Merge pull requests via squash
  merge only.
- Update [README.md](README.md) and the repository-level [CHANGELOG.md](CHANGELOG.md) in
  the same PR; every release entry in CHANGELOG.md must exist before the corresponding
  `vX.Y.Z` tag is created.
- A change to a skill bumps `metadata.version` in its SKILL.md (semver: patch for fixes
  and wording, minor for new behavior or an argument, major for a breaking change) and adds
  an entry `## [x.y.z] - YYYY-MM-DD - [A.B.C]` to the skill's own `CHANGELOG.md`, where
  `A.B.C` is the repository release. Every skill keeps its `LICENSE` and SPDX `license`
  field; a fork keeps the upstream license text and notice verbatim.
- Validate before publishing a release: `gh skill publish --dry-run`; publish with
  `gh skill publish --tag vX.Y.Z` (creates the GitHub Release).

## Tests

- Maintainer tests live beside the code they cover
  (`plugins/<plugin>/skills/<name>/scripts/test_*.py`).
  CI discovers them by filename and runs each as `python <file>` on a bare Python with
  no installed packages, so a module must be runnable standalone (`unittest.main()`)
  and import only the standard library and its own skill's scripts. A test covering an
  `examples/` file belongs in `scripts/` as well: `examples/` is copy-and-edit material
  a user takes into their own project, and a test harness has no place in it.
