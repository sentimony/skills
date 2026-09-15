import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))

from aggregate_results import aggregate_workspace, calculate_stats


class AggregateResultsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aggregate-results-")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name) / "workspace"
        self.workspace.mkdir()
        self.manifest = {
            "skill_name": "sample-skill",
            "eval_spec": "/tmp/evals.json",
            "eval_spec_sha256": "spec-sha",
            "template_sha256": "template-sha",
            "harness": "test-harness",
            "adapter": "/tmp/adapter.py",
            "model": "test-model",
            "runs_per_case": 1,
            "configs": ["baseline", "with_skill"],
        }
        self.metadata = {
            **self.manifest,
            "evals": [
                {
                    "id": "second",
                    "name": "Second case",
                    "prompt": "second prompt",
                    "expected_output": "second output",
                    "expectations": ["second expectation"],
                    "files": [],
                    "fixture": None,
                },
                {
                    "id": "first",
                    "name": "First case",
                    "prompt": "first prompt",
                    "expected_output": "first output",
                    "expectations": ["first expectation"],
                    "files": [],
                    "fixture": None,
                },
            ],
        }
        self.write_json("manifest.json", self.manifest)
        self.write_json("eval_metadata.json", self.metadata)

    def write_json(self, relative, value):
        path = self.workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def write_run(
        self,
        eval_id,
        config,
        run_number=1,
        status="complete",
        duration=1.0,
        changed=False,
        grading=None,
        **overrides,
    ):
        record = {
            "eval_id": eval_id,
            "eval_name": "Second case" if eval_id == "second" else "First case",
            "config": config,
            "status": status,
            "return_code": 0 if status == "complete" else None,
            "duration_seconds": duration,
            "changed": changed,
            "tool_calls": 1 if status == "complete" else None,
            "model": self.manifest["model"],
            "run_number": run_number,
        }
        record.update(overrides)
        eval_position = {case["id"]: index for index, case in enumerate(self.metadata["evals"], 1)}[eval_id]
        run_dir = self.workspace / f"eval-{eval_position}" / config / f"run-{run_number}"
        self.write_json(run_dir / "run.json", record)
        if grading is not None:
            self.write_json(run_dir / "grading.json", grading)
        return record

    @staticmethod
    def grading(pass_rate, passed=1, failed=0, total=1):
        return {
            "expectations": [
                {"text": "expectation", "passed": passed == total, "evidence": "evidence"}
            ],
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": total,
                "pass_rate": pass_rate,
            },
        }

    def test_calculate_stats_empty_sequence(self):
        self.assertEqual(
            calculate_stats([]),
            {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
        )

    def test_calculate_stats_one_value_has_zero_sample_stddev(self):
        self.assertEqual(
            calculate_stats([2.34567]),
            {"mean": 2.3457, "stddev": 0.0, "min": 2.3457, "max": 2.3457},
        )

    def test_calculate_stats_multiple_values_uses_sample_stddev(self):
        self.assertEqual(
            calculate_stats([1.0, 2.0, 4.0]),
            {"mean": 2.3333, "stddev": 1.5275, "min": 1.0, "max": 4.0},
        )

    def test_complete_without_grading_and_error_do_not_become_behavioral_scores(self):
        self.write_run("second", "baseline", duration=2.0, changed=True)
        self.write_run("second", "with_skill", status="error", duration=3.0)
        self.write_run("first", "baseline", status="timeout", duration=4.0)
        self.write_run("first", "with_skill", duration=5.0)

        result = aggregate_workspace(self.workspace)

        self.assertEqual(
            [run["eval_id"] for run in result["runs"]],
            ["second", "second", "first", "first"],
        )
        baseline = result["summary"]["baseline"]
        self.assertEqual(
            {key: baseline[key] for key in ("runs", "complete", "errors", "timeouts", "changed", "scored_runs")},
            {"runs": 2, "complete": 1, "errors": 0, "timeouts": 1, "changed": 1, "scored_runs": 0},
        )
        self.assertIsNone(baseline["pass_rate"])
        with_skill = result["summary"]["with_skill"]
        self.assertEqual(with_skill["errors"], 1)
        self.assertEqual(with_skill["timeouts"], 0)
        self.assertEqual(with_skill["scored_runs"], 0)
        self.assertIsNone(with_skill["pass_rate"])

    def test_unmatched_scored_records_do_not_produce_delta(self):
        self.write_run(
            "second",
            "baseline",
            grading=self.grading(1.0),
        )
        self.write_run(
            "first",
            "with_skill",
            grading=self.grading(0.0, passed=0, failed=1),
        )

        result = aggregate_workspace(self.workspace)

        self.assertEqual(result["summary"]["baseline"]["scored_runs"], 1)
        self.assertEqual(result["summary"]["with_skill"]["scored_runs"], 1)
        self.assertNotIn("delta", result)

    def test_matching_scored_records_produce_delta(self):
        self.write_run("second", "baseline", grading=self.grading(0.5, passed=1, failed=1, total=2))
        self.write_run("second", "with_skill", grading=self.grading(1.0))

        result = aggregate_workspace(self.workspace)

        self.assertEqual(result["delta"]["pass_rate"], 0.5)

    def test_manifest_and_run_identity_mismatch_is_rejected(self):
        self.write_run("second", "baseline", model="other-model")

        with self.assertRaises(ValueError):
            aggregate_workspace(self.workspace)

    def test_incompatible_manifest_identity_is_rejected_before_delta(self):
        self.write_run("second", "baseline", grading=self.grading(0.5, passed=1, failed=1, total=2))
        self.write_run("second", "with_skill", grading=self.grading(1.0))
        self.metadata["model"] = "other-model"
        self.write_json("eval_metadata.json", self.metadata)

        with self.assertRaises(ValueError):
            aggregate_workspace(self.workspace)


if __name__ == "__main__":
    unittest.main()
