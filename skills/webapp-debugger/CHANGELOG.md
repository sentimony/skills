# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.7] - 2026-11-07 - [0.0.101]

### Changed

- Workflow step 2 checks the connection mode with `agent-browser session info` before the
  first navigation: the run must use the own headless browser, an auto-connect or CDP
  connection stops it, the `Allow remote debugging?` prompt is never clicked, and the report
  names the mode (`20261101-0117`).

## [0.0.6] - 2026-11-04 - [0.0.99]

### Changed

- Step 1 checks the listeners on the port (`lsof -nP -iTCP:<port> -sTCP:LISTEN`, `lsof -p <pid> -a -d cwd -Fn`) and opens the explicit `127.0.0.1` or `[::1]` address of the current project's process when several listen (`20261028-1223`).

## [0.0.5] - 2026-10-27 - [0.0.95]

### Added

- `20261022-0041`: Timing pitfalls has a "Hidden page" item. Before checking timers,
  animations, polling, or `visibilitychange` logic, read `document.visibilityState`; on
  `hidden` the timing conclusions are coarse and the report says so. agent-browser 0.39
  has no flag that makes the page visible, so an exact-time check goes to `web-debug`
  and its `page.clock`. Reading the evidence adds that timer-driven text lags on a
  hidden page and is no defect until the page reads `visible`.
- `20261022-0353`: Workflow step 3 mocks the network before `open` when the project
  requires it or an action may write to a real backend: `--body` routes first, the
  catch-all `--abort` last, because in agent-browser 0.39 the first matching route
  wins, the reverse of Playwright. `--body` reads a fixture with `$(cat ...)`; a
  response that cannot be mocked (binary media, HLS, stateful pairs) stops the run with
  a pointer to `web-debug` instead of an unmocked page. Security Model names the routes.

## [0.0.4] - 2026-10-21 - [0.0.89]

### Changed

- The skill no longer hands the request to `debugging`. `/webapp-debugger` now drives a local
  web app through the agent-browser CLI: a private session, waits on concrete conditions,
  actions by accessibility refs, and console, page errors, network requests, and screenshots
  collected as evidence, with a Security Model. Requires `agent-browser` in PATH; it is
  installed, pinned to 0.39.0, only once the user authorizes setup.

## [0.0.3] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.2] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.1] - 2026-10-01 - [0.0.61]

### Added

- Experimental user-invoked entry point: `/webapp-debugger` hands the current request to the
  `debugging` skill.
