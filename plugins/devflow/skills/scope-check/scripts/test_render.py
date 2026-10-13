"""Standalone tests for scope-check render.py."""

import io
import json
import os
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

    def test_stable_path_uses_repo_parent_and_stem(self):
        self.assertEqual(
            render.html_path(self.spec, self.out),
            self.out / "scope-check" / "demo-repo" / "specs" / "20261014-0115-demo.html",
        )

    def test_path_without_git_uses_parent_dir_as_repo(self):
        loose = self.root / "loose" / "plans" / "plan.md"
        loose.parent.mkdir(parents=True)
        loose.write_text("# Plan\n", encoding="utf-8")
        self.assertEqual(
            render.html_path(loose, self.out),
            self.out / "scope-check" / "plans" / "plans" / "plan.html",
        )

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

    def test_page_guards_raw_html_and_unsafe_urls(self):
        page = render.render_html(SPEC, self.spec, "2026-10-14 01:23")
        self.assertIn("html(token)", page)
        self.assertIn("safeUrl(", page)
        for scheme in ('"http:"', '"https:"', '"mailto:"'):
            self.assertIn(scheme, page)

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
