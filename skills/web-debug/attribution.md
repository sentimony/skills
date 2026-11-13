# Attribution

web-debug is a fork of the webapp-testing skill by Anthropic
(https://github.com/anthropics/skills/tree/main/skills/webapp-testing),
licensed under Apache-2.0, © Anthropic, PBC.

Forked 2026-07-04 by Ihor Orlovskyi.

Modifications relative to upstream (notice per Apache-2.0 §4(b)):

- `scripts/with_server.py`: server output goes to log files instead of unread
  PIPEs (which deadlock the server at ~64KB); process-group cleanup via
  `start_new_session` + `killpg` with SIGTERM → SIGKILL escalation; preflight
  check that ports are free; startup failures include the server log tail;
  documented as POSIX-only.
- Waiting strategy: `domcontentloaded` + short-timeout `wait_for_function`
  with a text-free-page fallback, replacing `networkidle` (which never settles
  with HMR websockets).
- `SKILL.md`: SPDX license id, "Use when..." description, deduplicated
  sections, console + pageerror capture in the main example.
- Examples: portable `/tmp` output paths, `pageerror` handler, concrete-state
  waits instead of fixed timeouts.
- Typo fix: "abslutely" → "absolutely".
