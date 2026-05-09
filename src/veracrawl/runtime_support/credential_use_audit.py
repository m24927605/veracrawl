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

from veracrawl.contracts.errors import _redact_url
from veracrawl.contracts.security_privacy import CredentialUseRecord
from veracrawl.runtime_support.logging import get_logger
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_logger = get_logger(__name__)


class LoggingCredentialUseAuditWriter:
    """Structured-log-backed :class:`CredentialUseAuditPort` impl.

    **Fixture / development only.** Structured logging can drop /
    buffer / fail outside the contract this writer's caller
    assumes. design.md acceptance requires credential uses to
    produce durable :class:`CredentialUseRecord` outbox events
    that the audit pipeline can replay; a log line is not an
    append-only audit record. Phase 6 step 6.1 ships an outbox-
    backed alternate; production deployments wire that.

    The writer is therefore production-mode-gated symmetric with
    Phase 2 step 2.1's :class:`EnvVarVault`: under
    :class:`RuntimeMode.PRODUCTION` every ``record`` call raises
    :class:`ProductionRuntimeNotImplemented` so a wiring
    regression cannot silently route production credential-use
    audits through structured logs.

    Stateless — safe to share across runs / threads. The
    underlying structlog logger is itself thread-safe.

    URL sanitization (codex iter-1 important): the writer applies
    :func:`_redact_url` to the record's ``request_url`` field
    before logging. The adapter (Phase 2 step 2.4b) ALSO
    sanitizes at the record layer (codex iter-2 critical), so
    this is defense in depth.
    """

    def record(self, use_record: CredentialUseRecord) -> None:
        if current_mode() is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="logging_credential_use_audit",
                gate="credential_use_audit",
            )
        _logger.info(
            "credential_use",
            id=use_record.id,
            run_ref=use_record.run_ref,
            credential_scope_ref=use_record.credential_scope_ref,
            request_url=_redact_url(use_record.request_url),
            request_method=use_record.request_method,
            response_status=use_record.response_status,
            timestamp_iso=use_record.timestamp_used.isoformat(),
            attempt_evidence_ref=use_record.attempt_evidence_ref,
        )


__all__ = ["LoggingCredentialUseAuditWriter"]
