# Changelog

All notable changes to the `echarts` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

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
