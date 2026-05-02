from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    OpsFailureType,
    OpsRecoveryStatus,
    OpsSeverity,
    RecoveryActionType,
)
from veracrawl.contracts.ops import FailureRecord, RecoveryAction


def test_side_effecting_recovery_requires_policy_and_approval_refs() -> None:
    with pytest.raises(ValidationError):
        RecoveryAction(
            id="recovery-action:bad",
            failure_record_id="failure-record:bad",
            action_type=RecoveryActionType.DELETE_ARTIFACT,
            command_refs=["command:delete-artifact"],
            status=OpsRecoveryStatus.APPROVED,
        )


def test_completed_recovery_requires_result_refs() -> None:
    with pytest.raises(ValidationError):
        RecoveryAction(
            id="recovery-action:bad-completed",
            failure_record_id="failure-record:bad",
            action_type=RecoveryActionType.RETRY_COMMAND,
            command_refs=["command:retry"],
            status=OpsRecoveryStatus.COMPLETED,
        )


def test_failure_record_requires_policy_refs() -> None:
    with pytest.raises(ValidationError):
        FailureRecord(
            id="failure-record:bad",
            run_id="run:bad",
            failure_type=OpsFailureType.POLICY,
            failed_ref="recovery-action:bad",
            owner_service_ref="owner-service:ops",
            severity=OpsSeverity.HIGH,
            retryable=False,
        )
