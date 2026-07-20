---
name: typescript
description: You MUST use this when configuring tsconfig, resolving compiler errors, debugging slow type-checking, fixing module resolution or ESM/CJS issues, hardening strictness, migrating JavaScript or compiler majors such as TypeScript 7, or setting up type-checking in monorepos. Not for general feature work in TypeScript code.
metadata:
  author: Ihor Orlovskyi
  version: "1.2.2"
license: MIT
compatibility: Requires Python and a JavaScript package manager; TypeScript must be installed in the target project (locally or resolvable via npx).
---

# TypeScript

Use this skill to configure, diagnose, and fix TypeScript projects. It is a workflow, not a language reference: the type system syntax is assumed knowledge, and the focus is on compiler behavior, configuration, and cryptic failures.

**Helper Scripts Available**:
- `scripts/inspect_typescript.py` - Detects package manager, TypeScript version, a side-by-side native compiler (TypeScript 7 alias) and which tsconfig each `typecheck*` script targets, tsconfig files with extends chains and effective flags, framework checker (vue-tsc, nuxi, svelte-check, astro), source files not covered by any tsconfig, monorepo markers, linter, runner, and the recommended typecheck command
- `scripts/run_typecheck.py` - Runs type-checking through the detected package manager and summarizes errors by code and file
- `scripts/trace_perf.py` - Measures compilation via `--extendedDiagnostics`, flags anomalies, optionally writes a compiler trace

`<skill>` means the path to this local skill folder. Run helper scripts with `--help` when usage is unclear or before first use in a session. Prefer using helper scripts as black-box tools. Read or modify their source only when debugging the skill itself or when behavior is unclear. In a git worktree, resolve `<skill>` to the skill's absolute path: a relative `.agents/skills/...` (or `.claude/skills/...`) path may be gitignored and absent from the worktree checkout.

## Decision Tree

```
User task -> Existing project?
    - Yes -> Project docs (CLAUDE.md/AGENTS.md/README) or package.json already
             name the typecheck command, and it is a single tsconfig without
             extends? -> Use that command directly; skip the helper scripts.
             Otherwise run: python <skill>/scripts/inspect_typescript.py --root <project>
             Use detected manager, tsconfig chain, effective flags, monorepo layout.
    - No  -> Create the smallest strict tsconfig matching the runtime.
             Do not paste large config templates; set only what the project needs.

Next -> What is the symptom?
    - Type errors after a change      -> run_typecheck.py, then Error Playbook below
    - Cryptic compiler error          -> references/error-playbook.md
    - "Cannot find module" / imports  -> references/module-resolution.md
    - Slow tsc / slow editor          -> trace_perf.py, then Performance below
    - Audit / harden a green project -> Audit & Hardening below
    - JavaScript to TypeScript        -> references/migration.md
    - TypeScript 7 / native compiler  -> references/typescript-7-migration.md
    - Monorepo / project references   -> references/monorepo.md
    - New tsconfig / stricter flags   -> Configuration below
```

The helper scripts pay off in monorepos and extends chains; on a small project with one tsconfig, reading the config and running the checker directly is faster.

## Core Workflow

1. Inspect first: discover the package manager, tsconfig extends chain, effective flags, and monorepo layout before changing anything.
2. Match the project: keep its `module`/`moduleResolution` pair, its extends chain, and its package manager. Do not switch resolution strategies to silence one error.
3. Prefer the minimal fix: one flag, one type annotation, one dependency — not a rewritten tsconfig.
4. Verify narrowly first: `run_typecheck.py --project <pkg tsconfig>` or `--files` before a full-repo check.
5. Never "fix" an error with `any`, `as`, or `@ts-ignore` to get to green. Reaching for them means the actual cause is not yet understood; find it first, and use targeted narrowing or a documented `@ts-expect-error` only as a last resort. One pragmatic exception: casts at test mock boundaries (`mock as unknown as Service`) are acceptable in test files; production code is not.

## Configuration

Direction for new or hardened configs (adopt, do not paste wholesale):

