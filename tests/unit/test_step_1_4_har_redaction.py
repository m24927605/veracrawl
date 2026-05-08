"""Unit tests for HAR redaction (Phase 1 step 1.4).

design.md §4 Phase 1: "HAR PII redaction via structured parser ...
regex-only is rejected as insufficient." The acceptance criterion:

    HAR sidecar: parse HAR JSON, assert no header value matches the
    configured Authorization or Cookie tokens (redaction applied);
    assert no request URL substring matches a list of canary tokens
    the test injects in inputs.

These tests verify the structural pass over HAR 1.2 JSON: header
arrays, query strings, postData, cookies, and content bodies are
all redacted at field-level keys; canary tokens are scrubbed across
URL / value / body shapes.
"""

from __future__ import annotations

import json

import pytest

from veracrawl.runtime_support.har_redaction import (
    REDACTED_BODY,
    REDACTED_CANARY,
    REDACTED_VALUE,
    HarRedactionError,
    redact_har_payload,
)


def _har(entries: list[dict]) -> bytes:
    return json.dumps(
        {
            "log": {
                "version": "1.2",
                "creator": {"name": "veracrawl-test", "version": "0"},
                "entries": entries,
            }
        }
    ).encode("utf-8")


def _entry(
    *,
    url: str = "https://example.test/",
    request_headers: list[dict] | None = None,
    response_headers: list[dict] | None = None,
    request_cookies: list[dict] | None = None,
    response_cookies: list[dict] | None = None,
    query_string: list[dict] | None = None,
    post_data: dict | None = None,
    content: dict | None = None,
) -> dict:
    request: dict = {"method": "GET", "url": url}
    if request_headers is not None:
        request["headers"] = request_headers
    if request_cookies is not None:
        request["cookies"] = request_cookies
    if query_string is not None:
        request["queryString"] = query_string
    if post_data is not None:
        request["postData"] = post_data
    response: dict = {"status": 200}
    if response_headers is not None:
        response["headers"] = response_headers
    if response_cookies is not None:
        response["cookies"] = response_cookies
    if content is not None:
        response["content"] = content
    return {"request": request, "response": response}


