# Attribution

The relation-based replacement, the minimal-rewrite rule, and the preservation check,
part of dashfix since 1.3.0, adapt ideas from humanizer by blader
(https://github.com/blader/humanizer), commit 9862685f575c65a8247f90369951df1b3416e3d6,
released under the MIT License:

- section 8, "Dashes as the universal connector": a dash lets the writer skip choosing how
  two clauses relate; replace it with a period, comma, colon, or parentheses, or rewrite
  the sentence;
- "How to work", steps 2 and 3: keep every supported claim and check that a rewrite
  neither adds nor drops a fact, name, number, date, quote, or citation.

No text or code is copied. dashfix keeps its own policy where humanizer differs: it judges
every occurrence under the project and language rules rather than by dash frequency, and a
writer's dash habit does not override an explicit style rule.
