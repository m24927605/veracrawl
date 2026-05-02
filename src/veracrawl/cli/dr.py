"""Operational disaster recovery fixture runner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.cli.infrastructure import (
    RuntimeInfrastructureFixtureRunReport,
    run_runtime_infrastructure_fixture,
)
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, DRRestorePhase, DRRestoreRunStatus
from veracrawl.contracts.infrastructure import (
    RuntimeInfrastructureFixtureManifest,
    RuntimeInfrastructureReport,
)
from veracrawl.contracts.ops import DRRestoreFixtureManifest
from veracrawl.runtime_support.disaster_recovery import (
    OperationalDRGateResult,
    dr_restore_plan,
    run_operational_dr_gate,
)


class OperationalDRFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    dr_restore_plan_ref: Ref
    dr_restore_run_ref: Ref
    restore_scope_ref: Ref
    restore_point_ref: Ref | None = None
    backup_manifest_ref: Ref | None = None
    current_phase: DRRestorePhase
    run_status: DRRestoreRunStatus
    metadata_restore_ref: Ref | None = None
    artifact_reachability_report_ref: Ref | None = None
    event_replay_report_ref: Ref | None = None
    projection_rebuild_job_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    queue_recovery_refs: list[Ref] = Field(default_factory=list)
    runtime_infrastructure_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    validation_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    unresolved_refs: list[Ref] = Field(default_factory=list)
    data_loss_detected: bool = False


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_operational_dr_fixture(
    manifest: DRRestoreFixtureManifest,
    *,
    profile: str,
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    s3_endpoint_url: str | None = None,
    s3_bucket: str | None = None,
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
) -> OperationalDRFixtureRunReport:
    policy_refs = [f"policy:{manifest.id}:dr-restore"]
    approval_refs = [f"approval:{manifest.id}:dr-restore"]
    plan = dr_restore_plan(
        manifest.id,
        policy_decision_refs=policy_refs,
        approval_decision_refs=approval_refs,
    )
    runtime_report = None
    if manifest.scenario == "dr-restore-success":
        infrastructure_report = run_runtime_infrastructure_fixture(
            RuntimeInfrastructureFixtureManifest(
                id=manifest.id,
                scenario="operational-infrastructure-success",
                profile_refs=["target"],
                expected_completion_result=CompletenessResult.PASS,
                expected_operator_status="operational_infrastructure_completed",
            ),
            profile=profile,
            postgres_dsn=postgres_dsn,
            redis_url=redis_url,
            s3_endpoint_url=s3_endpoint_url,
            s3_bucket=s3_bucket,
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
        )
        runtime_report = _runtime_report_from_fixture(infrastructure_report)
    result = run_operational_dr_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        plan=plan,
        runtime_infrastructure_report=runtime_report,
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _runtime_report_from_fixture(
    report: RuntimeInfrastructureFixtureRunReport,
) -> RuntimeInfrastructureReport:
    return RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{report.fixture_id}:dr-gate",
        run_ref=f"run:{report.fixture_id}",
        infrastructure_spec_ref=report.infrastructure_spec_ref,
        live_adapter_families=report.live_adapter_families,
        persistence_report_refs=report.persistence_report_refs,
        queue_broker_report_refs=report.queue_broker_report_refs,
        object_store_report_refs=report.object_store_report_refs,
        persistence_adapter_refs=report.persistence_adapter_refs,
        queue_broker_adapter_refs=report.queue_broker_adapter_refs,
        object_store_adapter_refs=report.object_store_adapter_refs,
        transaction_refs=report.transaction_refs,
        command_record_refs=report.command_record_refs,
        idempotency_record_refs=report.idempotency_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        queue_topology_refs=report.queue_topology_refs,
        queue_item_refs=report.queue_item_refs,
        broker_operation_refs=report.broker_operation_refs,
        queue_operation_refs=report.queue_operation_refs,
        lease_refs=report.lease_refs,
        heartbeat_refs=report.heartbeat_refs,
        ack_refs=report.ack_refs,
        nack_refs=report.nack_refs,
        dead_letter_refs=report.dead_letter_refs,
        fencing_token_refs=report.fencing_token_refs,
        artifact_refs=report.artifact_refs,
        object_operation_refs=report.object_operation_refs,
        content_digest_refs=report.content_digest_refs,
        read_result_refs=report.read_result_refs,
        head_refs=report.head_refs,
        list_refs=report.list_refs,
        delete_refs=report.delete_refs,
        lifecycle_state_refs=report.lifecycle_state_refs,
        retention_policy_refs=report.retention_policy_refs,
        privacy_policy_refs=report.privacy_policy_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        policy_decision_refs=report.policy_decision_refs,
        contract_only_refs=report.contract_only_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
        idempotency_deduped=report.idempotency_deduped,
        operator_status=report.operator_status,
        completion_result=report.completion_result,
    )


def _to_run_report(
    *,
    manifest: DRRestoreFixtureManifest,
    profile: str,
    result: OperationalDRGateResult,
) -> OperationalDRFixtureRunReport:
    report = result.report
    run = result.run
    return OperationalDRFixtureRunReport(
        id=f"operational-dr-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.result,
        operator_status=report.operator_status,
        dr_restore_plan_ref=result.plan.id,
        dr_restore_run_ref=run.id,
        restore_scope_ref=report.restore_scope_ref,
        restore_point_ref=report.restore_point_ref,
        backup_manifest_ref=report.backup_manifest_ref,
        current_phase=run.current_phase,
        run_status=run.status,
        metadata_restore_ref=report.metadata_restore_ref,
        artifact_reachability_report_ref=report.artifact_reachability_report_ref,
        event_replay_report_ref=report.event_replay_report_ref,
        projection_rebuild_job_refs=report.projection_rebuild_job_refs,
        export_reconciliation_refs=report.export_reconciliation_refs,
        queue_recovery_refs=report.queue_recovery_refs,
        runtime_infrastructure_report_refs=report.runtime_infrastructure_report_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        policy_decision_refs=report.policy_decision_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        validation_refs=report.validation_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        contract_only_refs=report.contract_only_refs,
        missing_ref_fields=report.missing_ref_fields,
        unresolved_refs=report.unresolved_refs,
        data_loss_detected=report.data_loss_detected,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    s3_endpoint_url: str | None = None,
    s3_bucket: str | None = None,
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
) -> OperationalDRFixtureRunReport:
    manifest = DRRestoreFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_operational_dr_fixture(
        manifest,
        profile=profile,
        postgres_dsn=postgres_dsn,
        redis_url=redis_url,
        s3_endpoint_url=s3_endpoint_url,
        s3_bucket=s3_bucket,
        s3_access_key_id=s3_access_key_id,
        s3_secret_access_key=s3_secret_access_key,
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
    parser = argparse.ArgumentParser(prog="veracrawl-dr")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--postgres-dsn")
    run.add_argument("--redis-url")
    run.add_argument("--s3-endpoint-url")
    run.add_argument("--s3-bucket")
    run.add_argument("--s3-access-key-id")
    run.add_argument("--s3-secret-access-key")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        report = run_fixture(
            Path(args.fixture_dir),
            profile=args.profile,
            out=Path(args.out),
            postgres_dsn=args.postgres_dsn,
            redis_url=args.redis_url,
            s3_endpoint_url=args.s3_endpoint_url,
            s3_bucket=args.s3_bucket,
            s3_access_key_id=args.s3_access_key_id,
            s3_secret_access_key=args.s3_secret_access_key,
        )
        print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
        return 0
    parser.error(f"unsupported command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
