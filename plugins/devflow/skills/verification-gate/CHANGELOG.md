# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [1.1.2] - 2026-10-12 - [1.58.3]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 1.54.0. The skill instructions are unchanged.

## [1.1.1] - 2026-10-10 - [1.55.1]

### Changed

- Shorter body, same behavior: sections 3-5 keep their rules in the body; the
  tree-identity commands and the CI and check-record rules moved to
  `references/evidence-provenance.md`.

## [1.1.0] - 2026-10-09 - [1.54.0]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [1.0.5] - 2026-10-05 - [1.52.0]

### Changed
- The `not applicable` status is written `- not applicable` with a plain hyphen instead of
  an em dash, so a copied status no longer carries a typographic dash into reports, pull
  requests and commits.

## [1.0.4] - 2026-10-01 - [1.48.0]

### Added

- `agents/openai.yaml` with the Codex display name and short description.
- `metadata.internal: false` in the frontmatter.

## [1.0.3] - 2026-09-14 - [1.36.0]

Renamed skill reference.

### Changed

- Follow the `worktree-isolation` rename to `git-worktree-isolation`

## [1.0.2] - 2026-09-14 - [1.35.0]

Renamed skill reference.

### Changed

- Follow the `workspace-isolation` rename to `worktree-isolation`

## [1.0.1] - 2026-09-14 - [1.34.3]

Security Model release: the gate now documents its own trust boundary.

### Added

- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [1.0.0] - 2026-09-12 - [1.29.0]

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
