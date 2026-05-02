from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ExportDeliveryMode,
    ExportJobStatus,
    ExportTargetType,
)
from veracrawl.contracts.export import (
    ExportJob,
    ExportReconciliationReport,
    ExportTargetSpec,
)


def test_export_target_supports_all_target_types() -> None:
    for target_type in ExportTargetType:
        target = ExportTargetSpec(
            id=f"export-target:{target_type.value}",
            project_id="project:unit",
            target_type=target_type,
            destination_ref=f"destination:{target_type.value}",
            destination_schema_ref="destination-schema:unit",
            auth_scope_ref="auth-scope:unit",
            delivery_mode=ExportDeliveryMode.BATCH,
            idempotency_key_template="{project_id}:{target_id}:{output_manifest_hash}",
            policy_decision_refs=["policy:unit:export"],
        )
        assert target.target_type == target_type


def test_export_target_requires_idempotency_template() -> None:
    with pytest.raises(ValidationError):
        ExportTargetSpec(
            id="export-target:bad",
            project_id="project:bad",
            target_type=ExportTargetType.FILE,
            destination_ref="destination:bad",
            destination_schema_ref="destination-schema:bad",
            auth_scope_ref="auth-scope:bad",
            delivery_mode=ExportDeliveryMode.BATCH,
            idempotency_key_template="{project_id}",
            policy_decision_refs=["policy:bad:export"],
        )


def test_completed_export_job_requires_receipt_refs() -> None:
    with pytest.raises(ValidationError):
        ExportJob(
            id="export-job:bad",
            run_id="run:bad",
            export_target_spec_id="export-target:bad",
            output_refs=["published-output:bad"],
            destination_schema_version="v1",
            policy_decision_refs=["policy:bad:export"],
            idempotency_key_refs=["idempotency:bad"],
            status=ExportJobStatus.COMPLETED,
        )


def test_export_reconciliation_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        ExportReconciliationReport(
            id="export-reconciliation:bad",
            run_ref="run:bad",
            export_target_spec_refs=["export-target:bad"],
            export_job_refs=["export-job:bad"],
            export_attempt_refs=["export-attempt:bad"],
            delivery_receipt_refs=["receipt:bad"],
            destination_object_mapping_refs=["mapping:bad"],
            policy_decision_refs=["policy:bad:export"],
            operator_status="export_reconciliation_completed",
            completion_result=CompletenessResult.PASS,
        )
