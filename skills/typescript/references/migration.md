# JavaScript to TypeScript Migration

Incremental by design: the codebase stays green at every step. Do not attempt a big-bang rename.

## Phase 0: Baseline

1. Add TypeScript and a tsconfig that accepts the current code:
   ```json
   {
     "compilerOptions": {
       "allowJs": true,
       "checkJs": false,
       "noEmit": true,
       "strict": false,
       "module": "ESNext",
       "moduleResolution": "bundler",
       "target": "ES2022",
       "skipLibCheck": true
     },
     "include": ["src"]
   }
   ```
   Match `module`/`moduleResolution` to how the project actually runs (see module-resolution.md); the values above assume a bundled app.
2. Add a `typecheck` script and wire it into CI so regressions are caught from day one.
3. Install `@types/*` for the main dependencies (`npx typesync` automates discovery).

## Phase 1: New code in TS, hot files converted

- All new files are `.ts`/`.tsx`.
- Convert files in dependency order: leaves first (utilities without imports from the app), entry points last. Converting a file whose imports are still untyped `any`-poisons it.
- Per file: rename -> fix errors *in that file only* -> commit. Do not refactor logic during conversion; type what exists.
- Temporary `any` at conversion boundaries is acceptable if marked visible: prefer `TODO(ts-migration)` comments over silent `any` so remaining debt is greppable.

## Phase 2: checkJs for the remainder

- Flip `checkJs: true` to surface errors in unconverted JS.
- Use JSDoc as a bridge in JS files that will live a while:
  ```javascript
  /** @param {string} name @returns {import("./types").User} */
  function createUser(name) { ... }
  ```
- JSDoc types are checked by the same compiler — this is real coverage, not documentation.

## Phase 3: Ratchet strictness

Enable one flag at a time, fix fallout, commit, repeat — in this order (cheapest first):

1. `noImplicitAny`
2. `strictNullChecks` (the big one; budget accordingly)
3. `strict: true` (covers the rest of the family)
4. `noUncheckedIndexedAccess` (last; touches every index access)

Never enable a flag and commit with new errors suppressed by `@ts-ignore` — that inverts the ratchet.

## Traps

- **Enums and namespaces**: do not introduce them during migration; use literal unions and modules. They generate runtime code and complicate interop.
- **Class fields initialized in helpers**: `strictPropertyInitialization` will flag them; use definite assignment (`field!: T`) only with a comment saying which method initializes it.
- **Circular imports** become visible (and fatal for types) during conversion; break cycles with type-only imports: `import type { X } from "./x"`.
- **Build pipeline**: keep Babel/esbuild/bundler transpilation as is; `tsc` should stay `--noEmit` for checking. Changing the transpiler mid-migration multiplies risk.