- `strict: true` is the baseline; add `noUncheckedIndexedAccess` and `noImplicitOverride` when the codebase can absorb them.
- In an existing project, enable new strictness flags one at a time and fix fallout per flag; do not flip several at once.
- `module`/`moduleResolution`: `NodeNext` for Node libraries and servers, `ESNext`/`bundler` for bundled apps. These two options must be chosen as a pair; see references/module-resolution.md.
- `skipLibCheck: true` is a pragmatic default; remove it only when debugging a broken dependency's types.
- Respect the extends chain: change the leaf config for a package-local need, the base config for a repo-wide policy.
- Before a compiler-major migration, read the installed version from `node_modules/typescript/package.json`; dependency ranges and global `tsc` can describe a different compiler. For TypeScript 7, follow references/typescript-7-migration.md.
- Order new flags by fixing cost: `noUnusedLocals`/`noUnusedParameters` (cheap) -> `noFallthroughCasesInSwitch`/`noImplicitOverride` (near-free) -> `exactOptionalPropertyTypes` -> `noUncheckedIndexedAccess` (most expensive, last).

## Framework Projects (Vue, Nuxt, Svelte, Astro)

Plain `tsc --noEmit` silently ignores `.vue`/`.svelte`/`.astro` component files — a green run proves nothing there. Use the framework's checker:

| Stack | Typecheck command |
| --- | --- |
| Vue SFC | `vue-tsc --noEmit` |
| Nuxt | `npx nuxi typecheck` |
| Svelte / SvelteKit | `svelte-check` |
| Astro | `astro check` |

