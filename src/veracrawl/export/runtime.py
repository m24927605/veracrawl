"""Deterministic export connector runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    ExportAttemptStatus,
    ExportCorrectionStatus,
    ExportDeliveryMode,
    ExportFailureType,
    ExportJobStatus,
    ExportPropagationStatus,
    ExportTargetType,
    ExportWithdrawalReason,
    ExportWithdrawalStatus,
)
from veracrawl.contracts.export import (
    ExportAttempt,
    ExportCorrectionRecord,
    ExportDeliveryReceipt,
    ExportJob,
    ExportReconciliationReport,
    ExportTargetSpec,
    ExportWithdrawalAttempt,
    ExportWithdrawalJob,
)


@dataclass(frozen=True)
class ExportRuntimeResult:
    target_specs: list[ExportTargetSpec]
    export_jobs: list[ExportJob]
    export_attempts: list[ExportAttempt]
    delivery_receipts: list[ExportDeliveryReceipt]
    withdrawal_jobs: list[ExportWithdrawalJob]
    withdrawal_attempts: list[ExportWithdrawalAttempt]
    correction_records: list[ExportCorrectionRecord]
    report: ExportReconciliationReport


def run_export_connector(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> ExportRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:export"]
    failures = {
        "export-missing-receipt": (
            ExportFailureType.MISSING_DELIVERY_RECEIPT,
            "delivery_receipt_refs",
            CompletenessResult.FAIL,
        ),
        "duplicate-export-idempotency": (
            ExportFailureType.DUPLICATE_IDEMPOTENCY,
            "idempotency_key",
            CompletenessResult.FAIL,
        ),
        "withdrawal-missing-mapping": (
            ExportFailureType.WITHDRAWAL_MAPPING_MISSING,
            "external_object_mappings",
            CompletenessResult.FAIL,
        ),
        "destination-unsupported-withdrawal": (
            ExportFailureType.DESTINATION_UNSUPPORTED,
            "destination_unsupported",
            CompletenessResult.NEEDS_REVIEW,
        ),
        "correction-without-withdrawal": (
            ExportFailureType.CORRECTION_WITHOUT_WITHDRAWAL,
            "withdrawal_job_ref",
            CompletenessResult.FAIL,
        ),
    }
    if scenario in failures:
        failure, missing, result = failures[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing,
            completion_result=result,
            policy_refs=policy_refs,
        )
    return _success_result(fixture_id=fixture_id, scenario=scenario, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
) -> ExportRuntimeResult:
    target_type = (
        ExportTargetType.API if scenario == "export-api-success" else ExportTargetType.FILE
    )
    target = _target(fixture_id, target_type, policy_refs)
    output_refs = [f"published-output:{fixture_id}:v1"]
    replacement_refs = [f"published-output:{fixture_id}:v2"]
    export_job_ref = f"export-job:{fixture_id}"
    export_attempt = _export_attempt(fixture_id, export_job_ref, output_refs)
    receipt = _delivery_receipt(
        fixture_id=fixture_id,
        attempt_ref=export_attempt.id,
        destination_ref=target.destination_ref,
        delivered_output_refs=output_refs,
        withdrawn_output_refs=[],
    )
    export_job = _export_job(
        fixture_id,
        target.id,
        output_refs,
        policy_refs,
        status=ExportJobStatus.COMPLETED,
        attempt_refs=[export_attempt.id],
        receipt_refs=[receipt.id],
    )

    withdrawal_job_ref = f"export-withdrawal-job:{fixture_id}"
    withdrawal_attempt = _withdrawal_attempt(
        fixture_id=fixture_id,
        withdrawal_job_ref=withdrawal_job_ref,
        output_refs=output_refs,
    )
    withdrawal_receipt = _delivery_receipt(
        fixture_id=f"{fixture_id}:withdrawal",
        attempt_ref=withdrawal_attempt.id,
        destination_ref=target.destination_ref,
        delivered_output_refs=[],
        withdrawn_output_refs=output_refs,
    )
    withdrawal_attempt.delivery_receipt_ref = withdrawal_receipt.id
    withdrawal_job = _withdrawal_job(
        fixture_id,
        target.id,
        output_refs,
        policy_refs,
        status=ExportWithdrawalStatus.COMPLETED,
        attempt_refs=[withdrawal_attempt.id],
    )

    replacement_job = _export_job(
        f"{fixture_id}:replacement",
        target.id,
        replacement_refs,
        policy_refs,
        status=ExportJobStatus.QUEUED,
    )
    correction = ExportCorrectionRecord(
        id=f"export-correction:{fixture_id}",
        project_id=f"project:{fixture_id}",
        superseded_output_ref=output_refs[0],
        replacement_output_ref=replacement_refs[0],
        withdrawal_job_ref=withdrawal_job.id,
        replacement_export_job_ref=replacement_job.id,
        destination_object_mappings={
            output_refs[0]: [f"external-object:{fixture_id}:v1"],
            replacement_refs[0]: [f"external-object:{fixture_id}:v2"],
        },
        receipt_refs=[receipt.id, withdrawal_receipt.id],
        policy_decision_refs=policy_refs,
        status=ExportCorrectionStatus.PROPAGATED,
    )
    report = ExportReconciliationReport(
        id=f"export-reconciliation-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        export_target_spec_refs=[target.id],
        export_job_refs=[export_job.id, replacement_job.id],
        export_attempt_refs=[export_attempt.id],
        delivery_receipt_refs=[receipt.id, withdrawal_receipt.id],
        withdrawal_job_refs=[withdrawal_job.id],
        withdrawal_attempt_refs=[withdrawal_attempt.id],
        correction_record_refs=[correction.id],
        destination_object_mapping_refs=[f"destination-object-mapping:{fixture_id}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:export"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:export"],
        outbox_refs=[f"outbox:{fixture_id}:export"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}",
        operator_status="export_reconciliation_completed",
        completion_result=CompletenessResult.PASS,
    )
    return ExportRuntimeResult(
        target_specs=[target],
        export_jobs=[export_job, replacement_job],
        export_attempts=[export_attempt],
        delivery_receipts=[receipt, withdrawal_receipt],
        withdrawal_jobs=[withdrawal_job],
        withdrawal_attempts=[withdrawal_attempt],
        correction_records=[correction],
        report=report,
    )


def _target(
    fixture_id: str,
    target_type: ExportTargetType,
    policy_refs: list[Ref],
) -> ExportTargetSpec:
    return ExportTargetSpec(
        id=f"export-target:{fixture_id}",
        project_id=f"project:{fixture_id}",
        target_type=target_type,
        destination_ref=f"destination:{fixture_id}:{target_type.value}",
        destination_schema_ref=f"destination-schema:{fixture_id}:v1",
        auth_scope_ref=f"auth-scope:{fixture_id}:redacted",
        delivery_mode=ExportDeliveryMode.BATCH,
        idempotency_key_template="{project_id}:{target_id}:{output_manifest_hash}",
        policy_decision_refs=policy_refs,
    )


def _export_job(
    fixture_id: str,
    target_ref: Ref,
    output_refs: list[Ref],
    policy_refs: list[Ref],
    *,
    status: ExportJobStatus,
    attempt_refs: list[Ref] | None = None,
    receipt_refs: list[Ref] | None = None,
) -> ExportJob:
    return ExportJob(
        id=f"export-job:{fixture_id}",
        run_id=f"run:{fixture_id}",
        export_target_spec_id=target_ref,
        output_refs=output_refs,
        destination_schema_version="v1",
        policy_decision_refs=policy_refs,
        attempt_refs=attempt_refs or [],
        delivery_receipt_refs=receipt_refs or [],
        idempotency_key_refs=[f"idempotency-key:{fixture_id}:export"],
        status=status,
    )


def _export_attempt(
    fixture_id: str,
    export_job_ref: Ref,
    output_refs: list[Ref],
) -> ExportAttempt:
    receipt_ref = f"export-receipt:{fixture_id}"
    return ExportAttempt(
        id=f"export-attempt:{fixture_id}:1",
        export_job_id=export_job_ref,
        attempt_number=1,
        idempotency_key=stable_hash({"fixture": fixture_id, "output_refs": output_refs}),
        output_refs=output_refs,
        external_object_ids=[f"external-object:{fixture_id}:v1"],
        delivery_receipt_ref=receipt_ref,
        status=ExportAttemptStatus.COMPLETED,
    )


def _delivery_receipt(
    *,
    fixture_id: str,
    attempt_ref: Ref,
    destination_ref: Ref,
    delivered_output_refs: list[Ref],
    withdrawn_output_refs: list[Ref],
) -> ExportDeliveryReceipt:
    external_ids = [
        f"external-object:{fixture_id}:{index}" for index, _ in enumerate(
            delivered_output_refs or withdrawn_output_refs,
            start=1,
        )
    ]
    payload = {
        "attempt_ref": attempt_ref,
        "destination_ref": destination_ref,
        "external_object_ids": external_ids,
        "delivered_output_refs": delivered_output_refs,
        "withdrawn_output_refs": withdrawn_output_refs,
    }
    return ExportDeliveryReceipt(
        id=f"export-receipt:{fixture_id}",
        export_attempt_id=attempt_ref,
        destination_ref=destination_ref,
        external_object_ids=external_ids,
        delivered_output_refs=delivered_output_refs,
        withdrawn_output_refs=withdrawn_output_refs,
        delete_propagation_refs=[
            f"delete-propagation:{fixture_id}"
        ]
        if withdrawn_output_refs
        else [],
        receipt_hash=stable_hash(payload),
    )


def _withdrawal_job(
    fixture_id: str,
    target_ref: Ref,
    output_refs: list[Ref],
    policy_refs: list[Ref],
    *,
    status: ExportWithdrawalStatus,
    attempt_refs: list[Ref] | None = None,
) -> ExportWithdrawalJob:
    return ExportWithdrawalJob(
        id=f"export-withdrawal-job:{fixture_id}",
        project_id=f"project:{fixture_id}",
        export_target_spec_id=target_ref,
        output_version_refs=output_refs,
        reason=ExportWithdrawalReason.SUPERSEDED,
        policy_decision_refs=policy_refs,
        withdrawal_attempt_refs=attempt_refs or [],
        status=status,
    )


def _withdrawal_attempt(
    *,
    fixture_id: str,
    withdrawal_job_ref: Ref,
    output_refs: list[Ref],
) -> ExportWithdrawalAttempt:
    return ExportWithdrawalAttempt(
        id=f"export-withdrawal-attempt:{fixture_id}:1",
        export_withdrawal_job_id=withdrawal_job_ref,
        attempt_number=1,
        idempotency_key=stable_hash({"withdraw": fixture_id, "outputs": output_refs}),
        external_object_mappings={output_refs[0]: [f"external-object:{fixture_id}:v1"]},
        propagation_status=ExportPropagationStatus.PROPAGATED,
        delivery_receipt_ref=f"export-receipt:{fixture_id}:withdrawal",
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: ExportFailureType,
    missing_field: str,
    completion_result: CompletenessResult,
    policy_refs: list[Ref],
) -> ExportRuntimeResult:
    target = _target(fixture_id, ExportTargetType.FILE, policy_refs)
    report = ExportReconciliationReport(
        id=f"export-reconciliation-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        export_target_spec_refs=[target.id],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:export"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:export"],
        failure_report_refs=[f"export-failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=completion_result,
    )
    return ExportRuntimeResult(
        target_specs=[target],
        export_jobs=[],
        export_attempts=[],
        delivery_receipts=[],
        withdrawal_jobs=[],
        withdrawal_attempts=[],
        correction_records=[],
        report=report,
    )
