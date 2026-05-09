"""Unit tests for ``LoggingCredentialUseAuditWriter``."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from veracrawl.contracts.security_privacy import CredentialUseRecord
from veracrawl.ports.credential_use_audit import CredentialUseAuditPort
from veracrawl.runtime_support.credential_use_audit import (
    LoggingCredentialUseAuditWriter,
)


def _make_record(*, response_status: int | None = 200) -> CredentialUseRecord:
    return CredentialUseRecord(
        id="credential-use:abc123",
        run_ref="run:test:1",
        credential_scope_ref="cred-scope:ebay",
        request_url="https://api.example.com/v1/items",
        request_method="GET",
        response_status=response_status,
        timestamp_used=datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC),
        attempt_evidence_ref=None if response_status is not None else "attempt:abc",
    )


def test_record_writes_structured_event() -> None:
    writer = LoggingCredentialUseAuditWriter()
    with structlog.testing.capture_logs() as captured:
        writer.record(_make_record())
    matched = [entry for entry in captured if entry.get("event") == "credential_use"]
    assert len(matched) == 1
    entry = matched[0]
    assert entry["id"] == "credential-use:abc123"
    assert entry["run_ref"] == "run:test:1"
    assert entry["credential_scope_ref"] == "cred-scope:ebay"
    assert entry["request_url"] == "https://api.example.com/v1/items"
    assert entry["request_method"] == "GET"
    assert entry["response_status"] == 200
    assert entry["timestamp_iso"] == "2026-05-09T12:00:00+00:00"


def test_writer_satisfies_protocol() -> None:
    writer: CredentialUseAuditPort = LoggingCredentialUseAuditWriter()
    assert isinstance(writer, CredentialUseAuditPort)


def test_record_sanitizes_url_query_and_userinfo() -> None:
    """Codex iter-1 important: URLs commonly carry credentials in
    query strings or userinfo. The writer must drop both before
    logging. Same redaction helper Phase 0 step 0.4 uses for typed
    exception messages."""

    leaky = CredentialUseRecord(
        id="credential-use:abc",
        run_ref="run:test:1",
        credential_scope_ref="cred-scope:ebay",
        request_url="https://user:pass@api.example.com/v1/items?api_key=SECRET&session=DEADBEEF",
        request_method="GET",
        response_status=200,
        timestamp_used=datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC),
        attempt_evidence_ref=None,
    )
    writer = LoggingCredentialUseAuditWriter()
    with structlog.testing.capture_logs() as captured:
        writer.record(leaky)
    matched = [e for e in captured if e.get("event") == "credential_use"]
    assert len(matched) == 1
    logged_url = matched[0]["request_url"]
    assert "user:pass@" not in logged_url
    assert "SECRET" not in logged_url
    assert "DEADBEEF" not in logged_url
    assert "api_key" not in logged_url
    assert "session" not in logged_url
