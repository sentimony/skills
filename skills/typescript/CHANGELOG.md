# Changelog

All notable changes to the `typescript` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.3.0] - 2026-07-30

### Added
- Nuxt solution inspection for app, server, shared, and node generated programs with
  independent effective flags and production/tests/config coverage counts
- A stable `NUXT_GENERATED_CONFIGS_MISSING` diagnostic and Nuxt configuration ownership
  reference, without running prepare or exposing compiler file output
- Node runtime preflight with stable `NODE_RUNTIME_MISMATCH` and `NODE_RUNTIME_UNKNOWN`
  diagnostics before a typecheck can be misread as a TypeScript failure

### Changed
- Typecheck fallbacks use only existing local binaries; they no longer invoke direct
  package download launchers
- Typecheck summaries expose stable diagnostic/error codes and counts rather than raw
  compiler messages or filenames
- Nuxt coverage scans all repository candidates without a silent cap, keeps config
  paths/labels internal, and withholds aggregate counts when a local compiler fails
- Nuxt program inspection bounds compiler output bytes, individual output lines,
  and execution time; over-limit or non-terminating compilers are stopped, reaped,
  and represented only by stable diagnostics with unavailable coverage
- Node preflight strictly parses concrete versions and reports unsupported engine ranges
  as `NODE_RUNTIME_UNKNOWN`
- Performance tracing uses the verified local TypeScript compiler and never selects or
  recommends a package download launcher
- Performance tracing reports a stable `TRACE_LOCAL_COMPILER_UNAVAILABLE` diagnostic
  instead of exposing a local compiler path when its launcher cannot start
- Inspector package identity fields use stable installation/module/native-detection
  statuses instead of returning arbitrary package metadata values
- Uncovered source files are reported as production/tests/config counts instead of
  file paths, so repository-controlled names stay out of the report
- `typescript_installation` now carries the installation source and `typescript_version`
  a strictly parsed version or range, instead of the source occupying the version field
- Local compiler lookup walks up to the repository root, so a package-level `--root`
  finds a binary hoisted to a workspace root
- Nuxt inspection reports the generated programs that exist and flags the missing ones,
  instead of discarding every program when one config is absent
- Compiler-controlled paths are normalized as strings only, without a filesystem lookup

### Removed
- Unused package-manager detection from the performance tracer, and the unused
  by-file error grouping from the typecheck summary; the tracer now reports a single
  `TRACE_LOCAL_COMPILER_UNAVAILABLE` diagnostic for a missing local compiler

## [1.2.2] - 2026-07-20

Driven by real-world audit feedback from a Nuxt project (agilecharts) and two
earlier TypeScript 7 migration sessions.

### Added
- Audit & Hardening: "already healthy" rule — a green typecheck with the full
  strict set enabled means skip straight to the hygiene grep and report healthy
- Audit & Hardening: sampling heuristic for massive finding classes (30+
  non-null assertions → review a 10–15% sample and extrapolate)
- Framework Projects: generic `defineProps` as the fix for `config: any` props
  in Vue components
- Error playbook (quick table + reference): `ERR_PACKAGE_PATH_NOT_EXPORTED
  './lib/tsc'` after a direct `typescript@^7` bump — keep 6.x, alias 7
- typescript-7-migration reference: "Choosing the TS-7 target" checklist for
  greenfield side-by-side setups, plus a `types: []` vs `lib` globals note

## [1.2.1] - 2026-07-19

### Changed
- Description rewritten in "You MUST use this when…" style

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
  as `` `x!` `` instead of an isolated backticked exclamation mark; the scanner read
  the latter as a shell-command directive and flagged the skill.

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
