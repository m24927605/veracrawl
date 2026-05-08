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
   with ``<redacted-body>`` for **every** MIME type. Earlier
   versions exempted image / binary types but Playwright HAR
   embeds base64 PDFs, archives, private images, and account
   exports through the same field — none of those are safe to
   persist verbatim in evidence. The per-attempt response artifact
   path is the place to keep response bodies; HAR keeps them
   empty.
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
import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from veracrawl.runtime_support._log_redaction import is_sensitive_key

# HAR-specific sensitive-key extras. The structured-log helper covers
# generic patterns (``cookie`` / ``authorization`` / ``password`` /
# ``token`` / etc.) but misses common web credential names that show
# up in URL query / form / cookie arrays — ``session`` / ``sid`` /
# ``apikey`` / ``api_key`` / ``authtoken`` / ``auth_token`` / ``code``
# (OAuth code grant) / ``jwt`` / ``access_token`` / ``id_token`` /
# ``refresh_token``. Codex iter-4 important: persisting these in a
# HAR is a credential leak even when headers are clean.
_HAR_EXTRA_SENSITIVE_KEYS: tuple[str, ...] = (
    "session",
    "sid",
    "sessionid",
    "session_id",
    "session_token",
    "apikey",
    "api_key",
    "authtoken",
    "auth_token",
    "access_token",
    "id_token",
    "refresh_token",
    "code",
    "jwt",
    "state",  # OAuth state — opaque token, treat as sensitive
    "nonce",  # OIDC nonce
)


def _is_har_sensitive_key(name: str) -> bool:
    """Combine the project-wide sensitive-key matcher with HAR extras.

    Both checks are case-insensitive. CamelCase keys
    (``accessToken``, ``refreshToken``, ``sessionToken``,
    ``idToken``, ``apiKey``, ``authToken``) are normalized to
    snake_case before the extras lookup so a value like
    ``?accessToken=secret`` is treated the same as
    ``?access_token=secret`` (codex iter-5 critical: the previous
    extras were only snake_case + lowercase, so camelCase
    OAuth/OIDC tokens persisted verbatim).

    The extras match the *normalized* full name, not a substring,
    to avoid false positives like ``state_code`` or
    ``description``.
    """

    if is_sensitive_key(name):
        return True
    lower = name.lower()
    if lower in _HAR_EXTRA_SENSITIVE_KEYS:
        return True
    # camelCase → snake_case: insert ``_`` before any uppercase
    # letter that follows a lowercase letter, then lowercase.
    # ``accessToken`` → ``access_token``; ``apiKey`` → ``api_key``.
    snake = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()
    if snake in _HAR_EXTRA_SENSITIVE_KEYS:
        return True
    # Also strip non-alphanumerics so ``access-token`` /
    # ``access.token`` collapse to ``access_token``.
    collapsed = re.sub(r"[^a-z0-9]+", "_", snake).strip("_")
    return collapsed in _HAR_EXTRA_SENSITIVE_KEYS


REDACTED_VALUE = "<redacted>"
REDACTED_BODY = "<redacted-body>"
REDACTED_CANARY = "<redacted-canary>"

# HAR ``content.text`` is the response body Playwright embeds in the
# trace. Default policy: redact every present ``text`` field
# regardless of MIME type. Earlier we tried a MIME allowlist (text /
# json / form / xml) and left binary types alone, but Playwright
# embeds base64 PDFs, images, archives, and downloaded artifacts via
# the same field — those routinely carry PII (account exports,
# private documents, signed download URLs). HAR is evidence, not a
# response cache; the per-attempt artifact path is the right place
# to hold full bodies (with its own redaction pass), so we keep the
# HAR body slot empty and avoid the entire MIME-allowlist
# correctness debate.


def _canary_variants(canary: str) -> tuple[str, ...]:
    """Return the canary plus its common percent-encoded forms.

    A caller-declared canary like ``secret@example.com`` shows up in
    persisted HARs as ``secret%40example.com`` whenever the value
    rides through a URL query / form param. The substring scrub only
    catches whichever literal form is present, so we also try the
    URL-encoded variant. ``urllib.parse.quote`` covers the
    encode-everything case; if the canary already contains percent
    sequences, decoding back is unsafe (we can't tell apart
    accidental ``%`` chars from real escapes), so we just emit the
    encoded variant alongside.
    """

    from urllib.parse import quote

    variants = [canary]
    encoded = quote(canary, safe="")
    if encoded != canary:
        variants.append(encoded)
    # Also handle the common ``+`` for space encoding seen in form
    # bodies and query strings.
    plus_encoded = encoded.replace("%20", "+")
    if plus_encoded != encoded and plus_encoded not in variants:
        variants.append(plus_encoded)
    return tuple(variants)


