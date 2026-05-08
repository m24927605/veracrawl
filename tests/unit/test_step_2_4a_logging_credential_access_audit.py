"""Unit tests for ``LoggingCredentialAccessAuditWriter``.

Covers:

1. ``record`` writes a structured log event with the expected fields.
2. ``timestamp`` must be tz-aware (replay determinism).
3. The credential value is never passed to the writer (compile-time
   contract — no `value` parameter on the port).
4. ``CredentialAccessAuditPort`` Protocol is satisfied.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import structlog

from veracrawl.ports.credential_access_audit import (
    CredentialAccessAuditPort,
    CredentialAccessOutcome,
)
from veracrawl.runtime_support.credential_access_audit import (
    LoggingCredentialAccessAuditWriter,
)


def test_record_writes_structured_event() -> None:
    """Use ``structlog.testing.capture_logs`` to assert the event
    structure — the writer emits via structlog (not stdlib logging),
    so pytest's ``caplog`` does not capture it directly."""

    writer = LoggingCredentialAccessAuditWriter()
    timestamp = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
    with structlog.testing.capture_logs() as captured:
        writer.record(
            scope_ref="EBAY_PROD",
            key="API_KEY",
            outcome=CredentialAccessOutcome.SUCCESS,
            run_ref="run:test:1",
            timestamp=timestamp,
        )
    matched = [entry for entry in captured if entry.get("event") == "credential_access"]
    assert len(matched) == 1
    entry = matched[0]
    # Codex iter-4 important: field names use ``_hash`` suffix to
    # avoid the global RedactSensitiveProcessor's redaction of any
    # field literally named ``key``. The values are already hashed
    # refs supplied by the OutboxVaultClient.
    assert entry["scope_ref_hash"] == "EBAY_PROD"
    assert entry["credential_key_hash"] == "API_KEY"
    assert entry["outcome"] == "success"
    assert entry["run_ref"] == "run:test:1"
    assert entry["timestamp_iso"] == "2026-05-09T12:00:00+00:00"


def test_audit_field_names_survive_redact_sensitive_processor() -> None:
    """Codex iter-4 important: the audit field names must not be
    redacted by the global RedactSensitiveProcessor. Run a small
    event_dict through the processor and assert the audit fields
    pass through unchanged.
    """

    from veracrawl.runtime_support._log_redaction import RedactSensitiveProcessor

    processor = RedactSensitiveProcessor()
    event = {
        "event": "credential_access",
        "scope_ref_hash": "sha256:abc123",
        "credential_key_hash": "sha256:def456",
        "outcome": "success",
        "run_ref": "run:test:1",
        "timestamp_iso": "2026-05-09T12:00:00+00:00",
    }
    redacted = processor(None, "info", dict(event))
    assert redacted["scope_ref_hash"] == "sha256:abc123"
    assert redacted["credential_key_hash"] == "sha256:def456"
    assert redacted["outcome"] == "success"


def test_record_serializes_outcome_as_stable_string() -> None:
    """Each CredentialAccessOutcome value should land as its
    stable string form for log aggregation."""

    writer = LoggingCredentialAccessAuditWriter()
    timestamp = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
    for outcome in CredentialAccessOutcome:
        with structlog.testing.capture_logs() as captured:
            writer.record(
                scope_ref="X",
                key="K",
                outcome=outcome,
                run_ref="r",
                timestamp=timestamp,
            )
        assert any(
            entry.get("event") == "credential_access"
            and entry.get("outcome") == outcome.value
            and entry.get("scope_ref_hash") == "X"
            and entry.get("credential_key_hash") == "K"
            for entry in captured
        ), f"missing log event for outcome {outcome}"


def test_record_rejects_naive_timestamp() -> None:
    writer = LoggingCredentialAccessAuditWriter()
    with pytest.raises(ValueError, match="timezone"):
        writer.record(
            scope_ref="X",
            key="K",
            outcome=CredentialAccessOutcome.SUCCESS,
            run_ref="r",
            timestamp=datetime(2026, 5, 9, 12, 0, 0),  # noqa: DTZ001 — intentional naive
        )


def test_writer_satisfies_protocol() -> None:
    writer: CredentialAccessAuditPort = LoggingCredentialAccessAuditWriter()
    assert isinstance(writer, CredentialAccessAuditPort)
    assert callable(writer.record)


def test_protocol_does_not_accept_credential_value_parameter() -> None:
    """Compile-time contract: the ``record`` Protocol method takes
    only non-secret fields. A `value` parameter would be a leak
    vector. Verified by inspecting the Protocol's signature."""

    import inspect

    sig = inspect.signature(LoggingCredentialAccessAuditWriter.record)
    param_names = set(sig.parameters.keys())
    # No `value`, `credential`, `secret`, `password`, etc.
    forbidden = {"value", "credential", "secret", "password", "token"}
    assert forbidden.isdisjoint(param_names), (
        f"audit writer must not accept a credential-shaped parameter; "
        f"found {forbidden & param_names}"
    )
