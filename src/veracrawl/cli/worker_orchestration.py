"""Worker orchestration fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.scale import WorkerOrchestrationFixtureManifest
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.scale.worker_orchestration import (
    WorkerOrchestrationRuntimeResult,
    run_worker_orchestration_runtime,
)


class WorkerOrchestrationFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    production_persistence_runtime_report_ref: Ref | None = None
    queue_broker_conformance_report_ref: Ref | None = None
    live_http_acquisition_report_ref: Ref | None = None
    live_normalization_runtime_report_ref: Ref | None = None
    live_evidence_verification_runtime_report_ref: Ref | None = None
    scale_recovery_report_ref: Ref | None = None
    worker_pool_refs: list[Ref] = Field(default_factory=list)
    worker_heartbeat_refs: list[Ref] = Field(default_factory=list)
    worker_capacity_refs: list[Ref] = Field(default_factory=list)
    queue_item_refs: list[Ref] = Field(default_factory=list)
    shard_lease_refs: list[Ref] = Field(default_factory=list)
    lease_heartbeat_refs: list[Ref] = Field(default_factory=list)
    fencing_token_refs: list[Ref] = Field(default_factory=list)
    visibility_timeout_refs: list[Ref] = Field(default_factory=list)
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    retry_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    autoscaling_decision_refs: list[Ref] = Field(default_factory=list)
    pending_outbox_refs: list[Ref] = Field(default_factory=list)
    event_gap_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: str | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    hidden_dead_letter_refs: list[Ref] = Field(default_factory=list)
    duplicate_pollution_refs: list[Ref] = Field(default_factory=list)
    unrecovered_stale_lease_refs: list[Ref] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_worker_orchestration_fixture(
    manifest: WorkerOrchestrationFixtureManifest,
    *,
    profile: str,
) -> WorkerOrchestrationFixtureRunReport:
    result = run_worker_orchestration_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:worker-orchestration"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: WorkerOrchestrationFixtureManifest,
    profile: str,
    result: WorkerOrchestrationRuntimeResult,
) -> WorkerOrchestrationFixtureRunReport:
    report = result.report
    return WorkerOrchestrationFixtureRunReport(
        id=f"worker-orchestration-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        production_persistence_runtime_report_ref=(
            report.production_persistence_runtime_report_ref
        ),
        queue_broker_conformance_report_ref=report.queue_broker_conformance_report_ref,
        live_http_acquisition_report_ref=report.live_http_acquisition_report_ref,
        live_normalization_runtime_report_ref=report.live_normalization_runtime_report_ref,
        live_evidence_verification_runtime_report_ref=(
            report.live_evidence_verification_runtime_report_ref
        ),
        scale_recovery_report_ref=report.scale_recovery_report_ref,
        worker_pool_refs=report.worker_pool_refs,
        worker_heartbeat_refs=report.worker_heartbeat_refs,
        worker_capacity_refs=report.worker_capacity_refs,
        queue_item_refs=report.queue_item_refs,
        shard_lease_refs=report.shard_lease_refs,
        lease_heartbeat_refs=report.lease_heartbeat_refs,
        fencing_token_refs=report.fencing_token_refs,
        visibility_timeout_refs=report.visibility_timeout_refs,
        fairness_scope_refs=report.fairness_scope_refs,
        retry_refs=report.retry_refs,
        dead_letter_refs=report.dead_letter_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        duplicate_suppression_refs=report.duplicate_suppression_refs,
        backpressure_signal_refs=report.backpressure_signal_refs,
        autoscaling_decision_refs=report.autoscaling_decision_refs,
        pending_outbox_refs=report.pending_outbox_refs,
        event_gap_refs=report.event_gap_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_type=report.failure_type.value if report.failure_type else None,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        hidden_dead_letter_refs=report.hidden_dead_letter_refs,
        duplicate_pollution_refs=report.duplicate_pollution_refs,
        unrecovered_stale_lease_refs=report.unrecovered_stale_lease_refs,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> WorkerOrchestrationFixtureRunReport:
    manifest = WorkerOrchestrationFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_worker_orchestration_fixture(manifest, profile=profile)
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
    parser = argparse.ArgumentParser(prog="veracrawl-worker-orchestration")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-worker-orchestration"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
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