def _scrub_canary(value: str, canaries: tuple[str, ...]) -> str:
    """Replace every occurrence of any canary (and its encoded
    variants) in ``value`` with REDACTED_CANARY.

    Codex iter-4 important: a canary like ``secret@example.com``
    appearing in a URL query value gets percent-encoded to
    ``secret%40example.com`` by browsers. The substring scrub now
    tries both the literal form and the URL-encoded variant so the
    whole-document canary contract holds against encoding
    transformations.
    """

    out = value
    for canary in canaries:
        if not canary:
            continue
        for variant in _canary_variants(canary):
            if variant in out:
                out = out.replace(variant, REDACTED_CANARY)
    return out


def _redact_name_value_array(
    items: list[dict[str, Any]], canaries: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Walk a HAR ``[{"name": ..., "value": ...}, ...]`` array.

    Codex iter-5 critical: malformed entries (a string like
    ``"Authorization: Bearer secret"`` instead of a ``{name, value}``
    dict) used to pass through verbatim, defeating the privacy
    contract. Now: any non-dict entry, or any dict without the
    expected ``name`` / ``value`` shape, is **replaced wholesale**
    with a redaction marker dict — fail-closed because we cannot
    prove the malformed shape doesn't carry credentials.
    """

    out: list[dict[str, Any]] = []
    for entry in items:
        if not isinstance(entry, dict):
            out.append({"name": REDACTED_VALUE, "value": REDACTED_VALUE})
            continue
        name = entry.get("name")
        value = entry.get("value")
        new_entry = dict(entry)
        if isinstance(name, str) and _is_har_sensitive_key(name):
            new_entry["value"] = REDACTED_VALUE
        elif isinstance(value, str):
            new_entry["value"] = _scrub_canary(value, canaries)
        elif value is not None:
            # Non-string value of unknown shape — redact wholesale
            # rather than guessing whether it's safe to emit.
            new_entry["value"] = REDACTED_VALUE
        out.append(new_entry)
    return out


def _redact_cookie_array(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Walk a HAR ``cookies`` array and redact every cookie value.

    HAR request/response ``cookies`` entries use the cookie's own
    name as ``name`` (e.g. ``session``, ``sid``, ``csrf``,
    ``auth_token``), not a header carrier name like ``Cookie`` /
    ``Set-Cookie``. Those cookie names rarely match our generic
    sensitive-key patterns, so a name-based check would let
    session / auth cookies survive into persisted HARs.

    Cookies are session-bearing by construction — every value is
    a credential / state token. We unconditionally redact every
    ``value`` in cookie arrays (the ``name`` itself is not a
    secret; it's useful for replay diagnostics). This matches the
    cooperative-crawler policy that no captured cookie value ever
    reaches the evidence store in plaintext.
    """

    out: list[dict[str, Any]] = []
    for entry in items:
        if not isinstance(entry, dict):
            # Fail-closed on malformed cookie entries (codex iter-5
            # critical applied uniformly): replace with a redaction
            # marker rather than passing through unknown shapes.
            out.append({"name": REDACTED_VALUE, "value": REDACTED_VALUE})
            continue
        new_entry = dict(entry)
        if "value" in new_entry:
            new_entry["value"] = REDACTED_VALUE
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


def _redact_content(content: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    """Redact ``response.content.text`` unconditionally.

    Earlier versions exempted image / binary MIME types from body
    redaction. That was wrong: Playwright HAR ``content.text`` for
    binary types is a base64 blob that may embed PDFs, archives,
    private images, account exports, signed download URLs, and so
    on — none of which are safe to persist verbatim. The per-attempt
    response artifact path (with its own redaction pass) is the
    place to keep response bodies; HAR keeps them empty.

    Canary scrubbing is unnecessary when the body is replaced
    wholesale, but we keep the parameter for API uniformity (other
    redactors here also take canaries).
    """

    del canaries  # body is replaced wholesale; canaries can't survive
    out = dict(content)
    if "text" in out:
        out["text"] = REDACTED_BODY
    return out


def _redact_url(url: Any, canaries: tuple[str, ...]) -> Any:
    """Structurally redact a HAR URL.

    URLs in HAR entries can carry credentials in three places:

    * **Userinfo** (``https://user:pass@host``) — strip
      unconditionally; presenting it in evidence has no replay value.
    * **Sensitive query parameters** (``?password=hunter2&token=abc``,
      ``?api_key=...``) — re-emit with the value replaced by
      ``<redacted>`` whenever the key matches the project-wide
      sensitive-key patterns. Same patterns used for header arrays.
    * **Caller-declared canary substrings** — scrubbed across the
      reconstructed URL after structural redaction (catches anything
      the structural pass misses, e.g. canary embedded in path).
    """

    if not isinstance(url, str):
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        # Malformed URL — never emit the original; return a
        # fail-closed marker plus the canary scrub so canaries still
        # do not leak through.
        return _scrub_canary(REDACTED_VALUE, canaries)
    # Strip userinfo: rebuild netloc from hostname + (port if present).
    host = parts.hostname or ""
    try:
        port = parts.port
    except ValueError:
        port = None
    netloc = host if port is None else f"{host}:{port}"
    # Walk the query string and redact sensitive keys structurally.
    redacted_query: list[tuple[str, str]] = []
    if parts.query:
        for name, value in parse_qsl(parts.query, keep_blank_values=True):
            if _is_har_sensitive_key(name):
                redacted_query.append((name, REDACTED_VALUE))
            else:
                redacted_query.append((name, value))
    new_query = urlencode(redacted_query)
    rebuilt = urlunsplit(
        (parts.scheme, netloc, parts.path, new_query, "")
    )  # also drop fragment — never carries replay value
    return _scrub_canary(rebuilt, canaries)


def _redact_request(request: dict[str, Any], canaries: tuple[str, ...]) -> dict[str, Any]:
    out = dict(request)
    if isinstance(out.get("url"), str):
        out["url"] = _redact_url(out["url"], canaries)
    headers = out.get("headers")
    if isinstance(headers, list):
        out["headers"] = _redact_name_value_array(headers, canaries)
    cookies = out.get("cookies")
    if isinstance(cookies, list):
        # Cookies-by-name are credential-by-construction; redact every
        # value unconditionally (cookie *names* are too varied to
        # cover by sensitive-key patterns).
        out["cookies"] = _redact_cookie_array(cookies)
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
        out["cookies"] = _redact_cookie_array(cookies)
    if isinstance(out.get("redirectURL"), str):
        out["redirectURL"] = _redact_url(out["redirectURL"], canaries)
    content = out.get("content")
    if isinstance(content, dict):
        out["content"] = _redact_content(content, canaries)
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
        # Not a HAR shape — fail closed. Returning a synthetic empty
        # HAR would let an adapter regression silently persist a
        # ``redaction_applied=True`` artifact that does not actually
        # represent the captured trace, hiding the bug. The caller
        # already handles :class:`HarRedactionError` by dropping the
        # staging file without persistence (same behavior as a JSON
        # parse failure).
        raise HarRedactionError("HAR payload missing required ``log`` object")
    entries = log.get("entries")
    if entries is not None and not isinstance(entries, list):
        raise HarRedactionError("HAR ``log.entries`` must be a list when present")

    new_log = dict(log)
    if isinstance(entries, list):
        new_log["entries"] = [
            _redact_entry(entry, canaries) if isinstance(entry, dict) else entry
            for entry in entries
        ]
    new_doc = dict(document)
    new_doc["log"] = new_log
    # Codex iter-3 important #11: structural redaction covers the
    # documented HAR entry paths but HAR JSON also contains creator
    # / browser / page metadata, ``_`` extension fields, timings /
    # serverIPAddress / comment / cache fields, and adapter-specific
    # custom keys. A canary token landing in any of those would
    # survive the structural pass. Apply a final recursive substring
    # scrub over every string in the document so the contract
    # ("canary token never appears in persisted HAR bytes") holds
    # whole-document.
    if canaries:
        new_doc = _walk_scrub_canaries(new_doc, canaries)
    return json.dumps(new_doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _walk_scrub_canaries(value: Any, canaries: tuple[str, ...]) -> Any:
    """Recursively walk ``value`` and scrub canaries from every string.

    Final defense-in-depth pass: HAR shape evolves, vendors add
    custom fields under ``_<name>`` keys, and structural redaction
    only knows the documented paths. This walk guarantees the
    canary contract holds across the entire document.
    """

    if isinstance(value, str):
        return _scrub_canary(value, canaries)
    if isinstance(value, dict):
        # Codex iter-4 important: scrub canaries in keys too, not
        # just values. A canary in a HAR extension key
        # (``_<vendor>``) or a custom adapter metadata key would
        # otherwise survive in the persisted JSON bytes.
        scrubbed: dict[Any, Any] = {}
        for k, v in value.items():
            new_k = _scrub_canary(k, canaries) if isinstance(k, str) else k
            scrubbed[new_k] = _walk_scrub_canaries(v, canaries)
        return scrubbed
    if isinstance(value, list):
        return [_walk_scrub_canaries(item, canaries) for item in value]
    if isinstance(value, tuple):
        return tuple(_walk_scrub_canaries(item, canaries) for item in value)
    return value


__all__ = [
    "HarRedactionError",
    "REDACTED_BODY",
    "REDACTED_CANARY",
    "REDACTED_VALUE",
    "redact_har_payload",
]
