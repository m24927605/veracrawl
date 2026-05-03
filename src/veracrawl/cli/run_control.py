"""Production run-control fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from veracrawl.contracts.objective import (
    ProductionRunControlFixtureManifest,
    ProductionRunControlReport,
)
from veracrawl.control.run_control import run_production_run_control_fixture


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> ProductionRunControlReport:
    manifest = ProductionRunControlFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_production_run_control_fixture(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
    )
    if report.status != manifest.expected_status:
        raise ValueError(f"expected status {manifest.expected_status}, got {report.status}")
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            "expected completion result "
            f"{manifest.expected_completion_result}, got {report.completion_result}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(
            f"expected operator status {manifest.expected_operator_status}, "
            f"got {report.operator_status}"
        )
    if report.failure_type != manifest.expected_failure_type:
        raise ValueError(
            f"expected failure type {manifest.expected_failure_type}, got {report.failure_type}"
        )
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-run-control")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, ValueError, ValidationError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "status": report.status.value,
                    "completion_result": report.completion_result.value,
                    "operator_status": report.operator_status,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
