"""Tests for veracrawl.runtime_support._log_redaction."""

from __future__ import annotations

from typing import Any

import pytest

from veracrawl.runtime_support._log_redaction import (
    REDACTED,
    RedactSensitiveProcessor,
    is_sensitive_key,
)


@pytest.mark.parametrize(
    "key",
    [
        # body family
        "body",
        "request_body",
        "response_body",
        "response_text",
        # prompt family
        "prompt",
        "system_prompt",
        "user_prompt",
        # payload family
        "payload",
        "request_payload",
        # token family
        "token",
        "tokens",
        "auth_token",
        "access_token",
        "refresh_token",
        "bearer_token",
        "csrf_token",
        # secret family
        "secret",
        "client_secret",
        # key family
        "key",
        "api_key",
        "apikey",
        "api-key",
        "x-api-key",
        "private_key",
        "shared_key",
        # password family
        "password",
        "passwd",
        "user_password",
        # credentials family
        "credential",
        "credentials",
        "user_credentials",
        # cookie family
        "cookie",
        "set_cookie",
        "set-cookie",
        # authorization family
        "authorization",
        "proxy_authorization",
        "proxy-authorization",
        # csrf
        "csrf",
        "_csrf",
        # session id
        "session_id",
        "session-id",
        "user_session_id",
    ],
)
def test_is_sensitive_key_matches_known_sensitive(key: str) -> None:
    assert is_sensitive_key(key), f"{key!r} should be classified as sensitive"


@pytest.mark.parametrize(
    "key",
    [
        # generic non-sensitive names
        "event",
        "count",
        "url",
        "status_code",
        "elapsed_ms",
        "duration",
        # body-like but unrelated
        "body_size_bytes",
        "somebody",
        "nobody",
        "anybody",
        # key-like but unrelated
        "monkey",
        "donkey",
        # token-like but unrelated
        "tokenize",
        "tokenizer",
        # secret-like but unrelated
        "secrets_count",
        # session-like but not session id
        "session_count",
        "session_duration",
        # credential-like but unrelated
        "credentialed",
        # cookie-like but unrelated
        "cookies_accepted_at",  # ends with "at", not "cookie"
        # CSRF-like but not the field itself
        "csrfs_count",
    ],
)
def test_is_sensitive_key_does_not_false_positive(key: str) -> None:
    assert not is_sensitive_key(key), f"{key!r} should NOT be classified as sensitive"


def test_processor_redacts_in_place_at_top_level() -> None:
    proc = RedactSensitiveProcessor()
    event = {"event": "test", "body": "secret content", "count": 5}
    result = proc(None, "info", event)

    assert result is event
    assert result["body"] == REDACTED
    assert result["count"] == 5
    assert result["event"] == "test"


def test_processor_redacts_multiple_top_level_keys() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "auth_attempt",
        "authorization": "Bearer abc123",
        "api_key": "sk-secret",
        "password": "hunter2",
        "user": "alice",
        "request_body": "{}",
    }
    result = proc(None, "info", event)

    assert result["authorization"] == REDACTED
    assert result["api_key"] == REDACTED
    assert result["password"] == REDACTED
    assert result["request_body"] == REDACTED
    assert result["user"] == "alice"
    assert result["event"] == "auth_attempt"


def test_processor_redacts_nested_dict_keys() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "outbound_request",
        "headers": {
            "Authorization": "Bearer token",
            "X-API-Key": "sk-xyz",
            "User-Agent": "veracrawl/1",
            "Content-Type": "application/json",
        },
        "request": {
            "method": "POST",
            "body": "{\"q\":\"hello\"}",
        },
    }
    result = proc(None, "info", event)

    # Nested headers redacted
    assert result["headers"]["Authorization"] == REDACTED
    assert result["headers"]["X-API-Key"] == REDACTED
    # Benign headers preserved
    assert result["headers"]["User-Agent"] == "veracrawl/1"
    assert result["headers"]["Content-Type"] == "application/json"
    # Nested request body redacted; non-sensitive sibling preserved
    assert result["request"]["body"] == REDACTED
    assert result["request"]["method"] == "POST"


def test_processor_redacts_nested_list_of_dicts() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "batch_call",
        "calls": [
            {"id": "a", "body": "secret1"},
            {"id": "b", "body": "secret2"},
        ],
    }
    result = proc(None, "info", event)

    assert result["calls"][0]["id"] == "a"
    assert result["calls"][0]["body"] == REDACTED
    assert result["calls"][1]["id"] == "b"
    assert result["calls"][1]["body"] == REDACTED


def test_processor_redacts_deeply_nested() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "deep",
        "outer": {
            "middle": {
                "inner": {
                    "api_key": "sk-leak",
                    "ok": True,
                }
            }
        },
    }
    result = proc(None, "info", event)
    assert result["outer"]["middle"]["inner"]["api_key"] == REDACTED
    assert result["outer"]["middle"]["inner"]["ok"] is True


def test_processor_handles_tuples() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "tuple_case",
        "items": ({"body": "x"}, {"name": "y"}),
    }
    result = proc(None, "info", event)
    assert isinstance(result["items"], tuple)
    assert result["items"][0]["body"] == REDACTED
    assert result["items"][1]["name"] == "y"


def test_processor_caps_recursion_on_pathologically_deep_structure() -> None:
    proc = RedactSensitiveProcessor()
    # Build a structure 20 levels deep with a sensitive key at the bottom.
    # Cap is 12, so the deepest leaf will NOT be redacted (depth >= cap).
    deep: dict[str, Any] = {"body": "should-not-redact-too-deep"}
    for _ in range(20):
        deep = {"nest": deep}
    result = proc(None, "info", {"top": deep})
    # Walk down to verify no crash and predictable behavior.
    cur: Any = result["top"]
    for _ in range(20):
        cur = cur["nest"]
    # At depth > cap, redaction is skipped. The point is "no crash"; the
    # exact value at the leaf is implementation-defined (here: untouched).
    assert "body" in cur


def test_processor_preserves_benign_keys() -> None:
    proc = RedactSensitiveProcessor()
    event = {
        "event": "x",
        "body_size_bytes": 1024,
        "somebody": "alice",
        "monkey": "george",
        "tokenize": True,
        "session_duration": 30,
    }
    result = proc(None, "info", dict(event))

    for key, value in event.items():
        assert result[key] == value, f"{key!r} was wrongly redacted"


def test_processor_ignores_non_string_keys() -> None:
    proc = RedactSensitiveProcessor()
    event: dict[object, object] = {"event": "x", 42: "answer", "body": "secret"}
    result = proc(None, "info", event)  # type: ignore[arg-type]

    # int key preserved untouched (processor only acts on str keys).
    assert result[42] == "answer"  # type: ignore[index]
    assert result["body"] == REDACTED


def test_processor_handles_empty_dict() -> None:
    proc = RedactSensitiveProcessor()
    result = proc(None, "info", {})
    assert result == {}


def test_processor_passes_through_primitive_top_level_values() -> None:
    proc = RedactSensitiveProcessor()
    event = {"event": "x", "count": 5, "ok": True, "rate": 1.5, "name": None}
    result = proc(None, "info", dict(event))
    for key, value in event.items():
        assert result[key] == value


def test_redacted_constant_is_stable() -> None:
    assert REDACTED == "<redacted>"
