# Phase 5 size preflight

Read this in Phase 5 when a Codex budget is in play (the chain is within a margin of the
governing limit, or the proposed edits add text to an always-loaded file). Phase 6 checks
the result; this check runs before the user approves the exact fragments, so approval is
given for numbers that hold.

1. For every proposed fragment compute the UTF-8 byte delta (`len(text.encode())`), added
   minus removed.
2. A changed file feeds every chain that contains it: project the size of each descendant
   chain, not only the one at the starting directory, with all proposed changes applied
   together.
3. Measure rather than estimate: copy only the instruction files (`AGENTS.md`,
   `AGENTS.override.md`, fallback names) into a temporary tree, apply the proposed diffs
   there, and run `scripts/agents_chain_size.py <tmp> --budget <governing limit>`. The
   copy keeps the real tree untouched. If measuring is impossible, label the number
   "estimate".
4. Show before approval: the largest chain before and after, the governing limit and the
   headroom, as measured numbers.
5. If the diff crosses the limit, do not offer the fragment as ready: offer the full
   compensating diff (what moves behind a pointer or into a nested file) or a separate
   decision about the budget.
