# Migrating to TypeScript 7

TypeScript 7 is the stable, Go-based native compiler released on 2026-07-08. The
stable package is still `typescript`, and its command is still `tsc`; `tsgo` and
`@typescript/native-preview` were preview-era names. Migrate configuration and
tooling separately so a faster compiler does not hide an incompatible framework,
plugin, or compiler-API dependency.

## Migration map

1. Inventory the compiler, checker, and API consumers.
2. Use TypeScript 6 as the compatibility bridge.
3. Run TypeScript 6 and 7 side by side when tooling still needs the old API.
4. Switch the project compiler only after output and diagnostics agree.
5. Keep framework-specific checkers on their supported compiler.

## 1. Establish the baseline

Run the project inspection helper and record the exact installed version, not only
the range in `package.json`:

```bash
python <skill>/scripts/inspect_typescript.py --root .
node -p "require('./node_modules/typescript/package.json').version"
```

Then run the repository's existing typecheck, build, declaration emit, tests, and
framework checker. Save representative diagnostics and generated output. This
baseline distinguishes compiler differences from unrelated dependency upgrades.

Search for compiler coupling before changing the dependency:

```bash
rg "from ['\"]typescript['\"]|require\\(['\"]typescript['\"]\\)|tsserver|languageService|plugins" \
  --glob '!node_modules/**'
```

Treat direct imports from `typescript`, custom transformers, tsserver/language-service
plugins, and tools with a TypeScript peer dependency as migration blockers until
their installed versions explicitly support TypeScript 7. TypeScript 7.0 does not
ship a programmatic compiler API; a new API is planned for 7.1 and is not a drop-in
replacement for the TypeScript 6 API.

## 2. Cross the TypeScript 6 bridge

If the project is on TypeScript 5.x or earlier, upgrade to TypeScript 6 first. It is
the compatibility release designed to surface TypeScript 7 changes while the old
JavaScript API is still available.

With TypeScript 6:

- remove `ignoreDeprecations` and fix every reported deprecated option;
- temporarily enable `stableTypeOrdering` when comparing diagnostics or declaration
  output with TypeScript 7 (it makes TypeScript 6's type ordering match 7's), then
  remove it after the comparison — it is a diagnostic aid only and can slow
  TypeScript 6 checks by up to ~25%;
- set `rootDir` explicitly when the source tree is below the tsconfig directory;
- list required global type packages explicitly in `compilerOptions.types`;
- make `strict`, `module`, `moduleResolution`, and `target` explicit so new defaults
  do not silently change the project contract.

TypeScript 7 turns TypeScript 6 deprecations into errors. In particular, replace
legacy `node`/`node10`/`classic` resolution, legacy module formats, `baseUrl`, ES5
output, and other deprecated options according to the installed TypeScript 6 release
notes. Do not use `ignoreDeprecations` as a migration strategy.

## 3. Choose the adoption path

### Projects without compiler-API or plugin dependencies

Install the stable TypeScript 7 major with the repository's package manager, keeping
the lockfile change isolated from unrelated upgrades:

```bash
npm install -D typescript@^7
npx tsc --version
```

Translate `npm` to the detected package manager. Do not install
`@typescript/native-preview` for a stable migration and do not add a `tsgo` script:
those belong to pre-release builds before TypeScript 7.0 RC.

Run the same checks captured in the baseline. Compare:

- error codes and affected files;
- emitted JavaScript and declarations;
- project-reference build order and incremental rebuilds;
- watch-mode behavior;
- compiler time and peak memory using `trace_perf.py`.

Fix source or configuration differences; do not pin the preview package to preserve
old behavior.

### Projects that still need the TypeScript 6 API

Keep TypeScript 6 available and install TypeScript 7 under a second alias. Two
layouts exist; which one works depends on whether the API consumer resolves
`typescript` through a shim or needs the real package.

**Official compatibility-package layout** — `typescript` itself becomes the TS6
compat shim, following the TypeScript 7.0 announcement:

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

`@typescript/typescript6` re-exports the TypeScript 6 API (and exposes `tsc6` for
explicit comparisons), so API-dependent tooling keeps resolving `typescript` as 6
while the native compiler supplies `tsc`.