Framework-generated tsconfig (Nuxt `.nuxt/tsconfig.*`, SvelteKit `.svelte-kit/tsconfig.json`, Astro's base): never edit generated files — the effective flags may live there, not in the root config. Set options through the framework config (e.g. `typescript.tsConfig` in `nuxt.config.ts`) or the root tsconfig that extends the generated one. Template type errors surface as `__VLS_ctx.x is possibly 'undefined'` (TS18048) — the fix is in the SFC template or props; see references/error-playbook.md. A `config: any` prop on a component that renders several row/config shapes is a Vue-specific smell: type it with generic `defineProps` (`<script setup lang="ts" generic="TRow extends BaseRow">`) instead of `any`.

## Audit & Hardening

For "audit the TypeScript setup" or "tighten types" on a project that already checks green:

If the typecheck reports 0 errors and the strict set (`strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `noUnusedLocals`/`noUnusedParameters`, `noFallthroughCasesInSwitch`) is already enabled, there is likely nothing to harden: do not hunt for something to break — go straight to the hygiene grep (step 4) and report the setup as healthy.

1. Setup: `typescript` pinned in devDependencies; a `typecheck` script in package.json; CI runs it. "Pinned" here means at least a caret major-compatible range (`^6.0.3`) with a committed lockfile; prefer a tilde minor-compatible range (`~6.0.3`) or an exact pin (`6.0.3`) when a compiler patch has broken the build before. In a side-by-side compiler setup, audit every `typecheck*` script, not just `typecheck`: match each against the CI workflow and report any (e.g. a native `typecheck:ts7`) that CI never runs. `inspect_typescript.py` lists the native compiler and each script's target tsconfig.
2. Coverage: every `.ts`/`.tsx`/`.vue` file falls inside some tsconfig's `include` (inspect_typescript.py reports uncovered files) — uncovered code is never type-checked.
3. Effective strictness: read effective flags from the inspect output; framework-generated configs may set flags the root config does not show.
4. Hygiene grep: `: any`, `as any`, `@ts-ignore`, `@ts-expect-error`, and non-null assertions (the postfix `x!` operator). Prioritize exported/public APIs and component props > server boundaries > internal utilities. Replace assertions with real guards or type predicates; make a prop required instead of optional when every call site passes it. When one class of finding is massive (roughly 30+ occurrences of non-null `x!`), do not read each one: review a 10–15% sample, extrapolate, and state the sampling in the report.
5. Enable missing strictness flags one at a time, cheapest first (order above), fixing fallout per flag.

Linter rules (`no-explicit-any` and friends) are the linter's domain, not this skill's: note them in audit findings, fix them via lint config.

## Error Playbook (quick)

Full catalog with causes and prioritized fixes: references/error-playbook.md.

| Error | First move |
| --- | --- |
| TS2307 Cannot find module | Check `moduleResolution` matches how the code is run/bundled; then missing `@types` or `exports` map |
| TS2742 The inferred type cannot be named | Export the referenced type explicitly or annotate the declaration's return type |
| TS2589 Type instantiation is excessively deep | Break the recursion: simplify generic constraints, split unions, alias intermediate types |
| Excessive stack depth comparing types | Replace large type intersections with `interface extends`; limit recursive conditional types |
| TS5101 'baseUrl' is deprecated | Delete `baseUrl`; rewrite `paths` relative to the tsconfig (`"@/*": ["./src/*"]`) — `ignoreDeprecations` often masks exactly this |
| TypeScript 7 rejects a deprecated compiler option | Upgrade through TypeScript 6, remove `ignoreDeprecations`, and replace the option; see references/typescript-7-migration.md |
| TypeScript 7 reports missing Node/test globals | Set `compilerOptions.types` explicitly, for example `["node", "jest"]`; TypeScript 7 inherits TypeScript 6's empty default |
| A framework checker or tool fails after installing TypeScript 7 | Check its TypeScript peer range and compiler-API dependency; keep TypeScript 6 side by side when the tool has not added TypeScript 7 support |
| `ERR_PACKAGE_PATH_NOT_EXPORTED` for `./lib/tsc` (vue-tsc crashes after a TS bump) | vue-tsc/Volar loads `typescript/lib/tsc`, removed from `exports` in TypeScript 7; keep `typescript` on 6.x and put 7 under the `@typescript/native` alias |
| `__VLS_ctx.x` is possibly 'undefined' (TS18048) | Template error in a Vue SFC: make the prop required or default it, or guard in the template |
| Editor shows errors CLI does not (or reverse) | Compare the TypeScript versions: editor's bundled TS vs workspace `node_modules/typescript` |

## Performance

When type-checking or the editor is slow:

```bash
python <skill>/scripts/trace_perf.py --root .
python <skill>/scripts/trace_perf.py --root . --trace   # deeper: compiler trace
```

Reading the result: high `instantiations` or `check_time` dominating `total_time` means type-level complexity (heavy generics, huge unions, deep conditional types) — fix the types. High `files`/`lines` with modest check time means the program is too large — fix `include`/`exclude`, add project references, check that `node_modules` or generated output is not being picked up.

Standard remedies in order: precise `include`/`exclude` -> `skipLibCheck` -> `incremental` -> project references for multi-package repos.

## Common Failure Modes

- **`paths` aliases fail at runtime**: tsconfig `paths` are compile-time only; the bundler or runtime needs its own alias config. See references/module-resolution.md.
- **Conflicting `@types` versions**: duplicate `@types/node` (or react) across the tree; align versions or set `compilerOptions.types` explicitly.
- **Stale build state**: delete `.tsbuildinfo` (and `node_modules/.cache`) after config changes that should have changed the output but seemingly did not.
- **Editor vs CLI disagree**: different TypeScript versions; point the editor to the workspace version.
- **ESM/CJS mixing**: `require` of an ESM-only package or default-import mismatch; see references/module-resolution.md interop table.
- **Monorepo edits not picked up**: project references need `composite: true` and a build step (`tsc -b`); see references/monorepo.md.

## Reference Files

- `references/error-playbook.md` - Cryptic compiler errors: cause and prioritized fixes
- `references/module-resolution.md` - module/moduleResolution pairs, ESM/CJS interop, paths, exports maps
- `references/migration.md` - Incremental JavaScript-to-TypeScript migration
- `references/typescript-7-migration.md` - Compiler migration to TypeScript 7, including TypeScript 6 compatibility and framework constraints
- `references/monorepo.md` - Project references, composite builds, workspace typecheck order
