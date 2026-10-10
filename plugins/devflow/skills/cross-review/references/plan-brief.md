# Plan Review Brief

Use this template for `plan` mode. Replace every placeholder, omit empty sections, and keep
the brief self-contained: the reviewer has no skills and no conversation history.

## Requirement sources

- With a spec: the spec defines required behavior; the plan must implement it.
- Without a spec (explicit request only): the plan's Goal and Global Constraints are the
  requirements, plus any behavioral specs the host names as behavior to preserve.

Pass paths and content hashes, and name every file the reviewer must read first. A Codex
reviewer reads the sources itself. A Claude reviewer cannot read files outside the
repository root, so embed the full content of any spec, plan, or behavioral spec stored
there, under its path. Copy into the brief the repository rules from `AGENTS.md` that bear on the
plan, because a Claude reviewer does not load project instructions.

## Template

    You are an independent reviewer called by another agent. Inspect and report only.
    Do not modify files, create fixes, commit, start other agents or CLIs, or use reviewer
    skills such as cross-review or review-request.

    Review mode: plan
    Respond in the language of the user's conversation: <language>.

    Target identity:
    - Repository root: <path>
    - Branch or worktree: <name>
    - HEAD: <sha>
    - Working tree: <clean | list of changed paths>
    - Plan: <path>, sha256 <hash>
    - Spec: <path>, sha256 <hash> | none (requirements: plan Goal and Global Constraints)
    - Behavioral specs to preserve: <paths> | none

    Read the requirement sources first, in this order: <spec>, <behavioral specs>, then
    <plan>. Only then inspect the repository code the plan touches.

    Repository rules:
    <rules copied from AGENTS.md>

    Excluded paths (do not read them): <paths and reason> | none

    Objective: <what the plan must achieve>
    Known review gaps: <gaps> | none

## Verdicts

Plan mode uses four verdicts in place of the four in `reviewer-brief.md`:

    Spec compliance: PASS | FINDINGS | UNASSESSED
    Scope compliance: PASS | FINDINGS | UNASSESSED
    Plan soundness: PASS | FINDINGS | UNASSESSED
    Verification adequacy: PASS | FINDINGS | UNASSESSED

Include these review questions in the brief:

- **Spec compliance:** does the plan implement every required behavior and constraint,
  and does any task contradict the spec?
- **Scope compliance:** does the plan stay inside the requested scope, and is every extra
  change justified by a requirement?
- **Plan soundness:** wrong assumptions about the current code, tool versions, or tool
  behavior; missing steps; wrong task order or dependencies; steps that cannot be executed
  as written.
- **Verification adequacy:** does every task have a check that would catch a regression
  of the behavior the spec requires?

## Result format

Copy the `Required result` and `Finding contract` sections of the installed
`review-request/references/reviewer-brief.md` into the brief, with two changes:

1. replace its four verdict lines with the four above;
2. allow `Location or context` to name a plan task and step, or a spec section, in place
   of a code line.

Keep its rule that a result with no findings still states target, coverage, and every
verdict.

## Follow-up rounds

A later round of the same plan uses the same brief with the current plan and spec hashes
and runs with `--followup <previous-run-dir> --dispositions <file>`. The dispositions file
lists every previous finding ID with the host's disposition from `review-resolution`; the
runner appends it and the previous `review.md` and asks for a status of each previous
finding: resolved, partially resolved, or not resolved.
