# Changelog

All notable changes to the `web-debug` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.3.1] - 2026-08-02

### Changed

- `examples/console_audit.py`: renamed `HYDRATED_SELECTOR` to `CLIENT_ONLY_SELECTOR` and
  added a `wait_until_hydrated()` gate used in both the login block and the routes loop,
  replacing the fixed sleeps that the example previously used as a stand-in for a real
  hydration check. The remaining fixed waits are now named for the distinct hazard each
  one covers: a console-output collection window after render, and a
  `settle_dev_server_reload()` step before the login form, since the cold dev-server
  HMR reload can wipe typed values after handlers are already attached.
- `examples/console_audit.py`: the checkpoint write is now atomic (write to a temp file,
  then rename over the output), and a matching prior checkpoint (same base URL and route
  list) is resumed, skipping routes already recorded as `ok`; a route is written as
  `incomplete` (a new fourth status alongside `ok`, `hydration-error` and
  `navigation-error`) until it has finished and its messages have been counted, so an
  interrupted route is re-crawled instead of trusted. The checkpoint file's on-disk shape
  changed with resume: per-route results now sit under a `results` key alongside `base`
  and `routes`, where 1.3.0 wrote them at the top level. A resumed run says so on stdout
  and points at the file to delete for a fresh crawl.
- `examples/console_audit.py`: a resumed checkpoint is now validated against the bounds
  the example itself writes, and restricted to the routes of the current crawl. Message
  counts must be one or more, must not sum past `MAX_MESSAGES`, and their keys must not
  exceed `MAX_LEN` — a file claiming otherwise is not one this script produced. Since a
  route entry marked `ok` is skipped rather than re-crawled and then printed as an
  observation, accepting such a file would let a hand-edited or planted checkpoint
  suppress a route and put unbounded text of its own in the report.
- `with_server.py` prints the server log path (not its content) on the success path and
  again during shutdown, so a successful run doesn't leave the log location undiscoverable;
  the CLI surface is unchanged.
- SKILL.md Best Practices: readiness/hydration controls must be scoped to their landmark
  or container, since shells often duplicate the same control in a banner and a sidebar.

## [1.3.0] - 2026-07-31

### Changed

- Made server readiness probe the automation host, fail immediately for exited child processes,
  and display bounded sanitized server-log evidence.
- Normalized malformed server commands and launcher failures to fixed path-free
  diagnostics without tracebacks or raw command text.
- Added hydration-aware, checkpointed multi-route console-audit guidance and examples.
- Improved accessibility discovery for composite names, nested-scroll coverage, and SSR evidence.
- The console-audit example closes each route's page before counting its messages, so
  events emitted during teardown are still attributed to that route.
- The untrusted server-log banner states how many lines it shows out of the cap, and
  argument validation errors go to stderr like every other error path.

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
