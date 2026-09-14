# Attribution and Adaptation

`skill-crafting` is an original synthesis of two inspected skill-authoring sources. It keeps
the ideas listed below while using its own terminology, boundaries, and workflow. No
substantial upstream text is reproduced in this package.

## Anthropic `skill-creator`

- Source repository: [anthropics/skills](https://github.com/anthropics/skills/tree/34040c9c568585f6929bedeaad110ad08f079624)
- Source skill: [skill-creator/SKILL.md](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/skill-creator/SKILL.md)
- Source commit: `34040c9c568585f6929bedeaad110ad08f079624`
- License: Apache-2.0, from [skills/skill-creator/LICENSE.txt](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/skill-creator/LICENSE.txt)
- Copyright: Anthropic PBC, 2026.

Retained concepts include intent capture, create and improve modes, progressive disclosure,
paired evaluation, qualitative and objective evidence, trigger cases, cost and variance
observations, and transcript-based repeated-work discovery.

Intentionally excluded from the core are Claude Code-specific runners, event-stream parsing,
temporary command files, a mandatory viewer, and implicit dependency or configuration
assumptions. The current execution owner remains `skill-creator`.

## Obra `writing-skills`

- Source repository: [obra/superpowers](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
- Source skill: [writing-skills/SKILL.md](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-skills/SKILL.md)
- Source commit: `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`
- License: MIT, from [the repository LICENSE](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/LICENSE)
- Copyright: Jesse Vincent, 2025.

Retained concepts include RED/GREEN/REFACTOR as a guidance model, baseline before
prescription, skill categories, pressure scenarios, rationalization capture, failure-shaped
guidance, wording microtests, discovery optimization, token discipline, and anti-pattern
review.

Intentionally excluded from the core are a universal failing-test-first gate, absolute
wording without an observed failure, upstream-specific paths and subagent APIs, deployment
advice, and persuasion techniques as a required authoring method.

## Local adaptation

The package is distributed under the repository's MIT license. `skill-crafting` adds an
overlap and need decision, an orchestration/workflow category, risk-based tiers, a
runtime-neutral fallback, explicit eval ownership, and a completion evidence matrix. The
repository-local `docs/evals/` protocol remains compatible with `skill-creator`.

