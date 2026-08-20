# Changelog

Repository-level changelog. Versions here are repository git tags (`vX.Y.Z`);
individual skill versions live in each skill's `metadata.version`.

## [Unreleased]

Every session pays for skill descriptions in context; this batch trims the five most
expensive ones without changing any workflow.

### Changed
- `commit-all` 1.0.1, `dashfix` 1.2.1, `negafix` 1.2.1, `echarts` 1.1.3,
  `typescript` 1.3.3 - shorter frontmatter descriptions; workflow details the
  descriptions used to carry now live in the skill bodies.

## [1.12.0] - 2026-08-20

The two writing-style skills answer their 2026-08-19 field feedback: regex matches are
candidates until a verdict reads the sentence, and a single new file gets a pre-handoff
check that skips the project score. A new `commit-all` skill gathers the working tree
into one user-invoked commit.

### Added
- `commit-all` 1.0.0 - gather the working tree into one commit on the current branch
  with a generated English message; user-invoked only (`disable-model-invocation:
  true`), stops on `main`/`master`, previews mixed trees, supports `dry-run`, never
  pushes, never bypasses hooks, never rewrites history
- New "Git Workflow" group in `skills.sh.json` and the mirrored `git-workflow` plugin
  in the marketplace catalog for `commit-all`

### Changed
- `dashfix` 1.1.0 -> 1.2.0 - "Single-file check" inventories one file and reports
  candidate and replace counts separately; mixed-language Markdown classifies prose
  blocks, quotations, code fences, and diagnostics per block instead of one file-level
  verdict; a `replace` row's reason names the fix
- `negafix` 1.1.0 -> 1.2.0 - "Single-file check" verdicts every candidate from the full
  sentence before any rewrite; an exploratory `не A, а B` pattern for Ukrainian prose
  runs only on demand with a mandatory manual verdict; the counting-pass total counts
  candidates rather than violations

## [1.11.0] - 2026-08-11

The two writing-style skills answer their first field feedback: the dash ban learns
about language, both audits reach commit messages, both scores are normalized by project
size, and both skills ship a git hook.

### Added
- `dashfix` 1.0.0 -> 1.1.0 - "Language scope" makes the ban a rule of English typography
  that binds per file. In Ukrainian, Russian, Polish, and German the em dash is
  orthography, so the skill checks its form (em vs en, spacing, hyphen inside compounds)
  and a correct dash earns a fifth `justified` category. New `scripts/commit-msg` hook
  rejects a banned dash in a commit message and skips a message written in Cyrillic,
  with both limits of that heuristic documented (a Cyrillic name in an English message
  is skipped too, and Latin-script Polish and German cannot be detected at all), a
  `PreToolUse` snippet blocks the same mistake inside an agent session using perl alone
  (a `jq` pipeline exits 0 on a machine without `jq` and passes the commit through in
  silence), and an "Enforcement" section states that write mode does not survive a
  context compaction
- `negafix` 1.0.0 -> 1.1.0 - the same enforcement section with a warn-only
  `scripts/commit-msg` hook, chosen because the detection patterns overmatch by design,
  plus a note on how much noisier the Ukrainian patterns are than the English ones
- Both skills gain a commit-message inventory: `git log --grep` selects the commits,
  including merge commits and commits whose only hit sits in the body, and an inner `rg`
  pass prints the matching lines as `<hash>:<line>:<snippet>`. The history table reads
  like the working-tree one and stays out of the score. Both skills also let write mode
  inherit the quotation verdict, so reporting a violation stops breaking the rule
- Both skills add a counting pass (`rg --count-matches`) next to the line-oriented
  inventory, since `rg -n` prints a line holding two matches once. The occurrence total
  comes from the counting pass, a catalog row states how many occurrences its line
  carries, and a line whose occurrences disagree on the verdict splits into rows keyed
  `<location>#<n>`
- `negafix` sets its shared `PATTERN` once at the head of Step 1 and guards every later
  block with `: "${PATTERN:?...}"`, so a block run on its own aborts instead of handing
  `rg` an empty pattern that matches every line
- `negafix` adds `not a ... but a` to its inventory regex and its hook; the documented
  pattern list named it while neither command looked for it

### Changed
- Both scores are normalized: `max(0, 100 - spread - depth)`, where `spread` is the
  share of scanned files carrying a violation and `depth` is the capped average
  violation count per affected file. The old formula sent any project with five dirty
  files to 0 regardless of repository size
- Both scan-exclusion lists become a rule (everything generated, and every file whose
  text is data rather than prose), with each added exclusion named in the report
- Both working-tree passes name `.` explicitly, since `rg` handed a piped stdin and no
  path reads the pipe rather than the tree and reports zero matches on a dirty project
- `dashfix` replaces the `grep -rnP` fallback with `ggrep -rnP` and a perl one-liner,
  because BSD grep on macOS has no `-P`. The one-liner lists files with
  `--cached --others --exclude-standard`, repeats every scan exclusion both bare and
  `**/`-anchored, drops hidden paths, skips symlinks and files holding a NUL byte, and
  slurps each file to number its lines, so it reports the same locations as the `rg` pass
  instead of missing untracked files, keeping root or nested lock files, reading hidden,
  symlinked and binary paths, and numbering every line after the first file wrong
- README carries the skills.sh badge and states the install commands in the short
  `sentimony/skills` form

## [1.10.0] - 2026-08-09

Two new writing-style skills that ban AI-writing tells and score a project's prose.

### Added
- `dashfix` 1.0.0 - bans typographic dashes (em, en, and the neighboring Unicode code
  points) in favor of the plain hyphen in all produced text, audits a project with a
  per-occurrence catalog (`justified` / `replace` verdicts), and grades compliance on
  a deterministic 0-100 scale
