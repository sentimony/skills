# Project rule snippet

Offer this snippet for the project's AGENTS.md (or the file it imports). Add it only after the
user explicitly agrees; installing the skill never changes project context by itself.

```markdown
## Credentials

- Never print, echo, log, or read out credential values; check keys by name only.
- Use credentials inside a process (a project helper), never on the command line.
- Before any credential work, load the `secret-hygiene` skill.
```
