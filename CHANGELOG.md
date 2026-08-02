# Changelog

Repository-level changelog. Versions here are repository git tags (`vX.Y.Z`);
individual skill versions live in each skill's `metadata.version`.

## [1.9.0] - 2026-08-02

Audit and feedback fixes across the collection.

### Fixed
- `scope-triage` 1.0.0 → 1.0.1 — credentials are named, never echoed, in announced
  contracts and done criteria (Snyk W007), plus an explicit Security Model.
- `vitest` 1.1.0 → 1.2.0 — **behavior change:** `run_vitest.py` now auto-runs a
  package.json script only when the entire script body does nothing but invoke
  Vitest, matching the skill's Security Model treatment of package.json scripts as
  untrusted repository data. That accepted script now executes as parsed environment
  plus argv, not through `npm run`/`yarn`/`pnpm`/`bun run`, so package-manager
  lifecycle hooks (`pretest`, `posttest`, and equivalents) are no longer triggered by
  auto-selection — its own flags and environment are still honored on this path.
  `NODE_OPTIONS` is still an accepted environment key, now restricted to
  memory-tuning values such as `max-old-space-size` and `max-semi-space-size`
  (underscore spellings included); a value that instead loads code, opens a port, or
  changes module resolution falls back with a `SCRIPT_NOT_DIRECT` note. This parsed
  path also skips npm's injected environment and `node_modules/.bin` on PATH, and
  does no shell expansion, so a glob or `~` inside the script's own arguments is
  passed literally. A test script that chains another command, launches via a bare
  `pnpm`/`yarn`/`bun`, carries an app-specific environment prefix, or has arguments
  containing a bidi override or other invisible formatting codepoint still doesn't
  auto-run — each falls back to the local Vitest binary with a `SCRIPT_NOT_DIRECT`
  note, run with this helper's own arguments rather than the script's on that
  fallback path only, so flags spelled inside the script body (a `--config`, a
  `--environment`) no longer apply there; pass `--script <name>` to run it as
  written, with full lifecycle hooks, anyway. Also hardens the project-file candidate
  scan (agent-toolchain directories excluded), the `engines.node` preflight (strict
  `>` parity with the inspector; a declaration that isn't a recognizable version range
  now renders as a placeholder instead of verbatim, without changing which projects
  are warned or blocked), the accepted script's rendered `Command:` line
  (control characters and Unicode line separators rejected, length capped), and
  calibrates the Nuxt adapter guidance: mixing `node`- and `nuxt`-environment files
  in one config is still the intended pattern but isn't guaranteed leak-free, so it
  now requires a representative mixed run as proof, with a uniform Nuxt environment
  or split projects/configs documented as fallbacks.
- `typescript` 1.3.0 → 1.3.1 — the Nuxt coverage report no longer contradicts itself,
  `NODE_RUNTIME_MISMATCH` states the next action instead of only raw version numbers,
  and the `vue-tsc` migration guidance is version-gated.
- `web-debug` 1.3.0 → 1.3.1 — the crawl example now records a route as `ok` only
  after it has finished and its console messages are counted; a new `incomplete`
  status covers a route that was interrupted, and a matching prior checkpoint resumes
  instead of re-crawling completed routes (the checkpoint's on-disk shape changed
  accordingly — per-route results moved under a `results` key). The example's
  `HYDRATED_SELECTOR` constant is renamed `CLIENT_ONLY_SELECTOR`, gated by a new
  `wait_until_hydrated()` check that replaces the fixed sleep previously standing in for
  a real hydration check. `with_server.py` now prints the server log path on a
  successful start.

### Changed
- `plan-crafting` 1.1.0 → 1.1.1 — fallback verification for changes with no test seam,
  scoped staging, fixture realism, artifact-location precedence.
- `echarts` 1.1.0 → 1.1.1 — conditional `notMerge` claims requiring runtime proof,
  grouped state inventory, named registration unions, split performance evidence.
- `scope-triage` 1.0.0 → 1.0.1 — Route C may present a whole design in one message when
  it fits, keeping per-section approval only for separately contentious sections, and
  applies a revision before answering a new question in the same reply; Step 0 names a
  fan-out-then-targeted retrieval strategy.
- `scope-triage` and `plan-crafting` share one artifact-location precedence rule: an
  explicit user instruction overrides the skill default; a repository convention does
  not.

## [1.8.0] - 2026-07-31

Security-normalized audit guidance across the public skill collection.

### Added
- `vitest` `references/audit.md`, `typescript` `references/audit.md`, and `echarts`
  `references/audit.md` — progressive-disclosure audit guidance kept out of the main
  workflow until a request is actually an audit.