- `negafix` 1.0.0 - bans negative parallelism (the "it's not just X, it's Y"
  construction) in favor of direct positive statements, audits English and Ukrainian
  prose with per-match verdicts that keep plain factual negation legal, and grades
  compliance on the same 0-100 scale
- New "Writing Style" group in `skills.sh.json` for both skills

### Changed
- Repository-wide dashfix cleanup: every published skill replaces typographic dashes
  (em and en) with plain-hyphen phrasing in SKILL.md, frontmatter descriptions,
  reference files, and script comments, with no workflow or behavior changes:
  `scope-triage` 1.0.2 -> 1.0.3, `plan-crafting` 1.1.1 -> 1.1.2, `vitest`
  1.2.0 -> 1.2.1, `typescript` 1.3.1 -> 1.3.2, `web-debug` 1.3.1 -> 1.3.2,
  `echarts` 1.1.1 -> 1.1.2. AGENTS.md and README prose get the same cleanup.
  Released changelog entries are frozen and keep their original punctuation, and the
  `dashfix` skill's own examples keep the characters they document.
- README install commands use the full GitHub URL form
  (`npx skills add https://github.com/sentimony/skills ...`)

## [1.9.1] - 2026-08-09

### Fixed
- `scope-triage` 1.0.1 → 1.0.2 — the skills.sh Snyk audit still returned W007 (high) on
  1.0.1, because Step 0 and Route A asked the model to repeat "the literal values, names,
  and numbers from the request" and kept the secrets carve-out in a separate paragraph.
  Both places now ask for the request's domain values, the prohibition on reproducing a
  secret, token, key, password, connection string, or personal datum leads its own
  paragraph, and credentials are referenced by placeholder name in the done criterion,
  in every command, and in the Security Model. No workflow change.

## [1.9.0] - 2026-08-02

Five skills get audit and feedback fixes at patch level; `vitest` earns the minor bump
by changing how an auto-selected package script executes.

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
  changes module resolution falls back with a `SCRIPT_NOT_DIRECT` note. The parsed
  path does no shell expansion, so a glob or `~` inside the script's own arguments is
  passed literally. Separately and on **every** path, `--script` included, the runner
  now decides the child's environment rather than passing its own on: the variables a
  package manager injects (`npm_*`, `INIT_CWD`, `PROJECT_CWD`, `BERRY_BIN_FOLDER`)
  are dropped, every empty, relative, or project-touching entry is filtered out of
  `PATH`, and the launcher is resolved to an absolute path against that filtered
  `PATH` — otherwise a project could ship its own `node_modules/.bin/npx` and have the
  runner execute it. A `PATH` entry is judged by every component of it, not only by
  where it finally resolves, since a symlink inside the project can be repointed after
  the check; and the program found in a surviving directory is resolved too, so an
  allowed directory that merely links back into the project (what `npm link` writes)
  supplies nothing. Variables from your own shell, `NPM_TOKEN` and `NPM_CONFIG_*`
  included, are untouched. A `globalSetup` or test that shelled out to a sibling
  binary from `node_modules/.bin`, or read `npm_package_*`, is affected. The Node
  preflight in **both** helpers goes through the same filter and now runs after it,
  so a project shipping its own `node_modules/.bin/node` no longer answers the
  preflight's question about itself; the shared rule lives in a new
  `skills/vitest/scripts/node_environment.py`, and both entry points are unchanged. A test script that chains another command, launches via a bare
  `pnpm`/`yarn`/`bun`, carries an app-specific environment prefix, or has arguments
  containing a bidi override or other invisible formatting codepoint still doesn't
  auto-run — each falls back to the local Vitest binary with a `SCRIPT_NOT_DIRECT`
  note, run with this helper's own arguments rather than the script's on that
  fallback path only, so flags spelled inside the script body (a `--config`, a
  `--environment`) no longer apply there; pass `--script <name>` to run it as
  written, with full lifecycle hooks, anyway. A package.json the runner cannot read —
  bytes that are not UTF-8, a non-object top level, a `scripts` list, a script body
  that is not text — now takes the same fallback to the local binary (without that
  note, since no script was skipped) instead of ending the run with a traceback, and
  an undecodable `.nvmrc` or `.node-version` reads as an absent one. Also hardens the project-file candidate
  scan (agent-toolchain directories excluded), the `engines.node` preflight (strict
  `>` parity with the inspector; a declaration now renders verbatim only when it is
  composed entirely of version-range characters and stays within the render limit,
  otherwise as a placeholder, without changing which projects are warned or blocked),
  the accepted script's rendered `Command:` line
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
  a real hydration check, and a resumed checkpoint is validated against the bounds the
  example itself writes and restricted to the current route list, so a hand-edited file
  cannot mark a route `ok` to have it skipped. Console output and page errors are escaped
  as they are collected, so a page cannot repaint the terminal or forge a line of the
  report. `with_server.py` now prints the server log path on a successful start.

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
- CI runs every `test_*.py` under `skills/`, which no job had been doing — it validated
  frontmatter, compiled Python, and grepped for hidden Unicode, but ran no tests.
  `actions/checkout` and `actions/setup-python` are on v7 (the old pins forced Node 20
  onto a Node 24 runner). The hidden-Unicode scan takes its pattern from the runtime
  definition in `run_vitest.py` instead of keeping a second copy — read out of the source
  with `ast`, so the scan executes none of the code it is checking — checks itself against a
  positive control carrying every codepoint in that set, and distinguishes "found
  nothing" from "the scanner failed", which `! grep` had reported alike. AGENTS.md
  states what CI now does and what a maintainer test module has to be for CI to run it.

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
