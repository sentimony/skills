# Audit Reference

## Nuxt generated-program ownership

Nuxt solution configs are generated artifacts. Use their compiler output as audit
evidence, but do not edit them or run a generator implicitly.

| Generated config | Nuxt configuration owner |
| --- | --- |
| `.nuxt/tsconfig.app.json` | `typescript.tsConfig` |
| `.nuxt/tsconfig.node.json` | `typescript.nodeTsConfig` |
| `.nuxt/tsconfig.shared.json` | `typescript.sharedTsConfig` |
| `.nuxt/tsconfig.server.json` | `nitro.typescript.tsConfig` |

The Nuxt app program includes `server/**`, so its diagnostics are a superset of the
server program's. Never add per-program diagnostic counts: deduplicate by
`file:line:code` before reporting a trial-flag total, for example
`cat app.txt server.txt | rg -o '^[^(]+\(\d+,\d+\): error TS\d+' | sort -u | wc -l`.

When `.nuxt` is absent, report `NUXT_GENERATED_CONFIGS_MISSING`. Ask the user to run
the project’s documented prepare command and rerun the audit. The skill must not run
prepare itself: generation can execute project hooks and change the working tree.

When some generated configs exist and others do not, the state is
`NUXT_GENERATED_CONFIG_PARTIAL`, not a missing `.nuxt`: prepare has already run and this
Nuxt version simply does not generate every program. Audit the programs that exist, name
the absent ones as an explicit coverage gap, and do not ask for another prepare run.

A `*_LOCAL_COMPILER_UNAVAILABLE` diagnostic in a project without a `.git` directory
(an unpacked archive, a vendored copy) usually means the compiler is hoisted above the
inspected directory: the lookup only walks up inside a repository, so rerun with `--root`
at the workspace root instead of the package directory.

For an audit, inspect each existing generated program with its local checker: `vue-tsc`
for app and `tsc` for server, shared, and node. Compare only normalized repo-owned
paths internally. Report per-program effective flags and covered/uncovered counts for
production, tests, and config files; do not expose raw compiler output or file lists.
If any local compiler is unavailable or exits nonzero, retain every reported program identity
and their safe effective flags, report a stable diagnostic, and leave aggregate coverage
unavailable. Partial compiler output is not evidence for exact coverage.

## Uncovered tests: dry run

When the inspector reports uncovered test files, do not stop at the count. Create a
temporary config in an ignored directory of the project (for example
`test-results/tsconfig.tests.json`) that extends the generated app program and includes
the test globs; paths are relative to that file:

```json
{ "extends": "../.nuxt/tsconfig.app.json",
  "include": ["../tests/**/*.ts", "../vitest.config.ts"] }
```

run `npx vue-tsc --noEmit -p <that file>`, report the diagnostic count and the files,
then delete the config. The generated app program has `allowJs`, so `.mjs` imports are
typed and an old `@ts-expect-error` on them now reports TS2578 (unused directive): count
those as stale suppressions, not as new errors.

A standalone `tsconfig.*.json` that `extends` a generated Nuxt program and includes test
or edge-function files (for example `tsconfig.tests.json`, `netlify/tsconfig.json`) is a
companion program the inspector does not see: run its checker directly, report its file
count as covered by that program, and name it in the coverage section instead of leaving
the category at zero.

## Counting non-null assertions

Grep (any project): `rg -nP '(?<=[\w\)\]])!(?!=)' --type ts --type vue` counts the
postfix operator (a `!` right after an identifier, `)` or `]`) and excludes `!=`/`!==`
and prefix negation (`!ok`, `!!flag`); in `.vue` files drop matches inside
`class="..."`, where Tailwind's `!` important suffix looks identical. Report the count
with the command.

ESLint (projects with typescript-eslint): a temporary flat config outside the repository
tree that appends `{ rules: { '@typescript-eslint/no-non-null-assertion': 'error' } }`
to the project's exported config, run with `--no-config-lookup --format json` over the
production and test roots, gives a per-file count that survives multi-line expressions.
Delete the config afterwards.

## Repeat audits

When the repository holds a previous audit of the same subject, the report opens with a
status table for its findings, before any new finding:

| ID | Finding (one line) | Status | Verified at |
|---|---|---|---|

`Status` is exactly one of `closed`, `partial`, `open`. `Verified at` is the primary
source that proves the status (`path/to/file:line`, a command and its result, or a page
and observation), never the previous report itself. A `partial` row carries one sentence
saying what remains. An `open` row links to the new finding that continues it and does
not repeat its text. A finding closed by a previous audit is not re-reported as new.

Re-audit: when a previous audit of the same subject exists, a section may be inherited
by reference to the previous report instead of repeated, but only when the change set
since the previous base contains none of that section's inputs. Inputs are defined by
content, not by file name: the section lists the patterns it depends on, and the check
is run on both added and removed lines of the diff (`git diff <base> -- <paths> | rg
'^[+-]' | rg <pattern>`), because a deleted escaping, registration, or cleanup line is
as much a change as an added one. The check also covers the lockfile entries of the
packages the section relies on and every file the section depended on: any change to a
file it counted, a setup or helper file it read, or a mock or test file it sampled,
including a deletion, invalidates the section, since a changed helper body or an edited
existing test alters behavior without touching the pattern list or the config. A file
list alone (`git diff --name-only`) does not prove an input unchanged. When the inputs
of a section cannot be named, or the check is inconclusive, the section is re-measured.
Sections that measure runtime behavior (timings, browser evidence, coverage numbers) are
always re-measured. Sampling for a repeated class of finding is taken from files changed
since the previous base plus the two largest hotspots; the full-sample rule applies only
to a first audit or when the previous report is older than the project's release cadence.
The report names which sections were inherited, the inputs checked for each, which were
re-measured, and the base commit of the previous audit.

For this skill the inherited sections are the ownership mapping and the effective-flags
table: they may be carried over when the diff since the previous base changes no
`tsconfig*.json`, no `nuxt.config.*`, and no lockfile entry of `typescript`, `vue-tsc`,
or the framework packages. Coverage counts, diagnostic totals, and any timing from
`trace_perf.py` are re-measured every time. The delta sampling rule replaces the 10-15%
sample of step 4 in SKILL.md for a repeat audit: sample the files changed since the
previous base plus the two largest hotspots.

Every number in the report is produced by a tool that survives line wrapping and the
active shell: multi-line tags and calls are counted with a multiline-aware matcher
(`rg -U`, `perl -0777`), not `grep -c`; non-ASCII text is matched with a tool that
handles Unicode (`rg`, `perl -CSD`), and `type grep` is checked once per session because
a wrapper can change `--include` semantics. Every zero is confirmed by a control query on
the same files that must return a non-zero (for instance `<template>` or `import`); a
zero without a control does not enter the baseline. Locations cite line numbers read from
numbered output (`cat -n`, `rg -n`), never estimated from an unnumbered read. Counts from
a delegated search are re-measured before they appear in the report.
