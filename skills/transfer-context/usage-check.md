# Usage check

Run `usage --json` and act on its level:

1. `prepare`: save a checkpoint.
2. `refresh`: update the checkpoint.
3. `rotate`: update the checkpoint and suggest a new session with its resume prompt.
4. `ok`: take no action.
5. `unknown`: report that measurement is unavailable, without inventing a number.

Tokens are the only decision mode: the level is the highest threshold that the occupied
token count reaches. The default prepare, refresh and rotate thresholds are 100000, 125000
and 150000 tokens whether or not the window is known. When the window is known, `percent`
in the output is informational and never decides a level. Flags or `config.json` override a
threshold with an integer token count. A percentage such as `50%` stays accepted for older
callers: it is converted to tokens against the known window, and replaced by the default
token level for that threshold when the window is unknown. `threshold_mode` is `tokens`
(older checkpoints may record `absolute` or `percentage`).

Usage accepts `--statusline`, `--transcript <path>`, `--rollout <path>` and threshold
flags `--prepare`, `--refresh`, `--rotate`. All commands accept `--repo`, `--store` and
`--json`.
