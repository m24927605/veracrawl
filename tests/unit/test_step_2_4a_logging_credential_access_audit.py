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
    assert entry["scope_ref"] == "EBAY_PROD"
    assert entry["key"] == "API_KEY"
    assert entry["outcome"] == "success"
    assert entry["run_ref"] == "run:test:1"
    assert entry["timestamp_iso"] == "2026-05-09T12:00:00+00:00"


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
