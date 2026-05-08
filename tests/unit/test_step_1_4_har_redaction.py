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


def test_camelcase_credential_keys_redacted() -> None:
    """Iter-5 critical: camelCase OAuth/OIDC tokens (``accessToken``,
    ``refreshToken``, ``idToken``, ``sessionToken``, ``apiKey``,
    ``authToken``) must hit the same redaction path as snake_case."""

    payload = _har(
        [
            _entry(
                query_string=[
                    {"name": "accessToken", "value": "atok_secret_1"},
                    {"name": "refreshToken", "value": "rtok_secret_2"},
                    {"name": "idToken", "value": "itok_secret_3"},
                    {"name": "sessionToken", "value": "stok_secret_4"},
                    {"name": "apiKey", "value": "ak_secret_5"},
                    {"name": "authToken", "value": "atok_secret_6"},
                    {"name": "page", "value": "1"},  # benign
                ]
            )
        ]
    )
    redacted = redact_har_payload(payload)
    for token in (
        b"atok_secret_1",
        b"rtok_secret_2",
        b"itok_secret_3",
        b"stok_secret_4",
        b"ak_secret_5",
        b"atok_secret_6",
    ):
        assert token not in redacted, f"camelCase token leaked: {token!r}"
    out = json.loads(redacted)
    qs = out["log"]["entries"][0]["request"]["queryString"]
    assert next(q for q in qs if q["name"] == "page")["value"] == "1"


def test_kebabcase_credential_keys_also_redacted() -> None:
    """``access-token`` / ``access.token`` collapse to ``access_token``."""

    payload = _har(
        [
            _entry(
                query_string=[
                    {"name": "access-token", "value": "kebab_secret_1"},
                    {"name": "access.token", "value": "dot_secret_2"},
                ]
            )
        ]
    )
    redacted = redact_har_payload(payload)
    assert b"kebab_secret_1" not in redacted
    assert b"dot_secret_2" not in redacted


def test_malformed_header_array_entry_redacted_wholesale() -> None:
    """Iter-5 critical: a non-dict entry in a header array (e.g. a
    raw string ``"Authorization: Bearer secret"``) used to pass
    through verbatim. Must now be replaced wholesale with a
    redaction marker."""

    parsed = {
        "log": {
            "version": "1.2",
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.test/",
                        "headers": [
                            "Authorization: Bearer LEAKED_RAW_STRING_77",
                            {"name": "User-Agent", "value": "TestUA"},
                        ],
                    },
                    "response": {"status": 200},
                }
            ],
        }
    }
    payload = json.dumps(parsed).encode("utf-8")
    redacted = redact_har_payload(payload)
    assert b"LEAKED_RAW_STRING_77" not in redacted
    out = json.loads(redacted)
    headers = out["log"]["entries"][0]["request"]["headers"]
    # First entry was a raw string → replaced with redaction marker dict.
    assert headers[0] == {"name": REDACTED_VALUE, "value": REDACTED_VALUE}
    # Second entry stays.
    assert headers[1]["name"] == "User-Agent"


def test_malformed_cookie_array_entry_redacted_wholesale() -> None:
    parsed = {
        "log": {
            "version": "1.2",
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.test/",
                        "cookies": [
                            "session=LEAKED_COOKIE_88",
                            {"name": "theme", "value": "dark"},
                        ],
                    },
                    "response": {"status": 200},
                }
            ],
        }
    }
    payload = json.dumps(parsed).encode("utf-8")
    redacted = redact_har_payload(payload)
    assert b"LEAKED_COOKIE_88" not in redacted


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


def test_response_content_text_redacted_for_all_mimes() -> None:
    """Iter-2 #2 critical: ``content.text`` is replaced wholesale for
    every MIME, including base64-encoded binaries (PDFs, images,
    archives, account exports)."""

    cases = [
        ("text/html", "<html>secret-content-marker</html>"),
        ("application/json", '{"a":"secret"}'),
        ("application/pdf", "JVBERi0xLjQKJeLjz9MK"),  # base64 PDF prefix
        ("image/png", "iVBORw0KGgoAAAANSUhEUgAA"),
        ("application/octet-stream", "binary-marker-99"),
        ("application/zip", "UEsDBA=="),
    ]
    for mime, body in cases:
        payload = _har([_entry(content={"size": 100, "mimeType": mime, "text": body})])
        out = json.loads(redact_har_payload(payload))
        content = out["log"]["entries"][0]["response"]["content"]
        assert content["text"] == REDACTED_BODY, f"mime={mime} body not redacted"
        assert body.encode("utf-8") not in redact_har_payload(payload)


