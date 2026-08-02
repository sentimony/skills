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
  allowlist of keys (`NODE_ENV`, `CI`, `TZ`, `DEBUG`, `FORCE_COLOR`, `NO_COLOR`,
  `VITE_*`, `VITEST`/`VITEST_*`, and `NODE_OPTIONS` limited to the memory options
  `--max-old-space-size=N`/`--max-semi-space-size=N`), an optional launcher that runs
  the binary named by its next argument (`npx`, `npx --no-install`, `pnpm exec`,
  `bunx`), the `vitest` token, and arguments free of characters that chain, redirect,
  or substitute commands. Assignment *values* are restricted as well, to a conservative
  shell-inert character set carrying no whitespace, quotes, brackets, or glob
  characters, so a recognized key can still fall outside it: a glob-style value such as
  `DEBUG=vite:*` is not auto-selected and needs an explicit `--script`.
  Any other `NODE_OPTIONS` value — `--require`, `--import`,
  `--loader`/`--experimental-loader`, `--conditions`, `--env-file`, `--inspect` and its
  variants — is not auto-run, because it would load repository code or open a debugger
  port in the process this helper spawns before Vitest starts. Anything else falls back
  to `node_modules/.bin/vitest` and prints a note carrying the stable code
  `SCRIPT_NOT_DIRECT`. That fallback runs Vitest with this helper's own arguments, not
  the script's, so a suite that depended on flags spelled inside a body that was *not*
  recognized (a `--config`, a `--environment`) can fail differently until you pass them
  here or use `--script`. An explicit `--script <name>` still runs the named script,
  with a warning when its body is not direct.
