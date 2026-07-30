#!/usr/bin/env python3
"""
Diagnose TypeScript compilation performance via tsc --extendedDiagnostics.

Runs a clean (non-incremental) type check, parses the diagnostics counters,
and flags likely bottlenecks. With --trace also writes a compiler trace for
deeper analysis with @typescript/analyze-trace.

Usage:
    python <skill>/scripts/trace_perf.py --root .
    python <skill>/scripts/trace_perf.py --root . --project tsconfig.json --trace
    python <skill>/scripts/trace_perf.py --root . --json
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from local_tools import local_binary


# Maps tsc --extendedDiagnostics labels to metric keys.
METRIC_LABELS = {
    "Files": "files",
    "Lines": "lines",
    "Types": "types",
    "Instantiations": "instantiations",
    "Memory used": "memory_kb",
    "Check time": "check_time_s",
    "Total time": "total_time_s",
}

METRIC_RE = re.compile(r"^(?P<label>[A-Za-z ]+?):\s+(?P<value>[\d,.]+)(?P<unit>[Ks]?)\s*$")

THRESHOLDS = {
    "instantiations": 500_000,
    "types": 250_000,
    "files": 5_000,
    "memory_kb": 2_000_000,
}


def parse_metrics(output):
    metrics = {}
    for line in output.splitlines():
        match = METRIC_RE.match(line.strip())
        if not match:
            continue
        key = METRIC_LABELS.get(match.group("label").strip())
        if not key:
            continue
        value = float(match.group("value").replace(",", ""))
        metrics[key] = value
    return metrics


def analyze(metrics):
    findings = []
    for key, limit in THRESHOLDS.items():
        value = metrics.get(key)
        if value is not None and value > limit:
            findings.append("high {}: {:.0f} (threshold {})".format(key, value, limit))
    check = metrics.get("check_time_s")
    total = metrics.get("total_time_s")
    if check and total and total > 0 and check / total > 0.7:
        findings.append(
            "check time is {:.0%} of total: type complexity dominates; "
            "look for heavy generics, large unions, or deep conditional types".format(check / total)
        )
    if metrics.get("instantiations", 0) > THRESHOLDS["instantiations"]:
        findings.append(
            "fix direction: simplify generic constraints, split large unions, "
            "replace intersections with interface extends"
        )
    if not findings and metrics:
        findings.append("no obvious anomalies; if still slow, re-run with --trace")
    return findings


def build_command(root, args):
    """Build fixed argv for the verified project-local TypeScript compiler."""
    command = [
        str(local_binary(root, "tsc") or root / "node_modules/.bin/tsc"),
        "--noEmit",
        "--extendedDiagnostics",
        "--incremental",
        "false",
        "--pretty",
        "false",
    ]
    if args.project:
        command += ["-p", args.project]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--project", help="Path to a specific tsconfig (tsc -p)")
    parser.add_argument("--trace", action="store_true", help="Also write a compiler trace")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    root = Path(args.root)
    if not (root / "package.json").exists():
        print("Error: no package.json in {}".format(root), file=sys.stderr)
        return 2

    if local_binary(root, "tsc") is None:
        print("Diagnostic: TRACE_LOCAL_COMPILER_UNAVAILABLE", file=sys.stderr)
        return 2
    command = build_command(root, args)

    trace_dir = None
    if args.trace:
        trace_dir = tempfile.mkdtemp(prefix="ts-trace-")
        command += ["--generateTrace", trace_dir]

    try:
        result = subprocess.run(
            command, cwd=str(root), capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        print("Diagnostic: TRACE_LOCAL_COMPILER_UNAVAILABLE", file=sys.stderr)
        return 2

    output = (result.stdout or "") + (result.stderr or "")
    metrics = parse_metrics(output)
    findings = analyze(metrics)

    if not metrics:
        print("Diagnostic: TRACE_DIAGNOSTICS_UNAVAILABLE", file=sys.stderr)
        return result.returncode or 2

    if args.json:
        print(json.dumps({
            "exit_code": result.returncode,
            "metrics": metrics,
            "findings": findings,
            "trace_dir": trace_dir,
        }, indent=2))
        return result.returncode

    print("Metrics:")
    for key in ("files", "lines", "types", "instantiations", "memory_kb", "check_time_s", "total_time_s"):
        if key in metrics:
            print("  {}: {:.0f}".format(key, metrics[key]) if not key.endswith("_s")
                  else "  {}: {:.2f}".format(key, metrics[key]))
    print("\nFindings:")
    for finding in findings:
        print("  - {}".format(finding))
    if trace_dir:
        print("\nTrace written to: {}".format(trace_dir))
        status = "available" if local_binary(root, "analyze-trace") else "unavailable"
        print("Trace analyzer: local tool {}".format(status))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
