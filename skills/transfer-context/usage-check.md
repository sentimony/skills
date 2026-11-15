# Usage check

Run `usage --json` and act on its level:

1. `prepare`: save a checkpoint.
2. `refresh`: update the checkpoint.
3. `rotate`: update the checkpoint and suggest a new session with its resume prompt.
4. `ok`: take no action.
5. `unknown`: report that measurement is unavailable, without inventing a number.

The default prepare, refresh and rotate thresholds are 50%, 62% and 75% of the context
window, or 100000, 125000 and 150000 tokens when the window is unknown; flags or
`config.json` can override them with a percentage or an integer token count.

Usage accepts `--statusline`, `--transcript <path>`, `--rollout <path>` and threshold
flags `--prepare`, `--refresh`, `--rotate`. All commands accept `--repo`, `--store` and
`--json`.
