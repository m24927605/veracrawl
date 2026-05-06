"""Repair success rate benchmark CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.repair_success import (
    RepairSuccessBenchmarkResult,
    run_repair_success_benchmark,
)
from veracrawl.contracts.repair_success import RepairQualityManifest
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
) -> RepairSuccessBenchmarkResult:
    manifest = RepairQualityManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_repair_success_benchmark(
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


def _write_outputs(out: Path, result: RepairSuccessBenchmarkResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "repair_quality_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "seeded_repair_cases.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.seeded_cases],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "repair_attempts.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.repair_attempts],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = result.report
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": report.completion_result.value == "pass",
                "fixture_id": report.fixture_id,
                "completion_result": report.completion_result.value,
                "operator_status": report.operator_status,
                "repair_success_rate": report.repair_success_rate,
                "unsafe_bypass_rate": report.unsafe_bypass_rate,
                "unresolved_critical_rate": report.unresolved_critical_rate,
                "repairable_case_count": report.repairable_case_count,
                "repaired_case_count": report.repaired_case_count,
                "seeded_case_count": len(result.seeded_cases),
                "repair_attempt_count": len(result.repair_attempts),
                "total_token_count": report.total_token_count,
                "total_cost_usd": report.total_cost_usd,
                "p95_latency_ms": report.p95_latency_ms,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-repair-quality-benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-repair-success"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
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
                        "repair_success_rate": report.repair_success_rate,
                        "unsafe_bypass_rate": report.unsafe_bypass_rate,
                        "unresolved_critical_rate": report.unresolved_critical_rate,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
