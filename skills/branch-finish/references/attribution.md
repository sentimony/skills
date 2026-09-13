# Attribution and Adaptation

This skill is an original compact workflow informed by branch completion, worktree usage, and
verification practices in [obra/superpowers](https://github.com/obra/superpowers). It is not a
copy of an upstream skill.

The upstream material was inspected at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`
(release `v6.3.0`, 2026-08-12):

- [finishing-a-development-branch](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/finishing-a-development-branch)
- [using-git-worktrees](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/using-git-worktrees)
- [verification-before-completion](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/verification-before-completion)

The local responsibility boundaries were checked against
[`verification-gate`](https://github.com/sentimony/skills/tree/main/skills/verification-gate),
[`workspace-isolation`](https://github.com/sentimony/skills/tree/main/skills/workspace-isolation),
and [`review-resolution`](https://github.com/sentimony/skills/tree/main/skills/review-resolution).

## Retained mechanisms

- read-only environment detection before any option is presented;
- capturing the workspace path before any change of directory, because cleanup runs from
  outside the workspace;
- the normal checkout versus linked worktree distinction as the key to cleanup, with the
  submodule guard that keeps a submodule from being mistaken for a worktree;
- detached HEAD as a first-class state with a reduced option set;
- the owned versus externally owned workspace distinction;
- respecting a refused worktree removal rather than forcing past it;
- protecting untracked and uncommitted files with the same weight as tracked work;
- preserving the workspace on the pull request path, because review feedback is iterated there;
- stopping on a failing post-integration result and keeping the source as the recovery path;
- explicit confirmation with an impact summary before any discard.

## Deliberate divergences

- **Verification is delegated entirely to `verification-gate`.** Upstream runs the project test
  suite inline as its first step and again after merging. That standard is both too weak, since
  a green suite says nothing about typecheck, build, lint, or requirement coverage, and too
  strong, since it mandates the full suite where scoped equivalent evidence exists. This skill
  consumes one of four verdict values and defines none of them.
- **Verdict invalidation is general rather than a single hardcoded re-run.** Merge, rebase,
  conflict resolution, cherry-pick, manual integration edit, and dependency regeneration each
  produce a tree the prior verdict does not describe.
- **The base branch is resolved by a six-level evidence precedence** rather than taken from one
  weak source with a confirming question. Ambiguity forbids automatic merge instead of prompting
  a guess.
- **Ownership uses the six values `workspace-isolation` already emits.** Upstream infers
  ownership from whether the path sits under `.worktrees/` or `worktrees/`. A path is not
  provenance, and the inference fails precisely on a worktree someone else created at a familiar
  location.
- **Cleanup authority is restricted to `SKILL_OWNED`,** with `UNKNOWN` preserving, and workspace
  removal is separated from branch deletion so that each answers to its own gate.
- **Finish options are filtered by detected environment capability.** Upstream presents a fixed
  three-option menu; this skill offers four options and withholds any the environment does not
  permit, stating why.
- **Outcomes have a fixed vocabulary of seven labels,** so a successful integration with a
  refused cleanup has a name. Upstream leaves that combination unnamed.
- **No remote, branch, or forge name is assumed.** Upstream hardcodes `origin` in its push
  command and runs `git pull` automatically before merging; neither happens here.
- **Merge conflicts are classified `MECHANICAL` or `SEMANTIC`,** and a semantic conflict is
  never presented as a mechanical Git task.

## Intentionally excluded

- running the project test suite as this skill's own first step;
- the fixed three-option menu and its detached-HEAD two-option variant;
- path-based ownership inference from `.worktrees/` or `worktrees/`;
- the automatic `git pull` before merge;
- project setup and dependency installation, which belong to workspace creation;
- a persistent state directory under any name.

The upstream project is licensed under MIT. This skill is distributed under the repository's MIT
license with attribution retained here.
