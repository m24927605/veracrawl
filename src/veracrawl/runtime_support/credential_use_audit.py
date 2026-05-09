"""``LoggingCredentialUseAuditWriter`` — structured-log default.

The default :class:`~veracrawl.ports.credential_use_audit.CredentialUseAuditPort`
implementation. Writes one structured-log event per authorized
HTTP request via :func:`veracrawl.runtime_support.logging.get_logger`.
Phase 6 ships an outbox-backed alternate that satisfies the same
port; production deployments swap via wiring.

The structured fields mirror the Phase 0
:class:`CredentialUseRecord` contract — the writer just renders
the record's fields as keyword arguments. The credential value is
never on the record shape, so the writer cannot accidentally
expose the secret.

Field naming consideration (codex iter-4 lesson from step 2.4a):
the global ``RedactSensitiveProcessor`` redacts any top-level
field literally named ``key``. The Phase 0
:class:`CredentialUseRecord` doesn't use that field name — it has
``credential_scope_ref``, ``request_url``, ``request_method``,
``response_status``, ``timestamp_used``, ``attempt_evidence_ref``,
``id``, ``run_ref``. None of those collide with the redaction
processor.
"""

from __future__ import annotations

from veracrawl.contracts.security_privacy import CredentialUseRecord
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)


class LoggingCredentialUseAuditWriter:
    """Structured-log-backed :class:`CredentialUseAuditPort` impl.

    Stateless — safe to share across runs / threads. The
    underlying structlog logger is itself thread-safe.
    """

    def record(self, use_record: CredentialUseRecord) -> None:
        _logger.info(
            "credential_use",
            id=use_record.id,
            run_ref=use_record.run_ref,
            credential_scope_ref=use_record.credential_scope_ref,
            request_url=use_record.request_url,
            request_method=use_record.request_method,
            response_status=use_record.response_status,
            timestamp_iso=use_record.timestamp_used.isoformat(),
            attempt_evidence_ref=use_record.attempt_evidence_ref,
        )


__all__ = ["LoggingCredentialUseAuditWriter"]
