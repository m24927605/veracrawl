from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    DurableCommandRecordStatus,
    PersistenceAdapterKind,
    PersistenceCapability,
    PersistentQueueOperation,
    ScaleQueueName,
    UnitOfWorkStatus,
)
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceAdapterSpec,
    PersistenceRuntimeReport,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)


def test_persistence_adapter_requires_all_capabilities() -> None:
    spec = PersistenceAdapterSpec(
        id="persistence-adapter:unit",
        adapter_kind=PersistenceAdapterKind.REFERENCE_FILESYSTEM,
        capability_refs=list(PersistenceCapability),
        port_refs=["port:metadata", "port:event", "port:outbox", "port:artifact", "port:queue"],
        transaction_supported=True,
        idempotency_supported=True,
        lease_supported=True,
        policy_decision_refs=["policy:unit:persistence"],
    )
    assert len(spec.capability_refs) == len(PersistenceCapability)
    with pytest.raises(ValidationError):
        PersistenceAdapterSpec(
            id="persistence-adapter:bad",
            adapter_kind=PersistenceAdapterKind.EXTERNAL_ADAPTER,
            capability_refs=[PersistenceCapability.METADATA_STORE],
            port_refs=["port:metadata"],
            transaction_supported=True,
            idempotency_supported=True,
            lease_supported=True,
            policy_decision_refs=["policy:bad:persistence"],
        )


def test_committed_transaction_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        PersistenceTransactionRecord(
            id="transaction:bad",
            adapter_ref="adapter:bad",
            run_ref="run:bad",
            unit_of_work_ref="uow:bad",
            status=UnitOfWorkStatus.COMMITTED,
        )


def test_committed_idempotency_requires_side_effect_refs() -> None:
    with pytest.raises(ValidationError):
        IdempotencyPersistenceRecord(
            id="idempotency:bad",
            idempotency_key="idem:bad",
            command_identity="cmd|Fixture|bad|idem",
            command_record_ref="durable-command:bad",
            status=DurableCommandRecordStatus.COMMITTED,
        )


def test_heartbeat_queue_operation_requires_heartbeat_ref() -> None:
    with pytest.raises(ValidationError):
        PersistentQueueOperationRecord(
            id="queue-op:bad",
            queue_name=ScaleQueueName.FRONTIER,
            operation=PersistentQueueOperation.HEARTBEAT,
            queue_item_ref="queue-item:bad",
            lease_ref="lease:bad",
            lease_token_ref="lease-token:bad",
        )


def test_pass_report_requires_persistence_refs() -> None:
    with pytest.raises(ValidationError):
        PersistenceRuntimeReport(
            id="persistence-report:bad",
            run_ref="run:bad",
            operator_status="persistence_queue_runtime_completed",
            completion_result=CompletenessResult.PASS,
        )
