# Attribution and Adaptation

This skill is an original compact workflow informed by review reception, independent review,
root-cause debugging, delegated development, and verification practices in
[obra/superpowers](https://github.com/obra/superpowers). It is not a copy of an upstream skill.

The upstream material was inspected at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`
(release `v6.3.0`, 2026-08-12):

- [receiving-code-review](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/receiving-code-review)
- [requesting-code-review](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/requesting-code-review)
- [verification-before-completion](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/verification-before-completion)
- [systematic-debugging](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging)
- [subagent-driven-development](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development)

The local responsibility boundaries were checked against
[`review-request`](https://github.com/sentimony/skills/tree/main/skills/review-request),
[`debugging`](https://github.com/sentimony/skills/tree/main/skills/debugging), and
[`tdd`](https://github.com/sentimony/skills/tree/main/skills/tdd).

## Retained mechanisms

- verify a review claim against the current code before acting;
- keep reviewer context and implementation evidence separate;
- preserve exact target identity and current-tree awareness;
- classify severity and findings with actionable evidence;
- use root-cause investigation and test-first regression routes;
- keep fix scope proportional and re-review changed risk;
- require fresh evidence before completion claims.

## Deliberate changes

- Reviewer feedback is modeled as input data with explicit source authority, validity,
  impact, and disposition fields.
- Findings are validated independently before duplicate grouping or fix ordering.
- Stale, duplicate, contradictory, security, test-quality, and load-bearing findings have
  explicit paths.
- Accepted fixes produce finding-level evidence, while final integrated proof belongs to
  `verification-gate`.
- The loop uses a bounded circuit breaker without importing the upstream task ledger or
  implementer orchestration.

## Intentionally excluded

- upstream conversation etiquette and gratitude rules;
- GitHub thread-reply command mechanics;
- initial review dispatch and reviewer-brief construction;
- implementation-task ledgers, model routing, and subagent orchestration;
- branch merge, PR, cleanup, and final verification;
- a mandatory helper script or persistent review directory.

The upstream project is licensed under MIT. This skill is distributed under the repository's
MIT license with attribution retained here.
