# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.22] - 2026-11-13 - [0.0.107]

### Changed

- Description rewritten as a thesis plus "Use when ..." without "You MUST", at a lower token cost; triggers unchanged.
- Contract test asserts the new description wording.

## [0.0.21] - 2026-11-12 - [0.0.104]

### Changed

- Restructuring verification treats `docs/**/YYMMDDTHHMM-*` as dated documents next to
  `docs/**/YYYYMMDD-*`: matches there stay as history (20261112-0305).

## [0.0.20] - 2026-11-10 - [0.0.103]

### Added

- Added `argument-hint: "[audit]"` and a sentence in the audit section: after `/agent-instructions` (`$agent-instructions` in
  Codex), the word `audit` selects the audit mode (`20261003-1418`).
- Phase 5 checklist: search for inbound references with `git grep` before moving a section;
  matches in live files become their own Phase 5 item, matches in dated documents stay
  history (`20261019-0418`).
- Phase 2: delegated read-only readers for a surface the host cannot read itself. A reader's
  finding is a hypothesis the host verifies before a Phase 5 edit; refuted findings are
  reported as rejected (`20261110-1055`).

## [0.0.19] - 2026-11-07 - [0.0.102]

### Changed

- Renamed `maintaining-agent-context` to `agent-instructions`; invoke `/agent-instructions`.
  Only the name and its mentions changed.

## [0.0.18] - 2026-11-07 - [0.0.101]

### Changed

- `20261029-2011`: Phase 2 now checks a claim about another repository against that
  repository's default branch (`git -C <clone> show origin/<default>:<path>`), reports a
  differing working tree as a finding with a question, and records the clone's branch in
  the surface map; `references/assessment-criteria.md` Contradiction points to it.

## [0.0.17] - 2026-11-04 - [0.0.99]

### Changed

- `20261101-1221`: `scripts/agents_chain_size.py` no longer enters a directory below the
  root that holds `.git` (a nested checkout or linked worktree, which has its own Codex
  chain) and prints `skipped: nested checkout <path>` for it. Test with a worktree fixture.
- `20261101-1221`: `references/restructuring-verification.md` step 1 now says to snapshot
  the original in the same command that writes the file, or to compare the snapshot's
  sha256 right before the write and re-snapshot on a mismatch.

## [0.0.16] - 2026-10-27 - [0.0.95]

### Changed

- `20261024-2348`: `scripts/agents_chain_size.py` no longer measures a nested folder the
  root `AGENTS.md` or `CLAUDE.md` pulls in with a bare `@` import, nor
  `docs/session-learnings/`, as a Codex chain. It prints such a folder on its own
  `import (Claude Code): +N B` or `notes (session-learnings): +N B` line outside the
  budget, so the notes no longer turn the run `OVER` with exit 1. A code-span or
  punctuated `@` path, which Claude Code does not expand, still counts as a chain.
  Phase 1 maps the folder as "always (Claude Code import), not a Codex chain", and
  Phase 3 reports large notes as a triage finding that points at
  `session-learnings triage`, not a limit breach.

## [0.0.15] - 2026-10-12 - [0.0.83]

### Added

- `scripts/agents_chain_size.py` resolves the effective Codex `project_doc_max_bytes` and
  `project_doc_fallback_filenames` when `--budget` is omitted: the default,
  `/etc/codex/config.toml`, the user config in `CODEX_HOME`, a `--profile` file, the
  root's `.codex/config.toml` when the user config trusts it, and
  `/etc/codex/managed_config.toml`. It prints the limit with its source and notes for `-c`
  flags, MDM, an untrusted project config, and an ignored `.codex/config.local.toml`; a
  config that does not parse exits 2 naming only the file. `references/codex-loading.md`
  records the layer order observed in Codex CLI 0.162.1, including that a legacy
  `profile` key makes Codex refuse to start.

### Changed

- The description is rewritten as trigger, scope, and boundary, without workflow detail.

## [0.0.14] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.13] - 2026-10-10 - [0.0.78]

### Changed

