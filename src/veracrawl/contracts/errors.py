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
    requested origin / route / method so the audit trail can pinpoint
    *which* request the policy refused without exposing the credential
    value.
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
        super().__init__(
            f"credential scope refused {requested_method} "
            f"{requested_origin}{requested_route} (scope={scope_ref}): {reason}"
        )
