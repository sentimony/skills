# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.12] - 2026-11-07 - [0.0.101]

### Changed

- Section 4 adds a rule against rerunning a check for ceremony: evidence stays valid while
  tree identity, inputs, and conditions are unchanged, and capture time is recorded only
  when the claim depends on time or environment state (`20260915-1939`).
- `Tree identity` in `evidence-provenance.md` now records capture time only when the claim
  depends on time or environment state, matching the new rule (`20260915-1939`).

## [0.0.11] - 2026-11-04 - [0.0.99]

### Changed

- `Tree identity` states when a branch verification carries over to its merge commit: only
  when `git rev-parse <merge>^{tree}` equals the verified tree, otherwise a new run.

## [0.0.10] - 2026-11-04 - [0.0.98]

### Changed

- The LICENSE now names one copyright holder after a text-overlap review found no
  upstream text in this skill. This original workflow was informed by obra/superpowers ideas.

## [0.0.9] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.8] - 2026-10-10 - [0.0.76]

### Changed

- Shorter body, same behavior: sections 3-5 keep their rules in the body; the
  tree-identity commands and the CI and check-record rules moved to
  `references/evidence-provenance.md`.

## [0.0.7] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.6] - 2026-10-05 - [0.0.70]

### Changed
- The `not applicable` status is written `- not applicable` with a plain hyphen instead of
  an em dash, so a copied status no longer carries a typographic dash into reports, pull
  requests and commits.

## [0.0.5] - 2026-10-01 - [0.0.61]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [0.0.4] - 2026-09-14 - [0.0.50]

Renamed skill reference.

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [0.0.3] - 2026-09-14 - [0.0.49]

Renamed skill reference.

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [0.0.2] - 2026-09-14 - [0.0.48]

Security Model release: the gate now documents its own trust boundary.

### Added

- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [0.0.1] - 2026-09-12 - [0.0.38]

Initial release.

### Added

- A compact, stateless gate from completion claims to fresh, attributable evidence and
  explicit PASS, FAIL, INCOMPLETE VERIFICATION, or BLOCKED verdicts.
- Claim-first verification, equivalence checks, risk-based depth, and a verification
  matrix with separate acceptance, scope, current-tree integrity, and impact checks.
- Controller-level evidence for delegated work, runtime and framework delegation,
  staleness propagation, bounded failure routing, and explicit skill boundaries.
- References for verification depth and safety, evidence provenance, runtime verification,
  and upstream attribution, with an MIT license preserving upstream copyright.
