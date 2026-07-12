# Changelog

Repository-level changelog. Versions here are repository git tags (`vX.Y.Z`);
individual skill versions live in each skill's `metadata.version`.

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
  false positive by rewording an isolated `` `!` `` (non-null operator) that the
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
