# Attribution

This skill is an original compact adaptation informed by the MIT-licensed
[obra/superpowers systematic-debugging skill](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging)
and its [root-cause-tracing](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/root-cause-tracing.md),
[defense-in-depth](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/defense-in-depth.md),
and [condition-based-waiting](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/condition-based-waiting.md)
references as inspected at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`.

The adaptation retains the upstream root-cause-first loop, backward tracing, boundary
evidence, condition-based synchronization, defense-in-depth, and architecture escalation.
It adds a symptom contract, reproduction states, evidence labels, raw-data and black-box
control rules, environment comparisons, external-cause discipline, hypothesis ledger,
sample-size awareness, causal-fix budgeting, impact checks, uncertainty-aware exit,
observability cleanup, and explicit composition with neighboring Sentimony skills.

The public text was rewritten for the `debugging` contract. Upstream pressure fixtures,
helper scripts, framework-specific procedures, and persistent state are intentionally not
included. The public skill is distributed under the MIT license. Upstream copyright is
acknowledged in the repository license and this attribution record.
