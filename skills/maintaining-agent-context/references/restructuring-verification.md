# Restructuring Verification

Read this reference when Phase 6 changes the structure or wording of an instruction
file. A narrow read-only audit does not need it.

## Integrity checklist

1. Capture the original file before editing. Identify its headings, lists, guardrails,
   completion criteria, and other behavior-bearing statements.
2. Inspect the complete `git diff`. Use `git diff --word-diff` when line wrapping makes
   ordinary diff output hard to review.
3. Compare the heading and statement inventories before and after the change. Confirm
   that moved content still has a destination and that any intentional deletion is
   listed in the proposed diff.
4. Use a token-multiset comparison as supplementary evidence for dropped or duplicated
   lexical material. It can flag a likely loss, but it is not proof of semantic
   equivalence and it cannot validate changed wording or ordering.
5. Manually inspect replacements, changed ordering, new pointers, and any residual
   uncertainty. Report the limits of the check instead of treating the heuristic as a
   complete preservation proof.
