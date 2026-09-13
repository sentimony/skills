# Independence and Isolation

Detailed guidance for deciding whether work units may run at the same time. The main workflow
carries the summary; this file carries the checklists, the field lists, and the worked
contrasts.

## Per-pair independence checklist

Assess every candidate pair or group against each item. Absence of evidence is not evidence of
independence; an unexamined item is an open question, not a pass.

- **Dependencies.** Does either unit require the other to exist, run, or finish first?
- **Input dependencies.** Does either consume an artifact, value, or decision the other
  produces?
- **Output dependencies.** Does either produce something the other's correctness depends on?
- **Files and components touched.** Which paths, modules, and components does each expect to
  read and to change?
- **Interfaces consumed.** Which types, signatures, endpoints, and schemas does each rely on
  staying as they are?
- **Interfaces produced.** Which of those does each change, extend, or remove?
- **Shared state.** Which mutable state do both reach: databases, caches, fixtures, global
  configuration, singleton services?
- **External resources.** Which ports, accounts, sandboxes, queues, and third-party APIs do
  both touch?
- **Ordering constraints.** Does any correctness or safety property depend on one finishing
  before the other starts?

## Hidden dependencies

Filenames are the weakest signal available. These four patterns pass a filename check and
still couple the units:

- **Both edit a shared interface.** Two units extend the same type, endpoint, or protocol from
  different files. Each is locally coherent; together they produce a contract neither agent
  designed.
- **Both rely on an unchanged schema.** Neither unit edits the schema, and one of them changes
  behavior that only holds under the current shape of it.
- **Both assume the same generated artifact.** Client stubs, migration output, or compiled
  types regenerate under one unit and silently invalidate the other's assumptions.
- **One changes config the other consumes.** A feature flag, environment default, or build
  setting moves under one unit while the other's evidence was gathered under the old value.

## Mutation map fields

Record for each work unit before any mutating wave:

```text
files/directories expected to change
shared interfaces
generated artifacts
database/schema
ports/services
caches
temporary directories
external APIs/accounts
branch/workspace
```

### Worked example: disjoint files, shared database

```text
Agent A
files: src/auth/*
runtime: test DB
port: none

Agent B
files: src/catalog/*
runtime: same test DB
port: none
```

The file scopes do not intersect. The runtime does. Either unit can leave the database in a
state that invalidates the other's test evidence, and neither will produce a merge conflict
while doing it.

```text
NOT safely parallel yet
```

The wave becomes safe when the database state is isolated per unit, or when both units are
converted to read-only work.

## Isolation equivalence

Name the four kinds separately and check each one:

- **Context isolation.** Each agent reasons from its own brief without inheriting the parent
  transcript.
- **Filesystem isolation.** Each agent writes into its own checkout or workspace.
- **Runtime isolation.** Each agent drives its own processes, ports, databases, and caches.
- **External-state isolation.** Each agent acts on its own accounts, sandboxes, and remote
  resources.

A separate agent context is not a separate mutable environment. Neither is a separate
worktree.

### What survives a worktree boundary

Separate worktrees of one repository still share:

```text
database
Redis
fixed TCP ports
Docker container names
external sandbox/account
package-manager cache
global temp state
browser profile
service worker state
filesystem outside repo
```

Before a mutating parallel wave, ask directly: is every mutable resource relevant to these
work units either independent, immutable, or isolated? Only filesystem isolation is visible in
`git worktree list`; the rest has to be established deliberately.

## Shared-state veto

These resources block parallel mutation when no safe isolation exists:

```text
single production-like DB
same migration history
same fixed-port dev server
same mutable fixture directory
same external test account
same local singleton service
```

Sequentialize the affected units. Do not invent a locking protocol inside a generic skill when
the project provides no supporting mechanism for it.

## Worked contrast: an evolving contract across different files

```text
Task A -> modify the User type
Task B -> implement the API consuming User
Task C -> update the UI consuming User
```

Three units, three disjoint file sets, one evolving contract. They are not independent. B and
C both encode assumptions about a type that A is still changing, so their local correctness
depends on a shape that does not exist yet.

```text
A
-> integration barrier
-> B + C potentially parallel
```

Once the shared contract is stable, the remaining two units are genuinely independent and the
wave is safe.

## Worked contrast: filesystem isolated, runtime unsafe

```text
Agent A worktree -> migration A -> localhost:5432 test DB
Agent B worktree -> migration B -> localhost:5432 same test DB
```

Git isolation exists. Runtime isolation does not. Two migrations against one database produce
a combined schema neither agent validated, and the worktree boundary hides none of it. Do not
dispatch both mutation paths until the database state is independently isolated.
