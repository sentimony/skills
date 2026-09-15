import argparse
from collections.abc import Mapping
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

from eval_contract import load_eval_spec


CONFIGS = ("baseline", "with_skill")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _writable(root: Path) -> None:
    for directory, dirs, files in os.walk(root):
        for path in [Path(directory), *(Path(directory) / name for name in dirs + files)]:
            if not path.is_symlink():
                mode = path.stat().st_mode | stat.S_IWUSR
                if path.is_dir():
                    mode |= stat.S_IRUSR | stat.S_IXUSR
                path.chmod(mode)


def _relative(value: str) -> Path:
    path = Path(value)
    windows = PureWindowsPath(value)
    if not value or "\0" in value or path.is_absolute() or windows.anchor or ".." in path.parts or ".." in windows.parts:
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path


def _fixture_path(value: str) -> Path:
    path = _relative(value)
    if path.parts and path.parts[0] == "fixtures":
        path = Path(*path.parts[1:])
    return path


def _copy(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=False, dirs_exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=True)


def prepare_sandbox(template_root: Path, sandbox_root: Path, skill_name: str, config: str) -> None:
    name = _relative(skill_name)
    if len(name.parts) != 1 or name.name != skill_name:
        raise ValueError("skill_name must be one directory name")
    if config not in CONFIGS:
        raise ValueError(f"Unknown config: {config}")
    shutil.copytree(template_root, sandbox_root, symlinks=False)
    _writable(sandbox_root)
    if config == "baseline":
        for tree in (".agents", ".claude"):
            target = sandbox_root / tree / "skills" / name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()


def prepare_fixture(case: Mapping[str, Any], fixtures_root: Path, sandbox_root: Path) -> None:
    _prepare_fixture(case, Path(fixtures_root), Path(sandbox_root), 60)


def _prepare_fixture(case: Mapping[str, Any], fixtures_root: Path, sandbox_root: Path, timeout: float) -> None:
    for value in case.get("files", []):
        relative = _fixture_path(value)
        _copy(fixtures_root / relative, sandbox_root / relative)
        _writable(sandbox_root)
    fixture = case.get("fixture")
    if not fixture:
        return
    tokens = shlex.split(fixture)
    if not tokens:
        raise ValueError("Empty fixture command")
    relative = _fixture_path(tokens[0])
    source = fixtures_root / relative
    if len(tokens) == 1 and source.is_dir():
        _copy(source, sandbox_root)
        _writable(sandbox_root)
        return
    _copy(fixtures_root, sandbox_root / "fixtures")
    _writable(sandbox_root)
    subprocess.run(["sh", *tokens], cwd=sandbox_root, check=True, capture_output=True, timeout=timeout)


def _validate_envelope(envelope: Any, sandbox: Path) -> Path:
    if not isinstance(envelope, dict):
        raise ValueError("Adapter result must be a JSON object")
    if envelope.get("status") not in ("complete", "success"):
        raise ValueError(str(envelope.get("error", "Adapter did not complete")))
    count = envelope.get("tool_calls")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("Adapter tool_calls must be a nonnegative integer")
    answer = envelope.get("answer_path")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Adapter answer_path is missing")
    path = Path(answer)
    if not path.is_absolute():
        path = sandbox / path
    if not path.is_file() or not path.read_bytes().strip():
        raise ValueError("Adapter answer is missing or empty")
    return path


