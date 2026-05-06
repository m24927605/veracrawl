"""Ops replay and observability runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.ops import OpsReplayObservabilityFixtureManifest
from veracrawl.ops.replay_observability_runtime import (
    OpsReplayObservabilityRuntimeResult,
    run_ops_replay_observability_runtime,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class OpsReplayObservabilityFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    result_publication_export_report_ref: Ref | None = None
    worker_orchestration_runtime_report_ref: Ref | None = None
    ops_console_report_ref: Ref | None = None
    observability_report_ref: Ref | None = None
    run_control_action_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    evidence_review_refs: list[Ref] = Field(default_factory=list)
    replay_audit_view_refs: list[Ref] = Field(default_factory=list)
    graph_debug_refs: list[Ref] = Field(default_factory=list)
    export_status_refs: list[Ref] = Field(default_factory=list)
    withdrawal_status_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    dashboard_snapshot_refs: list[Ref] = Field(default_factory=list)
    alert_record_refs: list[Ref] = Field(default_factory=list)
    runbook_action_refs: list[Ref] = Field(default_factory=list)
    cost_metric_refs: list[Ref] = Field(default_factory=list)
    observability_signal_refs: list[Ref] = Field(default_factory=list)
    metric_sample_refs: list[Ref] = Field(default_factory=list)
    trace_span_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: str | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    stale_dashboard_refs: list[Ref] = Field(default_factory=list)
    unresolved_recovery_refs: list[Ref] = Field(default_factory=list)
    unsafe_operator_action_refs: list[Ref] = Field(default_factory=list)
    observability_gap_refs: list[Ref] = Field(default_factory=list)
    replay_gap_refs: list[Ref] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_ops_replay_observability_fixture(
    manifest: OpsReplayObservabilityFixtureManifest,
    *,
    profile: str,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> OpsReplayObservabilityFixtureRunReport:
    result = run_ops_replay_observability_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: OpsReplayObservabilityFixtureManifest,
    profile: str,
    result: OpsReplayObservabilityRuntimeResult,
) -> OpsReplayObservabilityFixtureRunReport:
    report = result.report
    return OpsReplayObservabilityFixtureRunReport(
        id=f"ops-replay-observability-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        result_publication_export_report_ref=report.result_publication_export_report_ref,
        worker_orchestration_runtime_report_ref=(report.worker_orchestration_runtime_report_ref),
        ops_console_report_ref=report.ops_console_report_ref,
        observability_report_ref=report.observability_report_ref,
        run_control_action_refs=report.run_control_action_refs,
        review_item_refs=report.review_item_refs,
        evidence_review_refs=report.evidence_review_refs,
        replay_audit_view_refs=report.replay_audit_view_refs,
        graph_debug_refs=report.graph_debug_refs,
        export_status_refs=report.export_status_refs,
        withdrawal_status_refs=report.withdrawal_status_refs,
        recovery_action_refs=report.recovery_action_refs,
        failure_record_refs=report.failure_record_refs,
        dr_restore_report_refs=report.dr_restore_report_refs,
        quality_report_refs=report.quality_report_refs,
        dashboard_snapshot_refs=report.dashboard_snapshot_refs,
        alert_record_refs=report.alert_record_refs,
        runbook_action_refs=report.runbook_action_refs,
        cost_metric_refs=report.cost_metric_refs,
        observability_signal_refs=report.observability_signal_refs,
        metric_sample_refs=report.metric_sample_refs,
        trace_span_refs=report.trace_span_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        redaction_map_refs=report.redaction_map_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_type=report.failure_type.value if report.failure_type else None,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        stale_dashboard_refs=report.stale_dashboard_refs,
        unresolved_recovery_refs=report.unresolved_recovery_refs,
        unsafe_operator_action_refs=report.unsafe_operator_action_refs,
        observability_gap_refs=report.observability_gap_refs,
        replay_gap_refs=report.replay_gap_refs,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> OpsReplayObservabilityFixtureRunReport:
    manifest = OpsReplayObservabilityFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_ops_replay_observability_fixture(
        manifest,
        profile=profile,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type.value
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-ops-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--telemetry-backend-ref")
    run.add_argument("--collector-handoff-ref")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-ops-runtime"):
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
                        "operator_status": report.operator_status,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    sys.exit(main())