def test_canary_token_scrubbed_from_url_path() -> None:
    """Canaries embedded in the URL path (not in a sensitive query
    key) survive structural redaction and need substring scrubbing."""

    payload = _har(
        [
            _entry(
                url="https://example.test/items/CANARY_TOKEN_42/details?page=1",
            )
        ]
    )
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_TOKEN_42"])
    assert b"CANARY_TOKEN_42" not in redacted
    out = json.loads(redacted)
    url = out["log"]["entries"][0]["request"]["url"]
    assert REDACTED_CANARY in url


def test_canary_token_in_non_sensitive_query_param_scrubbed() -> None:
    """A canary inside a non-sensitive query value (not redacted by
    is_sensitive_key) must still be substring-scrubbed."""

    payload = _har(
        [
            _entry(
                url="https://example.test/items?ref=CANARY_REF_99&page=1",
            )
        ]
    )
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_REF_99"])
    assert b"CANARY_REF_99" not in redacted


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


def test_unparseable_har_shape_raises() -> None:
    """Iter-2 #5: invalid HAR shape must raise so the caller drops
    the staging file rather than persisting a synthetic empty HAR
    that masks adapter regressions."""

    with pytest.raises(HarRedactionError):
        redact_har_payload(b'{"unrelated":"thing"}')


def test_non_dict_log_raises() -> None:
    with pytest.raises(HarRedactionError):
        redact_har_payload(b'{"log": "not-a-dict"}')


def test_non_list_entries_raises() -> None:
    with pytest.raises(HarRedactionError):
        redact_har_payload(b'{"log": {"version": "1.2", "entries": "nope"}}')


def test_missing_entries_field_is_ok() -> None:
    """An empty / entries-less HAR is valid (a session may produce
    no requests). Don't raise on absent ``entries``."""

    out = redact_har_payload(b'{"log": {"version": "1.2"}}')
    parsed = json.loads(out)
    assert parsed["log"]["version"] == "1.2"


def test_malformed_entry_field_types_dont_leak_secrets_via_canary_walk() -> None:
    """Iter-3 critical #2: the recursive canary scrub walks the
    entire document, so any caller-declared canary token survives
    structural redaction even when sub-shapes are malformed and
    structural redactors skipped them. Test that every injected
    sensitive value, declared as a canary, is gone from the
    persisted HAR."""

    parsed_input: dict = {
        "log": {
            "version": "1.2",
            "entries": [
                {
                    "request": {
                        # url is non-string → left as-is; no crash.
                        "url": 12345,
                        # headers is dict instead of list → ignored
                        # by structural redactor, but the canary walk
                        # at the end still scrubs the leaked value.
                        "headers": {"Authorization": "Bearer leaked-1"},
                        "cookies": {"session": "leaked-2"},
                        "queryString": "raw-string-leaked-3",
                        "postData": "raw-post-leaked-4",
                    },
                    "response": {
                        "headers": "string-leaked-5",
                        "content": "non-dict-leaked-6",
                    },
                },
                "scalar-entry-leaked-7",
            ],
        }
    }
    payload = json.dumps(parsed_input).encode("utf-8")
    canaries = [
        "leaked-1",
        "leaked-2",
        "leaked-3",
        "leaked-4",
        "leaked-5",
        "leaked-6",
        "leaked-7",
    ]
    redacted = redact_har_payload(payload, canary_tokens=canaries)
    # No leaked marker survives — the recursive canary walk catches
    # everything the structural redactor didn't.
    for canary in canaries:
        assert canary.encode() not in redacted, f"canary {canary} leaked"
    # Redaction completed without crashing.
    out = json.loads(redacted)
    assert isinstance(out["log"]["entries"], list)


