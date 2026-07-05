---
name: typescript
description: Use when configuring tsconfig, resolving TypeScript compiler errors, debugging slow type-checking or builds, fixing module resolution and ESM/CJS issues, migrating JavaScript to TypeScript, or setting up type-checking in monorepos.
metadata:
  author: Ihor Orlovskyi
  version: "1.0.0"
license: MIT
compatibility: Requires Python and a JavaScript package manager; TypeScript must be installed in the target project (locally or resolvable via npx).
---

# TypeScript

Use this skill to configure, diagnose, and fix TypeScript projects. It is a workflow, not a language reference: the type system syntax is assumed knowledge, and the focus is on compiler behavior, configuration, and cryptic failures.

**Helper Scripts Available**:
- `scripts/inspect_typescript.py` - Detects package manager, TypeScript version, tsconfig files with extends chains and effective flags, monorepo markers, linter, runner, and the recommended typecheck command
- `scripts/run_typecheck.py` - Runs type-checking through the detected package manager and summarizes errors by code and file
- `scripts/trace_perf.py` - Measures compilation via `--extendedDiagnostics`, flags anomalies, optionally writes a compiler trace

`<skill>` means the path to this local skill folder. Run helper scripts with `--help` when usage is unclear or before first use in a session. Prefer using helper scripts as black-box tools. Read or modify their source only when debugging the skill itself or when behavior is unclear.

## Decision Tree

```
User task -> Existing project?
    - Yes -> Run: python <skill>/scripts/inspect_typescript.py --root <project>
             Use detected manager, tsconfig chain, effective flags, monorepo layout.
    - No  -> Create the smallest strict tsconfig matching the runtime.
             Do not paste large config templates; set only what the project needs.

Next -> What is the symptom?
    - Type errors after a change      -> run_typecheck.py, then Error Playbook below
    - Cryptic compiler error          -> references/error-playbook.md
    - "Cannot find module" / imports  -> references/module-resolution.md
    - Slow tsc / slow editor          -> trace_perf.py, then Performance below
    - JavaScript to TypeScript        -> references/migration.md
    - Monorepo / project references   -> references/monorepo.md
    - New tsconfig / stricter flags   -> Configuration below
```

## Core Workflow

1. Inspect first: discover the package manager, tsconfig extends chain, effective flags, and monorepo layout before changing anything.
2. Match the project: keep its `module`/`moduleResolution` pair, its extends chain, and its package manager. Do not switch resolution strategies to silence one error.
3. Prefer the minimal fix: one flag, one type annotation, one dependency — not a rewritten tsconfig.
4. Verify narrowly first: `run_typecheck.py --project <pkg tsconfig>` or `--files` before a full-repo check.
5. Never "fix" an error with `any`, `as`, or `@ts-ignore` to get to green. Reaching for them means the actual cause is not yet understood; find it first, and use targeted narrowing or a documented `@ts-expect-error` only as a last resort.

## Configuration

Direction for new or hardened configs (adopt, do not paste wholesale):

- `strict: true` is the baseline; add `noUncheckedIndexedAccess` and `noImplicitOverride` when the codebase can absorb them.
- In an existing project, enable new strictness flags one at a time and fix fallout per flag; do not flip several at once.
- `module`/`moduleResolution`: `NodeNext` for Node libraries and servers, `ESNext`/`bundler` for bundled apps. These two options must be chosen as a pair; see references/module-resolution.md.
- `skipLibCheck: true` is a pragmatic default; remove it only when debugging a broken dependency's types.
- Respect the extends chain: change the leaf config for a package-local need, the base config for a repo-wide policy.

## Error Playbook (quick)

Full catalog with causes and prioritized fixes: references/error-playbook.md.

| Error | First move |
| --- | --- |
| TS2307 Cannot find module | Check `moduleResolution` matches how the code is run/bundled; then missing `@types` or `exports` map |
| TS2742 The inferred type cannot be named | Export the referenced type explicitly or annotate the declaration's return type |
| TS2589 Type instantiation is excessively deep | Break the recursion: simplify generic constraints, split unions, alias intermediate types |
| Excessive stack depth comparing types | Replace large type intersections with `interface extends`; limit recursive conditional types |
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
- `references/monorepo.md` - Project references, composite builds, workspace typecheck order