- The user-level `project_doc_max_bytes` governs the Codex budget also when a project
  instruction file already declares the repository personal. When the user says the
  repository is personal and no file declares it, Phase 5 proposes one line for the root
  `AGENTS.md`, naming the source of the limit rather than its number.

## [0.0.12] - 2026-10-10 - [0.0.75]

### Added

- A Capture session learnings mode for requests to record what the session learned, with
  candidates from the session, a level per candidate (including a project document), and
  the unchanged Phase 5 gate.
- Read-only `scripts/agents_chain_size.py` measures every `AGENTS.md` chain against a
  budget.
- The global section compares `~/.claude/CLAUDE.md` with the Codex home `AGENTS.md`.

### Changed

- The read-mostly guardrail covers `CLAUDE.local.md` and machine overrides, not
  user-level global files.

## [0.0.11] - 2026-10-10 - [0.0.74]

### Changed

- A request addressed to a `CLAUDE.md` shim (a lone `@AGENTS.md` import or a symlink)
  routes all work to `AGENTS.md`, leaves the shim unchanged, and says the routing aloud;
  Phase 5 approval for "CLAUDE.md" covers the matching `AGENTS.md` edits.
- The assessment criteria tell installed skill copies apart: a symlink into a local
  clone (live), a copy installed from a local path (snapshot), and a registry install
  (published release). Treating a copy as live is a stale-risk finding.
- `references/codex-loading.md` orders the config layers for `project_doc_max_bytes`
  (default, user config with an active profile, trusted project `.codex/config.toml`,
  `-c` launch flag; legacy managed configs above all) and notes that Codex reads no
  `.codex/config.local.toml`.
- Three contract tests cover these rules.

## [0.0.10] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.9] - 2026-10-05 - [0.0.72]

### Fixed

- `references/codex-loading.md` describes the Codex size budget as the source at
  `rust-v0.160.0` implements it: `project_doc_max_bytes` bounds only the project chain,
  the global `AGENTS.md` is unlimited and not counted, and the file at the boundary is
  truncated by bytes mid-text with only a log warning instead of being dropped whole.
- The reference notes that an untrusted project loads no project `AGENTS.md`, and that a
  `config.toml` which does not parse stops Codex from starting, so its limit never
  applies.
- The documentation link points to `learn.chatgpt.com`, where the old
  `developers.openai.com/codex` pages now redirect.
- A contract test pins the budget wording.

## [0.0.8] - 2026-10-05 - [0.0.71]

### Changed

- Phase 1 records the effective Codex `project_doc_max_bytes` with its source (the config
  file that sets it, or the default) instead of assuming the 32 KiB default.
- Phase 3 names the governing limit: for a shared repository the lower of the default and
  the project `.codex/config.toml`; a larger user-level value is only a note, and it
  governs only when the user says the repository is personal. A chain that fits the local
  limit but exceeds the default is a finding.
- `references/codex-loading.md` gains an "Effective size limit" section: which config
  files to read, reading only the two `project_doc_*` keys, the surface-map line format,
  and keeping a repository's own size budget apart from the platform limit.
- Contract tests pin the Phase 1 and Phase 3 rules and the bounded config read.

## [0.0.7] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.6] - 2026-09-15 - [0.0.52]

### Changed

- Narrowed the trigger to a repository's instruction and context architecture, naming the
  instruction layer of SKILL.md files rather than SKILL.md files as such, and excluding
  authoring or revising a skill. It competed with `skill-crafting` over any skill edit;
  that skill's description already routes instruction-architecture work here.

## [0.0.5] - 2026-09-14 - [0.0.48]

### Changed
- The Security Model section is renamed to title case and gains a capability
  statement: the skill reads files and runs local read-only shell tools, performs no
  network or publish action of its own, and writes only the Phase 6 edits the user
  approved in Phase 5.
- Contract tests look up the renamed section.

## [0.0.4] - 2026-09-08 - [0.0.33]

### Changed
- Phase 3 evaluates a directory-scoped split before proposing semantic compression
- The repository map now bounds the Codex trade-off before it is weighed, so a split is
  judged against one lost file read rather than against the bare loss of auto-loading
  when the always-loaded surface approaches its platform limit or a repository-set
  budget; nested instruction files are framed as a scoping mechanism of any
  repository, not only monorepos.