**Real-package layout (required for vue-tsc / Volar)** — keep `typescript` as the
genuine TypeScript 6 package and put the native compiler only under the alias:

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "^6.0.3"
  }
}
```

```json
{
  "scripts": {
    "typecheck": "vue-tsc --noEmit",
    "typecheck:ts7": "node node_modules/@typescript/native/bin/tsc -p netlify/tsconfig.json"
  }
}
```

Use this layout whenever a tool patches or requires `typescript`'s own files by
path. The compat package `npm:@typescript/typescript6` ships a shim whose entry is
`require("@typescript/old/lib/tsc.js")`; Volar (behind `vue-tsc@3.3.7`) tries to
patch `lib/tsc.js` and only understands a relative shim path, so it fails with
`Failed to locate tsc module path from shim`. Keeping `typescript` on the real 6.x
package avoids that: `vue-tsc` uses the genuine compiler API, and the native TS7
compiler runs as a separate script over the non-template tsconfigs it can handle.

With either layout, pin the range shown in the release notes for the versions in
the target lockfile, then verify the resolved binaries and package versions after
installation, because package-manager alias behavior and tool peer ranges differ.
`inspect_typescript.py` reports the framework compiler API, the native compiler,
and which tsconfig each `typecheck*` script targets, so you can confirm the split.

### Choosing the TS-7 target on a project without one

When no TS-7 tsconfig exists yet, do not point the native compiler at the whole
repo. Find the largest subtree that is (a) free of `.vue`/framework component
files, (b) free of direct `typescript`/compiler-API imports, and (c)
self-contained (no `paths` aliases into app code). Netlify/edge/serverless
functions and standalone Node scripts are the usual candidates. Give that
subtree its own strict tsconfig with `compilerOptions.types: []` and point
`typecheck:ts7` at it; everything else stays on the framework checker. Note
that `types: []` removes ambient `@types/*` global packages but not `lib`
globals — `console`, `URL`, `Request` still resolve through the base config's
`lib` entries.

Keep the side-by-side arrangement only while required. Re-check tool release notes
before every upgrade; move to the TypeScript 7 API only when the tool and installed
TypeScript release both document compatibility.

## 4. Framework and embedded-language projects

As of 2026-07-11, the TypeScript team says Vue, MDX, Astro, Svelte, and similar
embedded-language workflows generally cannot use TypeScript 7 because their tooling
depends on the missing compiler API. Angular template tooling has the same constraint.

- Keep `vue-tsc`, `nuxi typecheck`, `svelte-check`, and `astro check` on their
  supported TypeScript version; a green plain `tsc` run does not validate templates.
- For Angular, TypeScript 7 can provide fast project-wide CLI diagnostics where the
  project supports it, while TypeScript 6 continues to power template/editor tooling.
- Do not force peer-dependency overrides. Upgrade only when the framework checker or
  its underlying integration (for example Volar) explicitly announces TypeScript 7
  support.
- If the editor relies on a TypeScript language-service plugin, keep its TypeScript 6
  editor path until the plugin documents the TypeScript 7 LSP/API migration.

Re-check current framework documentation and the installed checker's peer dependency
before acting; this compatibility status is expected to change after TypeScript 7.1.

## 5. Roll out and retain a rollback path

Land the migration in stages: configuration cleanup, side-by-side compiler comparison,
then the default compiler switch. Preserve the TypeScript 6 lockfile revision or
compatibility script until CI, editor workflows, declarations, and framework checks
are green for the team.

Pin the chosen major range and commit the lockfile. In CI, print `tsc --version` so a
future dependency resolution cannot silently change which compiler produced the
result.

In a side-by-side setup, each compiler path is a separate CI gate: match every
`typecheck*` script (`typecheck`, `typecheck:ts7`, ...) against the workflow and
confirm each one runs. A native `typecheck:ts7` script that exists in package.json
but is absent from CI means the TypeScript 7 path is never actually exercised.

## Sources checked

- [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/),
  TypeScript team, 2026-07-08 — stable installation, `tsc`, TypeScript 6 compatibility
  package, missing API, breaking changes, and embedded-language limitations.
- [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/),
  TypeScript team, 2026-03-23 — bridge-release workflow, deprecations, default changes,
  and `stableTypeOrdering`.
- [microsoft/typescript-go](https://github.com/microsoft/typescript-go), checked
  2026-07-11 — native compiler implementation, preview-era `tsgo` naming, feature
  status, and intentional changes from TypeScript 6.

These sources describe a fast-moving transition. Before applying exact package or
tooling advice, compare them with the release notes for the versions present in the
target project's lockfile.
