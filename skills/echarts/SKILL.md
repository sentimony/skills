---
name: echarts
description: You MUST use this when building, styling, debugging, or optimizing Apache ECharts charts in JavaScript, React, or Vue — setup, lifecycle, responsive resizing, theming, large datasets, streaming, SSR, and symptoms like a blank chart, broken resize, stale series, or "component not exists" errors. Not for choosing chart types or for other charting libraries.
metadata:
  author: Ihor Orlovskyi
  version: "1.0.4"
license: MIT
compatibility: Requires a JavaScript package manager; `echarts` must be installed in the target project (framework wrappers are optional).
---

# ECharts

Use this skill to build, audit, or fix Apache ECharts charts without turning the task into an option-reference lookup. Match the project's existing setup first; only introduce wrappers or new dependencies when the project has none.

## Decision Tree

```
User task -> Does the project already use ECharts?
    - Yes -> Find existing chart components/helpers, reuse their init, theme,
             and resize patterns. Match import style (full vs echarts/core).
    - No -> Pick integration by framework:
        - React -> echarts-for-react wrapper, or a small hook around
                   init/dispose if the project avoids extra deps
        - Vue 3 -> vue-echarts wrapper, or composable around init/dispose
        - Vanilla / other -> echarts.init on a sized container

Next -> Bundle size a concern (app ships to users)?
    - Yes -> Import from 'echarts/core' and register only the used charts,
             components, and renderer (tree-shaking)
    - No / internal tool / prototype -> import * as echarts from 'echarts'

Then -> Build the smallest working option, render it, then layer on
        interactivity (tooltip, dataZoom, toolbox) and theming.
```

## Core Workflow

1. Inspect first: find existing ECharts usage, themes, and shared option helpers before writing a new chart.
2. Size the container: the container element must have non-zero width and height **before** `echarts.init` runs; a chart in a display:none or unmounted tab renders blank.
3. Own the lifecycle: one `init` per container, `resize()` on container size change, `dispose()` on unmount. Wrappers handle this; hand-rolled code must.
4. Update via `setOption`: default merge mode for incremental updates (streaming, new data); `notMerge: true` when the chart type or structure changes.
5. Verify visually: render the chart and check axes, labels, and tooltip against real data before polishing.

## Setup

```bash
npm install echarts                      # core library (always)
npm install echarts-for-react            # React wrapper (optional)
npm install vue-echarts                  # Vue 3 wrapper (optional)
```

Tree-shakeable imports for production bundles:

```ts
import * as echarts from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, DataZoomComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer]);
```

A missing registration fails at runtime with a console error naming the missing chart/component — register it, do not switch to full import to silence the error. It is a `console.error`, not a thrown exception, so unit tests pass silently over it; catch it by asserting on the console or the rendered output.

With multiple chart components in one codebase, prefer a shared registration module (one `echarts.use([...])` call imported everywhere) over per-component `use` lists — per-component lists drift out of sync and hide missing registrations until a component renders alone. Deliberate feature-specific registration in code-split routes is a valid exception for lazy-loaded dashboards.

Type imports: `import type { ... } from 'echarts'` is erased at compile time and does not affect the bundle — only **value** imports from the root package pull everything in. Some types (`XAXisComponentOption`, `DefaultLabelFormatterCallbackParams`) are exported only from the root, so mixing `import type` from `'echarts'` with values from `'echarts/core'` is normal; prefer `ComposeOption` from `'echarts/core'` for option types:

```ts
import type { ComposeOption } from 'echarts/core';
import type { LineSeriesOption } from 'echarts/charts';
import type { GridComponentOption, TooltipComponentOption } from 'echarts/components';

type ChartOption = ComposeOption<LineSeriesOption | GridComponentOption | TooltipComponentOption>;
```

## Lifecycle Rules

- **Vanilla**: keep the chart instance; call `chart.resize()` from a `ResizeObserver` on the container; call `chart.dispose()` before removing the container.
- **React (echarts-for-react)**: pass `option` as a prop; use `notMerge` prop when replacing structure; get the instance via `ref.getEchartsInstance()` only for imperative needs (streaming `setOption`, `dispatchAction`).
- **React (hand-rolled hook)**: `init` in an effect, `dispose` in its cleanup; keep `option` updates in a separate effect so the chart is not re-created on every render.
- **Vue (vue-echarts)**: use `:option` binding with `autoresize`; access the instance via template ref for `dispatchAction`. Pass `:update-options="{ notMerge: true }"` for structural option changes (chart type, series count, removing axes/series) — merge mode keeps stale series. Switch themes via the `theme` prop or `THEME_KEY` injection, not `update-options` (on older ECharts/vue-echarts versions, remount/re-init instead). Use the `group` prop to link charts (equivalent to `echarts.connect`).
- Never call `echarts.init` twice on the same DOM node; reuse the instance or dispose first (`echarts.getInstanceByDom` to check).

## Data and Options

- Prefer the `dataset` component (`source` + `encode`) when multiple series or charts share one table of data; use per-series `data` for simple single-series charts.
- Time series: use `xAxis: { type: 'time' }` with `[timestamp, value]` pairs instead of pre-formatting date strings into a category axis.
- Large categorical axes: set `axisLabel.interval`/`rotate` deliberately instead of accepting overlap.
- Tooltips: `trigger: 'axis'` for line/bar time series, `trigger: 'item'` for pie/scatter/map.
- Use `valueFormatter` or `tooltip.formatter` for units; keep number formatting in one shared helper when the dashboard has many charts.
- HTML tooltip `formatter` output is injected as HTML: escape untrusted data (series names, user-generated labels) with a shared escape helper, or use `tooltip.renderMode: 'richText'` to opt out of HTML entirely.

