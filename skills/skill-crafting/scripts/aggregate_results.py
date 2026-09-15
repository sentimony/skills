import argparse
import json
import math
import statistics
import sys
from pathlib import Path


IDENTITY_FIELDS = (
    "skill_name",
    "eval_spec",
    "eval_spec_sha256",
    "template_sha256",
    "harness",
    "adapter",
    "model",
    "runs_per_case",
    "configs",
)


def calculate_stats(values):
    numbers = [float(value) for value in values]
    if not numbers:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(statistics.mean(numbers), 4),
        "stddev": round(statistics.stdev(numbers), 4) if len(numbers) > 1 else 0.0,
        "min": round(min(numbers), 4),
        "max": round(max(numbers), 4),
    }


def _read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _same_identity(left, right, label):
    for field in IDENTITY_FIELDS:
        if field not in left or field not in right:
            raise ValueError(f"Missing {label} identity field: {field}")
        if left[field] != right[field]:
            raise ValueError(f"Incompatible {label} identity field: {field}")


def _valid_score(grading):
    if not isinstance(grading, dict) or not isinstance(grading.get("summary"), dict):
        return None
    summary = grading["summary"]
    required = ("passed", "failed", "total", "pass_rate")
    if any(key not in summary for key in required):
        return None
    passed, failed, total, rate = (summary[key] for key in required)
    if any(isinstance(value, bool) or not isinstance(value, int)
           for value in (passed, failed, total)):
        return None
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        return None
    if total <= 0 or passed < 0 or failed < 0 or passed + failed != total:
        return None
    try:
        numeric_rate = float(rate)
        expected_rate = passed / total
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(numeric_rate) or not 0 <= numeric_rate <= 1:
        return None
    if not math.isclose(numeric_rate, expected_rate, rel_tol=0.0, abs_tol=0.00005):
        return None
    return round(numeric_rate, 4)


def _read_score(path):
    try:
        return _valid_score(_read_json(path))
    except (OSError, UnicodeError, ValueError):
        return None


def _run_identity(record, manifest):
    for field in IDENTITY_FIELDS:
        if field in record and field in manifest and record[field] != manifest[field]:
            raise ValueError(f"Run does not match manifest: {field}")
    if "model" not in record:
        raise ValueError("Run is missing required identity field: model")
    if record.get("config") not in manifest.get("configs", ("baseline", "with_skill")):
        raise ValueError("Run has an unknown config")
    if record.get("status") not in ("complete", "error", "timeout"):
        raise ValueError("Run has an invalid status")
    if not isinstance(record.get("eval_id"), (str, int)) or isinstance(record.get("eval_id"), bool):
        raise ValueError("Run has an invalid eval_id")
    if isinstance(record.get("run_number"), bool) or not isinstance(record.get("run_number"), int):
        raise ValueError("Run has an invalid run_number")


def aggregate_workspace(workspace):
    workspace = Path(workspace)
    manifest = _read_json(workspace / "manifest.json")
    metadata = _read_json(workspace / "eval_metadata.json")
    if not isinstance(manifest, dict) or not isinstance(metadata, dict):
        raise ValueError("manifest.json and eval_metadata.json must be objects")
    _same_identity(metadata, manifest, "metadata/manifest")
    cases = metadata.get("evals")
    if not isinstance(cases, list):
        raise ValueError("eval_metadata.json evals must be a list")
    if any(not isinstance(case, dict) or "id" not in case for case in cases):
        raise ValueError("eval_metadata.json contains invalid eval cases")
    case_order = {case["id"]: index for index, case in enumerate(cases)}
    if len(case_order) != len(cases):
        raise ValueError("eval_metadata.json contains duplicate eval ids")

    config_order = {name: index for index, name in enumerate(manifest.get("configs", []))}
    records = []
    seen_keys = set()
    for path in workspace.rglob("run.json"):
        record = _read_json(path)
        if not isinstance(record, dict):
            raise ValueError(f"Run record must be an object: {path}")
        _run_identity(record, manifest)
        if record["eval_id"] not in case_order:
            raise ValueError(f"Run references unknown eval_id: {record['eval_id']}")
        run_key = (record["eval_id"], record["config"], record["run_number"])
        if run_key in seen_keys:
            raise ValueError(f"Duplicate run key: {run_key}")
        seen_keys.add(run_key)
        record = dict(record)
        grading_path = path.with_name("grading.json")
        score = _read_score(grading_path) if grading_path.is_file() else None
        if score is not None and record.get("status") == "complete":
            record["score"] = score
        records.append((case_order[record["eval_id"]], config_order.get(record["config"], 999),
                        record.get("run_number", 0), path.as_posix(), record))
    records.sort(key=lambda item: item[:4])
    runs = [item[4] for item in records]

    summary = {}
    scored_by_key = {}
    for config in manifest.get("configs", []):
        selected = [run for run in runs if run.get("config") == config]
        scores = [run["score"] for run in selected if "score" in run and run.get("status") == "complete"]
        durations = [float(run.get("duration_seconds", 0.0)) for run in selected
                     if "score" in run and run.get("status") == "complete"]
        for run in selected:
            if "score" in run:
                scored_by_key[(run["eval_id"], config, run["run_number"])] = run["score"]
        summary[config] = {
            "runs": len(selected),
            "complete": sum(run.get("status") == "complete" for run in selected),
            "errors": sum(run.get("status") == "error" for run in selected),
            "timeouts": sum(run.get("status") == "timeout" for run in selected),
            "changed": sum(run.get("changed") is True for run in selected),
            "scored_runs": len(scores),
            "pass_rate": round(statistics.mean(scores), 4) if scores else None,
            "duration_seconds": calculate_stats(durations),
        }
    result = {"manifest": manifest, "metadata": metadata, "runs": runs, "summary": summary}
    paired = []
    for run in runs:
        if run.get("config") == "baseline" and "score" in run:
            key = (run["eval_id"], "with_skill", run["run_number"])
            if key in scored_by_key:
                paired.append((run["score"], scored_by_key[key]))
    if paired:
        result["delta"] = {
            "pass_rate": round(statistics.mean(with_score - base_score for base_score, with_score in paired), 4),
            "scored_runs": len(paired),
        }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate deterministic evaluation results.")
    parser.add_argument("workspace", nargs="?", default=".", metavar="WORKSPACE")
    parser.add_argument("--output", type=Path, help="Write JSON to this file instead of stdout.")
    args = parser.parse_args(argv)
    payload = json.dumps(aggregate_workspace(args.workspace), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
