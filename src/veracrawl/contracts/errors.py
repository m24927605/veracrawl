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

from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit

# Sensitive substrings that must never appear unredacted in an exception
# message. Duplicated here intentionally rather than imported from
# ``contracts.security_privacy`` because that module already imports from
# this one (foundation cycle); the cost of duplication is one tuple,
# the cost of a cycle would be import-time deadlock.
#
# The list deliberately covers credential markers AND common PII /
# session-tracking parameter names that show up in URL queries, OAuth
# flows, and free-form error messages. ``_redact_field`` triggers a
# full-string ``[REDACTED]`` substitution if ANY marker matches — over-
# cautious by design (codex iter-5 important: ``session=`` /
# ``email=`` / ``jwt=`` outside the original credential tuple were
# slipping through ``reason`` text).
_REDACTABLE_MARKERS = (
    # Direct credential tokens
    "password",
    "secret",
    "token=",
    "api_key",
    "apikey=",
    "aws_access_key",
    "aws_secret",
    "bearer ",
    "authorization",
    # Internal markers
    "raw_prompt:",
    "raw_secret:",
    "raw_artifact:",
    # OAuth / OIDC parameters
    "access_token=",
    "refresh_token=",
    "id_token=",
    "oauth_token=",
    "code=",  # OAuth authorization code
    # Session / cookie / CSRF
    "session=",
    "sessionid=",
    "jsessionid=",
    "sid=",
    "phpsessid=",
    "csrf=",
    "csrf_token=",
    "xsrf=",
    "auth=",
    # JWT / signed payloads
    "jwt=",
    # PII
    "email=",
    "ssn=",
    "phone=",
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
        # Malformed URL — full redaction (codex iter-4 important):
        # ``_redact_field`` only catches a small marker list, so a
        # malformed URL containing userinfo or a query parameter
        # outside the marker tuple (``?session=...`` /
        # ``?code=...`` etc.) would otherwise survive into the log
        # line.
        return "[REDACTED]"
    try:
        port = parts.port
    except ValueError:
        return "[REDACTED]"
    netloc = parts.hostname or ""
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


class CredentialScopeReason(StrEnum):
    """Structured refusal classes for ``CredentialScopeViolation``.

    Phase 0 step 0.4 reservation pull-forward (Phase 2 step 2.2b):
    the original ``reason: str`` field on ``CredentialScopeViolation``
    was free-form text, redacted by a substring marker check before
    landing in the formatted exception message. That defended
    against the original credential-marker tuple, but a producer
    could in principle pipe arbitrary content (caller-supplied URLs,
    raw user input, a ``ValueError.args`` from elsewhere) into the
    field with a token that fell outside the marker tuple. A
    structured (enum-coded) shape closes the leak structurally:
    callers can only express known refusal classes, so there is no
    free-form text path to leak through.

    Values mirror the four refusal classes ``StrictAllowlistScope``
    (Phase 2 step 2.2a) emits at runtime; producers / adapters add
    new classes here when a new refusal mode lands.
    """

    ORIGIN_NOT_ALLOWED = "origin_not_allowed"
    ROUTE_NOT_ALLOWED = "route_not_allowed"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    EXPIRED = "expired"


_CREDENTIAL_SCOPE_REASON_VALUES: frozenset[str] = frozenset(
    member.value for member in CredentialScopeReason
)


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

    Structured ``reason`` (Phase 2 step 2.2b): the previous
    free-form ``reason: str`` field was a residual leak path —
    a producer could pipe arbitrary content with a token outside
    the redaction marker tuple. ``reason`` now must be a
    :class:`CredentialScopeReason` enum value (or a string that
    matches one of the enum's values). Anything else raises
    :class:`ValueError` at construction time, closing the leak
    structurally rather than via marker checks.
    """

    def __init__(
        self,
        *,
        scope_ref: str,
        requested_origin: str,
        requested_route: str,
        requested_method: str,
        reason: CredentialScopeReason | str,
    ) -> None:
        # All public attributes carry sanitized values. Exceptions
        # are routinely logged via ``logging.exception()`` and similar
        # paths that read ``__dict__`` (or ``vars(err)``) — storing
        # raw caller-supplied values on the instance would leak
        # credentials / PII into log lines that the formatted-message
        # redaction never sees. The audit pipeline reads structured
        # data from ``CredentialUseRecord`` in the outbox, not from
        # the raised exception, so losing fidelity here is fine.
        self.scope_ref = _redact_field(scope_ref)
        self.requested_origin = _redact_url(requested_origin)
        self.requested_route = _redact_route(requested_route)
        self.requested_method = _redact_field(requested_method)
        # Coerce to the enum so a plain str like ``"expired"`` works
        # for the (rare) caller that built the value programmatically,
        # but anything outside the enum's value set raises before the
        # exception even constructs — there is no free-form path.
        if isinstance(reason, CredentialScopeReason):
            self.reason: CredentialScopeReason = reason
        else:
            # Validate by membership in a precomputed value set rather
            # than ``CredentialScopeReason(reason)``. The enum's lookup
            # error stores the raw rejected ``reason`` in its
            # ``args``; even with ``from None`` clearing ``__cause__``,
            # Python's automatic ``__context__`` chaining would still
            # leak the credential-shaped input to any logging /
            # telemetry path that walks ``__context__``. Membership
            # check skips the lookup entirely so no chained exception
            # ever exists, and the raise lives outside any ``except``
            # block so ``__context__`` is also clean.
            valid = isinstance(reason, str) and reason in _CREDENTIAL_SCOPE_REASON_VALUES
            if not valid:
                raise ValueError(
                    "CredentialScopeViolation.reason must be a "
                    "CredentialScopeReason enum value (or its string "
                    "form); got an unknown value (redacted) — "
                    "free-form reasons were retired in Phase 2 step "
                    "2.2b to close a residual leak path"
                ) from None
            self.reason = CredentialScopeReason(reason)
        super().__init__(
            f"credential scope refused {self.requested_method} "
            f"{self.requested_origin}{self.requested_route} "
            f"(scope={self.scope_ref}): {self.reason.value}"
        )


# ---------------------------------------------------------------------------
# Provider-neutral model-provider exception surface (codex iter-4 important).
#
# Phase 4 ``OutboxBackedBudget`` and other core / domain components raise
# :class:`TokenBudgetExceeded` and :class:`StructuredOutputViolation`. They
# cannot import from ``veracrawl.adapters.*`` because core code must depend
# only on contracts / ports. The full v2 model-provider exception surface
# therefore lives here in :mod:`contracts.errors`; the existing
# ``adapters.model_providers.errors`` module has been reduced to a
# back-compat re-export so existing callers (the OpenAI adapter, tests,
# anything importing through the old path) continue to work.
# ---------------------------------------------------------------------------


class ModelProviderError(RuntimeError):
    """Adapter-level failure with structured fields and no body content.

    Inherits :class:`RuntimeError` so existing
    ``except RuntimeError`` handlers continue to match. Category-specific
    subclasses below additionally mix in one of the markers from this
    module (``RetryableError`` / ``FatalError`` / ``PolicyViolation``)
    so callers can dispatch on category without inspecting
    ``error_code``.

    The formatted message is provider-neutral on purpose: the
    ``ModelProviderPort`` v2 (Phase 4 step 4.1) is provider-blind, so
    the base class's message cannot privilege one provider. Concrete
    adapters that want a provider-flavored message subclass and
    override.
    """

    def __init__(
        self,
        *,
        status_code: int,
        error_code: str,
        request_id: str | None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        request_id_repr = request_id if request_id is not None else "<none>"
        super().__init__(
            f"model provider error: status={status_code} "
            f"code={error_code} request_id={request_id_repr}"
        )


class ProviderAuthFailed(ModelProviderError, FatalError):
    """401 / 403 — credential bad or revoked. Do not retry."""


class ProviderRateLimited(ModelProviderError, RetryableError):
    """429 — caller may retry under same policy after Retry-After."""


class ProviderServerError(ModelProviderError, RetryableError):
    """5xx — transient upstream error. Caller may retry."""


class ProviderBadRequest(ModelProviderError, FatalError):
    """400 / 422 — request shape rejected. Retrying without changes will not help."""


class ProviderNotFound(ModelProviderError, FatalError):
    """404 — model id or endpoint not found."""


class ProviderAdapterFailure(ModelProviderError, FatalError):
    """Catch-all for transport / decode failures the adapter could not classify."""


class TokenBudgetExceeded(ModelProviderError, PolicyViolation):
    """Raised when a model call would push run-level token usage past
    the declared ``TokenBudget`` (Phase 4 ``OutboxBackedBudget``).

    The exception is a ``PolicyViolation`` rather than a ``RetryableError``
    because retrying without changing the budget would just trigger the
    same refusal. Phase 5 ``RecoveryPort`` is expected to map this to
    ``RecoveryDecisionKind.ABANDON`` or ``REQUEST_REVIEW``.
    """


class StructuredOutputViolation(ModelProviderError, PolicyViolation):
    """Raised when a model returns JSON that does not validate against
    the declared ``ResponseFormat.json_schema`` (Phase 4 OpenAI / Anthropic
    adapters apply this on the parsed payload).

    Marker is ``PolicyViolation``: the contract requires schema-valid
    output and the adapter's job is to surface the contract breach,
    not silently coerce or retry. Recovery may legitimately ask the
    same model again with a follow-up prompt, but that's a Phase 5
    runtime decision, not the contract layer's call.
    """


_PROVIDER_ERROR_CODE_TO_CLASS: dict[str, type[ModelProviderError]] = {
    "AUTH_FAILED": ProviderAuthFailed,
    "RATE_LIMITED": ProviderRateLimited,
    "SERVER_ERROR": ProviderServerError,
    "BAD_REQUEST": ProviderBadRequest,
    "NOT_FOUND": ProviderNotFound,
    "ADAPTER_FAILURE": ProviderAdapterFailure,
    "TOKEN_BUDGET_EXCEEDED": TokenBudgetExceeded,
    "STRUCTURED_OUTPUT_VIOLATION": StructuredOutputViolation,
}


def classify_provider_error(
    *,
    status_code: int,
    error_code: str,
    request_id: str | None,
) -> ModelProviderError:
    """Return the marker-bearing subclass for ``error_code``.

    Falls back to :class:`ProviderAdapterFailure` (a ``FatalError``)
    for codes without a dedicated subclass so every classified error
    carries one of the recovery-dispatch markers
    (``RetryableError`` / ``FatalError`` / ``PolicyViolation``).
    Falling back to the bare ``ModelProviderError`` would leave the
    orchestrator's ``except FatalError:`` / ``except PolicyViolation:``
    branches blind to unknown codes (codex iter-3 important).
    """
    cls = _PROVIDER_ERROR_CODE_TO_CLASS.get(error_code, ProviderAdapterFailure)
    return cls(status_code=status_code, error_code=error_code, request_id=request_id)


def classify_provider_status(status: int) -> str:
    """Map an HTTP status code to one of the canonical ``error_code``
    strings the registry uses. Provider-neutral; the OpenAI / Anthropic
    adapters translate their wire status codes through this helper.
    """
    if status in (401, 403):
        return "AUTH_FAILED"
    if status == 429:
        return "RATE_LIMITED"
    if status == 404:
        return "NOT_FOUND"
    if status in (400, 422):
        return "BAD_REQUEST"
    if 500 <= status < 600:
        return "SERVER_ERROR"
    return "ADAPTER_FAILURE"


# ---------------------------------------------------------------------------
# s2 of general-purpose-crawler-agentification: typed errors for the
# LLM-driven CrawlPlanner adapter and the in-product replay consumer.
# ---------------------------------------------------------------------------


class ProviderTraceMissingError(VeraCrawlError, FatalError):
    """Raised when ``ProviderResponse.raw_response_ref`` is missing.

    The s2 ``LlmCrawlPlanner`` requires every successful model call to
    carry a non-blank ``raw_response_ref`` so the planner's
    ``PlanDecision.replay_refs`` is a complete byte-equal replay
    anchor. Provider adapters that have not yet been wired to the
    artifact store (s2.1) trip this gate. ``FatalError`` because the
    fix is upstream provider wiring, not retrying the same call.

    Constructor mirrors ``PromptTemplateNotFoundError``: a single
    domain-specific kwarg, no ``ModelProviderError`` plumbing.
    """

    def __init__(self, *, provider_request_id: str) -> None:
        self.provider_request_id = provider_request_id
        super().__init__(
            f"provider response for {provider_request_id!r} is missing raw_response_ref"
        )


class ReplayLookupMissError(VeraCrawlError, FatalError):
    """Raised by ``ReplayingModelProviderV2`` when no canned response
    is registered for a given ``ProviderRequest.id``.

    Indicates the replay bundle is incomplete or the request id was
    mutated between record and replay — both are upstream wiring bugs
    that retrying cannot fix.
    """

    def __init__(self, *, provider_request_id: str) -> None:
        self.provider_request_id = provider_request_id
        super().__init__(
            f"replay bundle has no canned response for {provider_request_id!r}"
        )
