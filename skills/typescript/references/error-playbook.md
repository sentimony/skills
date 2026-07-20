# TypeScript Compiler Error Playbook

Cause-first catalog of cryptic compiler errors. For each: what actually went wrong, then fixes in priority order (try the first; fall through only if it does not apply).

## TS2307: Cannot find module 'X' or its corresponding type declarations

Cause: the resolver cannot map the import specifier to a file *under the current `moduleResolution`*, or the module exists but ships no types.

1. Confirm the pairing: `module: NodeNext` requires `moduleResolution: NodeNext`; bundled apps use `module: ESNext` + `moduleResolution: bundler`. A specifier that works under `bundler` (extensionless deep import) can fail under `NodeNext`.
2. Under `NodeNext`, relative imports in ESM need explicit `.js` extensions in the source (`./util.js` importing `util.ts`). Missing extension -> TS2307/TS2835.
3. Package has no types: install `@types/<pkg>`; if none exists, add an ambient declaration:
   ```typescript
   // types/ambient.d.ts
   declare module "some-untyped-package";
   ```
   and make sure the file is inside `include`.
4. Package has an `exports` map that does not expose the subpath you import. Check `node_modules/<pkg>/package.json#exports`; import only exported subpaths.
5. Monorepo: the workspace package is not built (`tsc -b`) or not referenced; see monorepo.md.
6. Last resort: `npx tsc --traceResolution > resolution.log` and read the failed lookup chain for that one specifier.

## TS2742: The inferred type of 'X' cannot be named without a reference to 'Y'

Cause: a declaration's inferred type mentions a type from a transitive dependency that the consumer cannot import (common with pnpm's strict node_modules and library builds with `declaration: true`).

1. Annotate the exported declaration's type explicitly so nothing needs to be inferred.
2. Export the referenced type from your own package and use it in the annotation.
3. Add the transitive package as a direct dependency (pnpm: it must be importable by name).
4. For helpers: wrap with `ReturnType<typeof fn>` on an explicitly exported function.

## TS2589: Type instantiation is excessively deep and possibly infinite

Cause: recursive conditional/mapped types exceeded the compiler's instantiation depth — usually unbounded recursion over large unions or deeply nested generics.

1. Bound the recursion with a depth counter or terminate on `never`.
2. Split a large union input into smaller named aliases; the compiler memoizes per alias.
3. Replace chained intersections of mapped types with `interface extends`.
4. Check whether a library type (e.g. a deeply generic ORM/router) explodes on your input; pin a simpler explicit type parameter instead of relying on inference.

## "Excessive stack depth comparing types 'X' and 'Y'"

Cause: structural comparison of two huge or mutually recursive types.

1. Give the intermediate type a name (type alias or interface) — named types compare nominally-ish via identity fast path.
2. Prefer `interface extends` over `&` intersections for object composition.
3. Reduce generic variance pressure: annotate the variable instead of letting two inferred giants be compared.

## TS2345 / TS2322 with generics: argument/type not assignable

Cause (beyond the obvious): inference picked a narrower or wider type than expected.

1. Read the *last* "Type 'A' is not assignable to type 'B'" line in the chain — the innermost mismatch is the real one.
2. If a literal widened (`"a"` became `string`), use `as const` on the value or a `const` type parameter.
3. If a generic resolved to `unknown`/`{}`, the call site lost the inference source — pass the type argument explicitly once and see what breaks.
4. `exactOptionalPropertyTypes`: assigning `undefined` to an optional property is an error under this flag; omit the key instead.

## TS7016: Could not find a declaration file for module 'X'

Cause: JS package without bundled or DefinitelyTyped types.

1. `npm i -D @types/<pkg>` (check the exact name on npm).
2. No @types package: ambient `declare module "x";` in an included `.d.ts` (untyped but explicit).
3. Writing real declarations is worth it only for heavily used APIs; start minimal (declare just the functions you call).

## TS5101: Option 'baseUrl' is deprecated

Cause: TypeScript 6.x deprecates `baseUrl`; projects that carried `ignoreDeprecations` are often masking exactly this, and the error appears the moment that escape hatch is removed.

1. Delete `baseUrl` and rewrite `paths` entries relative to the tsconfig location: `"@/*": ["./src/*"]`.
2. Bare non-relative imports that relied on `baseUrl` alone (no `paths`): add explicit `paths` mappings or convert to relative imports.
3. Remove `ignoreDeprecations` afterwards so the next deprecation is not silently masked.

## `__VLS_ctx.x` is possibly 'undefined' (TS18048 in .vue files)

Cause: `vue-tsc` type-checks SFC templates through a generated context object named `__VLS_ctx`; the error points at template usage of an optional prop, ref, or injected value — the fix belongs in the component, not in any `__VLS_*` code.

1. If every parent already passes the prop, make it required (or give it a default) instead of optional.
2. Otherwise guard the usage in the template (`v-if`) or narrow it in `script setup` via a computed.
3. Template refs to child components: type them with `InstanceType<typeof ChildComponent>`.
4. Remember `tsc` never sees `.vue` files — only `vue-tsc` (or `nuxi typecheck`) surfaces these errors; a green plain `tsc` run is not evidence.

## ERR_PACKAGE_PATH_NOT_EXPORTED: './lib/tsc' is not defined by "exports"

Cause: `typescript` was bumped directly to `^7` while vue-tsc/Volar (or another tool) still requires `typescript/lib/tsc`, which TypeScript 7 removed from its `exports` map. This is a runtime crash of the checker, not a type error — do not try to parse diagnostics out of it.

1. Keep `typescript` on the genuine 6.x package and install TypeScript 7 only under a separate alias (`"@typescript/native": "npm:typescript@^7"`).
2. Follow the real-package layout in references/typescript-7-migration.md; run the native compiler as its own `typecheck:ts7` script over non-template tsconfigs.

## Editor and CLI disagree on errors

Cause: two different TypeScript versions (editor's bundled TS vs `node_modules/typescript`), or the editor uses a different tsconfig than the CLI run.

1. Compare versions: `npx tsc --version` vs the editor's TypeScript version indicator; switch the editor to the workspace version.
2. Check which tsconfig governs the file in the editor (monorepos: nearest config wins) vs which one the CLI ran with (`-p`).
3. Restart the editor's TS server after dependency or tsconfig changes; stale program state is common.
