# Changelog

Repository-level changelog and the only changelog: skills have no changelog of their own.
Versions here are repository git tags (`vX.Y.Z`).

## [1.54.1] - 2026-10-10

### Changed

- `commit-all`: step 1 starts from `git diff --stat` and reads full diffs only for code,
  configuration, and documentation, not large generated or data files. Step 4 excludes
  local tooling (`.envrc`, generated output) without stopping and names it. Step 5
  checks the summary length before committing and follows the repository's rules on
  what a commit message may quote, describing restricted changes by category and count.
  Amend is offered only to fix the previous commit, never for a new run with new work.
  Mechanics show both paths for a staged rename in a partial commit.
- `maintaining-agent-context`: a request addressed to a `CLAUDE.md` shim routes the
  work to `AGENTS.md` and says so. The assessment criteria tell a live symlink into a
  clone from an installed snapshot and a registry install. The Codex reference orders
  the config layers for `project_doc_max_bytes` (user, profile, trusted project, `-c`)
  and notes that Codex reads no `.codex/config.local.toml`.

### Removed

- The Release column from the README skill table: skills are not versioned individually,
  and the column only repeated the latest repository tag.

## [1.54.0] - 2026-10-09

### Added

- `commit-all`: `argument-hint: "[dry-run]"`, so the Claude Code `/` menu shows the
  documented argument.
- `skill-crafting`: create mode adds an `argument-hint` only for arguments the skill
  body documents.
- AGENTS.md records the `argument-hint` convention: a Claude Code field outside the Agent
  Skills specification, set only for documented slash arguments, never invented for a
  skill that runs from context alone.
- CI checks that an `argument-hint`, when present, is a non-empty single line with
  balanced `[]` and `<>`.

### Changed

- `commit-all` no longer sets `disable-model-invocation: true`: its description and
  security model now cover a request in words ("commit everything") as well as
  `/commit-all`, still without a commit message from the user.
- Skills are no longer versioned individually: repository releases are the only
  versions. `metadata.version` and `metadata.author` are removed from every SKILL.md,
  the README skill table drops
  its Skill Version column, and CI rejects the two fields instead of requiring a semver
  `metadata.version`. skills.sh may stop showing a per-skill version.
- `frontend-crafting`: a persisted review names the skill's release or commit instead of
  its version.

### Removed

- `license` from every SKILL.md frontmatter, and AGENTS.md no longer requires the
  field. The skill instructions are unchanged.
- Per-skill `CHANGELOG.md` files. This changelog is the only one; a skill's earlier
  history stays in git.
- Per-skill `LICENSE` files. The repository-level `LICENSE` (MIT) now carries Jesse
  Vincent's notice for the skills adapted from obra/superpowers, and `LICENSE-APACHE`
  covers `frontend-crafting` and `web-debug` with their copyright holders listed in
  `LICENSE`. Copies installed from a single skill directory no longer include a license
  file.
- `agents/openai.yaml` from every skill, with the AGENTS.md convention and the CI check
  for it. Codex now shows each skill under its frontmatter `name` and `description`.
- The `metadata` block from every SKILL.md frontmatter, and the CI check that required
  `metadata.internal: false`. A skill without the field stays visible to `npx skills`.

## [1.53.1] - 2026-10-05

### Fixed

- `maintaining-agent-context` 1.4.1: the Codex loading reference no longer counts the
  global `AGENTS.md` against `project_doc_max_bytes` and describes the boundary file as
  truncated mid-text with only a log warning, as the Codex source implements it. It also
  covers untrusted projects, a `config.toml` that does not parse, and the moved
  documentation URL.

## [1.53.0] - 2026-10-05

### Changed

- `maintaining-agent-context` 1.4.0: the audit reads the effective Codex
  `project_doc_max_bytes` and its source from the user-level and project `config.toml`
  instead of assuming the default. For a shared repository the governing limit is the
  lower of the default and the project config; a chain that fits only a larger local
  limit is reported as a finding.

## [1.52.0] - 2026-10-05

### Changed

- `dashfix` 2.1.0: the audit no longer scans commit messages in git history, since fixing
  them needs a rewrite the skill does not offer; the report closes with an offer to install
  the commit-msg hook in every audited repository that lacks it. The install command
  resolves the hooks directory with `git rev-parse --git-path hooks`, which covers
  worktrees and `core.hooksPath`.
- `verification-gate` 1.0.5: the `not applicable` status uses a plain hyphen
  (`- not applicable`) instead of an em dash, matching `inline-plan-dev` and
  `subagent-plan-dev`.
- `cross-review` 1.1.2: run report token counts carry thousands separators
  (`282,797 in`).

## [1.51.1] - 2026-10-05

### Fixed

- `cross-review` 1.1.1: run report formatted as multi-line output (Reviewer, Tokens, Cost,
  Session) without redundant skills line; documented requirement for opposite CLI and no
  same-CLI fallback.

## [1.51.0] - 2026-10-05

### Added

- `cross-review` 1.1.0: a run report with the reviewer's model, effort, skills, token
  counts, and approximate cost in `usage.json` and a one-line runner summary, with a session
  total after resume.
- `plan-crafting` 1.5.0: the execution choice offers a third option, another `cross-review`
  of the corrected plan against the spec, when the plan references a spec and
  `cross-review` is installed.

## [1.50.1] - 2026-10-04

### Changed

- `dashfix` 2.0.1: a dash that hides a reason, result, contrast, or condition routes to
  the `hidden logic` row and falls back to keeping ` - ` instead of a semicolon or period;
  `linked clauses` no longer claims such sentences.
- `tdd` 1.0.7: the title uses a colon in place of the typographic dash.
- Typographic dashes in English text are replaced with plain punctuation across the
  repository changelog and the `echarts`, `scope-triage`, `typescript`, `vitest` and
  `web-debug` changelogs, released sections included. Wording and facts are unchanged.

## [1.50.0] - 2026-10-04

### Changed

- `dashfix` 2.0.0: the plain hyphen is the only dash in every language. A spaced dash
  becomes a spaced hyphen, the relation table is optional better punctuation, a new
  `data` verdict covers characters that code reads, the audit reports counts instead of a
  score, and the `commit-msg` hook no longer skips Cyrillic messages.
- `prose-crafting` 1.0.2: the Ukrainian reference follows `dashfix` and no longer forbids
  replacing a Ukrainian dash with a hyphen.

## [1.49.0] - 2026-10-04

### Added

- `cross-review` 1.0.0: hands an implementation plan or a finished implementation to the
  opposite agent CLI (Codex for Claude Code, Claude Code for Codex) for an independent
  read-only review, with a self-contained brief, secret hygiene before the handoff, a
  target fingerprint, and the result passed to `review-resolution`. The stdlib runner
  `scripts/cross_review.py` carries a `CROSS_REVIEW_DEPTH` loop guard, fixed read-only
  argv for both CLIs on run and resume, the reviewed repository forced untrusted for the
  Codex reviewer so its project `.codex/config.toml` is not loaded, private run
  directories under the system temporary directory, and distinct exit codes; tests live in
  `scripts/test_cross_review.py`.