- **An auto-selected script no longer runs through the package manager, so its `pre`
  and `post` lifecycle scripts are no longer executed.** `npm run test` also runs
  `pretest` and `posttest`, and only the named script's body was ever checked, so a
  package.json could pair an accepted `"test": "vitest run"` with a `"pretest"` that
  runs anything at all. An auto-selected script is now spawned directly, without a
  shell and without a package manager: its environment assignments are applied to the
  child process (a `cross-env` prefix is dropped, since applying them is what it does),
  its launcher is kept as written, a bare `vitest` resolves to
  `node_modules/.bin/vitest` (and fails with the usual "No suitable Vitest command
  found" message when that is missing), and the script's own Vitest arguments are
  preserved ahead of this helper's. Human-readable output gains a `Script environment:`
  line listing the applied keys; values are never printed. `--script <name>` is
  unchanged and remains the way to run a script through the package manager with its
  lifecycle hooks.
- The `Command:` line is now rendered with per-argument shell quoting instead of a plain
  join, so it finally matches the argv the child receives: a body's
  `--testNamePattern "formats currency"` used to print as four tokens for three
  arguments, which read as a different command and did not survive a copy-paste. The
  rendered command is also cut to 1024 characters, after which the line carries
  `... [truncated, N characters total]` with the full length, since an accepted script's
  arguments are repository-controlled text with no length of their own; the `Command: `
  label and that marker sit outside the 1024, so the printed line runs to roughly 1073
  characters when the cut applies. Relatedly, an auto-selected body's arguments may no
  longer contain control characters or the Unicode line separators `U+2028`/`U+2029`
  (horizontal tab and space are still fine): that text is printed to a terminal, so an
  escape sequence in it could repaint or clear the reader's screen, and an embedded NUL
  could not be passed to a child process at all. Such a body now falls back with
  `SCRIPT_NOT_DIRECT` instead of being auto-run.
- The same argument rule now also excludes the invisible formatting codepoints
  `U+200B`–`U+200F`, `U+202A`–`U+202E`, `U+2066`–`U+2069` and `U+FEFF`. These carry no
  escape sequence, so excluding the control characters did not cover them, but they
  defeat the reason the `Command:` line is rendered at all: a right-to-left override
  leaves argv exactly as written and reverses how the path is *displayed*, so
  `vitest run --config <RLO>ot.tset/gifnoc<PDF>` shows a `--config config/test.to` the
  child never receives, and a zero-width character makes two different paths look
  identical. Only bidirectional *control* codepoints are excluded, never letters, so a
  right-to-left `--testNamePattern` written in Arabic or Hebrew is unaffected and still
  auto-runs. A body carrying one of the fifteen codepoints now falls back with
  `SCRIPT_NOT_DIRECT`.
- The `Script environment:` line is now cut to the same 1024 characters, with the same
  `... [truncated, N characters total]` marker. It renders key names, and `VITE_*` and
  `VITEST_*` are open-ended namespaces, so a package.json could choose a single
  2645-character key name and have it printed in full. The key rule already kept such a
  name free of control characters, but readable prose is still readable prose; values
  are still never printed and an ordinary prefix such as `NODE_ENV`/`CI` is unchanged.
- The `engines.node` preflight no longer prints the declaration verbatim. Its gate is a
  search for a version-looking substring anywhere in the string, not a full match, so
  `engines.node` could be `">=99.0.0 "` followed by escape sequences, injection prose and
  three thousand characters of padding: the version part decided that the project was
  warned, and the whole string was then interpolated into the warning. A declaration is
  now printed only when it is composed entirely of version-range characters (digits,
  `x`/`X` wildcards and prerelease tags, `.`, `-`, `+`, the comparators, `|`, `*`, `,`
  and spaces) and stays within the same 1024-character bound; anything else prints as
  `[unrenderable declaration, N characters]`. Those two conditions are what is enforced:
  the character set admits ASCII letters and spaces, so a printed declaration is bounded
  and free of control characters and invisible codepoints rather than certified to be a
  well-formed range. Which projects are warned, and which are
  blocked, is unchanged — `>=18.0.0 <21.0.0`, `^20.11.0`, `18.x`, `18 || 20 || 24` and
  the rest still read exactly as declared. The same rendering is applied to the
  `.nvmrc`/`.node-version`/`volta.node` blocker line, whose gate was already a full
  match but still admitted arbitrary leading and trailing Unicode whitespace.
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
- **An auto-selected script no longer receives npm's injected environment**, because it
  is no longer spawned by a package manager. On that path `npm_lifecycle_event`,
  `npm_package_name`, `npm_package_version`, `npm_config_user_agent` and `INIT_CWD` are
  all empty, and `node_modules/.bin` is not on `PATH`, so a sibling binary is not
  resolvable by bare name. Vitest itself is unaffected, and so are the `npx`,
  `pnpm exec` and `bunx` launchers, which set up their own resolution. Your project is
  affected only in the narrower case where a `globalSetup`, a Vitest config, or a test
  shells out to another `node_modules/.bin` binary by bare name, or reads
  `npm_package_*`/`npm_lifecycle_event`. `--script <name>` restores all of it, since it
  still runs through the package manager.
- **An auto-selected script's arguments are no longer shell-expanded**, because there is
  no shell on that path. Under `npm run`, `sh` expanded them before Vitest saw them:
  `vitest run src/**/*.test.ts` arrived as one argument per matching file and
  `--config ~/x.ts` as an absolute path under your home directory. Both are now passed
  literally, so Vitest receives the glob and the tilde as written — harmless where
  Vitest does its own glob matching, wrong where the shell was doing the work. Quoting
  is still honored (`--testNamePattern "formats currency"` remains one argument). Use
  `--script <name>` when a body relies on shell expansion.

### Added
- `scripts/test_run_vitest.py`: a regression module for the direct-Vitest-script
  predicate, covering shell chaining/redirection/substitution, newline chaining,
  npm/pnpm/yarn/bun launcher shadowing, npm exec package redirection, allowlisted vs.
  unrecognized environment keys (including `PATH`, package-manager config keys,
  dynamic-loader hooks, and code-loading `NODE_OPTIONS` values), the auto-selected
  execution path (no package-manager invocation, no `pretest` execution, preserved
  arguments, environment and launcher), and the runner's fallback/opt-in behavior end
  to end.

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
