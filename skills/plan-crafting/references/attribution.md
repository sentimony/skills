# Attribution

## Rewrite 2026-11-04

The inherited passages were rewritten in 0.0.1. A word-run comparison with the fork base
(`44c9b2d`) then found no shared run of six or more words, so the package `LICENSE` names one
copyright holder. The text below is the record of origin and describes the earlier fork
(versions before 0.0.1).

Source: obra/superpowers skills/writing-plans/SKILL.md
Source commit: 44c9b2d6e889982ac18c27d05a19fefe335194e1
Source file blob: dd2702b8bab0dbe6b6824d8d00669be44fbb8be7
Adapted on: 2026-07-29

This skill renames upstream `writing-plans` to `plan-crafting`, replaces
upstream-specific plan paths with neutral `docs/plans` paths, and uses unnamespaced
`subagent-driven-development` and `executing-plans` execution handoffs. It replaces
upstream `writing-plans` rather than complementing it, and takes approved designs from
`scope-triage`.

Version 0.0.5 adds a TDD-aware handoff: plans describe the behavior and acceptance evidence,
while `tdd` owns the test-first micro-cycle during task execution.

Version 0.0.17 hands the saved plan to the `scope-check` skill for an HTML preview and a
README index entry.
