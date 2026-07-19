---
name: vitest
description: You MUST use this when configuring, writing, debugging, running, or migrating Vitest tests in JavaScript/TypeScript projects — Vite, Vue, Nuxt, React, Next.js, Node libraries, workspaces, coverage, mocks, snapshots, flaky tests, and Jest migration.
metadata:
  author: Ihor Orlovskyi
  version: "1.0.2"
license: MIT
compatibility: Requires Python and a JavaScript package manager; Vitest must be installed in the target project before tests can run.
---

# Vitest

Use this skill to add, fix, or run Vitest tests without turning the task into a Vitest API reference lookup.

**Helper Scripts Available**:
- `scripts/inspect_vitest.py` - Detects package manager, Vitest config, scripts, test files, framework hints, and likely run commands
- `scripts/run_vitest.py` - Runs Vitest through the detected package manager with useful defaults

`<skill>` means the path to this local skill folder. Run helper scripts with `--help` when usage is unclear or before first use in a session. Prefer using helper scripts as black-box tools. Read or modify their source only when debugging the skill itself or when behavior is unclear.

## Decision Tree

```
User task -> Is this an existing project?
    - Yes -> Run: python <skill>/scripts/inspect_vitest.py --root <project>
             Use detected framework, config, aliases, and package manager.
    - No / new setup -> Inspect package.json manually if present, then create the
                        smallest Vitest setup that matches the runtime.

Next -> What is under test?
    - Node/library logic -> environment: node
    - React/Vue/Svelte component -> environment: jsdom or happy-dom
    - Nuxt/Vue app code -> prefer existing Nuxt/Vite test utilities and config
    - Edge/Workers code -> match the project's existing worker test setup
    - Browser-specific behavior -> consider Vitest browser mode only if already used

Then -> Write or fix one focused test, run it directly, then broaden only as needed.
```

## Core Workflow

1. Inspect first: discover existing scripts, config files, setup files, aliases, and test conventions.
2. Match the project: use its package manager, test naming, setup file, mock style, and import aliases.
3. Keep tests behavioral: assert public outcomes instead of private implementation details.
4. Isolate state: reset mocks, timers, DOM, environment variables, and module state when the test mutates them.
5. Verify narrowly first: run one file or name pattern before running the whole suite.

## Running Tests

Run helper help when needed:

```bash
python <skill>/scripts/run_vitest.py --help
```

Common pattern:

```bash
python <skill>/scripts/inspect_vitest.py --root .
python <skill>/scripts/run_vitest.py --root . -- tests/example.test.ts
python <skill>/scripts/run_vitest.py --root . --coverage -- tests/example.test.ts
python <skill>/scripts/run_vitest.py --root . --test-name "formats currency"
```

If the helper cannot infer the package manager or script, use the project's own command exactly as defined in `package.json`.

## CI-Only Failures

When tests fail in CI but pass locally, check environment differences before rewriting tests:

- Node version: `node -v`, `.nvmrc`, `.node-version`, `package.json#engines`
- Package manager and lockfile: use the same install command as CI
- Case-sensitive paths: Linux CI may fail on imports that macOS accepts
- Tracked files: verify that required fixtures/config files are committed
- Exact filename case: use `git ls-files` to confirm tracked path casing
- Environment variables: compare local `.env*` assumptions with CI config

Useful checks:

```bash
node -v
cat .nvmrc 2>/dev/null || true
node -p "require('./package.json').engines?.node" 2>/dev/null || true
git ls-files | grep -i 'expected-file-name'
git ls-files | awk '{ print tolower($0) }' | sort | uniq -d
```

## Project-Specific Adapters

### Plain Node / Library
Use `environment: 'node'`. Avoid DOM dependencies unless code requires browser APIs.

### Vue / Vite
Use Vue Test Utils or the project's existing Testing Library setup. Ensure `jsdom` or `happy-dom` exists before writing DOM/component tests.

### Nuxt
Prefer `@nuxt/test-utils` when present. Check whether the project uses `environment: 'nuxt'`, `happy-dom`, `jsdom`, or plain `node`. Do not replace Nuxt-aware tests with plain Vue tests for code that depends on Nuxt auto-imports, runtime config, plugins, routes, Nitro/server APIs, or module setup.

### Vue / Nuxt Gotchas
For Pinia-dependent components/composables, use the project's existing Pinia testing setup instead of hand-rolled mocks. For async Vue rendering, await framework utilities such as `nextTick`/`flushPromises` or Testing Library `findBy*` queries; do not sleep. For Suspense, async components, Teleport, plugins, or provide/inject, prefer existing project test helpers before creating new wrappers.

### React / Vite
Use React Testing Library when present. If using `toBeInTheDocument`, verify that `@testing-library/jest-dom/vitest` is imported in an existing setup file, or add it only when the dependency exists or is being installed.

### Next.js / React
For Next.js projects, prefer the existing project setup. Vitest is suitable for unit tests of client components and synchronous components, usually with React Testing Library and `jsdom`.

Do not assume Vitest can fully test async Server Components. For async Server Components, prefer the project's existing E2E setup, usually Playwright or another browser-level test runner.

### Monorepo / Multi-environment
Check for Vitest test projects/workspace configuration before creating a new config. Preserve existing project boundaries and environment-specific settings.

## Writing Patterns

- Use `describe`, `it`/`test`, `expect`, and `vi` from `vitest`.
- Use `vi.fn()` for function seams and `vi.mock()` for module boundaries.
- Prefer deterministic inputs over snapshots. Use snapshots only for stable, intentional structures.
- For dates and timers, use fake timers and restore real timers in teardown.
- For async code, await observable outcomes instead of sleeping.
- For components, render through the framework's testing library and assert accessible output.
- For repeated setup, prefer small local helpers or Vitest fixtures/`test.extend` over copy-pasting large setup blocks.
- For type-level assertions, use `expectTypeOf` or `assertType` only when the project already has type tests or the user explicitly asks.
- For coverage, add thresholds only when the project already enforces them or the user asks.
- When adding a sample test, pick a real existing source file. Do not invent fake modules just to demonstrate syntax.

## Migration Notes

Treat Jest migration as a focused refactor, not a blind full-suite rewrite. Migrate one file or repeated pattern first, then run narrow tests.

Map imports and globals deliberately:

- `jest.fn()` -> `vi.fn()`
- `jest.mock()` -> `vi.mock()`
- `jest.spyOn()` -> `vi.spyOn()`
- `jest.useFakeTimers()` -> `vi.useFakeTimers()`
- `jest.resetModules()` -> `vi.resetModules()`

Also check timer behavior, fake timers, snapshots, config differences, setup files, aliases, and test environment. Do not enable Vitest globals just to avoid imports unless the existing project already uses global test APIs.

## Common Failure Modes

- **Aliases fail**: make Vitest config reuse the same aliases as Vite/TS config.
- **DOM APIs missing**: choose `jsdom` or `happy-dom` for component tests.
- **Mocks leak between tests**: add `afterEach(() => vi.restoreAllMocks())` or project-equivalent cleanup.
- **Timer tests hang**: restore real timers and advance timers explicitly.
- **ESM/CJS mismatch**: follow the project module type and avoid mixing require/import patterns.
- **Flaky async tests**: wait for specific state, DOM text, emitted events, or resolved promises.

## Reference Examples

- `examples/node_function.test.ts` - Pure TypeScript/Node logic
- `examples/react_component.test.tsx` - React Testing Library style
- `examples/vue_component.test.ts` - Vue Test Utils style