- Assessment criteria: the root section gains the split procedure - map sections to
  directories, keep pre-open constraints in root, divide a section that describes two
  directories, pair every nested `AGENTS.md` with a `CLAUDE.md` shim, keep a
  repository map, measure the deepest root-to-cwd chain - with a minimum-size
  criterion instead of a number and the Claude Code / Codex trade-off stated.
- Guardrails: the split boundary can run inside a section.
- Phase 5 reads `restructuring-verification.md` before the first write of any change
  that moves content between files; the reference and its index entry say so, and
  its checklist warns against line-range extraction when assembling new files.
- Phase 6 re-verify checks that files created by the audit are tracked by version
  control (`git check-ignore`) and that a limit the audit writes into a file is
  satisfied by that file, corrected to the honest value rather than met with
  unapproved compression.
- Contract tests cover the new phrases.

## [0.0.3] - 2026-08-29 - [0.0.23]

### Changed
- Phase 1 records the unit and the command behind every size in the surface map and
  ships a Unicode-aware character-count recipe, so byte counts stop being reported
  as characters.
- Phase 1 keeps instruction files reached through a symlink that leaves the checkout
  on the map but outside the edit scope.
- "Pointers do the routing" keeps constraints that must hold before a target is
  opened (data boundaries, no-publish rules, permission gates) inline next to the
  pointer instead of behind it.
- Phase 3 reads file bodies, not heading maps, before judging duplication and
  contradiction.
- Phase 4 reports the same wrong fact found outside the instruction files (README,
  config-file comments) in its own section with an explicit question, and may state
  that the current structure is already the target.
- Phase 5 keeps the confirmation gate when the invocation itself asks to apply
  changes immediately; the agent says which side it follows and still shows diffs.
- Phase 6 re-checks edited lines and files against the limits the audit treated as
  governing.
- Assessment criteria: root section gains the "redundant with the environment"
  category for verified-but-cached commands and criteria for one-line import shims;
  the report structure gains an optional "Findings outside the instruction files"
  section.
- Reference Files index now lists `scripts/test_contract.py` as maintainer-only.

## [0.0.2] - 2026-08-25 - [0.0.22]

### Changed
- Phase 2 now supports risk-based spot-checking for large instruction surfaces,
  explicit verification statuses, coverage scope, and residual uncertainty.
- Phase 3 names the unit used for every size or limit claim and keeps bytes,
  characters, and lines distinct.
- Phase 5 exposes the trade-off between reformatting and compression for approval;
  Phase 6 applies only the approved choice while preserving semantic content.
- Phase 4 report structure now includes verification coverage and residual uncertainty.
- Read-only shell inspection is explicitly allowed while project and
  repository-controlled commands remain outside the audit phases.

### Added
- `references/restructuring-verification.md` - before-and-after integrity guidance
  with limitations for token-multiset checks.

## [0.0.1] - 2026-08-23 - [0.0.21]

### Added
- Initial release: audit, restructure, and maintain the full agent-context
  architecture of a repository (AGENTS.md, CLAUDE.md and variants, `.claude/rules/`,
  skills, linked agent docs) for Claude Code and Codex
- Six-phase workflow: discovery, project verification, context architecture
  analysis, quality report, proposed changes with user confirmation, apply and verify
- Security model: Phases 1-4 execute no project commands; already-active platform
  instructions keep their priority (conflicts get reported), newly opened audited
  content is untrusted data that grants no authorization, and only explicit user
  confirmation - scoped to the shown files and fragments - authorizes edits
- `scripts/test_contract.py` - CI-run static guard for the read-only, security,
  confirmation, and progressive-disclosure invariants and reference-pointer
  integrity
- `references/claude-code-loading.md` and `references/codex-loading.md` - per-agent
  loading mechanics, each read only when its platform is in scope
- `references/assessment-criteria.md` - per-file-type assessment criteria and
  report structure
- `references/attribution.md` - design lineage from `writing-for-agents`
  (Matt Pocock, MIT) and `claude-md-improver` (Anthropic, Apache-2.0)
