"""Tests for veracrawl.runtime_support._log_redaction."""

from __future__ import annotations

import pytest

from veracrawl.runtime_support._log_redaction import (
    REDACTED,
    RedactSensitiveProcessor,
    is_sensitive_key,
)


@pytest.mark.parametrize(
    "key",
    [
        "body",
        "request_body",
        "response_body",
        "response_text",
        "prompt",
        "system_prompt",
        "user_prompt",
        "payload",
        "request_payload",
        "token",
        "tokens",
        "auth_token",
        "access_token",
        "secret",
        "client_secret",
        "key",
        "api_key",
        "apikey",
        "api-key",
        "cookie",
        "set_cookie",
        "set-cookie",
        "authorization",
        "proxy_authorization",
        "proxy-authorization",
    ],
)
def test_is_sensitive_key_matches_known_sensitive(key: str) -> None:
    assert is_sensitive_key(key), f"{key!r} should be classified as sensitive"


@pytest.mark.parametrize(
    "key",
    [
        "event",
        "count",
        "url",
        "status_code",
        "elapsed_ms",
        "duration",
        "body_size_bytes",  # not a body content
        "somebody",  # word "body" appears but no boundary
        "nobody",
        "anybody",
        "monkey",  # ends with "key" but lacks api-prefix structure
        "fishbowl",
        "tokenize",  # "token" appears but no boundary suffix
        "Authorization_status",  # not exact match
        "secrets_count",  # plural with suffix
    ],
)
def test_is_sensitive_key_does_not_false_positive(key: str) -> None:
    assert not is_sensitive_key(key), f"{key!r} should NOT be classified as sensitive"


def test_processor_redacts_in_place() -> None:
    proc = RedactSensitiveProcessor()
    event = {"event": "test", "body": "secret content", "count": 5}
    result = proc(None, "info", event)

    assert result is event  # in-place mutation
    assert result["body"] == REDACTED
    assert result["count"] == 5
    assert result["event"] == "test"


def test_processor_redacts_multiple_keys() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "auth_attempt",
        "authorization": "Bearer abc123",
        "api_key": "sk-secret",
        "user": "alice",
        "request_body": "{}",
    }
    result = proc(None, "info", event)

    assert result["authorization"] == REDACTED
    assert result["api_key"] == REDACTED
    assert result["request_body"] == REDACTED
    assert result["user"] == "alice"
    assert result["event"] == "auth_attempt"


def test_processor_preserves_benign_keys() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "x",
        "body_size_bytes": 1024,
        "somebody": "alice",
        "monkey": "george",
        "tokenize": True,
    }
    result = proc(None, "info", dict(event))

    for key, value in event.items():
        assert result[key] == value, f"{key!r} was wrongly redacted"


def test_processor_ignores_non_string_keys() -> None:
    proc = RedactSensitiveProcessor()
    # structlog event_dict in practice has str keys, but the processor
    # should not crash on int keys if upstream code is unusual.
    event: dict[object, object] = {"event": "x", 42: "answer", "body": "secret"}
    result = proc(None, "info", event)  # type: ignore[arg-type]

    assert result[42] == "answer"
    assert result["body"] == REDACTED


def test_processor_handles_empty_dict() -> None:
    proc = RedactSensitiveProcessor()
    result = proc(None, "info", {})
    assert result == {}


def test_redacted_constant_is_stable() -> None:
    # Other modules and tests assert literal "<redacted>"; lock it in.
    assert REDACTED == "<redacted>"
