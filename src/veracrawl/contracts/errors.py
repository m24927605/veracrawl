"""Typed errors for foundation validation.

This module also defines three marker classes (``RetryableError``,
``FatalError``, ``PolicyViolation``) that adapter and runtime
exceptions mix in alongside their concrete base class. The markers
let callers dispatch on category — *should I retry?* / *am I done
with this URL?* / *did policy refuse this?* — without parsing prose
or peeking at enum values:

    try:
        adapter.execute(...)
    except RetryableError:
        schedule_retry(...)
    except PolicyViolation:
        record_audit_and_terminate(...)
    except FatalError:
        abandon(...)

The markers are plain (non-Exception) classes. A concrete exception
mixes one in alongside its base, e.g.
``NetworkTimeoutError(NetworkAdapterError, RetryableError)``. The
existing concrete bases (``ValueError`` for adapter errors,
``RuntimeError`` for model-provider errors,
``Exception`` via ``VeraCrawlError`` for foundation errors) stay as
they are so every existing ``except ValueError`` /
``except RuntimeError`` / ``except VeraCrawlError`` site keeps
matching. Markers are *additive* — they never replace a concrete
base.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

# Sensitive substrings that must never appear unredacted in an exception
# message. Duplicated here intentionally rather than imported from
# ``contracts.security_privacy`` because that module already imports from
# this one (foundation cycle); the cost of duplication is two short
# tuples, the cost of a cycle would be import-time deadlock.
_REDACTABLE_MARKERS = (
    "password",
    "secret",
    "token=",
    "api_key",
    "aws_access_key",
    "aws_secret",
    "bearer ",
    "authorization",
    "raw_prompt:",
    "raw_secret:",
    "raw_artifact:",
)


def _redact_field(value: str) -> str:
    """Return ``value`` with sensitive substrings replaced by ``[REDACTED]``.

    Used by :class:`CredentialScopeViolation` to scrub
    caller-supplied origin / route / reason strings before they land
    in the formatted exception message (and from there into logs and
    crash reports). The check is a substring match against the
    historical sensitive-marker tuple — overcautious by design,
    because the cost of a false-positive redaction in a log line is
    much smaller than the cost of a real credential leaking.
    """
    lowered = value.lower()
    for marker in _REDACTABLE_MARKERS:
        if marker in lowered:
            return "[REDACTED]"
    return value


def _redact_url(value: str) -> str:
    """Strip query / fragment / userinfo from a URL before logging.

    URL paths are usually safe; URL queries frequently carry API keys
    (``?api_key=...``), session tokens, or PII (``email=`` /
    ``code=`` / ``access_token=`` / ``jwt=`` / ``sid=``...). Phase 0
    cannot enumerate every safe parameter name, so the policy is
    drop-everything: the formatted message keeps only scheme + host +
    path, with userinfo (``user:pass@host``) stripped because it is
    always credential-bearing.

    Defensive parsing: ``urlsplit`` itself does not raise on the
    inputs we care about, but reading ``parts.port`` raises
    ``ValueError`` for malformed authorities like ``host:bad``. Wrap
    the access so a malformed URL becomes a plain ``[REDACTED]``
    instead of an unrelated ``ValueError`` that would prevent the
    policy exception from being raised at all (codex iter-2
    important: an exception constructor must not crash on caller
    input).
    """
    if "://" not in value:
        return _redact_field(value)
    try:
        parts = urlsplit(value)
    except ValueError:
        return _redact_field(value)
    netloc = parts.hostname or ""
    try:
        port = parts.port
    except ValueError:
        # Malformed authority — fall back to bare hostname, no port.
        port = None
    if port is not None:
        netloc = f"{netloc}:{port}"
    sanitized = urlunsplit((parts.scheme, netloc, parts.path, "", ""))
    return _redact_field(sanitized)


def _redact_route(value: str) -> str:
    """Strip query / fragment from a route path before logging.

    A route is a URL path component (no scheme / host) — the typical
    leak vector is ``?session=...`` / ``?api_key=...`` / ``#code=...``
    appended to a real route. Treating the route as plain text via
    ``_redact_field`` only catches the small marker list and lets
    other PII parameter names slip through. Drop the query and
    fragment unconditionally instead, then run the path-only result
    through the marker check as a final safety net.
    """
    path = value.split("#", 1)[0]
    path = path.split("?", 1)[0]
    return _redact_field(path)


class RetryableError(Exception):
    """Marker: the operation may be retried under the same policy.

    Mix in alongside a concrete exception base when the failure is
    transient (transport timeout, rate-limit with retry-after, 5xx).

    Markers subclass :class:`Exception` so ``except RetryableError:``
    works at runtime — Python's ``except`` clause requires the caught
    type to descend from :class:`BaseException`. The concrete
    exception's primary base (typically :class:`ValueError` or
    :class:`RuntimeError`) is preserved alongside the marker via
    multiple inheritance, so existing
    ``except ValueError`` / ``except RuntimeError`` sites keep
    matching unchanged.
    """


class FatalError(Exception):
    """Marker: do not retry; abandon the unit of work.

    Mix in alongside a concrete exception base when the failure is
    permanent (404 / 410, retry-exhausted, malformed contract).
    """


class PolicyViolation(Exception):
    """Marker: policy refused the operation.

    Mix in alongside a concrete exception base when the failure is
    a policy / charter / safety / budget refusal — denied egress,
    denied redirect, exceeded token budget, structured-output
    schema mismatch. ``PolicyViolation`` failures must not be
    retried automatically; they require an audit-recorded decision.
    """


class VeraCrawlError(Exception):
    """Base project exception."""


class ContractValidationError(VeraCrawlError):
    """Raised when contract data is invalid."""


class RegistryValidationError(VeraCrawlError):
    """Raised when the foundation registry is inconsistent."""


class PolicyViolationError(VeraCrawlError, PolicyViolation):
    """Raised when a denied or review-required policy is bypassed.

    The historical concrete exception for foundation policy refusal.
    Now also carries the :class:`PolicyViolation` marker so generic
    dispatch (``except PolicyViolation``) catches it.
    """


class ReplayValidationError(VeraCrawlError):
    """Raised when replay completeness cannot pass."""


class FixtureValidationError(VeraCrawlError):
    """Raised when a fixture or oracle is invalid."""


class AdapterConformanceError(VeraCrawlError):
    """Raised when an adapter cannot map to VeraCrawl contracts."""


class ImportBoundaryError(VeraCrawlError):
    """Raised when a core package imports forbidden dependencies."""


class CredentialScopeViolation(VeraCrawlError, PolicyViolation):
    """Raised when ``StrictAllowlistScope`` (Phase 2 step 2.2) refuses
    a credential-bearing request because its origin / route pattern /
    method falls outside the ``CredentialScope`` allowlist.

    Inherits :class:`VeraCrawlError` so existing
    ``except VeraCrawlError`` handlers continue to match, and mixes in
    :class:`PolicyViolation` so generic dispatch
    (``except PolicyViolation:``) catches scope refusals alongside
    other policy refusals (egress / redirect / token-budget /
    structured-output).

    Privacy contract: every public attribute (``scope_ref`` /
    ``requested_origin`` / ``requested_route`` / ``requested_method``
    / ``reason``) carries the *sanitized* value, not the raw caller
    input. Python exception logging routinely reaches into
    ``__dict__`` / ``vars(err)`` (for example ``logging.exception``
    formats with ``exc.__dict__``); storing raw caller-supplied
    strings on the exception instance would leak credentials and PII
    into log lines that the formatted-message redaction never sees.

    Sanitization rules:

    * ``requested_origin`` is reduced to scheme + host + path (query
      strings, fragments, and userinfo dropped — the typical
      credential-leak vector at this boundary is ``?api_key=...``
      or ``user:pass@host``); malformed authorities (e.g.,
      ``host:bad`` ports) fall back to a bare hostname instead of
      raising.
    * ``requested_route`` has query and fragment dropped
      unconditionally because the substring marker check cannot
      enumerate every PII parameter name (``session=`` / ``code=``
      / ``email=`` / ``jwt=`` and similar all carry credentials or
      PII outside the marker tuple).
    * Every field then runs through the substring marker check;
      anything matching is replaced with ``[REDACTED]``.

    Audit semantics: this exception is a *signal* — "scope refused
    request" — not the canonical audit record. The structured data
    the audit pipeline persists comes from ``CredentialUseRecord``
    (Phase 2 outbox row) where redaction is applied at write time
    in a controlled context. Losing fidelity on this exception's
    public attributes is therefore acceptable in exchange for
    closing the ``__dict__`` leak vector.
    """

    def __init__(
        self,
        *,
        scope_ref: str,
        requested_origin: str,
        requested_route: str,
        requested_method: str,
        reason: str,
    ) -> None:
        # All public attributes carry sanitized values. Exceptions
        # are routinely logged via ``logging.exception()`` and similar
        # paths that read ``__dict__`` (or ``vars(err)``) — storing
        # raw caller-supplied values on the instance would leak
        # credentials / PII into log lines that the formatted-message
        # redaction never sees. The audit pipeline reads structured
        # data from ``CredentialUseRecord`` in the outbox, not from
        # the raised exception, so losing fidelity here is fine
        # (codex iter-3 important).
        self.scope_ref = _redact_field(scope_ref)
        self.requested_origin = _redact_url(requested_origin)
        self.requested_route = _redact_route(requested_route)
        self.requested_method = _redact_field(requested_method)
        self.reason = _redact_field(reason)
        super().__init__(
            f"credential scope refused {self.requested_method} "
            f"{self.requested_origin}{self.requested_route} "
            f"(scope={self.scope_ref}): {self.reason}"
        )
