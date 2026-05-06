"""Contract registry CLI."""

from __future__ import annotations

import argparse
import sys

from veracrawl.contracts.registry import registry_json, validate_registry
from veracrawl.runtime_support.logging import bootstrap_cli_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-contracts")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--format", choices=["json"], default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-contracts"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "validate":
            report = validate_registry()
            print(registry_json())
            return 0 if report.ok else 1
        return 2


if __name__ == "__main__":
    sys.exit(main())
