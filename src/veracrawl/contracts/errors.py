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
    (``?api_key=...``), session tokens, or PII. Phase 0 cannot tell
    which, so the safest move is to drop the query and fragment
    entirely. Userinfo (``user:pass@host``) is always credential-
    bearing; strip it too. A field that doesn't parse as a URL is
    redacted as a plain string.
    """
    if "://" not in value:
        return _redact_field(value)
    try:
        parts = urlsplit(value)
    except ValueError:
        return _redact_field(value)
    netloc = parts.hostname or ""
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    sanitized = urlunsplit((parts.scheme, netloc, parts.path, "", ""))
    return _redact_field(sanitized)


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

    The exception carries the (opaque) credential scope ref and the
    requested origin / route / method as raw attributes so the audit
    pipeline can decide what to persist. The *formatted* message that
    lands in logs and stack traces, however, runs every caller-
    supplied string through a redaction helper:

    * ``requested_origin`` and ``requested_route`` are reduced to
      scheme + host + path (query strings, fragments, and userinfo
      are dropped — the typical credential-leak vector at this
      boundary is ``?api_key=...`` or ``user:pass@host``);
    * ``reason`` is scrubbed against the same sensitive-marker
      tuple ``security_privacy`` already uses (``password`` /
      ``token=`` / ``bearer`` / etc.) and replaced with
      ``[REDACTED]`` if any marker matches.

    The producer keeps full visibility via the typed attributes; only
    the human-readable message is scrubbed. ``scope_ref`` is
    rendered as-is because the documented contract requires it to be
    an opaque vault handle (the ``CredentialScope`` validator already
    rejects handles that look like secrets).
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
        self.scope_ref = scope_ref
        self.requested_origin = requested_origin
        self.requested_route = requested_route
        self.requested_method = requested_method
        self.reason = reason
        safe_origin = _redact_url(requested_origin)
        safe_route = _redact_field(requested_route)
        safe_reason = _redact_field(reason)
        safe_method = _redact_field(requested_method)
        super().__init__(
            f"credential scope refused {safe_method} "
            f"{safe_origin}{safe_route} (scope={scope_ref}): {safe_reason}"
        )
