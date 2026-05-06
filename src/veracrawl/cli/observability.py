"""Operational observability fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.ops import ObservabilityFixtureManifest
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.observability import (
    OperationalObservabilityGateResult,
    run_operational_observability_gate,
)


class OperationalObservabilityFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    signal_refs: list[Ref] = Field(default_factory=list)
    metric_sample_refs: list[Ref] = Field(default_factory=list)
    trace_span_refs: list[Ref] = Field(default_factory=list)
    alert_record_refs: list[Ref] = Field(default_factory=list)
    runbook_action_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    cost_metric_refs: list[Ref] = Field(default_factory=list)
    dashboard_snapshot_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    collector_handoff_refs: list[Ref] = Field(default_factory=list)
    telemetry_backend_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    stale_projection_refs: list[Ref] = Field(default_factory=list)
    unredacted_sensitive_fields: list[str] = Field(default_factory=list)
    unsafe_runbook_action_refs: list[Ref] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_operational_observability_fixture(
    manifest: ObservabilityFixtureManifest,
    *,
    profile: str,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> OperationalObservabilityFixtureRunReport:
    result = run_operational_observability_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: ObservabilityFixtureManifest,
    profile: str,
    result: OperationalObservabilityGateResult,
) -> OperationalObservabilityFixtureRunReport:
    report = result.report
    return OperationalObservabilityFixtureRunReport(
        id=f"operational-observability-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.result,
        operator_status=report.operator_status,
        signal_refs=report.signal_refs,
        metric_sample_refs=report.metric_sample_refs,
        trace_span_refs=report.trace_span_refs,
        alert_record_refs=report.alert_record_refs,
        runbook_action_refs=report.runbook_action_refs,
        quality_report_refs=report.quality_report_refs,
        cost_metric_refs=report.cost_metric_refs,
        dashboard_snapshot_refs=report.dashboard_snapshot_refs,
        projection_watermark_refs=report.projection_watermark_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        dr_restore_report_refs=report.dr_restore_report_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        redaction_map_refs=report.redaction_map_refs,
        collector_handoff_refs=report.collector_handoff_refs,
        telemetry_backend_refs=report.telemetry_backend_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_ref_fields=report.missing_ref_fields,
        stale_projection_refs=report.stale_projection_refs,
        unredacted_sensitive_fields=report.unredacted_sensitive_fields,
        unsafe_runbook_action_refs=report.unsafe_runbook_action_refs,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> OperationalObservabilityFixtureRunReport:
    manifest = ObservabilityFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    backend_ref = telemetry_backend_ref or os.getenv("VERACRAWL_TELEMETRY_BACKEND_REF")
    handoff_ref = collector_handoff_ref or os.getenv("VERACRAWL_COLLECTOR_HANDOFF_REF")
    report = run_operational_observability_fixture(
        manifest,
        profile=profile,
        telemetry_backend_ref=backend_ref,
        collector_handoff_ref=handoff_ref,
    )
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.operator_status != manifest.expected_failure_type.value
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-observability")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--telemetry-backend-ref")
    run.add_argument("--collector-handoff-ref")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-observability"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            report = run_fixture(
                Path(args.fixture_dir),
                profile=args.profile,
                out=Path(args.out),
                telemetry_backend_ref=args.telemetry_backend_ref,
                collector_handoff_ref=args.collector_handoff_ref,
            )
            print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
            return 0
        parser.error(f"unsupported command {args.command}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