def test_canary_in_creator_metadata_scrubbed() -> None:
    """Iter-3 important #11: HAR creator / browser metadata are not
    documented entry paths but the canary contract is whole-document.
    Any canary in those fields must be scrubbed."""

    payload = json.dumps(
        {
            "log": {
                "version": "1.2",
                "creator": {"name": "leaked-creator-CANARY_C", "version": "1.0"},
                "browser": {"name": "leaked-browser-CANARY_B", "version": "1.0"},
                "entries": [],
            }
        }
    ).encode("utf-8")
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_C", "CANARY_B"])
    assert b"CANARY_C" not in redacted
    assert b"CANARY_B" not in redacted


def test_canary_in_underscore_extension_field_scrubbed() -> None:
    """HAR allows ``_<name>`` extension fields. Canaries there must
    also be scrubbed."""

    payload = json.dumps(
        {
            "log": {
                "version": "1.2",
                "_vendor_extra": "embedded-CANARY_X-here",
                "entries": [],
            }
        }
    ).encode("utf-8")
    redacted = redact_har_payload(payload, canary_tokens=["CANARY_X"])
    assert b"CANARY_X" not in redacted


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


def test_image_content_text_also_redacted_wholesale() -> None:
    """Iter-2 #2: image bodies are also replaced wholesale. Earlier
    we exempted them; that left base64 PDFs / archives / private
    images visible if Playwright embedded them."""

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
    assert content["text"] == REDACTED_BODY


def test_url_with_userinfo_strips_credentials() -> None:
    """Iter-2 #1 critical: URL redaction must strip
    ``user:pass@host`` userinfo from request URLs."""

    payload = _har([_entry(url="https://alice:hunter2@example.test/items?page=1")])
    redacted = redact_har_payload(payload)
    assert b"alice" not in redacted
    assert b"hunter2" not in redacted
    out = json.loads(redacted)
    url = out["log"]["entries"][0]["request"]["url"]
    assert url == "https://example.test/items?page=1"


def test_url_with_sensitive_query_params_redacted_structurally() -> None:
    """Iter-2 #1 critical: sensitive query params (``password``,
    ``token``, ``api_key``, ``authorization``) are redacted
    structurally — same is_sensitive_key matcher as headers."""

    payload = _har(
        [
            _entry(
                url=(
                    "https://example.test/login?"
                    "password=hunter2&"
                    "api_key=ak_live_abc&"
                    "page=1&"
                    "token=tok_xyz"
                )
            )
        ]
    )
    redacted = redact_har_payload(payload)
    assert b"hunter2" not in redacted
    assert b"ak_live_abc" not in redacted
    assert b"tok_xyz" not in redacted
    out = json.loads(redacted)
    url = out["log"]["entries"][0]["request"]["url"]
    # Page param survives.
    assert "page=1" in url
    # Sensitive params keep their keys with redacted values.
    assert "password=" in url
    assert REDACTED_VALUE.replace("<", "%3C").replace(">", "%3E") in url or REDACTED_VALUE in url


def test_url_with_authorization_query_param_redacted() -> None:
    payload = _har([_entry(url="https://example.test/?authorization=Bearer+secret")])
    redacted = redact_har_payload(payload)
    assert b"secret" not in redacted


def test_url_fragment_dropped_unconditionally() -> None:
    """Fragments never carry replay value but can carry tokens
    (e.g. OAuth implicit-grant ``#access_token=...``)."""

    payload = _har([_entry(url="https://example.test/page#access_token=tok_xyz_99")])
    redacted = redact_har_payload(payload)
    assert b"tok_xyz_99" not in redacted
    out = json.loads(redacted)
    url = out["log"]["entries"][0]["request"]["url"]
    assert "#" not in url


def test_redirect_url_also_redacted_structurally() -> None:
    payload = _har(
        [
            _entry(
                response_headers=[],
            )
        ]
    )
    parsed = json.loads(payload)
    parsed["log"]["entries"][0]["response"]["redirectURL"] = (
        "https://example.test/?token=secret_redirect_99"
    )
    payload2 = json.dumps(parsed).encode("utf-8")
    redacted = redact_har_payload(payload2)
    assert b"secret_redirect_99" not in redacted
