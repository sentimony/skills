# Changelog

All notable changes to the `echarts` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.5] - 2026-07-20

Driven by real-world audit feedback from a Vue/Nuxt dashboard (agilecharts)
using vue-echarts with centralized design tokens.

### Added
- Audit checklist: design-tokens theming (shared constants module straight into
  options) recognized as a valid alternative to `registerTheme`
- Audit checklist: one-off hardcoded hex classified as duplication/extraction
  debt even in an otherwise exemplary project
- Common Failure Modes: "`notMerge: true` everywhere" pitfall — forfeits diff
  optimization and resets legend/dataZoom state; reserve it for structural changes

## [1.0.4] - 2026-07-19

### Changed
- `examples/vanilla_line.html` loads ECharts via a pinned UMD build with an SRI
  hash instead of a runtime ESM CDN import (Snyk W012: unverifiable external
  dependency)
- Description rewritten in "You MUST use this when…" style and shortened

## [1.0.3] - 2026-07-12

Hardening in response to the skills.sh Snyk audit (Warn / Medium, W012 —
unverifiable external dependency). No behavior change. PR #TBD.

### Changed
- `examples/vanilla_line.html`: pin the standalone CDN import to an exact
  release (`echarts@6.1.0`) instead of a floating `@6`, and note that ESM
  imports can't carry an SRI hash so pinning is the available integrity control.

## [1.0.2] - 2026-07-07

Improvements from second real-world usage feedback (repeat audit of the same
Vue dashboard).

### Added
- Tooltip security note: escape untrusted data in HTML formatters or use
  `renderMode: 'richText'`
- ComposeOption code example for tree-shaken option typing
- SSR registration parity: client and Node `use([...])` lists must match
- `connect`/`group` caveat: only link charts with compatible axis semantics
- Failure mode: `notMerge: true` resets legend/dataZoom interactive state
- ECharts 6 migration notes: default theme change (`echarts/theme/v5`),
  label overflow/name-overlap prevention on by default

### Changed
- Intro now says "build, audit, or fix" to match the description trigger
- Registration-failure note clarifies it is a `console.error`, not a throw

## [1.0.1] - 2026-07-07

Improvements from first real-world usage feedback (audit of a multi-chart Vue dashboard).

### Added
- Shared registration module guidance for codebases with multiple chart components
- Type imports note: `import type` from root is bundle-safe; some types are root-only
- ECharts 6 migration notes: `containLabel` → `{ outerBoundsMode: 'same',
  outerBoundsContain: 'axisLabel' }`, `LegacyGridContainLabel`
- "Auditing Existing Usage" checklist (registrations, lifecycle, update semantics,
  imports, deprecated API, duplication)
- vue-echarts gotchas: `update-options`/`notMerge` for structural changes, `theme`
  prop/injection for theme switching, `group` prop; expanded `echarts.connect` as
  a dashboard UX feature

### Changed
- description now includes "auditing"

## [1.0.0] - 2026-07-07

Initial release.

### Added
- SKILL.md covering ECharts setup, framework integration (vanilla, React, Vue),
  lifecycle management (init/resize/dispose), tree-shaken imports, dataset usage,
  theming, performance for large datasets, streaming updates, SSR, and common
  failure modes
- Reference examples: `examples/vanilla_line.html`, `examples/react_chart.tsx`,
  `examples/vue_chart.vue`
