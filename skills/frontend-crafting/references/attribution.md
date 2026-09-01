# Attribution

Maintainer-facing. This file is not part of the skill's runtime routing and is never loaded by an
agent using the skill.

frontend-crafting is an original work informed by four upstream skills. No substantial verbatim text
was copied from any of them; every rule is written in this skill's own words. The technical layer
in `references/quality-gate.md` mostly restates WCAG 2.2, the WAI-ARIA Authoring Practices, and
documented platform behavior on MDN, which are the primary sources for those requirements.

## Upstream sources

| Skill | Repository | License | Commit studied |
|---|---|---|---|
| `frontend-design` | https://github.com/anthropics/skills | Apache-2.0, Anthropic, PBC | 3b3fad96af16a10759d930941b4520ba0c40edae |
| `design-taste-frontend` | https://github.com/leonxlnx/taste-skill | MIT, Copyright (c) 2026 Leonxlnx | ccbc15639c97057cbfcf32ecebc38ef716e4bb37 |
| `web-design-guidelines` | https://github.com/vercel-labs/agent-skills | MIT, declared in README | 063bee94c3f4df8453406c830b0a7df0f2860278 |
| Web Interface Guidelines | https://github.com/vercel-labs/web-interface-guidelines | MIT, Copyright (c) 2025 Vercel Labs | e3d624baaf29dc1fc645aff3e38f03e564d2d6b1 |
| `impeccable` | https://github.com/pbakaus/impeccable | Apache-2.0 | e92bf2b774fc5d28175e35273677929228a50787 |

Vercel appears twice because the skill and the rules live in separate repositories: the
`web-design-guidelines` skill mostly fetches rules at runtime, while the rules themselves live in
`web-interface-guidelines`. The Vercel rules studied for this skill come from the second
repository.

## What was taken conceptually, from each

**Anthropic `frontend-design`** contributed the design-philosophy layer: designing from the actual
subject rather than from a library of moves, the brief taking precedence over the skill's own
defaults, the principle that structure must communicate real information, restraint around a
single signature idea, and the plan-critique-build-critique cycle.

**leonxlnx `design-taste-frontend`** contributed the operational heuristics: explicit brief
inference from named signals, the one-line design read, the distinction between greenfield,
preserving redesign, and replacing redesign, the audit-before-touching protocol including the
search baseline, the list of things that never change silently, modernization levers ordered by
risk, the requirement that motion be motivated, and the copy self-audit.

**Vercel** contributed the structure of the technical layer and the MUST/SHOULD gradation, along
with the finding format that cites file and line. The underlying requirements come from WCAG,
WAI-ARIA, and MDN rather than from Vercel; what was adopted is the organization and the
enumeration of cases worth checking.

**pbakaus `impeccable`** contributed the architecture: progressive disclosure through a thin
router, the four surface modes, separating visual critique from technical audit, P0-P3 severity
with definitions, bounded visual verification, the reusable craft floor loaded before editing, the
drift classification, the triage order for refinement, and the framing of category defaults as
things a brief can earn back.

## Adaptation

Three of the four sources were adapted rather than adopted. Notably, this skill drops the lists of
banned fonts, banned colors, numeric thresholds on subjective scales, framework-specific and
package-specific prescriptions, copy-style preferences belonging to one brand or one locale, and
mandatory theming requirements. It replaces them with mechanisms: an anti-default self-check
instead of a list of banned defaults, and diagnostics in the format default, rationale, legitimate
exceptions instead of aesthetic bans. It also vendors its technical rules rather than fetching
them at runtime, so a pinned version of the skill has pinned behavior.

The full analysis, including the keep/modify/drop decision for every rule and the resolution of
eleven contradictions between the sources, lives at
https://github.com/sentimony/skills-aiassist/blob/main/docs/researches/2026-09-01-frontend-craft-synthesis.md.

## License

frontend-crafting is licensed Apache-2.0, matching both Apache-licensed sources; the MIT-licensed
sources are compatible with that choice. Because no substantial portion of any source is
reproduced, no source license's copying conditions are triggered.

**No NOTICE file is required.** Apache-2.0 section 4(d) applies only when the upstream work
carries a NOTICE file. The Anthropic skill has none in its directory. The impeccable repository
does have a `NOTICE.md`, but it covers that project's `ios.md` and `android.md` reference files,
which are distilled from ehmo's `platform-design-skills` (MIT,
https://github.com/ehmo/platform-design-skills). frontend-crafting is web-oriented and uses neither
file, so that attribution chain does not extend to it. This decision is revisited if a verbatim
fragment from any Apache-licensed source is ever brought in, since the section 4(d) obligation
would arrive with it.
