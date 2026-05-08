"""HAR (HTTP Archive) redaction.

Phase 1 step 1.4 persists Playwright-captured HAR JSON to the
:class:`EvidenceArtifactStorePort`. Raw HAR entries embed
credentials (``Authorization`` / ``Cookie`` / ``Set-Cookie``),
session tokens (``X-Api-Key`` / ``X-Auth-Token``), and form-posted
secrets (``password=...``); persisting them in plaintext violates
the design's privacy contract (design.md §4 Phase 1: "HAR PII
redaction via structured parser ... regex-only is rejected as
insufficient").

This module provides a structured pass over HAR 1.2 JSON that:

1. **Walks header arrays** (``request.headers`` /
   ``response.headers`` / ``request.cookies`` /
   ``response.cookies``) and replaces every ``value`` whose
   ``name`` matches the project-wide sensitive-key patterns
   (reused from ``runtime_support._log_redaction``) with
   ``<redacted>``.
2. **Walks query-string arrays** and replaces sensitive values.
3. **Walks ``request.postData.params``** (form-urlencoded body)
   and replaces sensitive field values.
4. **Replaces ``content.text`` / ``postData.text``** unconditionally
   with ``<redacted-body>`` when ``content.mimeType`` is HTML / JSON
   / form-encoded — the body could carry rendered credentials,
   tokens, or PII regardless of the HTTP layer headers.
5. **Scrubs caller-supplied canary tokens**: any URL substring,
   header value substring, or text-body substring that matches one
   of ``canary_tokens`` is replaced with ``<redacted-canary>``.
   Lets tests prove the limiter does not leak inputs the caller
   knows are private (``test_har_does_not_contain_canary``).

The redaction is **structural**: we parse JSON, walk it, and
re-emit JSON. A regex-only redactor on the raw bytes (rejected by
design.md) cannot reliably distinguish a header value from a body
substring, would mis-handle JSON escapes, and produces
character-level false positives. The structural pass is also more
robust to HAR shape evolution because it only reads documented
fields.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from veracrawl.runtime_support._log_redaction import is_sensitive_key

REDACTED_VALUE = "<redacted>"
REDACTED_BODY = "<redacted-body>"
REDACTED_CANARY = "<redacted-canary>"

# Mime-types whose ``content.text`` we always scrub. We err on the
# side of over-redaction: HAR bodies are not the right place to read
# response payloads — that's what the per-attempt response artifact
# is for, and it gets its own redaction pass.
_REDACT_BODY_MIME_PREFIXES: tuple[str, ...] = (
    "text/",
    "application/json",
    "application/javascript",
    "application/xml",
    "application/x-www-form-urlencoded",
)


def _should_redact_body(mime: str | None) -> bool:
    if not mime:
        return True  # no mime → over-redact
    lower = mime.lower()
    return any(lower.startswith(prefix) for prefix in _REDACT_BODY_MIME_PREFIXES)


def _scrub_canary(value: str, canaries: tuple[str, ...]) -> str:
    """Replace every occurrence of any canary in ``value`` with REDACTED_CANARY."""

    out = value
    for canary in canaries:
        if canary and canary in out:
            out = out.replace(canary, REDACTED_CANARY)
    return out


def _redact_name_value_array(
    items: list[dict[str, Any]], canaries: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Walk a HAR ``[{"name": ..., "value": ...}, ...]`` array."""

    out: list[dict[str, Any]] = []
    for entry in items:
        if not isinstance(entry, dict):
            out.append(entry)
            continue
        name = entry.get("name")
        value = entry.get("value")
        new_entry = dict(entry)
        if isinstance(name, str) and is_sensitive_key(name):
            new_entry["value"] = REDACTED_VALUE
        elif isinstance(value, str):
            new_entry["value"] = _scrub_canary(value, canaries)
        out.append(new_entry)
    return out