def test_authorization_header_redacted() -> None:
    payload = _har(
        [
            _entry(
                request_headers=[
                    {"name": "Authorization", "value": "Bearer secret-token-123"},
                    {"name": "User-Agent", "value": "VeraCrawlTest/1.0"},
                ]
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    headers = out["log"]["entries"][0]["request"]["headers"]
    auth = next(h for h in headers if h["name"] == "Authorization")
    ua = next(h for h in headers if h["name"] == "User-Agent")
    assert auth["value"] == REDACTED_VALUE
    # Non-sensitive headers stay (they may carry canaries but not in this test).
    assert ua["value"] == "VeraCrawlTest/1.0"
    # The original token must be gone from the entire payload.
    assert b"secret-token-123" not in redact_har_payload(payload)


def test_cookie_array_values_redacted_unconditionally() -> None:
    """HAR ``cookies`` arrays use cookie names like ``session`` /
    ``sid`` / ``csrf`` / ``auth_token`` that don't match the
    generic sensitive-key patterns. Cookies are credential-by-
    construction; every value must be redacted."""

    payload = _har(
        [
            _entry(
                request_cookies=[
                    {"name": "session", "value": "session-token-abc"},
                    {"name": "sid", "value": "sid-token-xyz"},
                    {"name": "auth_token", "value": "tok-123"},
                    {"name": "theme", "value": "dark"},  # benign
                    {"name": "csrf", "value": "csrf-abcdef"},
                    {"name": "_ga", "value": "GA1.2.456.789"},  # tracking
                ],
                response_cookies=[
                    {"name": "session", "value": "session-set"},
                    {"name": "anything", "value": "any-value"},
                ],
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    req_cookies = out["log"]["entries"][0]["request"]["cookies"]
    res_cookies = out["log"]["entries"][0]["response"]["cookies"]
    # Every cookie value redacted, regardless of name match.
    for c in req_cookies:
        assert c["value"] == REDACTED_VALUE
    for c in res_cookies:
        assert c["value"] == REDACTED_VALUE
    redacted = redact_har_payload(payload)
    assert b"session-token-abc" not in redacted
    assert b"sid-token-xyz" not in redacted
    assert b"tok-123" not in redacted
    assert b"csrf-abcdef" not in redacted


def test_cookie_array_preserves_name_for_replay_diagnostics() -> None:
    """The cookie *name* is not a secret — preserving it lets replay
    diagnostics see which cookies were involved without leaking the
    value."""

    payload = _har([_entry(request_cookies=[{"name": "session", "value": "s"}])])
    out = json.loads(redact_har_payload(payload))
    cookie = out["log"]["entries"][0]["request"]["cookies"][0]
    assert cookie["name"] == "session"
    assert cookie["value"] == REDACTED_VALUE


def test_cookie_and_set_cookie_redacted() -> None:
    payload = _har(
        [
            _entry(
                request_headers=[
                    {"name": "Cookie", "value": "session=abc; theme=dark"},
                ],
                response_headers=[
                    {"name": "Set-Cookie", "value": "session=xyz; HttpOnly"},
                ],
                request_cookies=[
                    {"name": "session", "value": "abc"},
                    {"name": "theme", "value": "dark"},
                ],
                response_cookies=[
                    {"name": "session", "value": "xyz"},
                ],
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    entry = out["log"]["entries"][0]
    req_headers = entry["request"]["headers"]
    res_headers = entry["response"]["headers"]
    assert next(h for h in req_headers if h["name"] == "Cookie")["value"] == REDACTED_VALUE
    assert next(h for h in res_headers if h["name"] == "Set-Cookie")["value"] == REDACTED_VALUE
    # Cookie *arrays* are now redacted unconditionally (every value)
    # because cookie names like ``session`` / ``sid`` rarely match
    # generic sensitive-key patterns but cookies are credential-by-
    # construction. See ``test_cookie_array_values_redacted_unconditionally``.
    req_cookies = entry["request"]["cookies"]
    res_cookies = entry["response"]["cookies"]
    for c in req_cookies + res_cookies:
        assert c["value"] == REDACTED_VALUE
    redacted = redact_har_payload(payload)
    assert b'"value": "abc"' not in redacted
    assert b'"value": "xyz"' not in redacted


def test_x_api_key_and_x_auth_token_redacted() -> None:
    payload = _har(
        [
            _entry(
                request_headers=[
                    {"name": "X-Api-Key", "value": "ak_live_abcd1234"},
                    {"name": "X-Auth-Token", "value": "tok_xyz789"},
                ]
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    headers = out["log"]["entries"][0]["request"]["headers"]
    api_key = next(h for h in headers if h["name"] == "X-Api-Key")
    auth_tok = next(h for h in headers if h["name"] == "X-Auth-Token")
    assert api_key["value"] == REDACTED_VALUE
    assert auth_tok["value"] == REDACTED_VALUE
    redacted = redact_har_payload(payload)
    assert b"ak_live_abcd1234" not in redacted
    assert b"tok_xyz789" not in redacted


def test_query_string_password_redacted() -> None:
    payload = _har(
        [
            _entry(
                query_string=[
                    {"name": "password", "value": "hunter2"},
                    {"name": "page", "value": "1"},
                ]
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    qs = out["log"]["entries"][0]["request"]["queryString"]
    pw = next(q for q in qs if q["name"] == "password")
    page = next(q for q in qs if q["name"] == "page")
    assert pw["value"] == REDACTED_VALUE
    assert page["value"] == "1"


def test_post_data_text_unconditionally_redacted() -> None:
    """Form bodies / JSON bodies could carry credentials regardless of
    HTTP-layer headers. Redact the entire ``postData.text``."""

    payload = _har(
        [
            _entry(
                post_data={
                    "mimeType": "application/json",
                    "text": '{"username":"alice","password":"hunter2"}',
                    "params": [
                        {"name": "username", "value": "alice"},
                        {"name": "password", "value": "hunter2"},
                    ],
                }
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    post_data = out["log"]["entries"][0]["request"]["postData"]
    assert post_data["text"] == REDACTED_BODY
    pw = next(p for p in post_data["params"] if p["name"] == "password")
    assert pw["value"] == REDACTED_VALUE
    redacted = redact_har_payload(payload)
    assert b"hunter2" not in redacted


def test_response_content_text_redacted_for_html_and_json() -> None:
    payload = _har(
        [
            _entry(
                content={
                    "size": 100,
                    "mimeType": "text/html",
                    "text": "<html>secret-content-marker</html>",
                }
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    content = out["log"]["entries"][0]["response"]["content"]
    assert content["text"] == REDACTED_BODY
    assert b"secret-content-marker" not in redact_har_payload(payload)


def test_canary_token_scrubbed_from_url() -> None:
    payload = _har(
        [
            _entry(
                url="https://example.test/items?token=CANARY_TOKEN_42&page=1",
            )
        ]
    )
    out = json.loads(redact_har_payload(payload, canary_tokens=["CANARY_TOKEN_42"]))
    url = out["log"]["entries"][0]["request"]["url"]
    assert "CANARY_TOKEN_42" not in url
    assert REDACTED_CANARY in url
    # And the redacted bytes must not contain the canary anywhere.
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_TOKEN_42"])
    assert b"CANARY_TOKEN_42" not in redacted


def test_canary_token_scrubbed_from_non_sensitive_header_value() -> None:
    payload = _har(
        [
            _entry(
                request_headers=[
                    {
                        "name": "X-Custom-Header",
                        "value": "session-CANARY_BLOB_99-suffix",
                    },
                ]
            )
        ]
    )
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_BLOB_99"])
    assert b"CANARY_BLOB_99" not in redacted
    out = json.loads(redacted)
    headers = out["log"]["entries"][0]["request"]["headers"]
    custom = next(h for h in headers if h["name"] == "X-Custom-Header")
    assert REDACTED_CANARY in custom["value"]


def test_empty_canaries_iterable_skipped() -> None:
    payload = _har([_entry(url="https://example.test/x")])
    out_a = redact_har_payload(payload, canary_tokens=[])
    out_b = redact_har_payload(payload, canary_tokens=("",))
    assert json.loads(out_a)["log"]["entries"][0]["request"]["url"] == "https://example.test/x"
    assert json.loads(out_b)["log"]["entries"][0]["request"]["url"] == "https://example.test/x"


def test_invalid_json_raises_redaction_error() -> None:
    with pytest.raises(HarRedactionError):
        redact_har_payload(b"this is not json")


def test_unparseable_har_shape_returns_empty_har() -> None:
    """A JSON payload that lacks the HAR ``log`` shape returns an
    empty HAR document rather than the original — fail closed: never
    emit bytes whose redaction we could not verify."""

    out = redact_har_payload(b'{"unrelated":"thing"}')
    parsed = json.loads(out)
    assert parsed["log"]["entries"] == []
    assert b"unrelated" not in out


def test_non_string_url_left_unchanged() -> None:
    payload = json.dumps(
        {"log": {"version": "1.2", "entries": [{"request": {"url": 12345}}]}}
    ).encode("utf-8")
    out = json.loads(redact_har_payload(payload))
    assert out["log"]["entries"][0]["request"]["url"] == 12345


def test_password_field_in_query_string_redacted_case_insensitive() -> None:
    payload = _har(
        [
            _entry(
                query_string=[
                    {"name": "PASSWORD", "value": "hunter2"},
                    {"name": "Password", "value": "hunter3"},
                ]
            )
        ]
    )
    redacted = redact_har_payload(payload)
    assert b"hunter2" not in redacted
    assert b"hunter3" not in redacted


def test_image_response_content_not_redacted() -> None:
    """Images don't have field-level keys; we leave their text empty
    or base64'd bytes alone (they'd not normally have a ``text`` field
    anyway)."""

    payload = _har(
        [
            _entry(
                content={
                    "size": 1024,
                    "mimeType": "image/png",
                    "encoding": "base64",
                    "text": "iVBORw0KGgo=",
                }
            )
        ]
    )
    out = json.loads(redact_har_payload(payload))
    content = out["log"]["entries"][0]["response"]["content"]
    # Mime is image/* so the body redaction does not fire.
    assert content["text"] == "iVBORw0KGgo="


def test_canary_scrubbed_from_image_content_text() -> None:
    """Image / non-text MIME bodies bypass body over-redaction but
    must still go through canary scrubbing — a caller-declared
    canary token must never appear in the persisted HAR regardless
    of MIME."""

    payload = _har(
        [
            _entry(
                content={
                    "size": 100,
                    "mimeType": "image/png",
                    "text": "base64-prefix-CANARY_IN_IMG-suffix",
                }
            )
        ]
    )
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_IN_IMG"])
    assert b"CANARY_IN_IMG" not in redacted
    out = json.loads(redacted)
    content = out["log"]["entries"][0]["response"]["content"]
    assert REDACTED_CANARY in content["text"]


def test_canary_scrubbed_from_application_octet_stream_body() -> None:
    """``application/octet-stream`` is a binary type that bypasses
    body redaction — but canary scrubbing must still apply."""

    payload = _har(
        [
            _entry(
                content={
                    "size": 100,
                    "mimeType": "application/octet-stream",
                    "text": "binary-blob-with-CANARY_BLOB-inside",
                }
            )
        ]
    )
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_BLOB"])
    assert b"CANARY_BLOB" not in redacted