- `.claude-plugin/plugin.json` lists `./skills/cross-review`.

### Changed

- `plan-crafting` 1.4.0: `Execution Handoff` runs `cross-review` in `plan` mode after the
  plan is saved and before the execution choice, when the plan references a spec and the
  skill is installed. Without a spec the step is skipped; an unavailable reviewer or a
  failed, empty, or incomplete run is reported in one line and the normal handoff
  continues.
- `inline-plan-dev` 1.1.0: an execution record in the plan file keeps the resolved
  `BASE_SHA`, the repository root, and the initial dirty paths for resume. The final scope
  and diff review runs through `cross-review` in `implementation` mode when it is
  available and through `review-request` otherwise, after a deterministic footprint check
  against `BASE_SHA`.
- `subagent-plan-dev` 1.1.0: `.sdd/<plan-id>/state.json` records `base_sha`, `repo_root`,
  and `initial_dirty_paths` for resume. The whole-branch review runs through
  `cross-review` in `implementation` mode when it is available and through
  `review-request` otherwise; per-task review gates are unchanged.
- The Security Model of each of the three skills names what it may send through
  `cross-review` to the other agent CLI and its vendor API.

## [1.48.3] - 2026-10-01

### Changed

- `.gitignore` ignores `.env/`, where a clone keeps its local `GH_ACC` for `gh-switch`,
  so the file cannot be committed by accident.

## [1.48.2] - 2026-10-01

### Fixed

- `frontend-crafting` 1.3.4, `inline-plan-dev` 1.0.6 and `subagent-plan-dev` 1.0.6:
  the attribution references link the maintainer-repository research files under
  their new `YYYYMMDD-HHMM-` names.

## [1.48.1] - 2026-10-01

### Changed

