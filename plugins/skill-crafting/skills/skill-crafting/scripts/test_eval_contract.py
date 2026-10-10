import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from eval_contract import EvalSpecError, load_eval_spec, normalize_case, validate_document


class EvalContractTests(unittest.TestCase):
    def write_spec(self, payload):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = pathlib.Path(temporary.name)
        path = directory / "evals.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_normalizes_integer_string_and_fixture_shapes(self):
        path = self.write_spec(
            {
                "skill_name": "branch-finish",
                "evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e", "files": []},
                    {
                        "id": "early-exit",
                        "name": "server-exit",
                        "prompt": "q",
                        "expected_output": "f",
                        "expectations": ["x"],
                        "files": [],
                    },
                    {
                        "id": 2,
                        "prompt": "r",
                        "expected_output": "g",
                        "fixture": "fixtures/setup.sh s1",
                    },
                ],
            }
        )

        metadata, cases = load_eval_spec(path)

        self.assertEqual(metadata["skill_name"], "branch-finish")
        self.assertEqual([case["name"] for case in cases], ["1", "server-exit", "2"])
        self.assertEqual(cases[2]["fixture"], "fixtures/setup.sh s1")
        self.assertEqual(cases[1]["expectations"], ["x"])
        self.assertEqual(cases[0]["expectations"], [])
        self.assertEqual(cases[0]["fixture"], None)

    def test_rejects_boolean_id_and_missing_output_contract(self):
        boolean_id_path = self.write_spec(
            {
                "evals": [
                    {"id": True, "prompt": "p", "expected_output": "e"},
                ],
            }
        )
        missing_output_path = self.write_spec(
            {
                "evals": [
                    {"id": 2, "prompt": "q"},
                ],
            }
        )

        with self.assertRaises(EvalSpecError):
            load_eval_spec(boolean_id_path)
        with self.assertRaises(EvalSpecError):
            load_eval_spec(missing_output_path)

    def test_rejects_missing_or_non_list_evals(self):
        for payload in ({}, {"evals": {}}):
            with self.subTest(payload=payload):
                path = self.write_spec(payload)
                with self.assertRaises(EvalSpecError) as context:
                    load_eval_spec(path)
                self.assertEqual(context.exception.field, "evals")

    def test_rejects_empty_ids_and_wrong_id_types(self):
        for invalid_id in ("", "   ", 1.5, None, [], {}):
            with self.subTest(invalid_id=invalid_id):
                path = self.write_spec(
                    {
                        "evals": [
                            {"id": invalid_id, "prompt": "p", "expected_output": "e"},
                        ],
                    }
                )
                with self.assertRaises(EvalSpecError) as context:
                    load_eval_spec(path)
                self.assertEqual(context.exception.index, 0)
                self.assertEqual(context.exception.field, "id")

    def test_rejects_duplicate_ids_and_normalized_names(self):
        duplicate_id_path = self.write_spec(
            {
                "evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e"},
                    {"id": 1, "prompt": "q", "expected_output": "f"},
                ],
            }
        )
        duplicate_name_path = self.write_spec(
            {
                "evals": [
                    {"id": 1, "name": " Case ", "prompt": "p", "expected_output": "e"},
                    {"id": 2, "name": "case", "prompt": "q", "expected_output": "f"},
                ],
            }
        )

        with self.assertRaises(EvalSpecError) as duplicate_id:
            load_eval_spec(duplicate_id_path)
        self.assertEqual(duplicate_id.exception.index, 1)
        self.assertEqual(duplicate_id.exception.field, "id")

        with self.assertRaises(EvalSpecError) as duplicate_name:
            load_eval_spec(duplicate_name_path)
        self.assertEqual(duplicate_name.exception.index, 1)
        self.assertEqual(duplicate_name.exception.field, "name")

    def test_rejects_empty_prompt_and_empty_output_contract(self):
        for case in (
            {"id": 1, "prompt": "   ", "expected_output": "e"},
            {"id": 2, "prompt": "p", "expected_output": "", "expectations": []},
        ):
            with self.subTest(case=case):
                path = self.write_spec({"evals": [case]})
                with self.assertRaises(EvalSpecError) as context:
                    load_eval_spec(path)
                self.assertEqual(context.exception.index, 0)
                self.assertIn(context.exception.field, {"prompt", "expected_output"})

    def test_rejects_non_list_files(self):
        path = self.write_spec(
            {
                "evals": [
                    {
                        "id": 1,
                        "prompt": "p",
                        "expected_output": "e",
                        "files": "fixture.txt",
                    },
                ],
            }
        )

        with self.assertRaises(EvalSpecError) as context:
            load_eval_spec(path)

        self.assertEqual(context.exception.index, 0)
        self.assertEqual(context.exception.field, "files")

    def test_accepts_null_and_relative_fixture_values(self):
        path = self.write_spec(
            {
                "evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e", "fixture": None},
                    {"id": 2, "prompt": "q", "expected_output": "f", "fixture": "fixtures/demo"},
                    {
                        "id": 3,
                        "prompt": "r",
                        "expected_output": "g",
                        "fixture": "fixtures/setup.sh s1-preexisting",
                    },
                ],
            }
        )

        _, cases = load_eval_spec(path)

        self.assertIsNone(cases[0]["fixture"])
        self.assertEqual(cases[1]["fixture"], "fixtures/demo")
        self.assertEqual(cases[2]["fixture"], "fixtures/setup.sh s1-preexisting")

    def test_rejects_absolute_and_parent_traversing_fixture_paths(self):
        for fixture in ("/tmp/fixture", "../fixture", "fixtures/../fixture", "fixtures/setup.sh ../escape"):
            with self.subTest(fixture=fixture):
                path = self.write_spec(
                    {
                        "evals": [
                            {"id": 1, "prompt": "p", "expected_output": "e", "fixture": fixture},
                        ],
                    }
                )
                with self.assertRaises(EvalSpecError) as context:
                    load_eval_spec(path)
                self.assertEqual(context.exception.index, 0)
                self.assertEqual(context.exception.field, "fixture")

    def test_rejects_unsafe_fixture_option_values(self):
        for fixture in (
            "fixtures/setup.sh --dir=../escape",
            "fixtures/setup.sh --dir=/tmp/escape",
            r"fixtures/setup.sh --dir=..\escape",
            r"fixtures/setup.sh --dir=C:\escape",
            r"fixtures/setup.sh --dir=\\server\share",
            'fixtures/setup.sh --dir="/tmp/an escape"',
            "fixtures/setup.sh -d=../escape",
        ):
            with self.subTest(fixture=fixture):
                path = self.write_spec({"evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e", "fixture": fixture},
                ]})
                with self.assertRaises(EvalSpecError) as context:
                    load_eval_spec(path)
                self.assertEqual(context.exception.source, path)
                self.assertEqual(context.exception.index, 0)
                self.assertEqual(context.exception.field, "fixture")

    def test_preserves_safe_fixture_option_values(self):
        for options in (
            "--dir=fixtures/demo", "--dir=./fixtures/demo",
            r"--dir=fixtures\demo", '--dir="fixtures/a directory"',
            "--mode=fast --count=3 --enabled=true", '--label="scenario one"',
            "--label=", "--label=..draft", "--label=a=b",
            "--url=https://example.com/demo", "--ratio=16:9", "--fraction=1/2",
        ):
            fixture = f"fixtures/setup.sh {options}"
            with self.subTest(fixture=fixture):
                path = self.write_spec({"evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e", "fixture": fixture},
                ]})
                _, cases = load_eval_spec(path)
                self.assertEqual(cases[0]["fixture"], fixture)

    def test_error_preserves_source_index_and_field_in_message(self):
        path = self.write_spec(
            {
                "evals": [
                    {"id": 1, "prompt": "p", "expected_output": "e"},
                    {"id": 2, "prompt": "", "expected_output": "f"},
                ],
            }
        )

        with self.assertRaises(EvalSpecError) as context:
            load_eval_spec(path)

        error = context.exception
        self.assertEqual(error.source, path)
        self.assertEqual(error.index, 1)
        self.assertEqual(error.field, "prompt")
        self.assertIn(str(path), str(error))
        self.assertIn("[1]", str(error))
        self.assertIn("prompt", str(error))

    def test_public_normalizers_preserve_input_and_apply_name_precedence(self):
        source = pathlib.Path("evals.json")
        raw = {
            "id": 0,
            "eval_name": " Preferred ",
            "name": "fallback",
            "prompt": "  preserve this prompt  ",
            "expectations": ["observable outcome"],
        }
        original = json.loads(json.dumps(raw))
        expected = {
            "id": 0,
            "name": "Preferred",
            "prompt": "  preserve this prompt  ",
            "expected_output": "",
            "expectations": ["observable outcome"],
            "files": [],
            "fixture": None,
        }
        self.assertEqual(normalize_case(raw, 3, source), expected)
        cases = validate_document({"evals": [raw]}, source)
        self.assertEqual(cases, [expected])
        cases[0]["expectations"].append("another outcome")
        self.assertEqual(raw, original)

    def test_duplicate_textual_ids_are_rejected_even_with_distinct_names(self):
        path = self.write_spec({"evals": [
            {"id": 1, "name": "one", "prompt": "p", "expected_output": "e"},
            {"id": "1", "name": "two", "prompt": "p", "expected_output": "e"},
        ]})
        with self.assertRaises(EvalSpecError) as context:
            load_eval_spec(path)
        self.assertEqual(context.exception.field, "id")
        self.assertEqual(context.exception.index, 1)

    def test_invalid_case_field_types_have_context(self):
        source = pathlib.Path("cases/evals.json")
        for field, value in (
            ("eval_name", ""), ("name", None), ("prompt", 1),
            ("expected_output", []), ("expectations", "outcome"),
            ("expectations", [""]), ("expectations", [1]),
            ("files", [None]), ("fixture", []), ("fixture", ""),
            ("fixture", "fixtures/'unterminated"),
        ):
            with self.subTest(field=field, value=value):
                raw = {"id": 1, "prompt": "p", "expected_output": "e", field: value}
                with self.assertRaises(EvalSpecError) as context:
                    normalize_case(raw, 4, source)
                self.assertEqual(context.exception.source, source)
                self.assertEqual(context.exception.index, 4)
                self.assertEqual(context.exception.field, field)

    def test_rejects_non_object_documents_and_cases(self):
        source = pathlib.Path("evals.json")
        for document in (None, [], 1, "text"):
            with self.subTest(document=document):
                with self.assertRaises(EvalSpecError) as context:
                    validate_document(document, source)
                self.assertIsNone(context.exception.index)
                self.assertEqual(context.exception.field, "document")
        with self.assertRaises(EvalSpecError) as context:
            normalize_case([], 5, source)
        self.assertEqual(context.exception.index, 5)
        self.assertEqual(context.exception.field, "case")

    def test_fixture_validation_handles_quoting_and_portable_path_separators(self):
        source = pathlib.Path("evals.json")
        for fixture in (
            '"fixtures/a directory"',
            'fixtures/setup.sh "scenario one"',
        ):
            raw = {"id": 1, "prompt": "p", "expected_output": "e", "fixture": fixture}
            self.assertEqual(normalize_case(raw, 0, source)["fixture"], fixture)
        for fixture in (
            r"C:\fixtures\demo", r"fixtures\..\escape",
            r"fixtures/setup.sh ..\escape", r"fixtures/setup.sh C:\escape",
            'fixtures/setup.sh "/tmp/escape"', "fixtures/demo\0", '""',
        ):
            with self.subTest(fixture=fixture):
                raw = {"id": 1, "prompt": "p", "expected_output": "e", "fixture": fixture}
                with self.assertRaises(EvalSpecError) as context:
                    normalize_case(raw, 0, source)
                self.assertEqual(context.exception.field, "fixture")

    def test_metadata_and_source_bytes_are_preserved(self):
        path = self.write_spec({
            "skill_name": "demo", "custom": {"revision": 2},
            "evals": [{"id": "case", "prompt": "p", "expectations": ["outcome"]}],
        })
        before = path.read_bytes()
        metadata, cases = load_eval_spec(path)
        self.assertEqual(metadata, {"skill_name": "demo", "custom": {"revision": 2}})
        self.assertEqual(cases[0]["expected_output"], "")
        self.assertEqual(path.read_bytes(), before)

    def test_cli_reports_one_error_and_preserves_each_input(self):
        valid = self.write_spec({
            "evals": [{"id": 1, "prompt": "p", "expected_output": "e"}],
        })
        invalid = self.write_spec({"evals": [
            {"id": True, "prompt": "p"}, {"id": 2, "prompt": ""},
        ]})
        malformed = self.write_spec({})
        malformed.write_text("{broken JSON\n", encoding="utf-8")
        bad_encoding = self.write_spec({})
        bad_encoding.write_bytes(b"\xff")
        missing = valid.parent / "missing.json"
        for path, status in (
            (valid, 0), (invalid, 1), (malformed, 1), (bad_encoding, 1),
            (missing, 1), (valid.parent, 1),
        ):
            with self.subTest(path=path):
                before = path.read_bytes() if path.is_file() else None
                result = subprocess.run(
                    [sys.executable, "-B", str(pathlib.Path(__file__).with_name("validate_evals.py")), str(path)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual(result.stdout, "")
                if status:
                    self.assertEqual(len(result.stderr.splitlines()), 1)
                    self.assertIn(str(path), result.stderr)
                    self.assertIn("evals[", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                else:
                    self.assertEqual(result.stderr, "")
                if before is not None:
                    self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
