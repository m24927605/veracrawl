"""``OutboxCredentialUseAuditWriter`` — durable outbox-backed.

The production-ready :class:`CredentialUseAuditPort` impl. Wraps
the Phase 0 :class:`OutboxRepositoryPort` so each
:class:`CredentialUseRecord` lands as a durable outbox row that
the audit pipeline (Phase 6) dispatches.

This adapter is structurally complete (not gated under
PRODUCTION) but depends on injected components for actual
durability:

* ``record_persister``: a callable that durably stores the
  :class:`CredentialUseRecord` and returns its persistent
  payload ref. Phase 6 wires this to the project's record store
  (Postgres / S3 / etc.); fixture wiring uses a list-backed
  in-memory persister.
* ``outbox_repo``: :class:`OutboxRepositoryPort` (Phase 0
  contract) that writes the outbox row referencing the
  persisted payload.

The outbox row's ``dispatch_topic`` is the constant
``"credential-use"`` so Phase 6 dispatchers can subscribe to
this topic specifically.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.security_privacy import CredentialUseRecord
from veracrawl.ports.durable import OutboxRepositoryPort


class OutboxCredentialUseAuditWriter:
    """Outbox-backed :class:`CredentialUseAuditPort` impl.

    Stateless beyond its injected dependencies. Safe to share
    across runs / threads (the underlying ports are thread-safe).
    """

    def __init__(
        self,
        *,
        record_persister: Callable[[CredentialUseRecord], Ref],
        outbox_repo: OutboxRepositoryPort,
        command_result_ref: Ref,
        event_ref: Ref,
    ) -> None:
        # ``command_result_ref`` and ``event_ref`` are required by
        # the Phase 0 ``OutboxRecord`` contract. The orchestrator
        # supplies them at wiring time (typically the agent
        # runtime's run-control command/event refs that govern the
        # session). The same pair is reused for every audit row in
        # the run because they identify the run-control commit
        # that authorized the session, not the per-request flow.
        self._record_persister = record_persister
        self._outbox_repo = outbox_repo
        self._command_result_ref = command_result_ref
        self._event_ref = event_ref

    def record(self, use_record: CredentialUseRecord) -> None:
        payload_ref = self._record_persister(use_record)
        outbox_row = OutboxRecord(
            id=f"outbox:credential-use:{uuid.uuid4().hex}",
            run_ref=use_record.run_ref,
            command_result_ref=self._command_result_ref,
            event_ref=self._event_ref,
            dispatch_topic="credential-use",
            payload_ref=payload_ref,
            idempotency_key=use_record.id,
        )
        self._outbox_repo.append_outbox(outbox_row)


__all__ = ["OutboxCredentialUseAuditWriter"]
