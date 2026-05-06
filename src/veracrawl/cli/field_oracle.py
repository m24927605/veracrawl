"""Field oracle benchmark CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.field_oracle import (
    FieldOracleBenchmarkResult,
    run_field_oracle_benchmark,
)
from veracrawl.contracts.field_oracle import FieldOracleBenchmarkManifest
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


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
) -> FieldOracleBenchmarkResult:
    manifest = FieldOracleBenchmarkManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_field_oracle_benchmark(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
    )
    _write_outputs(out, result)
    report = result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    return result


def _write_outputs(out: Path, result: FieldOracleBenchmarkResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "field_oracle_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "schemas.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.schemas],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "expected_fields.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.expected_fields],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "field_evaluations.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.evaluations],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": result.report.completion_result.value == "pass",
                "fixture_id": result.report.fixture_id,
                "completion_result": result.report.completion_result.value,
                "operator_status": result.report.operator_status,
                "schema_count": result.report.schema_count,
                "expected_field_count": result.report.expected_field_count,
                "evaluated_field_count": result.report.evaluated_field_count,
                "accepted_field_count": result.report.accepted_field_count,
                "exact_match_count": result.report.exact_match_count,
                "normalized_match_count": result.report.normalized_match_count,
                "acceptable_partial_count": result.report.acceptable_partial_count,
                "replay_bundle_count": len(result.report.replay_bundle_refs),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-field-oracle-benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-field-oracle"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            report = result.report
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                        "schema_count": report.schema_count,
                        "expected_field_count": report.expected_field_count,
                        "accepted_field_count": report.accepted_field_count,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
