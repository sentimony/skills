# Changelog

All notable changes to the `typescript` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.2.0] - 2026-07-13

Driven by real-world feedback from a Vue/Netlify TypeScript 7 side-by-side migration.

### Added
- `inspect_typescript.py`: detects a side-by-side native compiler (a TypeScript 7
  alias installed next to the framework's TypeScript 6) and reports which tsconfig
  each `typecheck*` script targets, so multi-compiler setups are auditable
- `references/typescript-7-migration.md`: real-package dual-install layout that
  keeps `typescript` on genuine 6.x for vue-tsc/Volar (the compat-shim layout
  breaks Volar with "Failed to locate tsc module path from shim"), plus CI guidance
  to gate every compiler path

### Changed
- `inspect_typescript.py`: effective-flags report now includes `noImplicitOverride`,
  `noFallthroughCasesInSwitch`, `noUnusedLocals`, and `noUnusedParameters`; coverage
  now prints an explicit "complete / 0 uncovered" result instead of staying silent
- Audit & Hardening: clarified what "pinned" means (major/minor range vs exact pin)
  and to audit every `typecheck*` script against CI, not only `typecheck`
- Noted that `<skill>` should resolve to an absolute path in a git worktree, where
  the gitignored `.agents`/`.claude` skill symlinks may be absent

## [1.1.1] - 2026-07-12

Avoids the skills.sh "Contains Shell Commands" false-positive warning.
No behavior change.

### Changed
- Reworded the hygiene-grep item so the non-null assertion operator is written
  as `` `x!` `` instead of an isolated `` `!` ``; the scanner read the latter as a
  shell-command directive (``!`command` ``) and flagged the skill.

## [1.1.0] - 2026-07-11

### Added
- Focused `references/typescript-7-migration.md` guide for the stable native
  compiler: TypeScript 6 bridge, configuration cleanup, side-by-side compiler
  adoption, compiler-API constraints, framework compatibility, verification,
  and rollback
- Decision-tree route and quick error-playbook entries for TypeScript 7
  deprecations, missing global types, and API-dependent tooling failures

### Changed
- Description now triggers for compiler-major migrations such as TypeScript 7
- Configuration guidance now verifies the installed compiler version before a
  major-version migration

Research checked on 2026-07-11 against the TypeScript team's
[TypeScript 7.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
(2026-07-08), [TypeScript 6.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)
(2026-03-23), and the official
[`microsoft/typescript-go`](https://github.com/microsoft/typescript-go) repository.

## [1.0.1] - 2026-07-07

Driven by feedback from four real-world sessions (Vue/Nuxt audits and hardening tasks).

### Added
- Framework Projects section: vue-tsc / nuxi typecheck / svelte-check / astro check,
  framework-generated tsconfig guidance (never edit `.nuxt/tsconfig.*` etc.)
- Audit & Hardening section: setup/coverage/strictness checklist, hygiene grep
  patterns with prioritization, strictness flags ordered by fixing cost
- `inspect_typescript.py`: framework checker detection, report of source files
  not covered by any tsconfig (skipped for generated-config frameworks)
- `run_typecheck.py`: uses vue-tsc when present, falls back to `nuxi typecheck`
  for Nuxt projects
- Error playbook: TS5101 (`baseUrl` deprecated), `__VLS_ctx` / TS18048 in Vue SFCs

### Changed
- Decision tree: skip helper scripts when project docs already name the typecheck
  command or the project has a single tsconfig without extends
- Rule 5 (never silence errors with any/as/@ts-ignore): explicit exception for
  casts at test mock boundaries
- description: added audit/hardening trigger; excludes general feature work in TS codebases

## [1.0.0] - 2026-07-05

Initial release.

### Added
- SKILL.md covering tsconfig configuration, compiler error resolution, slow
  type-checking diagnostics, module resolution / ESM-CJS issues, JS-to-TS
  migration, and monorepo project references
- `scripts/inspect_typescript.py`, `scripts/run_typecheck.py`,
  `scripts/trace_perf.py` helper scripts
- `references/`: error-playbook, module-resolution, migration, monorepo
