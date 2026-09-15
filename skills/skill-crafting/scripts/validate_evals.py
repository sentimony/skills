"""Validate an eval specification without modifying it or executing fixtures."""

import argparse
import pathlib
import sys

from eval_contract import EvalSpecError, load_eval_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", metavar="SPEC", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        load_eval_spec(args.spec)
    except EvalSpecError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
