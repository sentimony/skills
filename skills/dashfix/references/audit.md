# Audit

The full audit procedure. Read it before the first command of an audit. Banned
characters, replacement, preservation check, verdicts, and enforcement stay in
`SKILL.md`; this file uses them and does not repeat them.

## Step 1 - Inventory

Working tree:

```bash
rg -nP --no-heading '[\x{2010}-\x{2015}\x{2212}]' \
  --glob '!package-lock.json' --glob '!*.min.*' --glob '!*.map' .
```

The trailing `.` is what keeps the scan honest: handed a piped stdin and no path, `rg`
reads that pipe instead of the tree and reports zero matches on a project full of them.

The audit covers the working tree only, not commit messages already in history: fixing
those needs a history rewrite, which is outside this skill, so counting them only adds
noise to the report. The hook in Enforcement keeps new ones clean.

`rg` skips `.git`, binary files, and everything in `.gitignore` by default. Add two
classes of exclusion yourself instead of copying a fixed list: everything generated
(lock files, minified bundles, source maps, snapshots, coverage output, generated
changelogs) and every file whose text is data rather than prose (fixtures, seed
databases, catalogs of titles and track names). Name each exclusion you added in the
report.

BSD `grep` on macOS has no `-P`, so `grep -rnP` fails there even though the same command
works inside an agent session that aliases `grep` to `ugrep`. Use GNU grep as `ggrep -rnP`,
or this fallback, which needs only perl:

```bash
git ls-files -z --cached --others --exclude-standard \
    ':!:package-lock.json' ':!:**/package-lock.json' \
    ':!:*.min.*' ':!:**/*.min.*' ':!:*.map' ':!:**/*.map' \
    ':!:.*' ':!:**/.*' |
  xargs -0 perl -CSD -0777 -ne 'next if -l $ARGV || /\0/;
    my $n = 0;
    for my $line (split /^/) {
      $n++;
      print "$ARGV:$n: $line" if $line =~ /[\x{2010}-\x{2015}\x{2212}]/;
    }' --
```

Every part of it exists to match what `rg` scans, because a fallback that reads a
different set of files reports different counts:

- `--others --exclude-standard` adds the untracked files that `rg` reads and still honors
  `.gitignore`; plain `git ls-files` sees only tracked files.
- Each exclusion appears twice, bare and with `**/`. A git pathspec is not a gitignore
  pattern: `**/package-lock.json` reaches the nested copies and leaves the one in the
  root, while an `rg` glob without a slash catches both.
- `':!:.*' ':!:**/.*'` drop hidden paths, which `rg` skips by default. To audit them,
  give `rg` its `--hidden` flag and drop these two pathspecs together.
- `next if -l $ARGV` skips symlinks, which `rg` follows only under `--follow`; without
  it a link and its target both reach the catalog and the same text is counted twice. To
  audit them, give `rg` its `--follow` flag and drop this test together.
- `next if /\0/` skips a file holding a NUL byte, which is the rule `rg` uses to call a
  file binary.
- Slurping with `-0777` and counting lines per file keeps the numbering right; with `-n`
  the counter `$.` runs on across the whole list and every line number after the first
  file points at the wrong line.
- The trailing `--` stops perl from reading a path such as `-weird.md` as its own
  switches and dying.

Treat the result as best effort even so, because two kinds of files still make the two
passes differ, and both are cheap to spot:

- A file whose bytes are not valid UTF-8 though it holds no NUL. `rg` skips it, perl
  reads it, and its catalog row shows replacement characters in the snippet.
- A file that `.gitignore` covers but that someone force-added with `git add -f`. `rg`
  goes by the ignore rules alone and skips it; `--exclude-standard` keeps it because it
  is in the index. `git ls-files --cached --ignored --exclude-standard` lists exactly
  these paths.

Drop the rows that come from either kind before counting, and say in the report that you
did.

Both commands print one line per matching line, so a line holding two dashes shows up
once. Take the occurrence total from a counting pass instead, and reconcile it with the
catalog:

```bash
rg -P --count-matches '[\x{2010}-\x{2015}\x{2212}]' \
  --glob '!package-lock.json' --glob '!*.min.*' --glob '!*.map' .
```

Report that total; the catalog must account for every occurrence in it. The total
counts every dash other than `-`, and the catalog decides how each one is fixed.

## Step 2 - Catalog

Start with one line that gives the occurrence total from the counting pass. Then one
table, grouped by file, one row per matching line. Show each character next to the
hyphen in the Char column, since `—` and `-` look alike in a terminal. The Reason column
gives the fix for a `replace` row (` - `, or the relation and its punctuation, see
Replacement) and the verdict with its cause for any other row. For a minimal rewrite the
reason carries the proposed sentence, so the user approves the actual text. When a line
holds more than one occurrence, say how many in the row. When their verdicts differ,
split the line into a row per occurrence and number them in reading order,
`<file>:<line>#<n>`, so no two rows share a key:

| Location | Snippet | Char | Reason |
| --- | --- | --- | --- |
| `docs/intro.md:12` | `fast — and safe` | `—` U+2014 vs `-` | ` - `, or commas (aside) |
| `docs/огляд.md:4` | `Один файл — одна сесія` | `—` U+2014 vs `-` | ` - ` |
| `docs/api.md:31` | `a — b – c` | `—` U+2014, `–` U+2013 vs `-` | 2 occurrences, ` - ` each |
| `docs/notes.md:8` | `pages 12–18` | `–` U+2013 vs `-` | range, `12-18` |
| `tests/format.test.ts:44` | `expect(out).toBe("a — b")` | `—` U+2014 vs `-` | data: expected output; fix with the formatter or leave |
| `STYLE.md:9` | `never write — in prose` | `—` U+2014 vs `-` | justified: the text is about the character |

Rows with the same snippet shape and the same fix may collapse into one row with their
locations listed, across files as well as within one.

## Step 3 - Report

Deliver in one message: the inventory commands and the occurrence total, the catalog,
and below it one summary line, "X to fix in Y files", with the `data` and `justified`
counts named beside it. Add the excluded paths and the files with the most occurrences.
Offer a fix pass; apply it only when the user asks.

Close with one line on the commit-msg hook for every audited repository that lacks it
(see Enforcement for how to check): it can be installed there so new commit messages stay
clean. Install it only when the user asks, as with fix mode.

## Fix mode details

Apply the fix from every `replace` row, run the preservation check on every fix that
adds, moves, or removes a word, leave `justified` rows untouched, and change a `data` row
only together with the code and tests that read it. Re-run the inventory and report
"Fixed in X places in Y files", with what is left and why.
