"""Standalone tests for doc-preview render.py."""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render  # noqa: E402

SPEC = """# Specification: preview

Text with </script> inside and <img src=x onerror=alert(1)> raw HTML.

- [x] done
- [ ] open

```mermaid
flowchart LR
  A --> B
```
"""


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "work" / "demo-repo"
        (self.repo / ".git").mkdir(parents=True)
        self.spec = self.repo / "docs" / "specs" / "20261014-0115-demo.md"
        self.spec.parent.mkdir(parents=True)
        self.spec.write_text(SPEC, encoding="utf-8")
        self.out = self.root / "tmp"

    def tearDown(self):
        self.tmp.cleanup()

    def test_stable_path_mirrors_repo_relative_path(self):
        path = render.html_path(self.spec, self.out)
        self.assertEqual(
            path,
            render.preview_root(self.out) / "demo-repo" / "docs" / "specs" / "20261014-0115-demo.html",
        )
        self.assertEqual(path, render.html_path(self.spec, self.out))

    def test_path_without_git_uses_parent_dir_as_root(self):
        loose = self.root / "loose" / "plans" / "plan.md"
        loose.parent.mkdir(parents=True)
        loose.write_text("# Plan\n", encoding="utf-8")
        self.assertEqual(
            render.html_path(loose, self.out),
            render.preview_root(self.out) / "plans" / "plan.html",
        )

    def test_non_markdown_name_keeps_full_extension(self):
        data = self.repo / "data" / "x.json"
        self.assertEqual(render.html_path(data, self.out).name, "x.json.html")

    def test_marker_mismatch_clears_repo_dir(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
        stale = render.preview_root(self.out) / "demo-repo" / "stale.html"
        stale.write_text("old", encoding="utf-8")
        other = self.root / "elsewhere" / "demo-repo"
        (other / ".git").mkdir(parents=True)
        note = other / "note.md"
        note.write_text("# Note\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render.main([str(note)], tmp_root=self.out), 0)
        self.assertFalse(stale.exists())
        self.assertTrue(render.html_path(note, self.out).exists())
        self.assertFalse(render.html_path(self.spec, self.out).exists())

    def test_same_root_keeps_other_pages(self):
        other = self.repo / "docs" / "plans" / "p.md"
        other.parent.mkdir(parents=True)
        other.write_text("# P\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            render.main([str(self.spec)], tmp_root=self.out)
            render.main([str(other)], tmp_root=self.out)
        self.assertTrue(render.html_path(self.spec, self.out).exists())
        self.assertTrue(render.html_path(other, self.out).exists())

    def test_legacy_dir_without_marker_is_cleared(self):
        legacy = render.preview_root(self.out) / "demo-repo" / "specs" / "old-0123.html"
        legacy.parent.mkdir(parents=True)
        render.preview_root(self.out).chmod(0o700)
        legacy.write_text("old", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            render.main([str(self.spec)], tmp_root=self.out)
        self.assertFalse(legacy.exists())
        self.assertTrue(render.html_path(self.spec, self.out).exists())

    def test_label_edge_cases(self):
        self.assertEqual(render.repo_label(Path("/")), "root")
        self.assertEqual(render.repo_label(Path("/a/b")), "b")
        self.assertEqual(render.repo_label(Path(".")), "root")
        self.assertEqual(render.repo_label(Path("..")), "root")

    def test_claim_refuses_symlinked_repo_dir(self):
        proot = render.preview_root(self.out)
        proot.mkdir(parents=True, mode=0o700)
        victim = self.root / "victim"
        victim.mkdir()
        keep = victim / "keep.txt"
        keep.write_text("keep", encoding="utf-8")
        (proot / "demo-repo").symlink_to(victim, target_is_directory=True)
        with self.assertRaises(OSError):
            render.claim_repo_dir(proot / "demo-repo", self.repo, proot)
        self.assertTrue(keep.exists())

    def test_claim_refuses_path_outside_preview_root(self):
        proot = render.preview_root(self.out)
        proot.mkdir(parents=True, mode=0o700)
        outside = self.root / "outside"
        outside.mkdir()
        keep = outside / "keep.txt"
        keep.write_text("keep", encoding="utf-8")
        with self.assertRaises(OSError):
            render.claim_repo_dir(outside, self.repo, proot)
        nested = proot / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(OSError):
            render.claim_repo_dir(nested, self.repo, proot)
        self.assertTrue(keep.exists())
        self.assertTrue((nested / "keep.txt").exists())

    def test_claim_refuses_symlink_to_dir_with_matching_marker(self):
        proot = render.preview_root(self.out)
        proot.mkdir(parents=True, mode=0o700)
        victim = self.root / "victim"
        victim.mkdir()
        (victim / render.ROOT_MARKER).write_text(str(self.repo.resolve()), encoding="utf-8")
        (proot / "demo-repo").symlink_to(victim, target_is_directory=True)
        with self.assertRaises(OSError):
            render.claim_repo_dir(proot / "demo-repo", self.repo, proot)
        self.assertEqual(sorted(p.name for p in victim.iterdir()), [render.ROOT_MARKER])

    def test_claim_refuses_lookalike_preview_dir_elsewhere(self):
        proot = render.preview_root(self.out)
        proot.mkdir(parents=True, mode=0o700)
        fake = self.root / "doc-preview-x" / "y"
        fake.mkdir(parents=True)
        (fake / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(OSError):
            render.claim_repo_dir(fake, self.repo, proot)
        self.assertTrue((fake / "keep.txt").exists())

    def test_claim_clears_dir_without_marker_and_writes_marker(self):
        proot = render.preview_root(self.out)
        repo_dir = proot / "demo-repo"
        repo_dir.mkdir(parents=True)
        (repo_dir / "old.html").write_text("old", encoding="utf-8")
        render.claim_repo_dir(repo_dir, self.repo, proot)
        self.assertFalse((repo_dir / "old.html").exists())
        marker = repo_dir / render.ROOT_MARKER
        self.assertEqual(marker.read_text(encoding="utf-8"), str(self.repo.resolve()))

    def test_same_filename_in_different_folders_has_independent_previews(self):
        other = self.repo / "archive" / "specs" / self.spec.name
        other.parent.mkdir(parents=True)
        other.write_text("# Other", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
            self.assertEqual(render.main([str(other)], tmp_root=self.out), 0)
        first = render.html_path(self.spec, self.out)
        second = render.html_path(other, self.out)
        self.assertNotEqual(first, second)
        self.assertIn("Specification: preview", first.read_text(encoding="utf-8"))
        self.assertIn("# Other", second.read_text(encoding="utf-8"))

    def test_untrusted_symlink_at_output_root_is_rejected(self):
        self.out.mkdir()
        victim = self.root / "victim"
        victim.mkdir()
        render.preview_root(self.out).symlink_to(victim, target_is_directory=True)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertNotEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
        self.assertEqual(list(victim.iterdir()), [])

    @unittest.skipUnless(hasattr(os, "getuid"), "POSIX permissions required")
    def test_shared_preview_root_is_rejected(self):
        root = render.preview_root(self.out)
        root.mkdir(parents=True)
        root.chmod(0o755)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertNotEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
        self.assertEqual(list(root.iterdir()), [])

    def test_target_symlink_does_not_overwrite_its_destination(self):
        target = render.html_path(self.spec, self.out)
        render.preview_root(self.out).mkdir(parents=True, mode=0o700)
        target.parent.mkdir(parents=True)
        victim = self.root / "victim.txt"
        victim.write_text("original", encoding="utf-8")
        target.symlink_to(victim)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
        self.assertEqual(victim.read_text(encoding="utf-8"), "original")

    def test_script_close_and_raw_html_stay_inert(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        body = page.split('<script type="application/json" id="source">', 1)[1]
        payload = body.split("</script>", 1)[0]
        self.assertNotIn("</script>", payload)
        self.assertNotIn("<img", payload)
        self.assertIn("\\u003c/script\\u003e", payload)

    def test_cdn_scripts_are_pinned_with_sri(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        for url, sri in ((render.MARKED_URL, render.MARKED_SRI), (render.MERMAID_URL, render.MERMAID_SRI)):
            self.assertTrue(sri.startswith("sha384-"))
            self.assertIn(
                f'<script src="{url}" integrity="{sri}" crossorigin="anonymous"></script>', page
            )
        self.assertIn("marked@18.1.1/", render.MARKED_URL)
        self.assertIn("mermaid@12.2.0/", render.MERMAID_URL)
        # highlight.js loads only on json, yaml and toml pages, never on Markdown.
        self.assertNotIn(render.HIGHLIGHT_URL, page)
        self.assertTrue(render.HIGHLIGHT_SRI.startswith("sha384-"))
        self.assertIn("highlightjs/cdn-assets@11.12.0/", render.HIGHLIGHT_URL)
        data_page = render.render_html("{}", self.spec.with_suffix(".json"), "2026-10-14 01:23", fmt="json")
        self.assertIn(
            f'<script src="{render.HIGHLIGHT_URL}" integrity="{render.HIGHLIGHT_SRI}" crossorigin="anonymous"></script>',
            data_page,
        )

    def test_page_guards_raw_html_and_unsafe_urls(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        self.assertIn("html(token)", page)
        self.assertIn("/^<\\/?(sup|sub|kbd)>$|^<br\\s*\\/?>$/i.test(tag)", page)
        self.assertIn("return escapeHtml(token.text);", page)
        self.assertIn("safeUrl(", page)
        for scheme in ('"http:"', '"https:"', '"mailto:"'):
            self.assertIn(scheme, page)

    def test_page_keeps_short_table_columns_on_one_line(self):
        self.assertEqual(render.NOWRAP_COLUMN_CHARS, 48)
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        self.assertIn("td code, td a, th { white-space: nowrap; }", page)
        self.assertIn(".nowrap { white-space: nowrap; }", page)
        self.assertIn("nowrapChars", page)
        body = page.split('<script type="application/json" id="model">', 1)[1]
        model = json.loads(body.split("</script>", 1)[0])
        self.assertEqual(model["nowrapChars"], render.NOWRAP_COLUMN_CHARS)

    def test_relative_urls_resolve_against_source_dir(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        body = page.split('<script type="application/json" id="base">', 1)[1]
        payload = body.split("</script>", 1)[0]
        self.assertEqual(json.loads(payload), self.spec.parent.as_uri() + "/")
        self.assertIn('getElementById("base")', page)

    def test_page_has_strict_mermaid_and_offline_fallback(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        self.assertIn('securityLevel: "strict"', page)
        self.assertIn("startOnLoad: false", page)
        self.assertIn('<pre id="fallback">', page)
        self.assertIn(str(self.spec), page)
        self.assertIn("2026-10-14 01:23", page)

    def test_main_writes_overwrites_and_prints_same_uri(self):
        target = render.html_path(self.spec, self.out)
        outputs = []
        for text in ("# First\n", "# Second\n"):
            self.spec.write_text(text, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = render.main([str(self.spec)], tmp_root=self.out)
            self.assertEqual(code, 0)
            outputs.append(buf.getvalue().strip())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], target.as_uri())
        self.assertIn("Second", target.read_text(encoding="utf-8"))
        self.assertNotIn("First", target.read_text(encoding="utf-8"))

    def test_page_has_inline_svg_favicon_with_dark_rule(self):
        import re
        import urllib.parse

        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        match = re.search(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml,([^"]+)">', page)
        self.assertIsNotNone(match)
        svg = urllib.parse.unquote(match.group(1))
        self.assertEqual(svg.count("<path "), 27)
        self.assertIn('stroke="currentColor"', svg)
        self.assertIn("prefers-color-scheme: dark", svg)
        self.assertIn('<path d="M10.5 14 L10.5 20" />', svg)
        self.assertIn('<path d="M6.5 8 L6.5 6" />', svg)

    def test_page_has_toc_slug_script_and_reserved_ids(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        self.assertIn('<nav id="toc" aria-label="Contents" hidden></nav>', page)
        self.assertIn("function slugify", page)
        self.assertIn('["content", "source", "base", "model", "fallback", "toc", "site-nav"]', page)
        self.assertIn("textContent", page.split("function buildToc", 1)[1])
        self.assertNotIn("innerHTML = toc", page)

    def _model(self, page_path):
        page = page_path.read_text(encoding="utf-8")
        body = page.split('<script type="application/json" id="model">', 1)[1]
        return json.loads(body.split("</script>", 1)[0].replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&"))

    def _render(self, source):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = render.main([str(source)], tmp_root=self.out)
        return code, err.getvalue()

    def test_collect_links_finds_only_existing_md_inside_root(self):
        req = self.repo / "docs" / "requests"
        req.mkdir(parents=True)
        (req / "a b.md").write_text("# A\n", encoding="utf-8")
        (req / "заявка.md").write_text("# Z\n", encoding="utf-8")
        (req / "UP.MD").write_text("# U\n", encoding="utf-8")
        (self.root / "outside.md").write_text("# O\n", encoding="utf-8")
        text = ("[x](../requests/a%20b.md#top) [y](../requests/заявка.md) [no](../requests/missing.md) "
                "[web](https://example.com/z.md) [out](../../../../outside.md) [pic](p.png) [anchor](#a) "
                "[mail](mailto:a@b.md) [file](file:///etc/x.md) [self](20261014-0115-demo.md) "
                "[spaced](<../requests/a b.md>) [up](../requests/UP.MD)\n\n"
                "[ref]: ../requests/a%20b.md\n")
        found = render.collect_links(text, self.spec, self.repo)
        self.assertEqual([p.name for p in found], ["a b.md", "заявка.md", "UP.MD"])

    def test_collect_links_rejects_symlink_leaving_repo(self):
        outside = self.root / "outside.md"
        outside.write_text("# O\n", encoding="utf-8")
        (self.spec.parent / "escape.md").symlink_to(outside)
        (self.spec.parent / "inside.md").write_text("# I\n", encoding="utf-8")
        found = render.collect_links("[a](escape.md) [b](inside.md)\n", self.spec, self.repo)
        self.assertEqual([p.name for p in found], ["inside.md"])

    def test_outside_and_symlinked_targets_are_not_rendered_or_listed(self):
        outside = self.root / "outside.md"
        outside.write_text("# O\n", encoding="utf-8")
        (self.spec.parent / "escape.md").symlink_to(outside)
        self.spec.write_text("[a](escape.md) [b](../../../../outside.md)\n", encoding="utf-8")
        code, _ = self._render(self.spec)
        self.assertEqual(code, 0)
        self.assertEqual(self._model(render.html_path(self.spec, self.out))["links"], [])
        written = [p.name for p in render.preview_root(self.out).rglob("*.html") if p.name != "_index.html"]
        self.assertEqual(written, [render.html_path(self.spec, self.out).name])

    def test_neighbor_rendered_once_and_skipped_when_fresh(self):
        req = self.repo / "docs" / "requests" / "r.md"
        req.parent.mkdir(parents=True)
        req.write_text("# R\n", encoding="utf-8")
        self.spec.write_text("[r](../requests/r.md)\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(render.main([str(self.spec)], tmp_root=self.out), 0)
        neighbor = render.html_path(req, self.out)
        self.assertTrue(neighbor.exists())
        self.assertEqual(buf.getvalue().strip(), render.html_path(self.spec, self.out).as_uri())
        before = neighbor.stat().st_mtime_ns
        with redirect_stdout(io.StringIO()):
            render.main([str(self.spec)], tmp_root=self.out)
        self.assertEqual(neighbor.stat().st_mtime_ns, before)
        req.write_text("# R2\n", encoding="utf-8")
        os.utime(req, (before / 1e9 + 5, before / 1e9 + 5))
        with redirect_stdout(io.StringIO()):
            render.main([str(self.spec)], tmp_root=self.out)
        self.assertIn("R2", neighbor.read_text(encoding="utf-8"))

    def test_neighbors_are_not_followed_further(self):
        a = self.repo / "docs" / "requests" / "a.md"
        b = self.repo / "docs" / "requests" / "b.md"
        a.parent.mkdir(parents=True)
        a.write_text("[b](b.md) [main](../specs/20261014-0115-demo.md)\n", encoding="utf-8")
        b.write_text("# B\n", encoding="utf-8")
        self.spec.write_text("[a](../requests/a.md)\n", encoding="utf-8")
        self._render(self.spec)
        self.assertTrue(render.html_path(a, self.out).exists())
        self.assertFalse(render.html_path(b, self.out).exists())
        # The neighbor rewrites its own links, but only to pages that exist (or are being written).
        self.assertEqual(self._model(render.html_path(a, self.out))["links"], [self.spec.resolve().as_uri()])

    def test_links_model_lists_only_previewed_targets(self):
        req = self.repo / "docs" / "requests" / "r.md"
        req.parent.mkdir(parents=True)
        req.write_text("# R\n", encoding="utf-8")
        self.spec.write_text("[r](../requests/r.md) [gone](../requests/none.md)\n", encoding="utf-8")
        self._render(self.spec)
        self.assertEqual(self._model(render.html_path(self.spec, self.out))["links"], [req.resolve().as_uri()])

    def test_unreadable_neighbor_does_not_fail_main_render(self):
        req = self.repo / "docs" / "requests"
        req.mkdir(parents=True)
        (req / "bad.md").write_bytes(b"\xff\xfe\x00bad")
        (req / "ok.md").write_text("# OK\n", encoding="utf-8")
        self.spec.write_text("[bad](../requests/bad.md) [ok](../requests/ok.md)\n", encoding="utf-8")
        code, err = self._render(self.spec)
        self.assertEqual(code, 0)
        self.assertIn("bad.md", err)
        self.assertEqual(self._model(render.html_path(self.spec, self.out))["links"], [(req / "ok.md").resolve().as_uri()])
        self.assertFalse(render.html_path(req / "bad.md", self.out).exists())

    def test_neighbor_in_nested_repo_is_not_rendered(self):
        nested = self.repo / "vendor" / "lib"
        (nested / ".git").mkdir(parents=True)
        (nested / "n.md").write_text("# N\n", encoding="utf-8")
        self.spec.write_text("[n](../../vendor/lib/n.md)\n", encoding="utf-8")
        self._render(self.spec)
        self.assertEqual(self._model(render.html_path(self.spec, self.out))["links"], [])
        self.assertFalse((render.preview_root(self.out) / "lib").exists())

    def test_page_rewrites_md_links_only_from_model(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23", model={"links": ["file:///x/a.md"]})
        self.assertIn('id="model"', page)
        self.assertIn("previewHref(token.href)", page)
        self.assertIn(r'replace(/\.md(?=[?#]|$)/i, ".html")', page)

    def _mirror(self):
        return render.preview_root(self.out) / "demo-repo"

    def test_index_pages_for_current_docs_and_root(self):
        (self.repo / "README.md").write_text("# Repo\n", encoding="utf-8")
        (self.repo / "docs" / "README.md").write_text("# Docs\n", encoding="utf-8")
        (self.repo / "docs" / "specs" / "<b>.md").write_text("# B\n", encoding="utf-8")
        (self.repo / ".hidden").mkdir()
        self._render(self.spec)
        mirror = self._mirror()
        for rel in ("docs/specs/_index.html", "docs/_index.html", "_index.html"):
            self.assertTrue((mirror / rel).exists(), rel)
        page = (mirror / "docs" / "specs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn("&lt;b&gt;.md", page)
        self.assertNotIn("<b>.md", page)
        self.assertIn('rel="icon"', page)
        self.assertNotIn(".hidden", (mirror / "_index.html").read_text(encoding="utf-8"))

    def test_index_entry_without_preview_links_to_source_md(self):
        self._render(self.spec)
        sibling = self.spec.parent / "other.md"
        sibling.write_text("# O\n", encoding="utf-8")
        render.render_index(self.spec.parent, self.repo, self.out)
        page = render.index_path(self.spec.parent, self.out, self.repo).read_text(encoding="utf-8")
        self.assertIn(sibling.resolve().as_uri(), page)
        self.assertIn("20261014-0115-demo.html", page)

    def test_underscore_index_md_blocks_index_page(self):
        (self.spec.parent / "_index.md").write_text("# mine\n", encoding="utf-8")
        code, err = self._render(self.spec)
        self.assertEqual(code, 0)
        self.assertIn("_index.md", err)
        self.assertFalse((self._mirror() / "docs" / "specs" / "_index.html").exists())
        hrefs = [e["href"] for e in self._model(render.html_path(self.spec, self.out))["nav"]]
        self.assertNotIn("_index.html", hrefs)

    def test_symlinked_dir_and_escaping_file_are_not_listed(self):
        outside = self.root / "elsewhere-dir"
        outside.mkdir()
        (outside / "secret.md").write_text("# S\n", encoding="utf-8")
        (self.repo / "repositories").symlink_to(outside, target_is_directory=True)
        (self.repo / "leak.md").symlink_to(outside / "secret.md")
        (self.repo / "node_modules").mkdir()
        self._render(self.spec)
        page = (self._mirror() / "_index.html").read_text(encoding="utf-8")
        for name in ("repositories", "leak.md", "node_modules", ".git"):
            self.assertNotIn(name, page)
        self.assertIn("docs", page)

    def test_index_escapes_and_encodes_odd_names(self):
        names = ['a"q&b <i>.md', "заявка x.md"]
        for name in names:
            (self.spec.parent / name).write_text("# X\n", encoding="utf-8")
        (self.repo / "docs" / "dir <u>&").mkdir()
        self._render(self.spec)
        page = (self._mirror() / "docs" / "specs" / "_index.html").read_text(encoding="utf-8")
        self.assertNotIn("<i>", page)
        self.assertNotIn("<u>", page)
        self.assertIn("a&quot;q&amp;b &lt;i&gt;.md", page)
        self.assertIn("заявка x.md", page)
        self.assertIn("%D0%B7%D0%B0%D1%8F%D0%B2%D0%BA%D0%B0%20x.md", page)
        self.assertNotIn('href="file:///' + "a\"", page)
        docs_page = (self._mirror() / "docs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn("dir &lt;u&gt;&amp;", docs_page)
        self.assertNotIn("<u>", docs_page)

    def test_index_links_preview_when_it_exists_and_subdir_index_when_present(self):
        self._render(self.spec)
        docs_page = (self._mirror() / "docs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn('href="specs/_index.html"', docs_page)
        spec_page = (self._mirror() / "docs" / "specs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn('href="20261014-0115-demo.html"', spec_page)
        (self.repo / "docs" / "other").mkdir()
        self._render(self.spec)
        docs_page = (self._mirror() / "docs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn("other", docs_page)
        self.assertNotIn("other/_index.html", docs_page)

    def test_entry_href_prefers_preview_then_source(self):
        md = self.spec.parent / "z.md"
        md.write_text("# Z\n", encoding="utf-8")
        page_dir = render.index_path(self.spec.parent, self.out, self.repo).parent
        self.assertEqual(render.entry_href(md, page_dir, self.out), md.resolve().as_uri())
        self._render(md)
        self.assertEqual(render.entry_href(md, page_dir, self.out), "z.html")

    def test_nav_lists_readmes_and_indexes(self):
        (self.repo / "README.md").write_text("# Repo\n", encoding="utf-8")
        (self.repo / "docs" / "README.md").write_text("# Docs\n", encoding="utf-8")
        (self.spec.parent / "README.md").write_text("# Specs\n", encoding="utf-8")
        self._render(self.spec)
        nav = self._model(render.html_path(self.spec, self.out))["nav"]
        self.assertEqual(
            [entry["href"] for entry in nav],
            ["../../README.html", "README.html", "../README.html",
             "_index.html", "../_index.html", "../../_index.html"],
        )
        for entry in nav:
            self.assertTrue((render.html_path(self.spec, self.out).parent / entry["href"]).resolve().exists(), entry)
        self.assertTrue(render.html_path(self.repo / "README.md", self.out).exists())

    def test_nav_without_readmes_lists_only_indexes_and_dedupes(self):
        loose = self.root / "loose" / "plan.md"
        loose.parent.mkdir(parents=True)
        loose.write_text("# P\n", encoding="utf-8")
        self._render(loose)
        nav = self._model(render.html_path(loose, self.out))["nav"]
        self.assertEqual([entry["href"] for entry in nav], ["_index.html"])

    def test_nav_labels_stay_data_and_hrefs_are_encoded(self):
        odd = self.repo / "docs" / "a b" / "<x>.md"
        odd.parent.mkdir()
        odd.write_text("# X\n", encoding="utf-8")
        (odd.parent / "README.md").write_text("# R\n", encoding="utf-8")
        self._render(odd)
        nav = self._model(render.html_path(odd, self.out))["nav"]
        self.assertTrue(any("a b" in entry["label"] for entry in nav))
        self.assertTrue(all(":" not in entry["href"] for entry in nav))
        page = render.html_path(odd, self.out).read_text(encoding="utf-8")
        self.assertIn('<footer id="site-nav"', page)
        self.assertIn("textContent", page.split('var siteNav', 1)[1].split("marked", 1)[0])

    def test_unreadable_dir_does_not_fail_main_render(self):
        from unittest import mock

        with mock.patch.object(Path, "iterdir", side_effect=PermissionError("denied")):
            code, err = self._render(self.spec)
        self.assertEqual(code, 0)
        self.assertIn("index", err)
        self.assertTrue(render.html_path(self.spec, self.out).exists())

    def test_index_stays_inside_preview_repo_dir(self):
        self._render(self.spec)
        before = sorted(str(p) for p in render.preview_root(self.out).parent.rglob("*") if "doc-preview-" not in str(p))
        self.assertEqual(before, [])
        with self.assertRaises(ValueError):
            render.render_index(self.root, self.repo, self.out)

    def test_neighbor_in_subfolder_of_repo_without_git_is_rendered(self):
        work = self.root / "w"
        (work / "sub").mkdir(parents=True)
        (work / "sub" / "n.md").write_text("# N\n", encoding="utf-8")
        (work / "a.md").write_text("[n](sub/n.md)\n", encoding="utf-8")
        code, _ = self._render(work / "a.md")
        self.assertEqual(code, 0)
        neighbor = render.preview_root(self.out) / "w" / "sub" / "n.html"
        self.assertTrue(neighbor.exists())
        self.assertEqual(self._model(render.html_path(work / "a.md", self.out))["links"],
                         [(work / "sub" / "n.md").resolve().as_uri()])

    def test_nested_repo_neighbor_is_skipped_even_without_outer_git(self):
        work = self.root / "w"
        (work / "sub" / ".git").mkdir(parents=True)
        (work / "sub" / "n.md").write_text("# N\n", encoding="utf-8")
        (work / "a.md").write_text("[n](sub/n.md)\n", encoding="utf-8")
        self._render(work / "a.md")
        self.assertEqual(self._model(render.html_path(work / "a.md", self.out))["links"], [])
        self.assertFalse((render.preview_root(self.out) / "w" / "sub").exists())
        self.assertFalse((render.preview_root(self.out) / "sub").exists())

    def test_preview_older_than_renderer_is_rerendered(self):
        req = self.repo / "docs" / "requests" / "r.md"
        req.parent.mkdir(parents=True)
        req.write_text("# R\n", encoding="utf-8")
        self.spec.write_text("[r](../requests/r.md)\n", encoding="utf-8")
        self._render(self.spec)
        page = render.html_path(req, self.out)
        page.write_text("STALE", encoding="utf-8")
        os.utime(req, (1000, 1000))
        os.utime(page, (2000, 2000))  # newer than the source, older than render.py
        self._render(self.spec)
        self.assertNotEqual(page.read_text(encoding="utf-8"), "STALE")

    def test_index_md_collision_ignores_case(self):
        folder = self.root / "case"
        folder.mkdir()
        self.assertFalse(render.has_index_md(folder))
        (folder / "_index.MD").write_text("# mine\n", encoding="utf-8")
        self.assertTrue(render.has_index_md(folder))
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertIsNone(render.render_index(folder, folder, self.out))
        self.assertIn("_index.md", err.getvalue())
        self.assertFalse(render.index_path(folder, self.out, folder).exists())

    def test_nested_repo_docs_is_not_in_nav_or_indexes(self):
        (self.repo / "docs" / ".git").mkdir()
        (self.repo / "docs" / "README.md").write_text("# Docs\n", encoding="utf-8")
        note = self.repo / "notes" / "n.md"
        note.parent.mkdir()
        note.write_text("# N\n", encoding="utf-8")
        self._render(note)
        nav = self._model(render.html_path(note, self.out))["nav"]
        self.assertEqual([e["label"] for e in nav], ["Index: notes/", "Index: demo-repo/"])
        self.assertFalse((self._mirror() / "docs").exists())

    def _swap_for_symlink(self, rel):
        """Replace a mirror folder with a symlink to an empty outside folder; return that folder."""
        outside = self.root / "outside-dir"
        outside.mkdir()
        mirror_dir = self._mirror() / rel
        shutil.rmtree(mirror_dir)
        mirror_dir.symlink_to(outside, target_is_directory=True)
        return outside

    def test_page_is_not_written_through_a_symlinked_mirror_folder(self):
        self.assertEqual(self._render(self.spec)[0], 0)
        outside = self._swap_for_symlink("docs")
        code, err = self._render(self.spec)
        self.assertEqual(code, 1)
        self.assertIn("symlink", err)
        self.assertEqual(list(outside.iterdir()), [])

    def test_neighbor_is_not_written_through_a_symlinked_mirror_folder(self):
        other = self.repo / "other"
        other.mkdir()
        (other / "n.md").write_text("# N\n", encoding="utf-8")
        self.spec.write_text("[n](../../other/n.md)\n", encoding="utf-8")
        self.assertEqual(self._render(self.spec)[0], 0)
        outside = self._swap_for_symlink("other")
        code, err = self._render(self.spec)
        self.assertEqual(code, 0)
        self.assertIn("skipping linked file", err)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertTrue(render.html_path(self.spec, self.out).exists())

    def test_index_is_not_written_through_a_symlinked_mirror_folder(self):
        self.assertEqual(self._render(self.spec)[0], 0)
        outside = self._swap_for_symlink("docs")
        with self.assertRaises(OSError):
            render.render_index(self.repo / "docs", self.repo, self.out)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_md_inside_repo_is_not_followed(self):
        (self.spec.parent / "real.md").write_text("# Real\n", encoding="utf-8")
        (self.spec.parent / "alias.md").symlink_to(self.spec.parent / "real.md")
        (self.spec.parent / "plain.md").write_text("# Plain\n", encoding="utf-8")
        found = render.collect_links("[a](alias.md) [p](plain.md)\n", self.spec, self.repo)
        self.assertEqual([p.name for p in found], ["plain.md"])
        self.spec.write_text("[a](alias.md) [p](plain.md)\n", encoding="utf-8")
        self.assertEqual(self._render(self.spec)[0], 0)
        self.assertFalse(render.html_path(self.spec.parent / "alias.md", self.out).exists())
        self.assertTrue(render.html_path(self.spec.parent / "plain.md", self.out).exists())
        links = self._model(render.html_path(self.spec, self.out))["links"]
        self.assertEqual([Path(u).name if "/" in u else u for u in (x.rsplit("/", 1)[-1] for x in links)], ["plain.md"])

    def test_symlinked_docs_inside_repo_gives_no_readme_or_index(self):
        elsewhere = self.repo / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "README.md").write_text("# Other\n", encoding="utf-8")
        shutil.rmtree(self.repo / "docs")
        (self.repo / "docs").symlink_to(elsewhere, target_is_directory=True)
        note = self.repo / "notes" / "n.md"
        note.parent.mkdir()
        note.write_text("# N\n", encoding="utf-8")
        self.assertEqual(render._readme_sources(note, self.repo), [])
        self.assertEqual(self._render(note)[0], 0)
        labels = [e["label"] for e in self._model(render.html_path(note, self.out))["nav"]]
        self.assertEqual(labels, ["Index: notes/", "Index: demo-repo/"])
        self.assertFalse((self._mirror() / "docs").exists())

    def test_symlinked_md_entry_in_index_links_to_raw_file(self):
        (self.spec.parent / "real.md").write_text("# Real\n", encoding="utf-8")
        alias = self.spec.parent / "alias.md"
        alias.symlink_to(self.spec.parent / "real.md")
        self.assertEqual(self._render(self.spec)[0], 0)
        page = (self._mirror() / "docs" / "specs" / "_index.html").read_text(encoding="utf-8")
        self.assertIn(">alias.md<", page)
        self.assertFalse(render.html_path(alias, self.out).exists())
        self.assertIn(render.entry_href(alias, self._mirror(), self.out, self.repo), page.replace("&amp;", "&"))

    def test_main_missing_file_fails(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = render.main([str(self.repo / "missing.md")], tmp_root=self.out)
        self.assertEqual(code, 1)
        self.assertIn("missing.md", err.getvalue())

    def test_main_without_argument_prints_usage(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = render.main([], tmp_root=self.out)
        self.assertEqual(code, 2)
        self.assertIn("usage", err.getvalue())


if __name__ == "__main__":
    unittest.main()
