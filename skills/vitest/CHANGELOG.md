# Changelog

All notable changes to the `vitest` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.1.1] - 2026-08-02

### Fixed
- **Behavior change: `run_vitest.py` now auto-runs a package.json script only when the
  entire script body is a direct Vitest invocation, matching the Security Model's
  treatment of package.json scripts as untrusted repository data.** Previously the
  runner auto-ran the first script whose body merely contained the substring
  `vitest`, so a script that also chained a second command, redirected output, or
  substituted a subshell would run anyway once auto-selected. Auto-selection now
  requires the whole body to be: an optional environment prefix drawn from a fixed
  allowlist of keys (`NODE_ENV`, `CI`, `TZ`, `NODE_OPTIONS`, `DEBUG`, `FORCE_COLOR`,
  `NO_COLOR`, `VITE_*`, `VITEST`/`VITEST_*`), an optional launcher that runs the binary
  named by its next argument (`npx`, `npx --no-install`, `pnpm exec`, `bunx`), the
  `vitest` token, and arguments free of characters that chain, redirect, or substitute
  commands. Anything else falls back to `node_modules/.bin/vitest` and prints a note
  carrying the stable code `SCRIPT_NOT_DIRECT`. An explicit `--script <name>` still
  runs the named script, with a warning when its body is not direct.
- `inspect_vitest.py`'s filesystem candidate scan now excludes agent-toolchain
  directories (`.agents`, `.claude`, `.opencode`, `.codex`, `.cursor`), so an
  installed skill's own bundled example tests (e.g. this skill's
  `examples/vue_component.test.ts` once installed under `.agents/skills/vitest/`) no
  longer inflate a project's reported test-file count.
- `run_vitest.py`'s `engines.node` preflight now matches `inspect_vitest.py`'s strict
  greater-than semantics: it warns when the current Node version is less than *or
  equal to* a strict `>` bound, not only when it is strictly less. Previously
  `engines.node: ">24.15.0"` on Node 24.15.0 was flagged incompatible by the inspector
  but produced no warning from the runner.
- Nuxt adapter guidance calibrated: mixing `node`- and `nuxt`-environment files via
  per-file directives on top of `defineVitestConfig` is the intended pattern but not
  guaranteed to be leak-free, since `defineVitestConfig` registers Nuxt auto-imports
  for the whole Vite worker. The adapter now recommends keeping per-file environments
  only after a representative mixed run proves no leak, and offers a uniform Nuxt
  environment or split Vitest projects/configs as fallbacks.
- SKILL.md Security Model: corrected "the `VITE_*` and `VITEST_*` namespaces" to "the
  `VITE_*` and `VITEST`/`VITEST_*` namespaces" — the accepted pattern also allows a
  bare `VITEST=` assignment, not only `VITEST_*`.

### Changed
- Scripts using bare `pnpm`, `yarn`, or `bun` as the launcher (e.g.
  `"test": "pnpm vitest run"`) are no longer auto-selected: those spellings resolve to
  a package.json script named `vitest` when one exists rather than to the installed
  binary. The runner falls back to `node_modules/.bin/vitest` and prints the
  `SCRIPT_NOT_DIRECT` note; pass `--script <name>` to run the script as written.
- Scripts with an app-specific environment prefix outside the allowlisted keys (e.g.
  `"test": "API_URL=https://x vitest run"`) are no longer auto-selected, since an
  unbounded key space cannot be distinguished from one that redirects what actually
  runs. Same fallback and `--script` opt-in as above.

### Added
- `scripts/test_run_vitest.py`: a regression module for the direct-Vitest-script
  predicate, covering shell chaining/redirection/substitution, newline chaining,
  npm/pnpm/yarn/bun launcher shadowing, npm exec package redirection, allowlisted vs.
  unrecognized environment keys (including `PATH`, package-manager config keys, and
  dynamic-loader hooks), and the runner's fallback/opt-in behavior end to end.

## [1.1.0] - 2026-07-31

### Added
- First-class existing-suite audit reference covering active-file evidence, fixed-seed order checks, clean-output findings, coverage scope and CI gates, local/CI parity, Nuxt mitigation choices, and residual risks
- Safe-report behavior tests for hostile repository data, strict Node declarations, ignored generated directories, and renderer parity

### Changed
- Inspector output is now a versioned normalized schema of enums, counts, and stable finding codes; human findings go to stderr and repository-controlled text is not emitted
- Filesystem candidate discovery now uses one pruned streaming traversal with
  deterministic filename order, explicit candidate and visited-file caps, and
  surfaced traversal errors; schema v2 reports bounded lower-bound semantics and
  a stable truncation reason
- Strict `engines.node` greater-than ranges now reject equality while
  greater-than-or-equal ranges continue to accept it
- Main skill description, decision tree, and Security Model now cover Vitest audits and untrusted repository/test data
- The filesystem candidate cap defaults to 5000 and only a candidate beyond the cap marks the count truncated, so an ordinary suite reports an exact bound
- Coverage providers and testing-library packages are detected again as allowlisted framework signals

### Removed
- Raw project root, config file names, test file names, suggested run command, and package script bodies from the report; the schema now carries enums, counts, and stable codes only

## [1.0.3] - 2026-07-20

Driven by real-world audit feedback from a Nuxt 4 project (agilecharts) with
mixed node/nuxt environment test files.

### Added
- Common Failure Modes: Nuxt auto-import leak into `environment: node` files
  (`window is not defined` / `useRuntimeConfig` crash at collection, shifted
  stack traces) — cause, diagnosis via transitive-import grep
- Common Failure Modes: do not delete `.nuxt`/`node_modules/.cache/nuxt`
  blindly; regenerate with `nuxt prepare`
- Nuxt adapter: config example for mixing node- and nuxt-environment files
  in one `defineVitestConfig`

## [1.0.2] - 2026-07-19

### Changed
- Description rewritten in "You MUST use this when…" style

## [1.0.1] - 2026-07-05

Node/environment diagnostics. PR #3.

### Added
- Guidance for "fails in CI, passes locally": check environment differences
  (Node version, `.nvmrc`, `package.json#engines`) before rewriting tests
- `scripts/inspect_vitest.py` and `scripts/run_vitest.py` helper scripts

### Changed
- Versioning switched from date-based (`2026.07.05`) to semver (`1.0.1`)

## [1.0.0] - 2026-07-05

Initial release (as `2026.07.05`). PR #2.

### Added
- SKILL.md covering configuring, writing, debugging, running, and migrating
  Vitest tests (Vite, Vue, Nuxt, React, Next.js, Node libraries, workspaces,
  coverage, mocks, snapshots, flaky tests, Jest migration)
