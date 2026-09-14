# Changelog

All notable changes to the `verification-gate` skill. Versions refer to `metadata.version`
in SKILL.md. This file is for maintainers and is never loaded by agents using the skill.

## [1.0.1] - 2026-09-14

Security Model release: the gate now documents its own trust boundary.

### Added

- Added a `## Security Model` section naming the skill's trusted and untrusted inputs, the
  rule that tool output is data rather than instructions, and whether the skill runs shell
  commands or network calls.

## [1.0.0] - 2026-09-12

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
