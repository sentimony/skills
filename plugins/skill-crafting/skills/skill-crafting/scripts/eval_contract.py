"""Validate and normalize portable eval specifications using the standard library."""

import json
import pathlib
import shlex
from collections.abc import Mapping
from typing import Any


class EvalSpecError(ValueError):
    """A validation failure with a source, zero-based case index, and field."""

    def __init__(self, source: pathlib.Path, index: int | None, field: str, message: str):
        self.source = pathlib.Path(source)
        self.index = index
        self.field = field
        # Document and read failures have no case index.
        super().__init__(f"{self.source}: evals[{index}].{field}: {message}")


def normalize_case(
    raw: Mapping[str, Any], index: int, source: pathlib.Path
) -> dict[str, Any]:
    """Return the seven contract fields without modifying the input case."""

    def fail(field: str, message: str) -> None:
        raise EvalSpecError(source, index, field, message)

    if not isinstance(raw, Mapping):
        fail("case", "must be an object")

    eval_id = raw.get("id")
    if isinstance(eval_id, bool) or not isinstance(eval_id, (int, str)):
        fail("id", "must be an integer or a non-empty string")
    if isinstance(eval_id, str) and not eval_id.strip():
        fail("id", "must be a non-empty string")

    name = str(eval_id).strip()
    for field in ("eval_name", "name"):
        if field in raw:
            value = raw[field]
            if not isinstance(value, str) or not value.strip():
                fail(field, "must be a non-empty string")
            name = value.strip()
            break

    prompt = raw.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        fail("prompt", "must be a non-empty string")

    expected_output = raw.get("expected_output", "")
    if not isinstance(expected_output, str):
        fail("expected_output", "must be a string")

    expectations = raw.get("expectations", [])
    if not isinstance(expectations, list) or any(
        not isinstance(item, str) or not item.strip() for item in expectations
    ):
        fail("expectations", "must be a list of non-empty strings")
    if not expected_output.strip() and not expectations:
        fail("expected_output", "requires non-empty expected_output or expectations")

    files = raw.get("files", [])
    if not isinstance(files, list):
        fail("files", "must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in files):
        fail("files", "entries must be non-empty strings")

    fixture = raw.get("fixture")
    if fixture is not None:
        if not isinstance(fixture, str) or not fixture.strip() or "\0" in fixture:
            fail("fixture", "must be null, a relative directory, or a setup command")
        try:
            # Check both separator styles so validation stays portable across hosts.
            tokens = shlex.split(fixture.replace("\\", "/"))
        except ValueError:
            fail("fixture", "must have balanced shell quoting")
        if not tokens:
            fail("fixture", "must contain a relative path")
        for token in tokens[:]:
            if token.startswith("-") and "=" in token:
                value = token.split("=", 1)[1]
                if value:
                    tokens.append(value)
        for token in tokens:
            posix_path = pathlib.PurePosixPath(token)
            windows_path = pathlib.PureWindowsPath(token)
            if (
                not token
                or posix_path.is_absolute()
                or windows_path.anchor
                or ".." in posix_path.parts
                or ".." in windows_path.parts
            ):
                fail("fixture", "paths and arguments must be relative without parent traversal")

    return {
        "id": eval_id,
        "name": name,
        "prompt": prompt,
        "expected_output": expected_output,
        "expectations": list(expectations),
        "files": list(files),
        "fixture": fixture,
    }


def validate_document(
    document: Mapping[str, Any], source: pathlib.Path
) -> list[dict[str, Any]]:
    """Validate a loaded document and return its normalized cases in source order."""
    if not isinstance(document, Mapping):
        raise EvalSpecError(source, None, "document", "must be an object")
    if not isinstance(document.get("evals"), list):
        raise EvalSpecError(source, None, "evals", "must be a list")

    cases = []
    ids = set()
    names = set()
    for index, raw in enumerate(document["evals"]):
        case = normalize_case(raw, index, source)
        # IDs also become environment values and paths in downstream runners.
        identity = str(case["id"]).strip()
        if identity in ids:
            raise EvalSpecError(source, index, "id", "duplicate ID")
        normalized_name = case["name"].casefold()
        if normalized_name in names:
            raise EvalSpecError(source, index, "name", "duplicate normalized name")
        ids.add(identity)
        names.add(normalized_name)
        cases.append(case)
    return cases


def load_eval_spec(path: pathlib.Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read UTF-8 JSON and return top-level metadata separately from eval cases."""
    source = pathlib.Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        raise EvalSpecError(source, None, "source", "cannot read UTF-8 input") from error
    except ValueError as error:
        raise EvalSpecError(source, None, "document", "invalid JSON") from error
    cases = validate_document(document, source)
    metadata = {key: value for key, value in document.items() if key != "evals"}
    return metadata, cases
