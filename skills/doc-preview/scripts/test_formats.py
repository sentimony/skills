import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

HIGHLIGHT_TAG = (
    f'<script src="{render.HIGHLIGHT_URL}" integrity="{render.HIGHLIGHT_SRI}" crossorigin="anonymous"></script>'
)


class FormatsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "demo-repo"
        (self.repo / ".git").mkdir(parents=True)
        self.out = self.root / "tmp"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def page(self, path):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(render.main([str(path)], tmp_root=self.out), 0)
        return render.html_path(path, self.out).read_text(encoding="utf-8")

    def model(self, page):
        raw = page.split('id="model">', 1)[1].split("</script>", 1)[0]
        return json.loads(raw)

    def test_limits_are_named_constants(self):
        self.assertEqual(render.MAX_ROWS, 5000)
        self.assertEqual(render.MAX_BYTES, 2 * 1024 * 1024)
        self.assertEqual(
            sorted(render.FORMATS),
            [".csv", ".json", ".md", ".toml", ".txt", ".yaml", ".yml"],
        )

    def test_json_valid_and_invalid(self):
        good = render.load_data(self.write("a.json", '{"a": 1}\n'))
        self.assertEqual((good["fmt"], good["error"]), ("json", None))
        self.assertEqual(good["text"], '{"a": 1}\n')
        bad = render.load_data(self.write("b.json", '{"a": }'))
        self.assertIn("line 1 column 7", bad["error"])
        self.assertEqual(bad["text"], '{"a": }')
        self.assertEqual(bad["fmt"], "json")

    def test_extension_is_case_insensitive(self):
        self.assertEqual(render.load_data(self.write("A.JSON", "{}"))["fmt"], "json")
        self.assertEqual(render.load_data(self.write("b.YML", "a: 1"))["fmt"], "yaml")

    @unittest.skipIf(render.tomllib is None, "tomllib needs Python 3.11")
    def test_toml_valid_and_invalid(self):
        self.assertIsNone(render.load_data(self.write("ok.toml", "a = 1\n"))["error"])
        bad = render.load_data(self.write("c.toml", "a = \n"))
        self.assertTrue(bad["error"])
        self.assertEqual(bad["text"], "a = \n")

    def test_toml_without_tomllib_is_shown_unchecked(self):
        with mock.patch.object(render, "tomllib", None):
            data = render.load_data(self.write("d.toml", "a = \n"))
        self.assertEqual((data["fmt"], data["error"], data["text"]), ("toml", None, "a = \n"))

    def test_yaml_and_txt_have_no_validation(self):
        for name in ("d.yaml", "d.yml", "e.txt"):
            data = render.load_data(self.write(name, "key: [unclosed\n"))
            self.assertIsNone(data["error"])
            self.assertEqual(data["text"], "key: [unclosed\n")

    def test_csv_rows_and_ragged_padding(self):
        data = render.load_data(self.write("f.csv", "a,b,c\n1,2\n3,4,5,6\n"))
        self.assertEqual(data["fmt"], "csv")
        self.assertEqual(data["rows"], [["a", "b", "c", ""], ["1", "2", "", ""], ["3", "4", "5", "6"]])
        self.assertEqual((data["total"], data["truncated"], data["error"]), (2, False, None))

    def test_csv_strips_bom_and_keeps_quoted_newlines(self):
        path = self.repo / "bom.csv"
        path.write_bytes(b'\xef\xbb\xbfname,note\r\nx,"two\nlines"\r\n')
        data = render.load_data(path)
        self.assertEqual(data["rows"], [["name", "note"], ["x", "two\nlines"]])

    def test_csv_error_falls_back_to_text(self):
        data = render.load_data(self.write("g.csv", 'a,"b\n'))
        self.assertEqual(data["fmt"], "txt")
        self.assertTrue(data["error"])
        self.assertEqual(data["text"], 'a,"b\n')

    def test_empty_csv_falls_back_to_text(self):
        data = render.load_data(self.write("empty.csv", ""))
        self.assertEqual(data["fmt"], "txt")
        self.assertTrue(data["error"])

    def test_csv_truncates_at_row_limit(self):
        body = "h\n" + "\n".join(str(i) for i in range(render.MAX_ROWS + 10)) + "\n"
        data = render.load_data(self.write("h.csv", body))
        self.assertTrue(data["truncated"])
        self.assertEqual(len(data["rows"]), render.MAX_ROWS + 1)
        self.assertIsNone(data["total"])
        self.assertEqual(data["notice"], f"Showing first {render.MAX_ROWS} rows")

    def test_csv_row_limit_parameter(self):
        data = render.load_data(self.write("p.csv", "h\n1\n2\n3\n4\n"), max_rows=2)
        self.assertEqual(data["rows"], [["h"], ["1"], ["2"]])
        self.assertEqual((data["truncated"], data["total"]), (True, None))
        exact = render.load_data(self.write("q.csv", "h\n1\n2\n"), max_rows=2)
        self.assertFalse(exact["truncated"])
        self.assertNotIn("notice", exact)

    def test_csv_truncates_at_byte_limit_before_row_limit(self):
        body = "h\n" + "".join("x" * 9 + "\n" for _ in range(20))
        data = render.load_data(self.write("r.csv", body), max_bytes=50)
        self.assertTrue(data["truncated"])
        self.assertLess(len(data["rows"]), 21)
        self.assertGreater(len(data["rows"]), 1)
        self.assertIsNone(data["total"])
        self.assertEqual(data["notice"], f"Showing first {len(data['rows']) - 1} rows")

    def test_text_truncates_at_byte_limit(self):
        data = render.load_data(self.write("i.txt", "x" * (render.MAX_BYTES + 100)))
        self.assertTrue(data["truncated"])
        self.assertLessEqual(len(data["text"].encode("utf-8")), render.MAX_BYTES)
        self.assertEqual(data["notice"], "Truncated at 2 MB")

    def test_text_byte_limit_parameter_cuts_on_character_boundary(self):
        data = render.load_data(self.write("j.txt", "й" * 10 + "\nsecond\n"), max_bytes=5)
        self.assertTrue(data["truncated"])
        self.assertEqual(data["text"], "йй")
        self.assertIsNone(data["total"])
        self.assertEqual(data["notice"], "Truncated at 5 bytes")
        whole = render.load_data(self.write("k.txt", "abc"), max_bytes=3)
        self.assertFalse(whole["truncated"])

    def test_cut_json_is_not_validated(self):
        data = render.load_data(self.write("l.json", '{"a": "' + "x" * 40 + '"}'), max_bytes=10)
        self.assertIsNone(data["error"])
        self.assertTrue(data["truncated"])

    def test_json_and_toml_with_bom_are_valid_and_shown_without_it(self):
        for name, body in (("bom.json", '{"a": 1}'), ("bom.toml", "a = 1\n"), ("bom.txt", "x\n")):
            path = self.repo / name
            path.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
            data = render.load_data(path)
            self.assertIsNone(data["error"], name)
            self.assertEqual(data["text"], body, name)

    def test_reading_stops_near_the_byte_limit(self):
        for name, body in (("big.txt", "x" * 5000), ("big.json", "[" + "1," * 3000 + "1]"),
                           ("big.csv", "h\n" + "1\n" * 3000)):
            path = self.write(name, body)
            reads = []
            real_open = Path.open

            class Counting:
                def __init__(self, handle):
                    self.handle = handle

                def read(self, size=-1):
                    assert size is not None and size >= 0, "unbounded read"
                    chunk = self.handle.read(size)
                    reads.append(len(chunk))
                    return chunk

                def __getattr__(self, attr):
                    return getattr(self.handle, attr)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.handle.close()

            def counting_open(self, *args, **kwargs):
                return Counting(real_open(self, *args, **kwargs))

            with mock.patch.object(Path, "open", counting_open), \
                    mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole file")), \
                    mock.patch.object(Path, "read_text", side_effect=AssertionError("whole file")):
                data = render.load_data(path, max_bytes=100)
            self.assertTrue(data["truncated"], name)
            self.assertLessEqual(sum(reads), 100 + 1 + 3, name)

    def test_truncated_csv_drops_the_cut_row_and_never_errors(self):
        body = 'h\n"a b",1\n"long quoted ' + "x" * 200 + '",2\n'
        data = render.load_data(self.write("cut.csv", body), max_bytes=40)
        self.assertEqual(data["fmt"], "csv")
        self.assertIsNone(data["error"])
        self.assertEqual(data["rows"], [["h", ""], ["a b", "1"]])

    def test_cut_inside_a_quoted_multiline_field_drops_that_record(self):
        data = render._csv_data('h,n\na,"first\npart', True, 5000)
        self.assertEqual(data["rows"], [["h", "n"]])
        self.assertEqual(data["notice"], "Showing first 0 rows")
        data = render._csv_data('h,n\nok,1\na,"first\npart', True, 5000)
        self.assertEqual(data["rows"], [["h", "n"], ["ok", "1"]])
        data = render._csv_data("h,n\nok,1\npartial", True, 5000)
        self.assertEqual(data["rows"], [["h", "n"], ["ok", "1"]])
        whole = render._csv_data("h,n\nok,1\n", True, 5000)
        self.assertEqual(whole["rows"], [["h", "n"], ["ok", "1"]])

    def test_unknown_extension_is_rejected_with_list(self):
        path = self.write("j.xyz", "x")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = render.main([str(path)], tmp_root=self.out)
        self.assertEqual(code, 2)
        self.assertIn("unsupported file type '.xyz'", err.getvalue())
        self.assertIn(".csv, .json, .md, .toml, .txt, .yaml, .yml", err.getvalue())
        self.assertFalse(render.preview_root(self.out).exists())

    def test_undecodable_file_fails_without_writing(self):
        path = self.repo / "bin.json"
        path.write_bytes(b"\xff\xfe\x00")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.assertEqual(render.main([str(path)], tmp_root=self.out), 1)
        self.assertFalse(render.preview_root(self.out).exists())

    def test_json_page_embeds_data_inertly(self):
        path = self.write("k.json", '{"x": "</script><img src=x onerror=alert(1)>"}')
        page = self.page(path)
        self.assertEqual(render.html_path(path, self.out).name, "k.json.html")
        model_payload = page.split('id="model">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<img", model_payload)
        self.assertNotIn("</script>", model_payload)
        self.assertIn("\\u003c/script\\u003e", model_payload)
        fallback = page.split('<pre id="fallback">', 1)[1].split("</pre>", 1)[0]
        self.assertNotIn("<img", fallback)
        self.assertIn("&lt;img", fallback)
        self.assertEqual(self.model(page)["data"]["text"], path.read_text(encoding="utf-8"))

    def test_data_pages_have_no_toc_content_or_markdown_scripts(self):
        page = self.page(self.write("m.json", "[1]"))
        self.assertEqual(self.model(page)["fmt"], "json")
        self.assertNotIn(render.MARKED_URL, page)
        self.assertNotIn(render.MERMAID_URL, page)
        self.assertIn('<nav id="toc" aria-label="Contents" hidden></nav>', page)
        self.assertIn("<title>m.json</title>", page)

    def test_highlight_script_only_on_highlighted_formats(self):
        for name in ("a.json", "a.yaml", "a.yml", "a.toml"):
            self.assertIn(HIGHLIGHT_TAG, self.page(self.write(name, "a: 1\n")), name)
        for name, body in (("a.txt", "plain"), ("a.csv", "h\n1\n"), ("a.md", "# T\n")):
            self.assertNotIn(render.HIGHLIGHT_URL, self.page(self.write(name, body)), name)

    def test_csv_with_parse_error_is_a_plain_text_page(self):
        page = self.page(self.write("e.csv", 'a,"b\n'))
        model = self.model(page)
        self.assertEqual(model["data"]["fmt"], "txt")
        self.assertEqual(model["fmt"], "txt")
        self.assertTrue(model["data"]["error"])
        self.assertNotIn(render.HIGHLIGHT_URL, page)

    def test_csv_page_keeps_cells_as_data(self):
        page = self.page(self.write("t.csv", "name,note\n<b>x</b>,\"</script><img src=x onerror=alert(1)>\"\n"))
        payload = page.split('id="model">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<b>", payload)
        self.assertNotIn("<img", payload)
        self.assertEqual(self.model(page)["data"]["rows"][1][0], "<b>x</b>")
        self.assertNotIn("<b>x</b>", page)
        self.assertNotIn("<img", page.split('<pre id="fallback">', 1)[1].split("</pre>", 1)[0])

    def test_csv_page_does_not_duplicate_rows_in_fallback(self):
        page = self.page(self.write("u.csv", "name\nvalue-unique-cell\n"))
        fallback = page.split('<pre id="fallback">', 1)[1].split("</pre>", 1)[0]
        self.assertEqual(page.count("value-unique-cell"), 1)
        self.assertNotIn("value-unique-cell", fallback)

    def test_truncation_notice_reaches_the_page_model(self):
        path = self.write("v.txt", "x" * 50)
        with mock.patch.object(render, "MAX_BYTES", 10):
            page = self.page(path)
        data = self.model(page)["data"]
        self.assertTrue(data["truncated"])
        self.assertEqual(data["text"], "x" * 10)
        self.assertEqual(data["notice"], "Truncated at 10 bytes")

    def test_data_page_has_navigation_and_favicon(self):
        self.write("README.md", "# R\n")
        page = self.page(self.write("docs/w.yaml", "a: 1\n"))
        self.assertIn('rel="icon"', page)
        labels = [entry["label"] for entry in self.model(page)["nav"]]
        self.assertIn("README.md", labels)
        self.assertIn("Index: docs/", labels)

    def test_folder_index_lists_only_markdown(self):
        self.page(self.write("docs/x.json", "{}"))
        self.page(self.write("docs/y.md", "# Y\n"))
        listing = render.index_path(self.repo / "docs", self.out, self.repo).read_text(encoding="utf-8")
        self.assertIn("y.md", listing)
        self.assertNotIn("x.json", listing)

    def test_json_and_md_with_same_stem_do_not_collide(self):
        a = render.html_path(self.write("n.json", "{}"), self.out)
        b = render.html_path(self.write("n.md", "# N\n"), self.out)
        self.assertNotEqual(a, b)

    def test_script_handles_data_pages_without_the_highlighter(self):
        script = render.SCRIPT
        self.assertIn("window.hljs", script)
        self.assertIn("hljs.highlightElement", script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML = data", script)

    def test_highlight_theme_is_inline_for_both_color_schemes(self):
        self.assertIn(".hljs-string", render.STYLE)
        self.assertIn("prefers-color-scheme: dark", render.STYLE)
        self.assertNotIn("highlight.js/styles", render.STYLE)
        self.assertEqual(len(re.findall(r"https?://", render.STYLE)), 0)

    def test_highlight_dependency_is_pinned(self):
        self.assertTrue(render.HIGHLIGHT_SRI.startswith("sha384-"))
        self.assertRegex(render.HIGHLIGHT_URL, r"^https://cdn\.jsdelivr\.net/npm/@highlightjs/cdn-assets@\d+\.\d+\.\d+/")


if __name__ == "__main__":
    unittest.main()
