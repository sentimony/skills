# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.16] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.15] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.14] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.13] - 2026-09-15 - [0.0.52]

### Added

- Named the boundary with `debugging` and `web-debug`: this skill owns ECharts mechanics,
  root-cause investigation and browser evidence belong to those. It matters for the skill's
  own blank-chart and broken-resize triggers.

### Changed

- Install examples take the command from the project's package manager instead of hardcoding
  `npm install`, which contradicted the skill's own "match the project's package manager"
  rule and its package-manager-neutral `compatibility` line. The security model follows.

## [0.0.12] - 2026-09-14 - [0.0.48]

### Added
- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [0.0.11] - 2026-09-07 - [0.0.31]

Driven by [2026-09-03](https://github.com/sentimony/skills-aiassist/blob/frontend-crafting/docs/feedbacks/2026-09-03-03-44_echarts.md), [2026-09-04](https://github.com/sentimony/skills-aiassist/blob/frontend-crafting/docs/feedbacks/2026-09-04-00-44_echarts.md), and [2026-09-04](https://github.com/sentimony/skills-aiassist/blob/frontend-crafting/docs/feedbacks/2026-09-04-02-58_echarts.md) audit feedback.

### Added
- Decision-tree routing for audits of projects without ECharts, with an applicability and repeat-audit section 0.
- DOM proxies for audits without a reachable instance, SVG dataZoom slider geometry, and a verified Playwright drag sequence.
- Render-completion criteria that distinguish direct instance evidence from indirect structure-stability evidence, plus two theme-proof profiles.
- A grid sweep for `trigger: 'item'` tooltips and explicit `unavailable` and time-boxed audit conventions.

## [0.0.10] - 2026-08-21 - [0.0.20]

Description-cost release: shorter frontmatter description, same behavior.

### Changed
- Trimmed the symptom list in the frontmatter description to the two most common
  triggers; the full symptom catalog stays in the skill body.

## [0.0.9] - 2026-08-09 - [0.0.17]

### Changed

- Replaced every typographic dash (em and en) in SKILL.md, including the frontmatter
  description, and in `references/audit.md` with plain-hyphen phrasing per the
  repository dashfix style; no workflow change

## [0.0.8] - 2026-08-02 - [0.0.15]

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

## [0.0.7] - 2026-07-31 - [0.0.14]

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

## [0.0.6] - 2026-07-20 - [0.0.12]

Driven by real-world audit feedback from a Vue/Nuxt dashboard (agilecharts)
using vue-echarts with centralized design tokens.

### Added
- Audit checklist: design-tokens theming (shared constants module straight into
  options) recognized as a valid alternative to `registerTheme`
- Audit checklist: one-off hardcoded hex classified as duplication/extraction
  debt even in an otherwise exemplary project
- Common Failure Modes: "`notMerge: true` everywhere" pitfall: forfeits diff
  optimization and resets legend/dataZoom state; reserve it for structural changes

## [0.0.5] - 2026-07-19 - [0.0.11]

### Changed
- `examples/vanilla_line.html` loads ECharts via a pinned UMD build with an SRI
  hash instead of a runtime ESM CDN import (Snyk W012: unverifiable external
  dependency)
- Description rewritten in "You MUST use this when…" style and shortened

## [0.0.4] - 2026-07-12 - [0.0.9]

Hardening in response to the skills.sh Snyk audit (Warn / Medium, W012:
unverifiable external dependency). No behavior change. PR #TBD.

### Changed
- `examples/vanilla_line.html`: pin the standalone CDN import to an exact
  release (`echarts@6.1.0`) instead of a floating `@6`, and note that ESM
  imports can't carry an SRI hash so pinning is the available integrity control.

## [0.0.3] - 2026-07-07 - [0.0.7]

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

## [0.0.2] - 2026-07-07 - [0.0.6]

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

## [0.0.1] - 2026-07-07 - [0.0.5]

Initial release.

### Added
- SKILL.md covering ECharts setup, framework integration (vanilla, React, Vue),
  lifecycle management (init/resize/dispose), tree-shaken imports, dataset usage,
  theming, performance for large datasets, streaming updates, SSR, and common
  failure modes
- Reference examples: `examples/vanilla_line.html`, `examples/react_chart.tsx`,
  `examples/vue_chart.vue`
