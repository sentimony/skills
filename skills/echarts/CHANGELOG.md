# Changelog

All notable changes to the `echarts` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.1.3] - 2026-08-21

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the symptom list in the frontmatter description to the two most common
  triggers; the full symptom catalog stays in the skill body.

## [1.1.2] - 2026-08-09

### Changed

- Replaced every typographic dash (em and en) in SKILL.md, including the frontmatter
  description, and in `references/audit.md` with plain-hyphen phrasing per the
  repository dashfix style; no workflow change

## [1.1.1] - 2026-08-02

### Changed
- `notMerge: true` interactive-state claims now conditional on wrapper, versions, and
  update path, with a requirement to prove a reset on the installed versions before
  reporting it, instead of inferring it from static source inspection
- Audit reference: state inventory (§1) and registration matrix (§2) allow one row/union
  for instances or paths that share a loader, owner, fallback, and transition, or one
  registration module, naming the group once instead of enumerating every instance/path
- Audit reference §5: classify the tooltip fixture's `/x` 404 as fixture-induced expected
  evidence, separate from the application diagnostics collected in §7
- Audit reference §6: split dataset measurement into two evidence records (current/
  representative dataset; source-cap or p99 fixture marked as a synthetic upper bound)
  and require naming a render-finished completion criterion before timing it
- Audit reference §4: toolbox testing scoped to the features the project actually
  configures, with custom/durable state capture and risk-proportional built-in checks

### Fixed
- Removed the unconditional claim that `notMerge: true` resets interactive state; it did
  not hold empirically on ECharts 6.1.0 + vue-echarts 8.0.1

## [1.1.0] - 2026-07-31

### Added
- Progressive-disclosure audit reference for state inventory, registration/render matrices,
  lifecycle, interactive-state ownership, tooltip trust, cardinality, zero-size gates, and
  browser evidence
- Explicit HTML-tooltip trust boundary separating ECharts-generated `params.marker` from
  external strings, stating the inert fixture value and the escaped rendering it must
  produce as two separate observations
- Browser audit requirement for `inside` dataZoom wheel behavior versus page scrolling

### Changed
- Replaced the fixed Canvas point-count claim with dataset/device/browser/interaction and
  SVG-output measurement guidance
- Reduced the primary skill's audit section to an entry point for the detailed reference

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
