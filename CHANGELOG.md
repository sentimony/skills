# Changelog

Repository-level changelog. Versions here are repository git tags (`vX.Y.Z`);
individual skill versions live in each skill's `metadata.version`.

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
