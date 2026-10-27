# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.3] - 2026-10-27 - [1.58.16]

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

## [1.1.2] - 2026-10-21 - [1.58.10]

### Changed

- The skill no longer hands the request to `debugging`. `/webapp-debugger` now drives a local
  web app through the agent-browser CLI: a private session, waits on concrete conditions,
  actions by accessibility refs, and console, page errors, network requests, and screenshots
  collected as evidence, with a Security Model. Requires `agent-browser` in PATH; it is
  installed, pinned to 0.39.0, only once the user authorizes setup.

## [1.1.1] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.0] - 2026-10-01 - [1.48.0]

### Added

- Experimental user-invoked entry point: `/webapp-debugger` hands the current request to the
  `debugging` skill.