- **Breaking for plugin users:** the marketplace is renamed from `sentimarket` to
  `sentimony` and its plugin from `sentiplug` to `skills`, in both
  `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, so the install command
  reads `skills@sentimony`. Remove the `sentimarket` marketplace, add `sentimony/skills`
  again, and install `skills@sentimony` (`claude plugin install` in Claude Code,
  `codex plugin add` in Codex). The README now documents the Codex install, which
  reads the same `.claude-plugin/marketplace.json`.

## [1.48.0] - 2026-10-01

### Added

- Experimental user-invoked skills `scope-check` 1.0.0 and `webapp-debugger` 1.0.0: each
  sets `disable-model-invocation: true` and hands the request to `scope-triage` and
  `debugging` respectively.

### Changed

- **Breaking for Claude Code plugin users:** the marketplace is renamed from
  `sentimony-agent-skills` to `sentimarket` and exposes one plugin, `sentiplug`, described
  by the new `.claude-plugin/plugin.json`, in place of the twelve group plugins
  (`design-planning`, `debugging`, and the rest). Uninstall the group plugins, remove the
  old marketplace, add `sentimony/skills` again, and install `sentiplug@sentimarket`.
- `.codex-plugin/plugin.json` packages the same skills as a Codex plugin.
- `skills.sh.json` is removed, so the skills.sh page lists the skills as one flat list
  instead of titled groups.
- Every skill gets a patch release (`branch-finish` 1.0.6, `commit-all` 1.1.3, `dashfix`
  1.3.1, `debugging` 1.0.11, `echarts` 1.2.3, `frontend-crafting` 1.3.3, `gh-switch`
  1.0.1, `git-worktree-isolation` 1.2.2, `inline-plan-dev` 1.0.5,
  `maintaining-agent-context` 1.3.3, `negafix` 1.4.1, `parallel-agents` 1.0.5,
  `plan-crafting` 1.3.4, `prose-crafting` 1.0.1, `review-request` 1.0.5,
  `review-resolution` 1.0.4, `scope-triage` 1.0.7, `secret-hygiene` 1.0.1,
  `skill-crafting` 1.1.3, `subagent-plan-dev` 1.0.5, `tdd` 1.0.6, `typescript` 1.4.3,
  `verification-gate` 1.0.4, `vitest` 1.3.3, `web-debug` 1.3.6) that adds
  `agents/openai.yaml` with Codex display metadata and `metadata.internal: false`. The
  skill instructions are unchanged.
- CI checks that `plugin.json` lists every skill and carries the newest release version,
  that each skill has a valid `agents/openai.yaml`, and that `metadata.internal` is false.

## [1.47.0] - 2026-10-01

### Added

- `gh-switch` 1.0.0: before project-scoped gh commands on github.com, switches to the
  already logged-in account named by `GH_ACC` in the project's `.env/.env` and reports
  the switch in one line. Joins the `Git Workflow` group, whose description now covers
  GitHub CLI operations.

## [1.46.0] - 2026-09-30

### Changed

- `web-debug` 1.3.5 restructures its Security Model into user-controlled inputs,
  untrusted inputs, collected content as data, and capabilities, to address the
  skills.sh Snyk W011 finding; the workflow is unchanged.
- `AGENTS.md` retires the `negafix` W011 baseline row after the skills.sh scan of
  2026-09-28, later than the `v1.44.0` merge, reported no issues, and marks the
  `web-debug` row for confirmation against the first scan after this release.

## [1.45.0] - 2026-09-28

### Added

- `secret-hygiene` 1.0.0: an advisory procedure that keeps credential values out of agent
  transcripts, tool output, logs, commits, and PR texts while the agent still uses them.
  New `Security` group in `skills.sh.json` and `security` plugin in `marketplace.json`.

## [1.44.0] - 2026-09-27

### Changed

- `negafix` 1.4.0 gives `justified contrast` only when someone voiced the rejected
  position and the reason names where, reversing the 1.3.0 ruling that let a factual
  constraint in the negated half shield a two-half contrast from `violation` on its own.

## [1.43.0] - 2026-09-26

### Fixed

- `skill-crafting` 1.1.2 hardens `scripts/run_eval.py`: the adapter receives an environment
  allowlist plus the runner-set `EVAL_*` variables (other variables via `--pass-env NAME`,
  rejected with exit code 2 before the workspace exists when malformed or runner-set;
  forwarded names recorded in `run.json`), `EVAL_TIMEOUT` sits below the runner's own
  cutoff, and an `answer_path` outside the sandbox or run directory is an error. The
  Security Model now states that the eval spec, fixtures, template, and adapter are
  operator-trusted and that the temporary sandbox is not a security boundary.
- `AGENTS.md` records the skills.sh Snyk W011 findings on `negafix` and `web-debug` as
  baseline: both skills exist to read third-party text and already treat it as untrusted.

## [1.42.0] - 2026-09-26

### Added

- `prose-crafting` 1.0.0 edits prose for its reader, purpose, context, and author's voice
  while preserving meaning, with rewrite, audit, and explain modes, a pattern catalog
  under stable semantic IDs, and English and Ukrainian guidance. Adapted in part from
  `blader/humanizer`; dash policy stays with `dashfix` and negative parallelism with
  `negafix`. The `Writing Style` group and `writing-style` plugin descriptions now cover
  prose editing as well as bans.

## [1.41.0] - 2026-09-26

### Changed

- `dashfix` 1.3.0 chooses the replacement for a banned dash by the relation it hides,
  splits a sentence overloaded with dashes before classifying each dash, leaves an
  awkward but grammatical comma pair to prose editing, and checks that a fix which adds,
  moves, or removes a word keeps every fact, attribution, qualifier, number, date, and
  relation.
  Detection, verdicts, and the score are unchanged.

## [1.40.0] - 2026-09-26

### Added

- `negafix` 1.3.0 catches negative parallelism split across two sentences, judges each
  candidate by an information-gain test and a claim-preservation check, and watches
  three adjacent shapes (`rather than`, unsupported objections, clipped negative tails)
  as exploratory signals outside the score. Adapted from `blader/humanizer` patterns 1
  and 5; the skill stays a narrow negative-framing checker.

## [1.39.0] - 2026-09-16

### Fixed

- Deterministic defects found by inspection: `git-worktree-isolation` 1.2.1 canonicalizes
  `workspace_root` for library callers and drops a dead `rev-parse` call; `review-request`
  1.0.4 uses one `UNASSESSED` literal across all four verdicts; `branch-finish` 1.0.5 moves
  `CLEANUP INCOMPLETE` out of the outcome labels into its own cleanup status; `commit-all`
  1.1.2 resolves the repository's actual default branch instead of assuming `main`/`master`.
- `skill-crafting` 1.1.1 requires at least one should-not-trigger case in prose and points
  to its own evaluation reference. The concept existed only as a table cell that required
  nothing, and 4 of 4 answers failed that expectation in both arms of eval-4.

### Changed

- Narrowed trigger boundaries so descriptions claim no more than the bodies deliver:
  `dashfix` 1.2.3 and `negafix` 1.2.3 no longer trigger on prose "anywhere in a project",
  and `negafix` states that ordinary factual negation is out of scope; `tdd` 1.0.5 covers
  behavior changes and refactors with a checkable contract rather than "any" change;
  `maintaining-agent-context` 1.3.2 owns instruction architecture rather than any SKILL.md
  edit.
- Named missing composition boundaries: `vitest` 1.3.2 and `tdd` 1.0.5 against `tdd` and
  `verification-gate` respectively, `echarts` 1.2.2 and `frontend-crafting` 1.3.2 against
  `debugging`. `typescript` 1.4.2 and `vitest` 1.3.2 mark Python optional, `echarts` 1.2.2
  takes install commands from the project's package manager, `parallel-agents` 1.0.4 drops
  a hardcoded agent count, `scope-triage` 1.0.6 checks compatibility before asking the user,
  and `web-debug` 1.3.4 aligns its heading and gates the Playwright install.

### Added

- `inline-plan-dev` 1.0.4 and `subagent-plan-dev` 1.0.4 report plan progress as a counted
  status line at each task boundary, carrying no percentage and depending on no
  vendor-specific output channel.
- `debugging` 1.0.10 records symptom provenance as `PRE-EXISTING`, `INTRODUCED` or `UNKNOWN`
  in step 0.

## [1.38.0] - 2026-09-15

### Added

- `skill-crafting` 1.1.0: package-owned portable eval contract, validator, fresh-sandbox
  runner, and deterministic aggregator, with runtime adapters and isolated artifacts.
  Default installation is `skill-creator`-free; trigger-boundary evidence confirms sole
  ownership in the tested installation. The behavioral result is PARTIAL because of
  timeout and runtime variance, with no cross-harness comparison.

## [1.37.0] - 2026-09-14

### Added

- `skill-crafting` 1.0.0: methodology for creating, improving, evaluating, and optimizing
  reusable agent skills with category, risk, trigger, and evidence boundaries.

## [1.36.0] - 2026-09-14

### Changed

- `worktree-isolation` is now `git-worktree-isolation` 1.2.0, naming the mechanism the workflow
  reaches for most often. The selection hierarchy is untouched: reusing existing safe isolation
  still comes first, a harness-native workspace second, a manual Git worktree third, and safe
  work in place stays a legitimate outcome. Eight skills that reference it follow the rename:
  `branch-finish` 1.0.4, `debugging` 1.0.9, `inline-plan-dev` 1.0.3, `parallel-agents` 1.0.3,
  `review-request` 1.0.3, `review-resolution` 1.0.3, `subagent-plan-dev` 1.0.3 and
  `verification-gate` 1.0.3. Frozen changelog entries keep the previous names.

## [1.35.0] - 2026-09-14

### Changed

- `workspace-isolation` is now `worktree-isolation` 1.1.0. The public name changes and the old
  one disappears from the registry; the skill keeps its full scope, and a Git worktree stays one
  option among existing isolated checkouts, harness-native workspaces, containers and safe work
  in place. Eight skills that reference it follow the rename: `branch-finish` 1.0.3, `debugging`
  1.0.8, `inline-plan-dev` 1.0.2, `parallel-agents` 1.0.2, `review-request` 1.0.2,
  `review-resolution` 1.0.2, `subagent-plan-dev` 1.0.2 and `verification-gate` 1.0.2. Frozen
  changelog entries keep the old name, which is correct for a historical record.
- `scope-triage` 1.0.5 and `plan-crafting` 1.3.3: specs and plans are saved under
  `YYYYMMDD-HHMM-<topic>.md`, so several documents written on one day order by creation time.
  The `-design` suffix `scope-triage` used is dropped, since the timestamp already distinguishes
  them.

## [1.34.3] - 2026-09-14

### Changed

- Every skill now documents a `## Security Model` section with the same four components: which
  inputs are user-controlled, which are untrusted, that tool output is data rather than
  instructions, and whether the skill runs shell commands or network calls. Five skills gained
  a section, nine had theirs renamed or gathered from an existing rule, and five had missing
  components filled in. `web-debug` and `scope-triage` already satisfied the contract and are
  unchanged.
- `AGENTS.md`: the skills.sh audit guidance now states all four components a Security Model
  section must carry, and the Snyk baseline row for `review-resolution` points at its new line
  numbers.

## [1.34.2] - 2026-09-14

### Changed

- `plan-crafting` 1.3.1 and `tdd` 1.0.3: add the fork maintainer to the LICENSE copyright
  notice, the only two forked skills that were missing it.

## [1.34.1] - 2026-09-13

### Changed

- `branch-finish` 1.0.1: report `Verification: <verdict>` instead of a literal `PASS` in the
  two templates whose outcome does not require a passing verdict, and state that `MERGE_BASE`
  resolves a base only when exactly one other branch is a candidate.

## [1.34.0] - 2026-09-13

### Added

- `.sdd/` to the repository `.gitignore`. This repository is itself a plausible
  `subagent-plan-dev` target, so its state directory would otherwise appear as untracked
  noise in a release diff.

### Changed

- Consolidated the registry groupings from sixteen groups to ten in `skills.sh.json` and
  `.claude-plugin/marketplace.json`, replacing the single-skill groups the workflow chain
  created with `Execution`, `Debugging`, `Review & Verification`, `Completion & Workspace`,
  `Frontend`, and `TypeScript & Testing`. Every published skill appears exactly once. Plugin
  `name` values are install identity, so each merged group keeps an existing name and only
  its description and skill list change.
