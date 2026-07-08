# Changelog

All notable changes to the `echarts` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

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
