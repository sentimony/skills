# Changelog

All notable changes to the `typescript` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.0] - 2026-07-05

Initial release.

### Added
- SKILL.md covering tsconfig configuration, compiler error resolution, slow
  type-checking diagnostics, module resolution / ESM-CJS issues, JS-to-TS
  migration, and monorepo project references
- `scripts/inspect_typescript.py`, `scripts/run_typecheck.py`,
  `scripts/trace_perf.py` helper scripts
- `references/`: error-playbook, module-resolution, migration, monorepo