- `README.md`: added a `Development Workflow` section naming `scope-triage` as the entry
  point, with the main development flow and the failure path as Mermaid diagrams, the four
  composability properties, and the list of conditional capabilities. The skill table is
  now grouped to match the registries, and the install block moved above it.
- `scope-triage` 1.0.4: name `tdd` and `debugging` as skill references in Route A instead of
  the bare words, so the router's handoff into implementation is unambiguous.

## [1.33.1] - 2026-09-13

### Changed

- `debugging` 1.0.6: route a review finding with an unclear cause to `review-resolution`
  instead of the upstream `receiving-code-review` name.
- `tdd` 1.0.2: route root-cause investigation to `debugging` instead of the upstream
  `systematic-debugging` name, in three places.

## [1.33.0] - 2026-09-13

### Added

- `branch-finish` 1.0.0: decide what happens to verified work and execute that decision
  safely, with read-only environment detection, six-level base-branch resolution by evidence
  precedence, four environment-filtered finish options, merge-conflict classification,
  idempotent resumption, separate gates for workspace removal and branch deletion, a
  seven-label outcome vocabulary, and a read-only state inspector with its test.

### Changed

- `debugging` 1.0.5: route review acquisition and branch completion to `review-request` and
  `branch-finish` instead of the upstream `requesting-code-review` and
  `finishing-a-development-branch` names.

## [1.32.0] - 2026-09-13

### Added

- `inline-plan-dev` 1.0.0: execute an existing implementation plan inline in the current
  session, with plan-versus-reality reconciliation, a two-value blocker taxonomy,
  proportional verification depth, a deterministic scope check, durable resume in the plan
  file, and a fixed six-row final verification matrix.
- `subagent-plan-dev` 1.0.0: execute an existing implementation plan through scoped
  subagents under a controller, with a pre-flight pass, an explicit dependency model,
  per-task risk classification, semantic harness capability detection, plan-scoped durable
  state in `.sdd/`, controller-owned verification before acceptance, a deterministic scope
  check, three-value review verdicts with conditional domain review, four stagnation
  signals feeding a four-step escalation ladder, and the same fixed six-row final
  verification matrix.
- New `Plan Execution` registry group in `skills.sh.json` and the mirrored marketplace
  catalog, carrying both execution modes.

### Changed

- `plan-crafting` 1.2.0 to 1.3.0: route plan execution to `inline-plan-dev` and
  `subagent-plan-dev` in the plan header note and the execution handoff, replacing the
  upstream `executing-plans` and `subagent-driven-development` names, and present the two
  execution modes as an equal choice.
- `tdd` 1.0.0 to 1.0.1: route task ordering, execution mode, task ledger, and subagent
  orchestration to `inline-plan-dev` and `subagent-plan-dev`.
- `debugging` 1.0.3 to 1.0.4: route plan execution failures to `inline-plan-dev` and
  `subagent-plan-dev`, and attribute execution state to the execution mode rather than to
  `.sdd/`.
- `AGENTS.md`: rebuild the known Snyk baseline findings table from a full local pre-flight.
  It listed two skills and one scan date while the scanner reports the same attribution
  redaction finding in seven, including `echarts`, which the previous text called clean. A
  separate third-party content exposure finding in `review-resolution` is now tracked too.

## [1.31.1] - 2026-09-13

### Fixed

- README skills table: the `debugging` row still showed 1.0.2, because the bump to 1.0.3 in
  `v1.31.0` updated the skill's `metadata.version` and CHANGELOG but not the table.

## [1.31.0] - 2026-09-13

### Added

- `parallel-agents` 1.0.0: prove work units independent, map mutable state, dispatch one
  bounded parallel wave, and reconcile results before integration.
- New `Orchestration` registry group in `skills.sh.json` and the mirrored marketplace catalog.

### Changed

- `debugging` 1.0.2 to 1.0.3: route independent evidence streams to `parallel-agents`, which
  owns independence assessment, isolation topology, and bounded dispatch.

## [1.30.0] - 2026-09-13

### Added

- `workspace-isolation` 1.0.0: safe workspace selection, detection, and creation with explicit
  ownership, baseline, and handoff.
- New `Workspace` registry group in `skills.sh.json` and the mirrored marketplace catalog.

### Changed

- `debugging` 1.0.1 to 1.0.2: route safe workspace setup to `workspace-isolation`, which owns
  isolation and records the workspace that runs and inspects the code.

## [1.29.0] - 2026-09-12

### Added

- `verification-gate` 1.0.0: a completion gate that turns proposed completion claims into
  evidence-backed verdicts against the current tree.
- New `Verification` registry group in `skills.sh.json` and the mirrored marketplace catalog.

### Changed

- `debugging` 1.0.0 to 1.0.1: route final verification to `verification-gate`, which owns
  the authoritative completion matrix and requires fresh evidence after a fix.

## [1.28.0] - 2026-09-12

### Added

- `review-resolution` 1.0.0: a compact workflow for validating, classifying, and resolving
  code-review findings with finding-level evidence, explicit dispositions, bounded loops, and
  proportional re-review.
- Added `review-resolution` to the mirrored `Code Review` registry and marketplace group.

## [1.27.0] - 2026-09-12

### Added

- `review-request` 1.0.0: a compact workflow for preparing and dispatching independent
  code review against explicit requirements, an exact implementation boundary, and the
  actual committed or working-tree diff.
- New `Code Review` registry group in `skills.sh.json` and the mirrored marketplace catalog.

## [1.26.0] - 2026-09-11

### Added

- `debugging` 1.0.0: canonical root-cause-first methodology for bugs, regressions, failing
  tests, build and integration failures, flaky behavior, performance anomalies, and other
  unexpected technical behavior.
- New `Debugging` registry group in `skills.sh.json` and the mirrored marketplace catalog.

### Changed

- `web-debug` 1.3.2 to 1.3.3: added a reciprocal boundary with `debugging` so browser/runtime
  observation and root-cause methodology compose without competing responsibilities.

## [1.25.0] - 2026-09-11

### Added

- `tdd` 1.0.0: a framework-neutral behavior-first TDD workflow with valid RED, acceptance
  boundaries, risk-based evidence, and explicit test-quality gates.

### Changed

- `plan-crafting` 1.1.2 to 1.2.0: behavior-changing tasks now hand their test-first
  micro-cycle to `tdd` and avoid test-after task wording.
- Testing registries now expose `tdd`.

## [1.24.0] - 2026-09-08

### Changed
- `maintaining-agent-context` 1.2.0 to 1.3.0 - added a directory-scoped split as the
  remedy for an over-budget root, the Claude Code / Codex split trade-off, a
  version-control check for files the audit creates, an honest-limit rule and an
  earlier trigger for the restructuring checklist.

## [1.23.0] - 2026-09-08

### Changed
- `frontend-crafting` 1.2.1 to 1.3.0 - added a composite Step 0 mode for a single surface, a
  `pass`/`fail`/`unavailable` status for static-only checks, a rule that `unavailable` is never a
  severity, a first-audit clause, a baseline and finding boundary, an absence-check validation
  rule, and a persisted-review header contract.

