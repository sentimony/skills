# Nuxt Audit Ownership

Nuxt solution configs are generated artifacts. Use their compiler output as audit
evidence, but do not edit them or run a generator implicitly.

| Generated config | Nuxt configuration owner |
| --- | --- |
| `.nuxt/tsconfig.app.json` | `typescript.tsConfig` |
| `.nuxt/tsconfig.node.json` | `typescript.nodeTsConfig` |
| `.nuxt/tsconfig.shared.json` | `typescript.sharedTsConfig` |
| `.nuxt/tsconfig.server.json` | `nitro.typescript.tsConfig` |

When `.nuxt` is absent, report `NUXT_GENERATED_CONFIGS_MISSING`. Ask the user to run
the project’s documented prepare command and rerun the audit. The skill must not run
prepare itself: generation can execute project hooks and change the working tree.

For an audit, inspect each existing generated program with its local checker: `vue-tsc`
for app and `tsc` for server, shared, and node. Compare only normalized repo-owned
paths internally. Report per-program effective flags and covered/uncovered counts for
production, tests, and config files; do not expose raw compiler output or file lists.