## Performance

- Canvas (default renderer) is fine up to ~100K points; use SVG renderer only for small charts needing crisp export or DOM-level styling.
- For large line/scatter series: enable `large: true` and `sampling: 'lttb'` on the series; turn off `animation` for initial render of big datasets.
- Millions of points: use `echarts-gl` (WebGL) — a separate dependency; add it only when actually needed.
- Streaming: call `setOption({ series: [{ data }] })` on the existing instance (merge mode); do not re-init or pass `notMerge` per tick.
- Many charts on one page: share a single `ResizeObserver`/resize handler and use `echarts.connect` for linked tooltips/dataZoom instead of duplicating handlers. `connect` is also a UX feature for dashboards: `chart.group = 'name'; echarts.connect('name')` (or the vue-echarts `group` prop) syncs tooltips and dataZoom across related charts. Only link charts with compatible axis semantics (same x-axis type and domain); a chart with a different axis belongs in its own group or unlinked.

## Theming

- Register a theme once (`echarts.registerTheme('name', themeObject)`) and pass the name to every `init`; do not copy color arrays into each chart's option.
- Dark mode: prefer `init(el, null, ...)` plus a registered dark theme, or `darkMode: true` in the option. Switch themes at runtime with `chart.setTheme(...)` (ECharts 6) or the vue-echarts `theme` prop; on ECharts 5 themes are fixed at init time — re-init (dispose + init) there.
- Keep chart-independent styling (font family, palette) in the theme; keep data-dependent styling (visualMap ranges, markLines) in the option.

## SSR and Export

- Server-side rendering (reports, emails, OG images): `echarts.init(null, null, { renderer: 'svg', ssr: true, width, height })` then `renderToSVGString()` — Node only, no DOM needed.
- If option builders are shared between the browser and a Node SVG renderer, keep both `echarts.use([...])` registration points covering the same set — a narrower server-side list silently renders without the missing components.
- Client image export: enable `toolbox.feature.saveAsImage`, or call `chart.getDataURL({ pixelRatio: 2 })` programmatically.

## ECharts 6 Migration Notes

- `grid.containLabel` is deprecated. The semantics-preserving migration is `containLabel: true` → `{ outerBoundsMode: 'same', outerBoundsContain: 'axisLabel' }`; set `grid.outerBounds` only when you need a custom constraint rect (it is a separate part of the new layout API). The legacy behavior still works only if `LegacyGridContainLabel` (from `'echarts/features'`) is registered — treat remaining `containLabel: true` usages as tech debt when auditing.
- The default theme changed in v6 (palette and component layout). To keep the v5 look during migration: `import 'echarts/theme/v5'` and pass `'v5'` as the theme to `init`.
- Axis label overflow prevention and axis-name overlap prevention are on by default in v6, which can shift layouts slightly; disable with `grid.outerBoundsMode: 'none'` and `xAxis/yAxis.nameMoveOverlap: false` when pixel-parity with v5 matters.
- Check the installed major version (`node_modules/echarts/package.json`) before recommending options; deprecations surface as console warnings, not errors.

## Auditing Existing Usage

When reviewing (not building) a codebase's ECharts usage, check in order:

1. **Registrations**: one shared `use([...])` module vs per-component lists that drift; missing or duplicated registrations; with SSR, verify the client and server `use([...])` lists cover the same components.
2. **Lifecycle**: every `init` has a matching `dispose`; resize observed on the container, not the window.
3. **Update semantics**: `notMerge`/`update-options` used where chart type, series count, or axes/series are removed.
4. **Imports**: value imports from root `'echarts'` in tree-shaken builds; `import type` is fine.
5. **Deprecated API**: `containLabel` and other version-migration debt (see migration notes above).
6. **Duplication**: repeated option/formatter logic that belongs in a shared helper or registered theme.

## Common Failure Modes

- **Blank chart, no error**: container had zero size at init (hidden tab, flex parent without height, init before mount). Fix sizing/timing, then call `resize()`.
- **Chart does not update**: a new option object with merge mode silently keeps stale series/axes — use `notMerge: true` when removing series or changing chart type.
- **Legend/dataZoom selection lost after update**: `notMerge: true` resets interactive state; capture `chart.getOption().legend[0].selected` (and dataZoom range) before the update and pass it back in the new option.
- **"Component xxx not exists" / missing chart**: tree-shaken build without the registration; add it to `echarts.use([...])`.
- **Memory growth in SPA**: instances not disposed on route change; verify `dispose()` runs in unmount cleanup.
- **Chart wrong size after sidebar/panel toggle**: window `resize` event never fired; observe the container (ResizeObserver / `autoresize`), not the window.
- **Tooltip clipped**: set `tooltip.confine: true` or `appendToBody`-style `tooltip.appendTo` when the chart sits in an overflow-hidden container.
- **Sluggish with big data**: animation on + no sampling; set `animation: false`, `sampling: 'lttb'`, `large: true` before reaching for WebGL.

## Reference Examples

- `examples/vanilla_line.html` - Vanilla JS time-series line chart with resize handling
- `examples/react_chart.tsx` - React component with tree-shaken imports and echarts-for-react
- `examples/vue_chart.vue` - Vue 3 component using vue-echarts with autoresize
