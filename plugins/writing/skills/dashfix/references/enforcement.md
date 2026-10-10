# Agent hook enforcement

The `commit-msg` hook in `SKILL.md`, Enforcement, rejects a commit message with a banned
dash while `git commit` runs. Stop the same mistake before the tool call by adding a
`PreToolUse` matcher to `.claude/settings.json`. It reads the hook payload with perl alone,
since a `jq` pipeline exits 0 on a machine without `jq` and lets the commit through in
silence:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "perl -CSD -0777 -ne 'exit 0 unless /git\\s+commit/; exit 0 unless /[\\x{2010}-\\x{2015}\\x{2212}]|\\\\u(?:201[0-5]|2212)/i; print STDERR \"dashfix: typographic dash in the commit command; use the plain hyphen\\n\"; exit 2'"
          }
        ]
      }
    ]
  }
}
```
