"""Production benchmark release gate fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionBenchmarkReleaseFailureType,
)
from veracrawl.contracts.release import ProductionBenchmarkReleaseFixtureManifest
from veracrawl.release.benchmark_gate import (
    ProductionBenchmarkReleaseResult,
    run_production_benchmark_release_gate,
)


class ProductionBenchmarkReleaseFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    release_status: str
    target_runtime_report_ref: Ref | None = None
    source_coverage_report_ref: Ref | None = None
    product_acceptance_report_ref: Ref | None = None
    security_privacy_report_ref: Ref | None = None
    result_publication_export_report_ref: Ref | None = None
    worker_orchestration_runtime_report_ref: Ref | None = None
    ops_replay_observability_runtime_report_ref: Ref | None = None
    source_gate_refs: list[Ref] = Field(default_factory=list)
    processing_gate_refs: list[Ref] = Field(default_factory=list)
    evidence_gate_refs: list[Ref] = Field(default_factory=list)
    verification_gate_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    export_gate_refs: list[Ref] = Field(default_factory=list)
    replay_gate_refs: list[Ref] = Field(default_factory=list)
    ops_gate_refs: list[Ref] = Field(default_factory=list)
    scale_gate_refs: list[Ref] = Field(default_factory=list)
    safety_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    benchmark_run_refs: list[Ref] = Field(default_factory=list)
    slo_metric_refs: list[Ref] = Field(default_factory=list)
    release_decision_refs: list[Ref] = Field(default_factory=list)
    audit_report_refs: list[Ref] = Field(default_factory=list)
    failure_type: ProductionBenchmarkReleaseFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_gate_refs: list[Ref] = Field(default_factory=list)
    slo_violation_refs: list[Ref] = Field(default_factory=list)
    release_blocker_refs: list[Ref] = Field(default_factory=list)
    false_ready_refs: list[Ref] = Field(default_factory=list)
    replay_gap_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_production_benchmark_release_fixture(
    manifest: ProductionBenchmarkReleaseFixtureManifest,
    *,
    profile: str,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> ProductionBenchmarkReleaseFixtureRunReport:
    result = run_production_benchmark_release_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: ProductionBenchmarkReleaseFixtureManifest,
    profile: str,
    result: ProductionBenchmarkReleaseResult,
) -> ProductionBenchmarkReleaseFixtureRunReport:
    report = result.report
    return ProductionBenchmarkReleaseFixtureRunReport(
        id=f"production-benchmark-release-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        release_status=report.release_status,
        target_runtime_report_ref=report.target_runtime_report_ref,
        source_coverage_report_ref=report.source_coverage_report_ref,
        product_acceptance_report_ref=report.product_acceptance_report_ref,
        security_privacy_report_ref=report.security_privacy_report_ref,
        result_publication_export_report_ref=(
            report.result_publication_export_report_ref
        ),
        worker_orchestration_runtime_report_ref=(
            report.worker_orchestration_runtime_report_ref
        ),
        ops_replay_observability_runtime_report_ref=(
            report.ops_replay_observability_runtime_report_ref
        ),
        source_gate_refs=report.source_gate_refs,
        processing_gate_refs=report.processing_gate_refs,
        evidence_gate_refs=report.evidence_gate_refs,
        verification_gate_refs=report.verification_gate_refs,
        publication_gate_refs=report.publication_gate_refs,
        export_gate_refs=report.export_gate_refs,
        replay_gate_refs=report.replay_gate_refs,
        ops_gate_refs=report.ops_gate_refs,
        scale_gate_refs=report.scale_gate_refs,
        safety_gate_refs=report.safety_gate_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        artifact_refs=report.artifact_refs,
        redaction_map_refs=report.redaction_map_refs,
        benchmark_run_refs=report.benchmark_run_refs,
        slo_metric_refs=report.slo_metric_refs,
        release_decision_refs=report.release_decision_refs,
        audit_report_refs=report.audit_report_refs,
        failure_type=report.failure_type,
        failure_report_refs=report.failure_report_refs,
        missing_gate_refs=report.missing_gate_refs,
        slo_violation_refs=report.slo_violation_refs,
        release_blocker_refs=report.release_blocker_refs,
        false_ready_refs=report.false_ready_refs,
        replay_gap_refs=report.replay_gap_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> ProductionBenchmarkReleaseFixtureRunReport:
    manifest = ProductionBenchmarkReleaseFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_production_benchmark_release_fixture(
        manifest,
        profile=profile,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result}"
        )
    if report.release_status != manifest.expected_release_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.release_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-release-gate")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--telemetry-backend-ref")
    run.add_argument("--collector-handoff-ref")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(
                Path(args.fixture_dir),
                profile=args.profile,
                out=Path(args.out),
                telemetry_backend_ref=args.telemetry_backend_ref,
                collector_handoff_ref=args.collector_handoff_ref,
            )
        except (OSError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "completion_result": report.completion_result.value,
                    "release_status": report.release_status,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
