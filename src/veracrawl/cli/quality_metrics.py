"""Precision/recall quality metric benchmark CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.quality_metrics import (
    QualityMetricBenchmarkResult,
    run_quality_metric_benchmark,
)
from veracrawl.contracts.quality_metrics import QualityMetricManifest
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
) -> QualityMetricBenchmarkResult:
    manifest = QualityMetricManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_quality_metric_benchmark(
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


def _write_outputs(out: Path, result: QualityMetricBenchmarkResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "precision_recall_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "confusion_records.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.confusion_records],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "slice_metrics.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.slice_metrics],
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
                "precision": result.report.precision,
                "recall": result.report.recall,
                "f1": result.report.f1,
                "critical_field_precision": result.report.critical_field_precision,
                "false_positive_rate": result.report.false_positive_rate,
                "false_negative_rate": result.report.false_negative_rate,
                "abstention_rate": result.report.abstention_rate,
                "unsupported_rate": result.report.unsupported_rate,
                "needs_review_rate": result.report.needs_review_rate,
                "confusion_record_count": len(result.confusion_records),
                "slice_metric_count": len(result.slice_metrics),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-quality-metrics")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-quality-metrics"):
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
                        "precision": report.precision,
                        "recall": report.recall,
                        "f1": report.f1,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