## [1.22.0] - 2026-09-07

### Changed
- `echarts` 1.1.3 to 1.2.0 - added applicability and repeat-audit routing, DOM proxy evidence, verified SVG dataZoom slider geometry, render-completion and theme-proof criteria, tooltip grid sweeps, and explicit unavailable and time-boxed audit conventions.

## [1.21.0] - 2026-09-07

### Changed
- `vitest` 1.2.1 to 1.3.0 - expanded first and repeat audits with stdout, structural
  assertion, threshold headroom, end-to-end gate, runtime evidence, and measurement
  contracts; qualified Vitest 5 isolation advice; added keyed Nuxt data teardown; and
  tightened Nuxt and `cross-env` guidance.

## [1.20.0] - 2026-09-07

### Added
- `typescript` 1.4.0: Nuxt program ownership, solution-config and traced-number guidance, audit recipes for diagnostic deduplication, uncovered tests, companion programs, non-null assertions, and repeat audits.

## [1.19.1] - 2026-09-02

### Changed
- `frontend-crafting` 1.2.0 to 1.2.1 - the quality gate names an unset threshold as an assumption
  instead of a silent number, and polish keeps a change to the side or region the request named.

## [1.19.0] - 2026-09-02

Frontend work now declares its workflow and surface mode in a fixed line before any file is
touched, and reviews build on the audits a repository already has.

### Changed
- `frontend-crafting` 1.1.0 to 1.2.0 - a numbered Step 0 fixes the announcement format and fires
  before the first file write and before any finding or verdict, so a review that writes nothing
  is still covered, repository-wide announcements name the dominant modes present, reviews
  locate prior audits and report their findings as resolved or still open while inheriting
  established measurements by reference, a finding is defined as an itemised entry with user
  impact required at every severity, and external CDN resources on a plain HTML and CSS brief
  must be named among the approximations

## [1.18.0] - 2026-09-01

Repository-wide frontend reviews now make their coverage inspectable and verify search-driven
findings before publication.

### Changed
- `frontend-crafting` 1.0.0 to 1.1.0 - repository reviews group multiple surfaces by mode and
  declare scope, sampling, and exclusions; clean checks become quantitative baseline evidence;
  every finding is traced to primary code, delegated counts are remeasured, and the quality gate
  detects unintended mixed-language interfaces and missing element-level `lang` attributes

## [1.17.0] - 2026-09-01

A new skill for frontend design work, distilled from four upstream skills into an
original router-and-references architecture.

### Added
- `frontend-crafting` 1.0.0 - create, redesign, review, and polish user interfaces
  through mode detection (Persuade/Operate/Read/Experience), a subject-derived
  design read stated before code, severity-graded review findings, and a
  verifiable technical quality gate; defers browser-driving verification to
  `web-debug`.

## [1.16.0] - 2026-08-30

An explicit `/commit-all` now commits in one shot: the file list and message become a
progress update instead of a confirmation gate.

### Changed
- `commit-all` 1.0.1 to 1.1.0 - pre-existing tracked changes and a missing session
  snapshot no longer pause the run; the remaining stop conditions are the default
  branch, suspicious untracked files, and unsafe path arguments, with `dry-run` as the
  guaranteed stop before committing.

## [1.15.0] - 2026-08-29

The agent-context audit measures sizes in the right unit from the start, keeps
safety constraints ahead of the pointers they guard, and holds its confirmation gate
against "apply immediately" invocations.

### Changed
- `maintaining-agent-context` 1.1.0 to 1.2.0 - measurement recipe and edit-scope
  rule for cross-repository symlinks in Phase 1, inline safety constraints next to
  pointers, out-of-scope findings and "structure already correct" in the report,
  confirmation gate kept under "apply immediately", post-edit limit checks, and
  criteria for redundant commands and import shims.

## [1.14.0] - 2026-08-25

The agent-context audit workflow now reports verification boundaries honestly and
protects instruction content during restructuring.

### Changed
- `maintaining-agent-context` 1.0.0 to 1.1.0 - risk-based verification statuses,
  explicit measurement units, a read-only shell boundary, Phase 4 coverage reporting,
  and approved formatting trade-offs with before-and-after integrity checks.

## [1.13.0] - 2026-08-24

A new skill treats a repository's agent instruction files as one architecture and
keeps it aligned with the codebase.

### Added
- `maintaining-agent-context` 1.0.0 - audit, restructure, and maintain agent
  instruction files (AGENTS.md, CLAUDE.md variants, `.claude/rules/`, skills, linked
  agent docs) for Claude Code and Codex: read-only discovery and verification, a
  quality report before any edit, diff-style proposals with user confirmation,
  per-file-type assessment criteria instead of a universal rubric
- New "Agent Context" group in `skills.sh.json` and the mirrored `agent-context`
  plugin in the marketplace catalog for `maintaining-agent-context`

## [1.12.1] - 2026-08-21

Every session pays for skill descriptions in context; this batch trims the five most
expensive ones without changing any workflow.

### Changed
- `commit-all` 1.0.1, `dashfix` 1.2.1, `negafix` 1.2.1, `echarts` 1.1.3,
  `typescript` 1.3.3 - shorter frontmatter descriptions; workflow details the
  descriptions used to carry now live in the skill bodies.

## [1.12.0] - 2026-08-20

The two writing-style skills answer their 2026-08-19 field feedback: regex matches are
candidates until a verdict reads the sentence, and a single new file gets a pre-handoff
check that skips the project score. A new `commit-all` skill gathers the working tree
into one user-invoked commit.

### Added
- `commit-all` 1.0.0 - gather the working tree into one commit on the current branch
  with a generated English message; user-invoked only (`disable-model-invocation:
  true`), stops on `main`/`master`, previews mixed trees, supports `dry-run`, never
  pushes, never bypasses hooks, never rewrites history
- New "Git Workflow" group in `skills.sh.json` and the mirrored `git-workflow` plugin
  in the marketplace catalog for `commit-all`

### Changed
- `dashfix` 1.1.0 -> 1.2.0 - "Single-file check" inventories one file and reports
  candidate and replace counts separately; mixed-language Markdown classifies prose
  blocks, quotations, code fences, and diagnostics per block instead of one file-level
  verdict; a `replace` row's reason names the fix
- `negafix` 1.1.0 -> 1.2.0 - "Single-file check" verdicts every candidate from the full
  sentence before any rewrite; an exploratory `не A, а B` pattern for Ukrainian prose
  runs only on demand with a mandatory manual verdict; the counting-pass total counts
  candidates rather than violations

## [1.11.0] - 2026-08-11

The two writing-style skills answer their first field feedback: the dash ban learns
about language, both audits reach commit messages, both scores are normalized by project
size, and both skills ship a git hook.

