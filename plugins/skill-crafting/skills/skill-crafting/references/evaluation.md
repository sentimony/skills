# Evaluation Protocol

Use this reference when selecting or recording evidence for a skill. The core skill chooses
the category and tier; this file supplies the mechanics that make the choice reproducible.
The portable contract is owned by this package. Validate `evals.json` with
`skills/skill-crafting/scripts/eval_contract.py` and
`skills/skill-crafting/scripts/validate_evals.py`, execute cases with
`skills/skill-crafting/scripts/run_eval.py`, and aggregate results with
`skills/skill-crafting/scripts/aggregate_results.py`. The repository root
`docs/evals/tools/build_template.py`, `claude_adapter.py`, and `codex_adapter.py` provide
runtime-neutral template and harness adapters. A runner must preserve equivalent evidence
without making the core depend on a particular runtime.

## 1. Evaluation brief

Write one brief before running a case:

| Field | Required content |
| --- | --- |
| Intent | Capability, intended users, and reusable scope |
| Boundary | Input, action, and observable outcome |
| Category | Primary skill category and acceptance boundary |
| Failure | Baseline failure or reason no failure is expected |
| Tier | Light, Standard, or Adversarial with the reason |
| Configuration | Skill version, model, repository, instructions, fixtures, portable runner, and selected root adapter |
| Comparison | No skill, old skill, or an explicit Light exception |

Keep the task prompt realistic. Include enough context for the agent to make the intended
decision, while leaving room for the candidate to show whether it handles the boundary.
Avoid prompts that merely repeat the desired answer.

## 2. Baseline and candidate

For create mode, run the same prompt without the candidate and with the candidate. The
no-skill run establishes what the runtime already does. For improve mode, snapshot the old
skill and compare it with the candidate; a no-skill run can be an additional reference when
it answers a separate question.

Use fresh contexts for paired runs. Freeze the candidate worktree for the entire run package.
Record the exact commit or file fingerprint even when the skill is uncommitted. Preserve the
same model, project instructions, input files, and environment in both configurations. The
runner records manifest identity, including the spec and template hashes, harness, model, and
run configuration. Every case starts from a fresh copy of a read-only template; baseline
removes both `.agents/skills/<skill>` and `.claude/skills/<skill>` before fixture setup.

If an independent context or stable runner is unavailable, use the strongest available
fallback and state the missing independence. A self-report from the author is useful context,
but it is not paired baseline evidence.

## 3. Cases by tier

### Light

Use cases that observe retrieval, application, or structure:

- one realistic happy path;
- one gap, stale fact, or missing-input case;
- positive and near-miss trigger prompts;
- structural checks for frontmatter, links, and supporting-file addresses.

Record why paired execution or adversarial pressure would add little signal. That reason is
part of the evidence, not an implicit omission.

### Standard

Use several realistic cases with different inputs or decisions:

- no-skill or old-skill baseline;
- candidate output and substantive assertions;
- qualitative review for judgment-heavy outcomes;
- fresh-context repeat when variance matters;
- trigger, runtime, and cost observations.

Assertions should inspect the promised boundary. An assertion that a file exists, a heading is
present, or a tool was called is sufficient only when that shape is itself the contract.

### Adversarial

Add cases where the agent has a plausible reason to bypass the guidance. Combine pressures
such as a deadline, sunk work, authority, fatigue, or a request to keep the process short.
Capture the exact bypass or rationalization. Then tie the correction to a form that fits the
failure and rerun the same case.

Treat a new rationalization as a new failure. A pass that happens after repeated retries with
no causal wording or structural change does not establish hardening.

## 4. Assertions and qualitative review

Use a small set of independent assertions per case. Good assertions describe observable
content, decisions, boundaries, or omissions. Mix positive and negative assertions when a
failure mode includes a forbidden shortcut.

For subjective outcomes, keep the qualitative review separate from formal assertions. The
reviewer should record what was inspected, what was convincing, what was weak, and whether
the weakness affects the acceptance boundary. Do not manufacture a numeric score for a
subjective result without a stable rubric.

Every graded run records expectations with exactly these fields:

```json
{
  "text": "The candidate selects the Standard tier for a reusable technique.",
  "passed": true,
  "evidence": "The response names the category, baseline, and Standard checks."
}
```

Evidence must point to the output or transcript observation that supports the result. A
grader's summary without attributable evidence is an open claim.

## 5. Trigger boundary

Keep should-trigger and should-not-trigger cases close to the skill's actual competition:

- should-trigger: create, improve, evaluate, optimize, architecture, or trigger strategy;
- adjacent: instruction maintenance, implementation planning, TDD, code review, and completion
  verification;
- should-not-trigger: one-off use, pure diagnosis, mechanical edits, or runner-only execution.

Near-miss cases should share vocabulary with the skill while requiring the adjacent owner.
Run each case at least twice when the trigger decision is unstable. Report trigger rate and
the tested description, model, and runtime. A runner-only request is not a craft decision and
should not trigger this skill.

## 6. Metrics and interpretation

Useful metrics include expectation pass rate, trigger rate, execution time, token or output
cost, tool calls, errors, and run-to-run variance. Report the mean and spread when repeated
runs exist. Keep per-run pass rate distinct from an expectation-weighted total.

Metrics are complementary evidence. A faster candidate with a trigger regression or a lower
pass rate is not an improvement. A higher pass rate with a large token increase may require a
progressive-disclosure or repeated-work review. A metric with no meaningful baseline signal
is a limitation, not a reason to invent a delta.

## 7. Repeated work and scripts

Inspect raw JSONL transcripts and run artifacts for repeated deterministic work. Bundle a script
only when the operation:

1. recurs across realistic cases;
2. has a stable input and output contract;
3. reduces error or context cost; and
4. can be maintained without a new runtime dependency.

One repeated manual action is a hypothesis. Confirm it in later cases before adding a script.
The package scripts have direct addresses in `SKILL.md`: `eval_contract.py` and
`validate_evals.py` validate the contract, `run_eval.py` owns execution, and
`aggregate_results.py` owns deterministic aggregation. Root adapters
`build_template.py`, `claude_adapter.py`, and `codex_adapter.py` remain outside the core
contract and select the runtime.

## 8. Evidence record

For each case, preserve a compact record with:

- case id and prompt version;
- candidate and comparison identity;
- model, runner, repository instructions, fixtures, and context conditions;
- output paths, raw JSONL transcript paths, and run artifact paths;
- assertion results and qualitative notes;
- timing, tokens, tool calls, errors, timeouts, and variance when available; errors and
  timeouts remain separate from behavioral failures;
- failures, the change made in response, and the recheck result;
- unresolved limitations and their owner.

For a runner with multiple files, keep its documented layout. In particular, use one top-level
directory per iteration, put raw JSONL and run artifacts under each eval and configuration, save
timing as soon as a run completes, and verify that baseline runs did not read candidate files.
The aggregator counts only complete runs with explicit `grading.json`; missing grading yields
no score, never an invented zero. Emit deltas only for matching records within one manifest,
and do not compare scores across harnesses, models, specs, or templates.