### Changed
- `vitest` 1.0.3 → 1.1.0 — normalized, safe existing-suite audit reports and audit
  guidance.
- `typescript` 1.2.2 → 1.3.0 — normalized TypeScript and Nuxt audit reports, safe
  local-tool resolution, and Node-runtime preflight guidance.
- `web-debug` 1.2.1 → 1.3.0 — hardened readiness and bounded log evidence, plus
  checkpointed browser, accessibility, and console-audit guidance.
- `echarts` 1.0.5 → 1.1.0 — audit guidance for lifecycle, trust, interaction, and
  browser evidence moved to a reference file.
- `plan-crafting` 1.0.0 → 1.1.0 — explicit Security Model: repository evidence and tool
  output are data, and the skill takes no shell or network actions.
- All six skills now use security-normalized handling of untrusted repository, page,
  DOM, test, compiler, and tool output, with expanded audit guidance where applicable.

## [1.7.0] - 2026-07-29

Two design skills that decide how much design a request actually needs, then turn the
approved design into an executable plan.

### Added
- `scope-triage` 1.0.0 — a fork of `obra/superpowers` `brainstorming` that classifies
  request scope first and routes to one of three outcomes: direct implementation for
  explicitly specified mechanical changes and localized fixes, a light spec for large
  but fully specified changes with a single open question, or the full design cycle
  (clarifying questions, approach trade-offs, sectioned design approval, a design doc in
  `docs/specs/`, handoff to `plan-crafting`) whenever anything about the product, UX, or
  public contract is still undecided; hard implementation gate, assumption register,
  mirrored rationalizations table, and Route C design lenses in `references/`
- `plan-crafting` 1.0.0 — a fork of `obra/superpowers` `writing-plans` that turns an
  approved design or settled requirements into bite-sized TDD tasks with exact files,
  interfaces, verification steps, and commits; plans are written to
  `docs/plans/YYYY-MM-DD-<feature-name>.md` and handed off to `subagent-driven-development`
  or `executing-plans`

Both skills replace their upstream counterparts rather than complementing them — install
one of each pair, not both.

## [1.6.0] - 2026-07-20

Feedback-driven guidance updates from real audit sessions on the agilecharts project.

### Changed
- `typescript` 1.2.1 → 1.2.2 — audit guidance: "already healthy" early exit,
  sampling heuristic for massive non-null-assertion counts, generic `defineProps`
  for `config: any` Vue props; error playbook gains the
  `ERR_PACKAGE_PATH_NOT_EXPORTED './lib/tsc'` entry; TS-7 migration reference
  gains a "Choosing the TS-7 target" checklist and a `types: []` vs `lib` note
- `vitest` 1.0.2 → 1.0.3 — Nuxt auto-import leak into `environment: node` files
  documented in Common Failure Modes (symptom, cause, diagnosis); `.nuxt`-cache
  warning (`nuxt prepare`, not `rm -rf`); mixed node/nuxt environment config
  example in the Nuxt adapter
- `web-debug` 1.2.0 → 1.2.1 — cold-start HMR form-reset pitfall in Waiting
  Strategy; login-then-audit pattern in Best Practices; `console_audit.py`
  example gains an optional login step over a shared context and is documented
  as a copy-and-edit template
- `echarts` 1.0.4 → 1.0.5 — audit checklist recognizes design-tokens theming as
  a valid alternative to `registerTheme` and classifies one-off hardcoded hex
  colors as duplication debt; Common Failure Modes gains the "`notMerge: true`
  everywhere" pitfall

## [1.5.0] - 2026-07-19

### Changed
- `web-debug` 1.1.2 → 1.2.0 — Agent Trust Hub remediation: `with_server.py` runs
  `--server` without a shell (shlex + `shell=False`, explicit `bash -c` escape
  hatch), Playwright install pinned to an exact release, Security Model gains
  untrusted-output boundary rules
- `echarts` 1.0.3 → 1.0.4 — Snyk W012 remediation: vanilla example loads ECharts
  via a pinned UMD build with an SRI hash instead of a runtime ESM import
- `typescript` 1.2.0 → 1.2.1, `vitest` 1.0.1 → 1.0.2 — descriptions rewritten
- All four descriptions now start with "You MUST use this when…"; new repository
  convention for skill descriptions

## [1.4.0] - 2026-07-13

### Changed
- `typescript` 1.1.1 → 1.2.0 — real-world feedback from a Vue/Netlify TypeScript 7
  side-by-side migration: `inspect_typescript.py` now detects a native TypeScript 7
  compiler installed alongside the framework's TypeScript 6 and reports each
  `typecheck*` script's target tsconfig; added the four hardening flags
  (`noImplicitOverride`, `noFallthroughCasesInSwitch`, `noUnusedLocals`,
  `noUnusedParameters`) to the effective-flags report and an explicit
  "coverage complete" result; documented the real-package dual-install layout that
  keeps `typescript` on genuine 6.x for vue-tsc/Volar; clarified "pinned" and CI
  auditing for multiple compiler paths