def _redact_post_data(post_data: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    """Redact ``request.postData``: params + text body."""

    out = dict(post_data)
    params = out.get("params")
    if isinstance(params, list):
        out["params"] = _redact_name_value_array(params, canaries)
    text = out.get("text")
    if isinstance(text, str):
        # Unconditionally redact — postData text is the request body
        # which can carry credentials in form-encoded shape that the
        # ``params`` walk does not catch (e.g. raw JSON body).
        out["text"] = REDACTED_BODY
    return out


def _redact_content(content: dict[str, Any]) -> dict[str, Any]:
    """Redact ``response.content.text`` based on mimeType."""

    out = dict(content)
    text = out.get("text")
    if isinstance(text, str) and _should_redact_body(out.get("mimeType")):
        out["text"] = REDACTED_BODY
    return out


def _redact_url(url: Any, canaries: tuple[str, ...]) -> Any:
    if not isinstance(url, str):
        return url
    return _scrub_canary(url, canaries)


def _redact_request(request: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    out = dict(request)
    if isinstance(out.get("url"), str):
        out["url"] = _redact_url(out["url"], canaries)
    headers = out.get("headers")
    if isinstance(headers, list):
        out["headers"] = _redact_name_value_array(headers, canaries)
    cookies = out.get("cookies")
    if isinstance(cookies, list):
        out["cookies"] = _redact_name_value_array(cookies, canaries)
    query = out.get("queryString")
    if isinstance(query, list):
        out["queryString"] = _redact_name_value_array(query, canaries)
    post_data = out.get("postData")
    if isinstance(post_data, dict):
        out["postData"] = _redact_post_data(post_data, canaries)
    return out


def _redact_response(response: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    out = dict(response)
    headers = out.get("headers")
    if isinstance(headers, list):
        out["headers"] = _redact_name_value_array(headers, canaries)
    cookies = out.get("cookies")
    if isinstance(cookies, list):
        out["cookies"] = _redact_name_value_array(cookies, canaries)
    if isinstance(out.get("redirectURL"), str):
        out["redirectURL"] = _redact_url(out["redirectURL"], canaries)
    content = out.get("content")
    if isinstance(content, dict):
        out["content"] = _redact_content(content)
    return out


def _redact_entry(entry: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    out = dict(entry)
    request = out.get("request")
    if isinstance(request, dict):
        out["request"] = _redact_request(request, canaries)
    response = out.get("response")
    if isinstance(response, dict):
        out["response"] = _redact_response(response, canaries)
    return out


class HarRedactionError(ValueError):
    """Raised when the HAR payload cannot be parsed as JSON.

    The caller should treat the original payload as un-persistable
    (do not write the unredacted bytes — fail closed). The HAR file
    is best-effort evidence; losing one is acceptable, leaking
    credentials is not.
    """


def redact_har_payload(
    payload: bytes,
    *,
    canary_tokens: Iterable[str] = (),
) -> bytes:
    """Return a redacted HAR JSON payload.

    Args:
        payload: Raw HAR 1.2 JSON bytes (UTF-8).
        canary_tokens: Optional substrings the caller knows must not
            appear in the persisted HAR (e.g. test inputs the caller
            wants to verify never leak). Empty tokens are ignored.

    Raises:
        HarRedactionError: if the payload is not valid JSON. The
            caller must not persist the original bytes — there is
            no safe way to redact a HAR we cannot parse, and a
            leaked Authorization header inside an unparsed JSON
            blob is exactly the contract this function exists to
            uphold.

    Returns:
        UTF-8 encoded bytes of the redacted HAR JSON.
    """

    try:
        document = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HarRedactionError(f"HAR payload is not valid JSON: {exc}") from exc

    canaries = tuple(token for token in canary_tokens if token)

    log = document.get("log") if isinstance(document, dict) else None
    if not isinstance(log, dict):
        # Not a HAR shape — return a structurally-empty HAR so
        # callers downstream don't choke, but never persist the
        # original (which we cannot prove is safe).
        empty = {
            "log": {
                "version": "1.2",
                "creator": {"name": "veracrawl", "version": "0"},
                "entries": [],
            }
        }
        return json.dumps(empty, separators=(",", ":")).encode("utf-8")

    new_log = dict(log)
    entries = new_log.get("entries")
    if isinstance(entries, list):
        new_log["entries"] = [
            _redact_entry(entry, canaries) if isinstance(entry, dict) else entry
            for entry in entries
        ]
    new_doc = dict(document)
    new_doc["log"] = new_log
    return json.dumps(new_doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


__all__ = [
    "HarRedactionError",
    "REDACTED_BODY",
    "REDACTED_CANARY",
    "REDACTED_VALUE",
    "redact_har_payload",
]
