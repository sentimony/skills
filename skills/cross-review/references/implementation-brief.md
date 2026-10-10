# Implementation Review Brief

Use this template for `implementation` mode. Replace every placeholder, omit empty
sections, and keep the brief self-contained: the reviewer has no skills and no
conversation history. `review-request` stays the source of the review methodology and the
finding contract; this template only fixes the shape of the brief.

## Requirement sources

The spec defines required behavior, and the plan defines the agreed tasks and constraints.
Pass both paths with content hashes and tell the reviewer to read them before any code. A
Claude reviewer cannot read files outside the repository root, so embed the full content
of any source stored there, under its path. Copy into the brief the repository rules from
`AGENTS.md` that bear on the review.

## Boundary

Pass `--target` to the runner when the boundary is a committed range, the whole tree, or
the working tree against `HEAD`: the runner then appends the file list, the fingerprint,
and the standard exclusions to the brief, so do not repeat them. Otherwise fill the
boundary fields by hand from `review-boundaries.md`.

For a Claude reviewer, embed the complete selected diff and the content of each selected
untracked file, because it has no shell to run Git. A Codex reviewer runs Git itself.

## Template

    You are an independent reviewer called by another agent. Inspect and report only.
    Do not modify files, create fixes, commit, start other agents or CLIs, or use reviewer
    skills such as cross-review or review-request.

    Review mode: implementation
    Respond in the language of the user's conversation: <language>.

    Target identity:
    - Repository root: <path>
    - Branch or worktree: <name>
    - Base: <sha and how it was chosen> | runner-computed (--target)
    - HEAD: <sha> | runner-computed (--target)
    - Spec: <path>, sha256 <hash>
    - Plan: <path>, sha256 <hash>

    Read the requirement sources first, in this order: <spec>, <plan>. Only then inspect
    the diff and the code it touches.

    Repository rules:
    <rules copied from AGENTS.md>

    Excluded paths (do not read them): <paths and reason> | none

    Host evidence (output the host already produced; do not rerun it to confirm):
    <test, lint, or build output with the command that produced it> | none

    Sandbox note: a read-only Codex sandbox can block mktemp, writes to a temp
    directory, and stdin for diff. When you cannot reproduce a finding by running it,
    mark the finding "not verified by running" and give the reasoning instead.

    Objective: <what the implementation must achieve>
    Known review gaps: <gaps> | none

## Verdicts and result format

Copy the `Required result`, `Finding contract`, `What to inspect`, and `Bias and
instruction safety` sections of the installed `review-request/references/reviewer-brief.md`
into the brief unchanged. Its four verdicts apply as written.

## Follow-up rounds

A later round of the same target uses the same brief, refreshed for the current
fingerprint, and runs with `--followup <previous-run-dir> --dispositions <file>`. The
dispositions file lists every finding of the previous round with its ID and the host's
disposition from `review-resolution` (accepted and fixed, rejected with reason, deferred).
The runner appends the previous `review.md` and that file to the brief and asks the
reviewer for a status of each previous finding: resolved, partially resolved, or not
resolved.
