# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each heading ends with the repository release that shipped the version.

## [0.0.9] - 2026-11-12 - [0.0.104]

### Changed

- Bare `<sup>`, `<sub>`, `<kbd>` and `<br>` tags without attributes render as markup, as on
  GitHub, so version tags in `<sup>` look the same in the preview. Any other raw HTML,
  including these tags with attributes, is still displayed as text.
- Previews live at mirror paths, `<tmp>/doc-preview-<uid>/<repo>/<path from the repo root>.html`,
  with a root marker per repo folder; a folder whose marker names another root is cleared
  first.
- Relative `.md` links in a document open the linked file's preview: the renderer renders each
  linked file inside the repo too (depth 1) unless its preview is already fresh.
- Pages get a table of contents with working anchors, a footer with the repo, `docs/` and
  folder `README.md` previews, generated `_index.html` folder indexes, and a favicon that
  follows the dark color scheme.
- Table columns whose longest line is up to 48 characters no longer wrap; code and links
  in cells never wrap.
- Symlinks inside the repo are not followed: linked files, README files and folders reached
  through one are skipped (a symlinked `.md` still appears in its folder index as a raw
  link). Pages are never written through a symlink in the preview folder.
- Escaped pipes inside code in a table cell and a `<br>` in a cell render as on GitHub.

### Added

- `.json`, `.yaml`/`.yml`, `.toml`, `.csv` and `.txt` files, with numbered lines, JSON and
  TOML (Python 3.11+) parse errors, CSV tables, and a cut at 5000 CSV rows or 2 MB with a
  notice (a cut CSV shows only complete records). Any other extension exits with code 2.
- `highlight.js` 11.12.0 (`@highlightjs/cdn-assets`, pinned with a sha384 hash) on JSON, YAML
  and TOML pages; pages stay readable without it. Security Model and known limits updated.
- `test_formats.py` and browser checks covering the owner's request cases 1-11.

## [0.0.8] - 2026-11-07 - [0.0.102]

### Changed

- Renamed `scope-check` to `doc-preview`; invoke `/doc-preview <path>`. Only the name and
  its mentions changed.

## [0.0.7] - 2026-11-07 - [0.0.101]

### Changed

- Returned under the `scope-check` name as the full preview skill: `doc-preview` is removed
  in this release, and the rename of `scope-check` to `doc-preview` moves to the next release.
  Invoke `/scope-check <path>`.
- Previews any saved Markdown file, not only a request, spec or plan.

## [0.0.6] - 2026-11-05 - [0.0.100]

### Changed

- Renamed scope-check to doc-preview, added browser opening and accessible code copying,
  and supported explicit request previews and independent preview opt-outs.

## [0.0.5] - 2026-11-04 - [0.0.99]

### Changed

- The report line names the document kind (request, spec or plan), so a request is not
  taken for a spec and the next workflow step fits the actual document (`20261031-2038`).

## [0.0.4] - 2026-10-14 - [0.0.84]

### Changed

- **Breaking:** rewritten from scratch. `/scope-check` no longer runs `scope-triage`;
  it renders a saved spec or plan to an HTML preview in the OS temp directory, prints a
  clickable `file://` link, and adds the file to the folder `README.md` index when one
  exists. `scope-triage` and `plan-crafting` call it after writing and after each edit.

## [0.0.3] - 2026-10-12 - [0.0.82]

### Added

- `LICENSE` (MIT), this `CHANGELOG.md`, and `metadata.version` and `license` in the
  frontmatter, all removed in 0.0.73. The skill instructions are unchanged.

## [0.0.2] - 2026-10-09 - [0.0.73]

### Removed

- `license` from the frontmatter; the license lives in the skill's `LICENSE` file.
  The skill instructions are unchanged.
- `metadata.author` and `metadata.version` from the frontmatter: skills are no longer
  versioned individually, only repository releases are.

## [0.0.1] - 2026-10-01 - [0.0.61]

### Added

- Experimental user-invoked entry point: `/scope-check` hands the current request to the
  `scope-triage` skill.
