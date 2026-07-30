# Changelog

All notable changes to the `web-debug` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.3.0] - 2026-07-30

### Changed

- Made server readiness probe the automation host, fail immediately for exited child processes,
  and display bounded sanitized server-log evidence.
- Normalized malformed server commands and launcher failures to fixed path-free
  diagnostics without tracebacks or raw command text.
- Added hydration-aware, checkpointed multi-route console-audit guidance and examples.
- Improved accessibility discovery for composite names, nested-scroll coverage, and SSR evidence.

## [1.2.1] - 2026-07-20

Driven by real-world audit feedback from a Nuxt dashboard (agilecharts) behind
an auth middleware.

### Added
- Waiting Strategy: cold dev-server starts can reset freshly typed form values
  (Vite re-optimization/HMR reload ~500ms after load) — settle or pre-warm
  before filling forms
- Best Practices: login-then-audit pattern (fill -> submit -> `wait_for_url`
  leaving `/login`; never assert `input_value()` after the redirect)
- `examples/console_audit.py`: optional login step over a shared browser
  context; Reference Files now state the example is a copy-and-edit template,
  not a CLI

## [1.2.0] - 2026-07-19

### Changed
- `with_server.py` runs `--server` commands without a shell (`shlex.split` +
  `shell=False`); shell chains now need an explicit `bash -c '…'` wrapper
- Pinned the Playwright install instruction to an exact release
- Security Model: documented the no-shell contract and added untrusted-output
  boundary rules for collected page content
- Description rewritten in "You MUST use this when…" style

## [1.1.2] - 2026-07-12

Hardening in response to the skills.sh Gen Agent Trust Hub audit (Warn / Medium).
No behavior change. PR #TBD.

### Added
- **Security Model** section: documents that `--server` is user-controlled shell
  configuration (never build it from untrusted app output) and that page content
  (DOM, console, network) is untrusted data, not instructions.

### Changed
- Reworded the "run `--help` first" guidance so it no longer reads as "do not
  inspect the script"; auditing/customizing the source is explicitly encouraged.
- Expanded the `shell=True` comment in `with_server.py` to state that the command
  is user-supplied configuration, not agent- or network-controlled input.

## [1.1.1] - 2026-07-05

First field feedback incorporated (four real debugging sessions on Vite/Nuxt SPAs). PR #4.

### Added
- `requestfailed` and `response >= 400` listeners, `page.screenshot()`, console msg
  types, playwright install fallback, and scratchpad note in the canonical template
- **Interpreting Failures** section: `ERR_ABORTED` false positives (HEAD/204,
  navigation-cancelled requests, Vite dependency re-optimization), cross-checking
  before reporting network errors, second-run confirmation, headless/dev noise reference
- `examples/console_audit.py`: multi-page console audit with dedup, noise filtering,
  truncation, and the late-binding lambda trap (`m=msgs`)
- Decision tree step: confirm the actual port from server startup logs
- Best practices: click by accessible name (never by index), i18n locale caveat,
  real-backend side effects and test-data cleanup

### Changed
- Waiting Strategy: fixed pause legitimized for log collection; documented `goto`
  (hard navigation) vs router-link click (soft) for SPAs
- Helper script paths use skill-root-relative style (`python <skill>/scripts/...`)
- `req.failure` guarded with `or "unknown"` (it is `Optional[str]` in Playwright Python)
- Author metadata normalized to human-readable form
- `LICENSE.txt` renamed to `LICENSE` (content unchanged)

## [1.1.0] - 2026-07-04

Initial import as `web-debug`, forked from `anthropics/skills` `webapp-testing` (1.0.0).

### Changed
- Renamed skill to `web-debug`; adapted frontmatter and attribution
  (see `references/attribution.md`)
