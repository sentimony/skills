# Attribution and Adaptation

Verification Gate is an original compact adaptation of verification ideas from
obra/superpowers. It is not a fork. Its claim matrix, tree identity, equivalence checks,
and verdict contract are authored for the surrounding sentimony skills.

The upstream material was inspected at commit
`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`. Stable source paths:

- [Upstream verification skill](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/verification-before-completion/SKILL.md)
- [Upstream branch completion boundary](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/finishing-a-development-branch/SKILL.md)
- [Upstream review feedback boundary](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/receiving-code-review/SKILL.md)
- [Upstream task orchestration boundary](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development/SKILL.md)
- [Upstream MIT license](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/LICENSE)

## Retained

- Fresh, complete verification and interpreted results before completion claims.
- Independent inspection of actual changes and results after delegated implementation.
- Separate evidence for tests, build, bug resolution, and requirements.

## Changed

- Begin with proposed claims and their acceptance boundaries before choosing commands.
- Check that evidence observes the relevant object, conditions, and boundary.
- Identify the current worktree, staged and unstaged changes, and selected untracked
  inputs; invalidate affected evidence after material changes.
- Make applicability, failures, and unverified gaps explicit in a lightweight matrix.
- Choose depth by risk and change impact, with separate acceptance and scope checks.
- Return PASS, FAIL, INCOMPLETE VERIFICATION, or BLOCKED for an identified claim set.
- Delegate runtime and framework mechanics to specialists while retaining responsibility
  for evidence sufficiency and the final verdict.

## Excluded

- Universal admonitions about every positive statement and repeated rationalization
  tables; the gate targets completion claims and has a defined trivial-edit threshold.
- Implementation and root-cause procedures, test-first cycles, reviewer dispatch,
  finding disposition, task orchestration, and executor-owned fix loops.
- Branch integration, cleanup, deployment, and publishing operations.
- Mandatory project commands, helper scripts, and persistent verification infrastructure.

The bounded retry rule governs re-entry after an owner supplies a fix. It gives this
skill no implementation or orchestration ownership. Long upstream passages and workflow
implementations were not copied into this package.

The upstream project uses MIT. The package LICENSE preserves Jesse Vincent's 2025
copyright notice alongside Ihor Orlovskyi's 2026 notice and the repository's MIT wording.
