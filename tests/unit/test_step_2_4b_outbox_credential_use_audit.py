"""Unit tests for ``OutboxCredentialUseAuditWriter``.

The durable production-ready :class:`CredentialUseAuditPort` impl.
Asserts: every ``record`` call persists the use record + writes
one outbox row referencing the persistent payload, with the
canonical ``"credential-use"`` dispatch topic.
"""

from __future__ import annotations

from datetime import UTC, datetime

from veracrawl.adapters.credential_vault.outbox_credential_use_audit import (
    OutboxCredentialUseAuditWriter,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.security_privacy import CredentialUseRecord
from veracrawl.ports.credential_use_audit import CredentialUseAuditPort


class _InMemoryOutboxRepo:
    """Minimal :class:`OutboxRepositoryPort` impl that records
    outbox rows for assertion."""

    def __init__(self) -> None:
        self.appended: list[OutboxRecord] = []

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.appended.append(record)
        return f"outbox-ref:{record.id}"

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        del run_ref
        return list(self.appended)

    def mark_outbox_dispatched(
        self, outbox_ref: Ref, *, dispatched_at_ref: Ref
    ) -> OutboxRecord:
        del outbox_ref, dispatched_at_ref
        raise NotImplementedError

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        del outbox_ref, error_ref
        raise NotImplementedError


def _make_use_record() -> CredentialUseRecord:
    return CredentialUseRecord(
        id="credential-use:abc",
        run_ref="run:test:1",
        credential_scope_ref="cred-scope:ebay",
        request_url="https://api.example.com/v1/items",
        request_method="GET",
        response_status=200,
        timestamp_used=datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC),
        attempt_evidence_ref=None,
    )


def test_record_persists_payload_and_appends_outbox_row() -> None:
    persisted: list[CredentialUseRecord] = []

    def persister(rec: CredentialUseRecord) -> Ref:
        persisted.append(rec)
        return f"payload:{rec.id}"

    repo = _InMemoryOutboxRepo()
    writer = OutboxCredentialUseAuditWriter(
        record_persister=persister,
        outbox_repo=repo,
        command_result_ref="cmd-result:run:test:1",
        event_ref="event:run:test:1",
    )
    use_record = _make_use_record()
    writer.record(use_record)

    assert len(persisted) == 1
    assert persisted[0] is use_record
    assert len(repo.appended) == 1
    outbox_row = repo.appended[0]
    assert outbox_row.run_ref == use_record.run_ref
    assert outbox_row.command_result_ref == "cmd-result:run:test:1"
    assert outbox_row.event_ref == "event:run:test:1"
    assert outbox_row.dispatch_topic == "credential-use"
    assert outbox_row.payload_ref == f"payload:{use_record.id}"
    assert outbox_row.idempotency_key == use_record.id


def test_writer_satisfies_protocol() -> None:
    repo = _InMemoryOutboxRepo()

    def persister(rec: CredentialUseRecord) -> Ref:
        del rec
        return "payload:fixture"

    writer: CredentialUseAuditPort = OutboxCredentialUseAuditWriter(
        record_persister=persister,
        outbox_repo=repo,
        command_result_ref="cmd:r",
        event_ref="event:r",
    )
    assert isinstance(writer, CredentialUseAuditPort)


def test_writer_does_not_gate_under_production() -> None:
    """The outbox-backed writer IS production-ready (durable);
    no ProductionRuntimeNotImplemented gate."""

    from veracrawl.runtime_support.runtime_mode import (
        RuntimeMode,
        with_runtime_mode,
    )

    persisted: list[CredentialUseRecord] = []
    repo = _InMemoryOutboxRepo()
    writer = OutboxCredentialUseAuditWriter(
        record_persister=lambda r: (persisted.append(r), f"payload:{r.id}")[1],
        outbox_repo=repo,
        command_result_ref="cmd:r",
        event_ref="event:r",
    )
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        writer.record(_make_use_record())
    assert len(persisted) == 1
    assert len(repo.appended) == 1