### Added
- `dashfix` 1.0.0 -> 1.1.0 - "Language scope" makes the ban a rule of English typography
  that binds per file. In Ukrainian, Russian, Polish, and German the em dash is
  orthography, so the skill checks its form (em vs en, spacing, hyphen inside compounds)
  and a correct dash earns a fifth `justified` category. New `scripts/commit-msg` hook
  rejects a banned dash in a commit message and skips a message written in Cyrillic,
  with both limits of that heuristic documented (a Cyrillic name in an English message
  is skipped too, and Latin-script Polish and German cannot be detected at all), a
  `PreToolUse` snippet blocks the same mistake inside an agent session using perl alone
  (a `jq` pipeline exits 0 on a machine without `jq` and passes the commit through in
  silence), and an "Enforcement" section states that write mode does not survive a
  context compaction
- `negafix` 1.0.0 -> 1.1.0 - the same enforcement section with a warn-only
  `scripts/commit-msg` hook, chosen because the detection patterns overmatch by design,
  plus a note on how much noisier the Ukrainian patterns are than the English ones
- Both skills gain a commit-message inventory: `git log --grep` selects the commits,
  including merge commits and commits whose only hit sits in the body, and an inner `rg`
  pass prints the matching lines as `<hash>:<line>:<snippet>`. The history table reads
  like the working-tree one and stays out of the score. Both skills also let write mode
  inherit the quotation verdict, so reporting a violation stops breaking the rule
- Both skills add a counting pass (`rg --count-matches`) next to the line-oriented
  inventory, since `rg -n` prints a line holding two matches once. The occurrence total
  comes from the counting pass, a catalog row states how many occurrences its line
  carries, and a line whose occurrences disagree on the verdict splits into rows keyed
  `<location>#<n>`
- `negafix` sets its shared `PATTERN` once at the head of Step 1 and guards every later
  block with `: "${PATTERN:?...}"`, so a block run on its own aborts instead of handing
  `rg` an empty pattern that matches every line
- `negafix` adds `not a ... but a` to its inventory regex and its hook; the documented
  pattern list named it while neither command looked for it

### Changed
- Both scores are normalized: `max(0, 100 - spread - depth)`, where `spread` is the
  share of scanned files carrying a violation and `depth` is the capped average
  violation count per affected file. The old formula sent any project with five dirty
  files to 0 regardless of repository size
- Both scan-exclusion lists become a rule (everything generated, and every file whose
  text is data rather than prose), with each added exclusion named in the report
- Both working-tree passes name `.` explicitly, since `rg` handed a piped stdin and no
  path reads the pipe rather than the tree and reports zero matches on a dirty project
- `dashfix` replaces the `grep -rnP` fallback with `ggrep -rnP` and a perl one-liner,
  because BSD grep on macOS has no `-P`. The one-liner lists files with
  `--cached --others --exclude-standard`, repeats every scan exclusion both bare and
  `**/`-anchored, drops hidden paths, skips symlinks and files holding a NUL byte, and
  slurps each file to number its lines, so it reports the same locations as the `rg` pass
  instead of missing untracked files, keeping root or nested lock files, reading hidden,
  symlinked and binary paths, and numbering every line after the first file wrong
- README carries the skills.sh badge and states the install commands in the short
  `sentimony/skills` form

## [1.10.0] - 2026-08-09

Two new writing-style skills that ban AI-writing tells and score a project's prose.

### Added
- `dashfix` 1.0.0 - bans typographic dashes (em, en, and the neighboring Unicode code
  points) in favor of the plain hyphen in all produced text, audits a project with a
  per-occurrence catalog (`justified` / `replace` verdicts), and grades compliance on
  a deterministic 0-100 scale
- `negafix` 1.0.0 - bans negative parallelism (the "it's not just X, it's Y"
  construction) in favor of direct positive statements, audits English and Ukrainian
  prose with per-match verdicts that keep plain factual negation legal, and grades
  compliance on the same 0-100 scale
- New "Writing Style" group in `skills.sh.json` for both skills

### Changed
- Repository-wide dashfix cleanup: every published skill replaces typographic dashes
  (em and en) with plain-hyphen phrasing in SKILL.md, frontmatter descriptions,
  reference files, and script comments, with no workflow or behavior changes:
  `scope-triage` 1.0.2 -> 1.0.3, `plan-crafting` 1.1.1 -> 1.1.2, `vitest`
  1.2.0 -> 1.2.1, `typescript` 1.3.1 -> 1.3.2, `web-debug` 1.3.1 -> 1.3.2,
  `echarts` 1.1.1 -> 1.1.2. AGENTS.md and README prose get the same cleanup.
  Released changelog entries are frozen and keep their original punctuation, and the
  `dashfix` skill's own examples keep the characters they document.
- README install commands use the full GitHub URL form
  (`npx skills add https://github.com/sentimony/skills ...`)

## [1.9.1] - 2026-08-09

### Fixed
- `scope-triage` 1.0.1 → 1.0.2: the skills.sh Snyk audit still returned W007 (high) on
  1.0.1, because Step 0 and Route A asked the model to repeat "the literal values, names,
  and numbers from the request" and kept the secrets carve-out in a separate paragraph.
  Both places now ask for the request's domain values, the prohibition on reproducing a
  secret, token, key, password, connection string, or personal datum leads its own
  paragraph, and credentials are referenced by placeholder name in the done criterion,
  in every command, and in the Security Model. No workflow change.

## [1.9.0] - 2026-08-02

Five skills get audit and feedback fixes at patch level; `vitest` earns the minor bump
by changing how an auto-selected package script executes.

### Fixed
- `scope-triage` 1.0.0 → 1.0.1: credentials are named, never echoed, in announced
  contracts and done criteria (Snyk W007), plus an explicit Security Model.