## [1.3.1] - 2026-07-12

Security-audit hardening from the skills.sh scanners. No behavior change.

### Changed
- `web-debug` 1.1.1 → 1.1.2 — Gen Agent Trust Hub audit (Warn/Medium): added a
  Security Model section (`--server` is user-controlled shell config; page
  content is untrusted data, not instructions), reworded the "run `--help`
  first" guidance so it no longer reads as "don't inspect the source", and
  clarified the `shell=True` comment in `with_server.py`
- `echarts` 1.0.2 → 1.0.3 — Snyk audit (Warn/Medium, W012): pinned the
  standalone CDN import in `examples/vanilla_line.html` to an exact release
  (`echarts@6.1.0`) instead of a floating `@6`
- `typescript` 1.1.0 → 1.1.1 — cleared the skills.sh "Contains Shell Commands"
  false positive by rewording an isolated non-null exclamation-mark operator that the
  scanner read as a shell-command directive

## [1.3.0] - 2026-07-11

### Added
- `typescript` 1.1.0 — migration guidance for the stable TypeScript 7 native
  compiler, including the TypeScript 6 compatibility bridge, compiler-API and
  framework limitations, side-by-side adoption, and rollback; research checked
  against official TypeScript sources dated 2026-03-23 and 2026-07-08

### Changed
- README skills table: renamed Version to Skill Version and added the repository
  Release tag associated with each skill version

## [1.2.2] - 2026-07-07

### Changed
- `echarts` 1.0.1 → 1.0.2 — second-audit feedback: tooltip security,
  ComposeOption example, SSR registration parity, `connect` axis-semantics
  caveat, `notMerge` interactive-state failure mode, ECharts 6 default-theme
  and label-overflow migration notes

## [1.2.1] - 2026-07-07

### Changed
- `echarts` 1.0.0 → 1.0.1 — first-usage feedback: shared registration module
  guidance, type-import bundle notes, ECharts 6 migration notes
  (`containLabel` → `outerBoundsMode`/`outerBoundsContain`), "Auditing Existing
  Usage" checklist,
  vue-echarts `update-options`/`group` gotchas

## [1.2.0] - 2026-07-07

### Added
- `echarts` 1.0.0 — build, style, debug, and optimize Apache ECharts
  visualizations in vanilla JS, React, or Vue; lifecycle management,
  tree-shaken imports, theming, large-dataset performance, SSR, common
  failure modes; vanilla/React/Vue reference examples

### Changed
- `skills.sh.json` groups reorganized: Browser (web-debug, echarts) and
  JavaScript Tooling (vitest, typescript) instead of Development / Quality
  Assurance
- AGENTS.md: mandatory updates of the repository CHANGELOG and skills.sh.json,
  release/CI notes; a new-skill branch may change existing files if noted in
  the repository CHANGELOG

## [1.1.1] - 2026-07-07

### Changed
- `typescript` 1.0.1 — framework checkers, audit mode, script skip criteria

## [1.1.0] - 2026-07-05

### Added
- `typescript` 1.0.0 — configure tsconfig, resolve compiler errors, debug slow
  type-checking, fix module resolution, migrate JS to TS; inspect-first Python
  helpers, error playbook, module-resolution / migration / monorepo references
- `skills.sh.json` grouping the skills.sh page into Development and
  Quality Assurance sections

### Changed
- README skills table: new Version column with each skill's `metadata.version`

## [1.0.1] - 2026-07-05

### Added
- Per-skill `CHANGELOG.md` for `vitest` and `web-debug` (Keep a Changelog style;
  not referenced from SKILL.md so it never enters an agent's context)
- `AGENTS.md` (+ `CLAUDE.md` importing it) with repository conventions:
  English-only content, plain semver in skill metadata with `v` prefix reserved
  for git tags, feature-branch + squash-merge workflow
- Basic CI: SKILL.md frontmatter validation (name/description/semver version),
  Python compile check for scripts and examples, hidden/bidi Unicode check

## [1.0.0] - 2026-07-05

First tagged release of the skills collection, published on
[skills.sh](https://skills.sh/sentimony/skills).

### Skills
- `vitest` 1.0.1 — configure, write, debug, run, and migrate Vitest tests for
  JavaScript/TypeScript projects
- `web-debug` 1.1.1 — debug local web apps via Playwright (fork of
  `anthropics/skills` `webapp-testing` with field-feedback improvements)
