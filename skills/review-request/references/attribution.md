# Attribution and Adaptation

This skill is an original workflow informed by the review, feedback, subagent orchestration,
and verification skills in obra/superpowers. It is not a copy of an upstream skill.

The upstream material was inspected at commit b36e0829c6d0140e93cfef2ca599b1b07d4a7797
(release v6.3.0, 2026-08-12):

- requesting-code-review:
  https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/requesting-code-review
- receiving-code-review:
  https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/receiving-code-review
- subagent-driven-development:
  https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/subagent-driven-development
- verification-before-completion:
  https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/verification-before-completion

Retained ideas:

- an isolated reviewer perspective;
- explicit requirements and review target identity;
- diff-first inspection;
- separate review verdicts;
- structured findings with severity;
- proportional reviewer selection and specialist routing;
- fresh evidence as a separate verification responsibility.

Changed for this skill:

- the target model explicitly covers committed ranges and current working trees;
- selected untracked files and content identities are part of a working-tree boundary;
- requirements, scope, quality, risk, evidence, and gaps are explicit brief fields;
- review output is handed to review-resolution without fixing or disposition;
- stale reviews and idempotent reuse are tied to a target fingerprint;
- harness capabilities are detected and degraded gracefully.

Intentionally excluded:

- upstream fix loops, finding disposition, and re-review execution;
- implementation-task ledgers and subagent task orchestration;
- branch completion and final verification;
- a mandatory helper script or persistent review directory.

These exclusions preserve the responsibility boundaries of the surrounding sentimony skills.
The upstream project is licensed under MIT; this skill is distributed under the repository's
MIT license with attribution retained here.