- `vitest` 1.1.0 → 1.2.0: **behavior change:** `run_vitest.py` now auto-runs a
  package.json script only when the entire script body does nothing but invoke
  Vitest, matching the skill's Security Model treatment of package.json scripts as
  untrusted repository data. That accepted script now executes as parsed environment
  plus argv, not through `npm run`/`yarn`/`pnpm`/`bun run`, so package-manager
  lifecycle hooks (`pretest`, `posttest`, and equivalents) are no longer triggered by
  auto-selection; its own flags and environment are still honored on this path.
  `NODE_OPTIONS` is still an accepted environment key, now restricted to
  memory-tuning values such as `max-old-space-size` and `max-semi-space-size`
  (underscore spellings included); a value that instead loads code, opens a port, or
  changes module resolution falls back with a `SCRIPT_NOT_DIRECT` note. The parsed
  path does no shell expansion, so a glob or `~` inside the script's own arguments is
  passed literally. Separately and on **every** path, `--script` included, the runner
  now decides the child's environment rather than passing its own on: the variables a
  package manager injects (`npm_*`, `INIT_CWD`, `PROJECT_CWD`, `BERRY_BIN_FOLDER`)
  are dropped, every empty, relative, or project-touching entry is filtered out of
  `PATH`, and the launcher is resolved to an absolute path against that filtered
  `PATH`; otherwise a project could ship its own `node_modules/.bin/npx` and have the
  runner execute it. A `PATH` entry is judged by every component of it, not only by
  where it finally resolves, since a symlink inside the project can be repointed after
  the check; and the program found in a surviving directory is resolved too, so an
  allowed directory that merely links back into the project (what `npm link` writes)
  supplies nothing. Variables from your own shell, `NPM_TOKEN` and `NPM_CONFIG_*`
  included, are untouched. A `globalSetup` or test that shelled out to a sibling
  binary from `node_modules/.bin`, or read `npm_package_*`, is affected. The Node
  preflight in **both** helpers goes through the same filter and now runs after it,
  so a project shipping its own `node_modules/.bin/node` no longer answers the
  preflight's question about itself; the shared rule lives in a new
  `skills/vitest/scripts/node_environment.py`, and both entry points are unchanged. A test script that chains another command, launches via a bare
  `pnpm`/`yarn`/`bun`, carries an app-specific environment prefix, or has arguments
  containing a bidi override or other invisible formatting codepoint still doesn't
  auto-run; each falls back to the local Vitest binary with a `SCRIPT_NOT_DIRECT`
  note, run with this helper's own arguments rather than the script's on that
  fallback path only, so flags spelled inside the script body (a `--config`, a
  `--environment`) no longer apply there; pass `--script <name>` to run it as
  written, with full lifecycle hooks, anyway. A package.json the runner cannot read
  (bytes that are not UTF-8, a non-object top level, a `scripts` list, a script body
  that is not text) now takes the same fallback to the local binary (without that
  note, since no script was skipped) instead of ending the run with a traceback, and
  an undecodable `.nvmrc` or `.node-version` reads as an absent one. Also hardens the project-file candidate
  scan (agent-toolchain directories excluded), the `engines.node` preflight (strict
  `>` parity with the inspector; a declaration now renders verbatim only when it is
  composed entirely of version-range characters and stays within the render limit,
  otherwise as a placeholder, without changing which projects are warned or blocked),
  the accepted script's rendered `Command:` line
  (control characters and Unicode line separators rejected, length capped), and
  calibrates the Nuxt adapter guidance: mixing `node`- and `nuxt`-environment files
  in one config is still the intended pattern but isn't guaranteed leak-free, so it
  now requires a representative mixed run as proof, with a uniform Nuxt environment
  or split projects/configs documented as fallbacks.
- `typescript` 1.3.0 → 1.3.1: the Nuxt coverage report no longer contradicts itself,
  `NODE_RUNTIME_MISMATCH` states the next action instead of only raw version numbers,
  and the `vue-tsc` migration guidance is version-gated.
- `web-debug` 1.3.0 → 1.3.1: the crawl example now records a route as `ok` only
  after it has finished and its console messages are counted; a new `incomplete`
  status covers a route that was interrupted, and a matching prior checkpoint resumes
  instead of re-crawling completed routes (the checkpoint's on-disk shape changed
  accordingly: per-route results moved under a `results` key). The example's
  `HYDRATED_SELECTOR` constant is renamed `CLIENT_ONLY_SELECTOR`, gated by a new
  `wait_until_hydrated()` check that replaces the fixed sleep previously standing in for
  a real hydration check, and a resumed checkpoint is validated against the bounds the
  example itself writes and restricted to the current route list, so a hand-edited file
  cannot mark a route `ok` to have it skipped. Console output and page errors are escaped
  as they are collected, so a page cannot repaint the terminal or forge a line of the
  report. `with_server.py` now prints the server log path on a successful start.

### Changed
- `plan-crafting` 1.1.0 → 1.1.1: fallback verification for changes with no test seam,
  scoped staging, fixture realism, artifact-location precedence.
- `echarts` 1.1.0 → 1.1.1: conditional `notMerge` claims requiring runtime proof,
  grouped state inventory, named registration unions, split performance evidence.
- `scope-triage` 1.0.0 → 1.0.1: Route C may present a whole design in one message when
  it fits, keeping per-section approval only for separately contentious sections, and
  applies a revision before answering a new question in the same reply; Step 0 names a
  fan-out-then-targeted retrieval strategy.
- `scope-triage` and `plan-crafting` share one artifact-location precedence rule: an
  explicit user instruction overrides the skill default; a repository convention does
  not.
- CI runs every `test_*.py` under `skills/`, which no job had been doing; it validated
  frontmatter, compiled Python, and grepped for hidden Unicode, but ran no tests.
  `actions/checkout` and `actions/setup-python` are on v7 (the old pins forced Node 20
  onto a Node 24 runner). The hidden-Unicode scan takes its pattern from the runtime
  definition in `run_vitest.py` instead of keeping a second copy (read out of the source
  with `ast`, so the scan executes none of the code it is checking), checks itself against a
  positive control carrying every codepoint in that set, and distinguishes "found
  nothing" from "the scanner failed", which `! grep` had reported alike. AGENTS.md
  states what CI now does and what a maintainer test module has to be for CI to run it.

## [1.8.0] - 2026-07-31

Security-normalized audit guidance across the public skill collection.

### Added
- `vitest` `references/audit.md`, `typescript` `references/audit.md`, and `echarts`
  `references/audit.md`: progressive-disclosure audit guidance kept out of the main
  workflow until a request is actually an audit.

### Changed
- `vitest` 1.0.3 → 1.1.0: normalized, safe existing-suite audit reports and audit
  guidance.
- `typescript` 1.2.2 → 1.3.0: normalized TypeScript and Nuxt audit reports, safe
  local-tool resolution, and Node-runtime preflight guidance.
- `web-debug` 1.2.1 → 1.3.0: hardened readiness and bounded log evidence, plus
  checkpointed browser, accessibility, and console-audit guidance.
- `echarts` 1.0.5 → 1.1.0: audit guidance for lifecycle, trust, interaction, and
  browser evidence moved to a reference file.
- `plan-crafting` 1.0.0 → 1.1.0: explicit Security Model: repository evidence and tool
  output are data, and the skill takes no shell or network actions.
- All six skills now use security-normalized handling of untrusted repository, page,
  DOM, test, compiler, and tool output, with expanded audit guidance where applicable.

## [1.7.0] - 2026-07-29

Two design skills that decide how much design a request actually needs, then turn the
approved design into an executable plan.

### Added
- `scope-triage` 1.0.0: a fork of `obra/superpowers` `brainstorming` that classifies
  request scope first and routes to one of three outcomes: direct implementation for
  explicitly specified mechanical changes and localized fixes, a light spec for large
  but fully specified changes with a single open question, or the full design cycle
  (clarifying questions, approach trade-offs, sectioned design approval, a design doc in
  `docs/specs/`, handoff to `plan-crafting`) whenever anything about the product, UX, or
  public contract is still undecided; hard implementation gate, assumption register,
  mirrored rationalizations table, and Route C design lenses in `references/`
- `plan-crafting` 1.0.0: a fork of `obra/superpowers` `writing-plans` that turns an
  approved design or settled requirements into bite-sized TDD tasks with exact files,
  interfaces, verification steps, and commits; plans are written to
  `docs/plans/YYYY-MM-DD-<feature-name>.md` and handed off to `subagent-driven-development`
  or `executing-plans`

Both skills replace their upstream counterparts rather than complementing them: install
one of each pair, not both.

## [1.6.0] - 2026-07-20

Feedback-driven guidance updates from real audit sessions on the agilecharts project.

