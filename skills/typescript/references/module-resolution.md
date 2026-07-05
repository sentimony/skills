# Module Resolution and ESM/CJS

## Choosing module / moduleResolution (always as a pair)

| Scenario | module | moduleResolution | Notes |
| --- | --- | --- | --- |
| Node library or server (ESM or dual) | NodeNext | NodeNext | Mirrors real Node behavior; relative ESM imports need `.js` extensions in source |
| App built by a bundler (Vite, esbuild, webpack) | ESNext | bundler | Extensionless imports OK; bundler owns runtime resolution |
| Legacy CJS-only Node project | CommonJS | node10 | Only for old projects; do not start new code here |

Rules:
- Never mix pairs (e.g. `module: ESNext` + `moduleResolution: NodeNext`) to silence an error — the compiler will accept code the runtime rejects, or vice versa.
- `package.json#type` decides how `.ts`/`.js` files are treated under NodeNext: `"type": "module"` -> ESM; absent -> CJS. `.mts`/`.cts` override per file.

## ESM/CJS interop

| Situation | What happens | Fix |
| --- | --- | --- |
| `require()` of an ESM-only package | Runtime error `ERR_REQUIRE_ESM` | `await import("pkg")` (needs async context or TLA), or migrate the consumer to ESM |
| Default import of a CJS package from ESM | Sometimes the whole `module.exports` lands on `.default` | Try `import pkg from` first; if shape is wrong, `import * as pkg` or `(await import("pkg")).default` |
| `esModuleInterop: false` with default imports | TS2613/TS1259 | Enable `esModuleInterop` (and keep it on; it matches bundler/Node behavior) |
| Dual package (both ESM and CJS builds) | Node may load two copies (state duplication) | Import consistently from one format across the app |

## tsconfig `paths` are compile-time only

`paths` teaches the *type checker* about aliases; nothing at runtime reads tsconfig.

- Bundler apps: mirror the alias in the bundler config (Vite `resolve.alias`, webpack `resolve.alias`).
- Node without bundler: prefer package.json `imports` (`#alias/*`) which Node resolves natively; avoid tsconfig paths for runtime code.
- Tests: Vitest/Jest need the alias in their own config too (Vitest inherits Vite's).

Symptom of getting this wrong: `tsc` passes, runtime throws `Cannot find module '@/...'`.

## package.json `exports` for libraries

- Once `exports` exists, only listed subpaths are importable — deep imports break by design.
- Provide `types` first in each condition block; order inside a condition object matters.
- Minimal dual-safe shape:
  ```json
  {
    "exports": {
      ".": {
        "types": "./dist/index.d.ts",
        "import": "./dist/index.js",
        "require": "./dist/index.cjs"
      }
    }
  }
  ```
- Validate with `npx @arethetypeswrong/cli --pack .` when publishing types.

## Debugging resolution

```bash
npx tsc --traceResolution > resolution.log 2>&1
grep -A2 "Resolving module 'the-failing-one'" resolution.log
```

Read the candidate list: it shows exactly which files/conditions the resolver tried and why each was rejected.
