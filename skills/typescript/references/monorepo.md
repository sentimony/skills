# TypeScript in Monorepos

## Two viable strategies

1. **Project references** (`tsc -b`): each package is a TS project with `composite: true`; the compiler builds dependencies first and consumes their `.d.ts`. Correct, incremental, editor-friendly; requires build discipline.
2. **Single-program checking**: one root tsconfig includes all sources; packages import each other's *source* via workspace aliases. Simpler, no build step for types, but check time grows with the whole repo and package boundaries are not enforced.

Pick based on what the repo already does (`inspect_typescript.py` shows `references` and `composite`). Do not migrate between strategies as a side effect of another task.

## Project references setup

Root tsconfig (build orchestrator only, checks nothing itself):

```json
{
  "files": [],
  "references": [
    { "path": "./packages/core" },
    { "path": "./packages/ui" },
    { "path": "./apps/web" }
  ]
}
```

Each referenced package:

```json
{
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "declarationMap": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "references": [{ "path": "../core" }],
  "include": ["src"]
}
```

- `composite: true` implies `declaration`; `declarationMap` makes go-to-definition land in source, not `.d.ts` — always enable it.
- A package's `references` must list its *workspace dependencies* — keep it in sync with package.json deps.
- Build/typecheck with `tsc -b` (root) — not `tsc -p` per package; `-b` resolves order and skips up-to-date projects.

## Typecheck order and CI

- `tsc -b --verbose` prints the resolved build order — use it to understand what rebuilds and why.
- In CI, `tsc -b` at the root is the whole-repo typecheck; per-package `tsc -b packages/x` checks a subtree.
- Task runners (turbo/nx): the typecheck task must declare dependency on upstream builds (`"dependsOn": ["^build"]` in turbo terms), or packages will type-check against stale `.d.ts`.

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| TS6306: Referenced project must have `composite: true` | A `references` entry points at a non-composite package | Add `composite: true` (and `outDir`/`rootDir`) to that package |
| Edits in dep not visible in consumer | Consumer reads stale `dist/*.d.ts` | Run `tsc -b` (or the repo's build task); check `declarationMap` for editor nav |
| TS2307 for a workspace package | Package not built yet, or `exports` hides the subpath | Build first; verify `exports` exposes what is imported |
| Phantom errors after refactor | Stale `.tsbuildinfo` | `tsc -b --clean` then rebuild (or delete `**/*.tsbuildinfo`) |
| Whole repo rechecks on any change | No project references (single program) | Expected under strategy 2; adopt references only as a deliberate migration |

## pnpm specifics

- Strict `node_modules` means transitive types are not reachable — TS2742 in library builds; add the direct dependency (see error-playbook.md).
- Workspace protocol (`"@mono/core": "workspace:*"`) plus `exports` with a `types` condition is the reliable way for consumers to see fresh types without deep imports.
