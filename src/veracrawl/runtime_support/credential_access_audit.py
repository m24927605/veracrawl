"""``LoggingCredentialAccessAuditWriter`` — structured-log default.

The default :class:`~veracrawl.ports.credential_access_audit.CredentialAccessAuditPort`
implementation. Writes one structured-log event per credential
fetch attempt via :func:`veracrawl.runtime_support.logging.get_logger`
so existing log aggregation pipelines (Datadog / Splunk / OTLP) can
correlate vault accesses with run identifiers + structured outcomes
without a separate persistence layer. Phase 6 ships an outbox-
backed alternate that satisfies the same port; production
deployments swap via wiring.

The structured fields emitted:

* ``event``: ``"credential_access"`` (stable string for log
  aggregation grep).
* ``scope_ref``: caller-supplied (env-var-safe shape, OR the
  literal ``"[REDACTED]"`` placeholder when the original failed
  identifier-shape validation).
* ``key``: caller-supplied (env-var-safe shape, OR
  ``"[REDACTED]"``).
* ``outcome``: structured ``CredentialAccessOutcome`` value.
* ``run_ref``: caller-supplied opaque identifier.
* ``timestamp_iso``: ISO-8601 tz-aware string (deterministic
  serialization for replay).

The credential value is **never** logged. The structured-log
processor pipeline (``RedactSensitiveProcessor``) provides defense
in depth in case a future change inadvertently passes credential
data through; this writer's contract guarantees it never does so
intentionally.
"""

from __future__ import annotations

from datetime import datetime

from veracrawl.contracts.common import Ref
from veracrawl.ports.credential_access_audit import CredentialAccessOutcome
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)


class LoggingCredentialAccessAuditWriter:
    """Structured-log-backed :class:`CredentialAccessAuditPort` impl.

    Stateless — safe to share across runs / threads. The underlying
    structlog logger is itself thread-safe.
    """

    def record(
        self,
        *,
        scope_ref: str,
        key: str,
        outcome: CredentialAccessOutcome,
        run_ref: Ref,
        timestamp: datetime,
    ) -> None:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError(
                "credential access audit timestamp must be timezone-aware "
                "(replay determinism)"
            )
        _logger.info(
            "credential_access",
            scope_ref=scope_ref,
            key=key,
            outcome=outcome.value,
            run_ref=run_ref,
            timestamp_iso=timestamp.isoformat(),
        )


__all__ = ["LoggingCredentialAccessAuditWriter"]