def run_case(
    case: Mapping[str, Any], template_root: Path, run_dir: Path, config: str,
    adapter: Path, model: str, timeout: float, fixtures_root: Path,
) -> dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    result = {"eval_id": case["id"], "eval_name": case["name"], "config": config,
              "status": "error", "return_code": None, "duration_seconds": 0.0,
              "changed": None, "tool_calls": None, "model": model}
    (run_dir / "prompt.txt").write_text(case["prompt"], encoding="utf-8")
    for name in ("transcript.jsonl", "adapter-result.json", "stderr.log", "tree.diff"):
        (run_dir / name).touch()
    temporary = Path(tempfile.mkdtemp(prefix="eval-session-"))
    sandbox = temporary / "sandbox"
    before = temporary / "before"
    try:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        prepare_sandbox(Path(template_root), sandbox, case["skill_name"], config)
        _prepare_fixture(case, Path(fixtures_root), sandbox, timeout)
        if config == "baseline":
            skill_name = _relative(case["skill_name"])
            for tree in (".agents", ".claude"):
                target = sandbox / tree / "skills" / skill_name
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
        shutil.copytree(sandbox, before, symlinks=False)
        env = dict(os.environ, EVAL_TRANSCRIPT_PATH=str(run_dir / "transcript.jsonl"),
                   EVAL_CONFIG=config, EVAL_ID=str(case["id"]), EVAL_NAME=case["name"], EVAL_MODEL=model)
        adapter = Path(adapter).resolve()
        command = [sys.executable, str(adapter)] if adapter.suffix == ".py" else [str(adapter)]
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, timeout)
        with (run_dir / "adapter-result.json").open("wb") as stdout, (run_dir / "stderr.log").open("wb") as stderr:
            completed = subprocess.run(command, input=case["prompt"].encode("utf-8"), cwd=sandbox,
                                       env=env, stdout=stdout, stderr=stderr, timeout=remaining)
        result["return_code"] = completed.returncode
        if completed.returncode:
            raise ValueError(f"Adapter exited with code {completed.returncode}")
        envelope = json.loads((run_dir / "adapter-result.json").read_text(encoding="utf-8"))
        if isinstance(envelope, dict) and envelope.get("status") == "timeout":
            result.update(status="timeout", error=str(envelope.get("error", "Adapter reported timeout")))
        else:
            answer = _validate_envelope(envelope, sandbox)
            persisted_answer = run_dir / "answer.txt"
            if answer.resolve() != persisted_answer:
                shutil.copyfile(answer, persisted_answer)
            result.update(status="complete", tool_calls=envelope["tool_calls"], answer_path=str(persisted_answer))
            if "usage" in envelope:
                result["usage"] = envelope["usage"]
    except subprocess.TimeoutExpired as error:
        result.update(status="timeout", error=f"Run exceeded timeout of {timeout} seconds")
        if error.stderr:
            with (run_dir / "stderr.log").open("ab") as output:
                output.write(error.stderr)
    except (OSError, ValueError, KeyError, shutil.Error, subprocess.CalledProcessError) as error:
        result["error"] = str(error)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            (run_dir / "stderr.log").write_bytes(error.stderr)
    finally:
        if before.exists():
            try:
                diff = subprocess.run(
                    ["git", "diff", "--no-index", "--no-ext-diff", "--no-textconv", "--", "before", "sandbox"],
                    cwd=temporary, capture_output=True, timeout=timeout,
                )
                (run_dir / "tree.diff").write_bytes(diff.stdout)
                if diff.returncode not in (0, 1):
                    raise ValueError(f"git diff exited with code {diff.returncode}: {diff.stderr.decode('utf-8', errors='replace')}")
                result.update(changed=diff.returncode == 1, diff_status="complete")
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                result.update(diff_status="error", status="error", changed=None,
                              error=f"{result.get('error', '')} {error}".strip())
        _writable(temporary)
        shutil.rmtree(temporary)
        result["duration_seconds"] = time.monotonic() - started
        _write_json(run_dir / "timing.json", {"duration_seconds": result["duration_seconds"]})
        _write_json(run_dir / "run.json", result)
        if result["status"] == "complete":
            (run_dir / ".complete").touch()
    return result


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()

    def visit(directory: Path, ancestors: frozenset[Path]) -> None:
        resolved = directory.resolve()
        if resolved in ancestors:
            raise ValueError(f"Template contains a directory cycle: {directory}")
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            if path.is_dir():
                digest.update(b"D")
                visit(path, ancestors | {resolved})
            else:
                data = path.read_bytes()
                digest.update(b"F" + len(data).to_bytes(8, "big") + data)

    visit(root, frozenset())
    return digest.hexdigest()


def run_eval(
    spec_path: Path, template_root: Path, workspace: Path, adapter: Path,
    runs: int, fixtures_root: Path, model: str, timeout: float,
) -> dict[str, Any]:
    spec_path, template_root = Path(spec_path).resolve(), Path(template_root).resolve()
    workspace, adapter = Path(workspace).resolve(), Path(adapter).resolve()
    metadata, cases = load_eval_spec(spec_path)
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 1:
        raise ValueError("runs must be a positive integer")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    skill_name = metadata.get("skill_name")
    if not isinstance(skill_name, str) or len(_relative(skill_name).parts) != 1 or Path(skill_name).name != skill_name:
        raise ValueError("spec skill_name must be one directory name")
    if workspace == template_root or template_root in workspace.parents:
        raise ValueError("workspace must be outside the template")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("workspace must be empty to preserve previous runs")
    manifest = {"skill_name": skill_name, "eval_spec": str(spec_path),
                "eval_spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
                "template_sha256": _tree_hash(template_root),
                "harness": metadata.get("harness", adapter.stem), "adapter": str(adapter),
                "model": model, "runs_per_case": runs, "configs": list(CONFIGS)}
    workspace.mkdir(parents=True, exist_ok=True)
    _write_json(workspace / "manifest.json", manifest)
    _write_json(workspace / "eval_metadata.json", {**metadata, **manifest, "evals": cases})
    records = []
    for index, case in enumerate(cases, 1):
        for config in CONFIGS:
            for number in range(1, runs + 1):
                directory = workspace / f"eval-{index}" / config / f"run-{number}"
                record = run_case(dict(case, skill_name=skill_name), template_root, directory,
                                  config, adapter, model, timeout, fixtures_root)
                record["run_number"] = number
                _write_json(directory / "run.json", record)
                records.append(record)
    return {"manifest": manifest, "runs": records}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run eval cases in fresh sandboxes through an external adapter.")
    parser.add_argument("spec", type=Path, metavar="SPEC")
    parser.add_argument("template", type=Path, metavar="TEMPLATE")
    parser.add_argument("workspace", type=Path, metavar="WORKSPACE")
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--fixtures-root", type=Path)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    try:
        result = run_eval(args.spec, args.template, args.workspace, args.adapter, args.runs,
                          args.fixtures_root or args.spec.parent / "fixtures", args.model, args.timeout)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    return int(any(record["status"] != "complete" for record in result["runs"]))


if __name__ == "__main__":
    sys.exit(main())
