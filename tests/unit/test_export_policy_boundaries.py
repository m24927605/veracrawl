from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    ExportCorrectionStatus,
    ExportPropagationStatus,
    ExportWithdrawalReason,
    ExportWithdrawalStatus,
)
from veracrawl.contracts.export import (
    ExportCorrectionRecord,
    ExportWithdrawalAttempt,
    ExportWithdrawalJob,
)


def test_withdrawal_job_requires_policy_refs() -> None:
    with pytest.raises(ValidationError):
        ExportWithdrawalJob(
            id="export-withdrawal-job:bad",
            project_id="project:bad",
            export_target_spec_id="export-target:bad",
            output_version_refs=["published-output:bad"],
            reason=ExportWithdrawalReason.OPERATOR_WITHDRAWAL,
            status=ExportWithdrawalStatus.QUEUED,
        )


def test_propagated_withdrawal_requires_external_mappings_and_receipt() -> None:
    with pytest.raises(ValidationError):
        ExportWithdrawalAttempt(
            id="export-withdrawal-attempt:bad",
            export_withdrawal_job_id="export-withdrawal-job:bad",
            attempt_number=1,
            idempotency_key="withdrawal:bad",
            propagation_status=ExportPropagationStatus.PROPAGATED,
        )


def test_destination_unsupported_withdrawal_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ExportWithdrawalAttempt(
            id="export-withdrawal-attempt:unsupported",
            export_withdrawal_job_id="export-withdrawal-job:unsupported",
            attempt_number=1,
            idempotency_key="withdrawal:unsupported",
            propagation_status=ExportPropagationStatus.DESTINATION_UNSUPPORTED,
        )


def test_propagated_correction_requires_withdrawal_and_replacement_refs() -> None:
    with pytest.raises(ValidationError):
        ExportCorrectionRecord(
            id="export-correction:bad",
            project_id="project:bad",
            superseded_output_ref="published-output:v1",
            replacement_output_ref="published-output:v2",
            policy_decision_refs=["policy:bad:export"],
            status=ExportCorrectionStatus.PROPAGATED,
        )
