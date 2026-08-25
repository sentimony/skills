# Assessment criteria by file type

Read this during Phase 3 (context architecture analysis) and when writing the Phase 4
quality report. Read selectively: only the sections for surface types present in your
Phase 1 map, plus "Cross-cutting checks" and "Quality report structure" at the end.
There is no universal rubric: each file type earns its place in context
differently, so judge each against its own criteria. Prefer evidence-based findings with
a severity and a concrete action; use a numeric score only when the user asks for one or
when comparing two versions of the same file.

## Root project instructions (AGENTS.md, CLAUDE.md at repo root)

Loaded in every session, so every line pays rent every turn. Judge by:

- **Navigation**: does it orient the agent in the codebase - key directories, entry
  points, module boundaries - without narrating structure that one `ls` reveals?
- **Core commands**: a command belongs here only when the environment cannot answer
  it cheaply and unambiguously - several similar scripts with one canonical choice,
  a required working directory or ordering, non-obvious arguments, or safety
  constraints; a script that `package.json` states plainly needs no copy. Commands
  that are documented must be current and copy-paste runnable; verify against
  package scripts and CI config, not by running them. Absence of a command is a gap
  only when the environment leaves the right workflow genuinely unclear.
- **Universal gotchas**: quirks that bite in most sessions (ordering constraints,
  environment traps, "why we do it this way" for unusual patterns).
- **Cache discipline**: anything restating package scripts, config files, or directory
  listings is a cache of an environment lookup. Keep it only when the lookup is
  genuinely expensive or unreliable; otherwise the environment is the source of truth
  and the copy will go stale.
- **Branch purity**: instructions that apply only to some task types belong behind a
  pointer or a conditional rule, not inline.

## Global instructions (user-level, e.g. `~/.claude/CLAUDE.md`)

Loaded in every session of every project. Judge by stability and universality: durable
user-wide preferences and workflow rules belong here; anything project-specific or
likely to change with the current job does not. Flag project details that leaked
upward - they will silently apply to unrelated repositories.

## Local instructions (e.g. `CLAUDE.local.md`, other gitignored overrides)

Personal or machine-specific: local ports, private paths, personal habits. Judge by
whether each line is genuinely machine- or person-bound; anything the whole team needs
belongs in the shared file. Never propose committing these or copying secrets out of
them.

## Package-specific and nested instructions (monorepos)

Loaded only when the agent works in that subtree. Judge by locality: local conventions,
commands, and boundaries for that package only. Flag content that duplicates the root
file (the root is the single source of truth for shared rules) and root content that
belongs down here instead.

## Conditional rules (e.g. `.claude/rules/*.md` with glob frontmatter)

Judge by trigger precision:

- Does the glob match exactly the files the rule is about? Too broad wastes tokens on
  unrelated work; too narrow means the rule silently never fires.
- Is the rule's body self-contained for its trigger, without depending on another file
  that may not be loaded?
- A rule without any trigger condition is always-loaded content in disguise - assess it
  as root instructions.

## Linked references (docs reached via pointers from instruction files)

Judge the pair, pointer plus target:

- **Discoverability**: does the pointer state what the material is and the distinct
  conditions for reaching it? A must-read target behind a vague pointer is a
  reliability bug - sharpen the pointer before inlining the material.
- **Narrow scope**: one topic per file; a grab-bag target defeats conditional loading.
- **Currency**: linked docs go stale quietly because no session forces them into view;
  spot-check claims against the code they describe.
- Verify every link resolves - and that the target is intact: a pointer that resolves
  to an empty, truncated, or garbled file is a broken pointer with extra steps.

## Skills (SKILL.md and bundled resources)

- **Invocation accuracy**: the description is the always-loaded pointer; it should name
  the distinct trigger branches without restating the workflow, and without synonym
  padding.
- **Workflow reliability**: steps in order, each with a completion criterion the agent
  can check.
- **Progressive disclosure**: SKILL.md carries what every invocation needs; material
  only some branches reach lives in `references/` behind clear read-when conditions.
- **Bundled scripts**: deterministic, documented, and actually referenced from the
  workflow.

## Cross-cutting checks (all file types)

- **Duplication**: the same rule in two surfaces (AGENTS.md vs CLAUDE.md, root vs
  package, rule vs skill). Name which file should be the single source of truth and
  what the other becomes (a pointer, or nothing).
- **Contradiction**: two surfaces disagreeing; the agent's behavior then depends on
  load order. Severity follows impact: critical when it steers commands, safety
  rules, or architecture boundaries; lower when the disagreement is cosmetic.
- **Derived values**: test counts, issue counts, file inventories, tool versions
  that a command can produce - remove rather than refresh. Versions that are
  themselves the contract (a pinned toolchain requirement, a release version a
  process depends on) are rules, not derived values - keep them.
- **Stability**: would this line survive the next normal refactor? Temporary states
  and in-flight migrations need a date or removal.
- **Actionability**: could an agent act on this line without guessing? "Be careful
  with the API layer" fails; "API handlers must not import from `db/` directly -
  go through `services/`" passes.
- **No-ops**: generic best practices the model already follows by default spend
  tokens to change nothing.

## Quality report structure

Present the Phase 4 report in this shape:

```
## Agent Context Audit

### Instruction surfaces
| File | Agent(s) | Scope | Loading |
(one row per discovered file; Loading = always / conditional-on-<trigger> / on-demand via pointer)

### Findings
Grouped by severity (critical / important / minor). Each finding: file, evidence,
concrete action. Cover: stale or wrong content, duplication, contradictions,
always-loaded content that should move down, missing must-know context, weak pointers.

### Verification coverage and residual uncertainty
State whether Phase 2 verification was exhaustive or risk-based spot-checked. For
spot-checked verification, name every high-risk claim covered, define the
representative sample and its scope, and list claims unverifiable at this depth.

### Recommended target structure
The proposed file layout and what moves where.

### Priorities and context-cost direction
Each recommendation: priority, and whether it increases, keeps neutral, or decreases
always-loaded context cost. State direction only - do not invent token percentages
without an actual measurement.
```
