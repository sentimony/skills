# Restructuring Verification

Read this reference in Phase 5, before the first write of any change that moves
content between files or rewords an instruction file; Phase 6 applies its checklist.
A narrow read-only audit does not need it.

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
5. When a new file is assembled from fragments of the old one, extract sections by
   heading, never by line range: line-range extraction clips or duplicates at section
   boundaries, and the multiset check in point 4 is what catches it.
6. Manually inspect replacements, changed ordering, new pointers, and any residual
   uncertainty. Report the limits of the check instead of treating the heuristic as a
   complete preservation proof.