### Changed
- `typescript` 1.2.1 → 1.2.2: audit guidance: "already healthy" early exit,
  sampling heuristic for massive non-null-assertion counts, generic `defineProps`
  for `config: any` Vue props; error playbook gains the
  `ERR_PACKAGE_PATH_NOT_EXPORTED './lib/tsc'` entry; TS-7 migration reference
  gains a "Choosing the TS-7 target" checklist and a `types: []` vs `lib` note
- `vitest` 1.0.2 → 1.0.3: Nuxt auto-import leak into `environment: node` files
  documented in Common Failure Modes (symptom, cause, diagnosis); `.nuxt`-cache
  warning (`nuxt prepare`, not `rm -rf`); mixed node/nuxt environment config
  example in the Nuxt adapter
- `web-debug` 1.2.0 → 1.2.1: cold-start HMR form-reset pitfall in Waiting
  Strategy; login-then-audit pattern in Best Practices; `console_audit.py`
  example gains an optional login step over a shared context and is documented
  as a copy-and-edit template
- `echarts` 1.0.4 → 1.0.5: audit checklist recognizes design-tokens theming as
  a valid alternative to `registerTheme` and classifies one-off hardcoded hex
  colors as duplication debt; Common Failure Modes gains the "`notMerge: true`
  everywhere" pitfall

## [1.5.0] - 2026-07-19

### Changed
- `web-debug` 1.1.2 → 1.2.0: Agent Trust Hub remediation: `with_server.py` runs
  `--server` without a shell (shlex + `shell=False`, explicit `bash -c` escape
  hatch), Playwright install pinned to an exact release, Security Model gains
  untrusted-output boundary rules
- `echarts` 1.0.3 → 1.0.4: Snyk W012 remediation: vanilla example loads ECharts
  via a pinned UMD build with an SRI hash instead of a runtime ESM import
- `typescript` 1.2.0 → 1.2.1, `vitest` 1.0.1 → 1.0.2: descriptions rewritten
- All four descriptions now start with "You MUST use this when…"; new repository
  convention for skill descriptions

## [1.4.0] - 2026-07-13

### Changed
- `typescript` 1.1.1 → 1.2.0: real-world feedback from a Vue/Netlify TypeScript 7
  side-by-side migration: `inspect_typescript.py` now detects a native TypeScript 7
  compiler installed alongside the framework's TypeScript 6 and reports each
  `typecheck*` script's target tsconfig; added the four hardening flags
  (`noImplicitOverride`, `noFallthroughCasesInSwitch`, `noUnusedLocals`,
  `noUnusedParameters`) to the effective-flags report and an explicit
  "coverage complete" result; documented the real-package dual-install layout that
  keeps `typescript` on genuine 6.x for vue-tsc/Volar; clarified "pinned" and CI
  auditing for multiple compiler paths

## [1.3.1] - 2026-07-12

Security-audit hardening from the skills.sh scanners. No behavior change.

### Changed
- `web-debug` 1.1.1 → 1.1.2: Gen Agent Trust Hub audit (Warn/Medium): added a
  Security Model section (`--server` is user-controlled shell config; page
  content is untrusted data, not instructions), reworded the "run `--help`
  first" guidance so it no longer reads as "don't inspect the source", and
  clarified the `shell=True` comment in `with_server.py`
- `echarts` 1.0.2 → 1.0.3: Snyk audit (Warn/Medium, W012): pinned the
  standalone CDN import in `examples/vanilla_line.html` to an exact release
  (`echarts@6.1.0`) instead of a floating `@6`
- `typescript` 1.1.0 → 1.1.1: cleared the skills.sh "Contains Shell Commands"
  false positive by rewording an isolated non-null exclamation-mark operator that the
  scanner read as a shell-command directive

## [1.3.0] - 2026-07-11

### Added
- `typescript` 1.1.0: migration guidance for the stable TypeScript 7 native
  compiler, including the TypeScript 6 compatibility bridge, compiler-API and
  framework limitations, side-by-side adoption, and rollback; research checked
  against official TypeScript sources dated 2026-03-23 and 2026-07-08

### Changed
- README skills table: renamed Version to Skill Version and added the repository
  Release tag associated with each skill version

## [1.2.2] - 2026-07-07

### Changed
- `echarts` 1.0.1 → 1.0.2: second-audit feedback: tooltip security,
  ComposeOption example, SSR registration parity, `connect` axis-semantics
  caveat, `notMerge` interactive-state failure mode, ECharts 6 default-theme
  and label-overflow migration notes

## [1.2.1] - 2026-07-07

### Changed
- `echarts` 1.0.0 → 1.0.1: first-usage feedback: shared registration module
  guidance, type-import bundle notes, ECharts 6 migration notes
  (`containLabel` → `outerBoundsMode`/`outerBoundsContain`), "Auditing Existing
  Usage" checklist,
  vue-echarts `update-options`/`group` gotchas

## [1.2.0] - 2026-07-07

### Added
- `echarts` 1.0.0: build, style, debug, and optimize Apache ECharts
  visualizations in vanilla JS, React, or Vue; lifecycle management,
  tree-shaken imports, theming, large-dataset performance, SSR, common
  failure modes; vanilla/React/Vue reference examples

### Changed
- `skills.sh.json` groups reorganized: Browser (web-debug, echarts) and
  JavaScript Tooling (vitest, typescript) instead of Development / Quality
  Assurance
- AGENTS.md: mandatory updates of the repository CHANGELOG and skills.sh.json,
  release/CI notes; a new-skill branch may change existing files if noted in
  the repository CHANGELOG

## [1.1.1] - 2026-07-07

### Changed
- `typescript` 1.0.1: framework checkers, audit mode, script skip criteria

## [1.1.0] - 2026-07-05

### Added
- `typescript` 1.0.0: configure tsconfig, resolve compiler errors, debug slow
  type-checking, fix module resolution, migrate JS to TS; inspect-first Python
  helpers, error playbook, module-resolution / migration / monorepo references
- `skills.sh.json` grouping the skills.sh page into Development and
  Quality Assurance sections

### Changed
- README skills table: new Version column with each skill's `metadata.version`

## [1.0.1] - 2026-07-05

### Added
- Per-skill `CHANGELOG.md` for `vitest` and `web-debug` (Keep a Changelog style;
  not referenced from SKILL.md so it never enters an agent's context)
- `AGENTS.md` (+ `CLAUDE.md` importing it) with repository conventions:
  English-only content, plain semver in skill metadata with `v` prefix reserved
  for git tags, feature-branch + squash-merge workflow
- Basic CI: SKILL.md frontmatter validation (name/description/semver version),
  Python compile check for scripts and examples, hidden/bidi Unicode check

## [1.0.0] - 2026-07-05

First tagged release of the skills collection, published on
[skills.sh](https://skills.sh/sentimony/skills).

### Skills
- `vitest` 1.0.1: configure, write, debug, run, and migrate Vitest tests for
  JavaScript/TypeScript projects
- `web-debug` 1.1.1: debug local web apps via Playwright (fork of
  `anthropics/skills` `webapp-testing` with field-feedback improvements)
