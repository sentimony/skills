# Attribution

This skill is an original work. Version 1.3.0 adapts three ideas from the MIT-licensed
[blader/humanizer](https://github.com/blader/humanizer/blob/9862685f575c65a8247f90369951df1b3416e3d6/SKILL.md)
skill as inspected at commit `9862685` (2026-09-06): the split-across-sentences form and
the clipped negative tail from its pattern 1 ("Not X but Y"), the "keep a contrast only
when both halves carry information" criterion from the same pattern, and the
"objection nobody raised" criterion from its pattern 5 ("Arguing with no one").

The adaptation keeps negafix narrow: the split form joins the scored catalog as a
contextual pattern, the reversed contrast, the unsupported objection, and the clipped
tail are exploratory signals outside the score, and the information-gain criterion is
expressed as a verdict procedure feeding the existing four verdicts. Voice matching,
vocabulary lists, AI-likeness scoring, and the other humanizer patterns are
intentionally not included. No upstream text is reproduced. The public skill is
distributed under the MIT license; upstream copyright is acknowledged here.
