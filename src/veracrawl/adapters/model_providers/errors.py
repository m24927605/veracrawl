"""Provider-neutral model-provider exception types.

Phase 0 step 0.4 codex iter-1 surfaced that ``TokenBudgetExceeded`` and
``StructuredOutputViolation`` are *shared* domain / policy errors that
both the OpenAI Responses adapter (Phase 4 step 4.2) and the
Anthropic Messages adapter (Phase 4 step 4.3) plus the
``OutboxBackedBudget`` (Phase 4 step 4.5) need to import. Defining
them inside the OpenAI adapter would force every other consumer to
reach across the provider-blind boundary into an OpenAI-specific
module.

The same coupling argument applies to the existing
``ModelProviderError`` base and the per-status-code Provider* subclasses:
the v2 ``ModelProviderPort`` (Phase 4 step 4.1) is provider-blind, so
the typed exceptions it raises must also be provider-blind. This
module is therefore the canonical home for the model-provider
exception surface; ``openai_responses`` re-exports the same names for
backwards compatibility with existing tests / callers.

Charter contract: error paths must NEVER include response bodies,
prompt content, or context payloads in raised exceptions. The
constructor only accepts ``status_code`` / ``error_code`` /
``request_id``; there is no field that could carry caller content
into a log line or stack trace.
"""

from __future__ import annotations

from veracrawl.contracts.errors import FatalError, PolicyViolation, RetryableError


class ModelProviderError(RuntimeError):
    """Adapter-level failure with structured fields and no body content.

    Inherits :class:`RuntimeError` so existing
    ``except RuntimeError`` handlers continue to match. Category-specific
    subclasses below additionally mix in one of the markers from
    :mod:`veracrawl.contracts.errors` (``RetryableError`` /
    ``FatalError`` / ``PolicyViolation``) so callers can dispatch on
    category without inspecting ``error_code``.
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
            f"OpenAI Responses API error: status={status_code} "
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


_ERROR_CODE_TO_CLASS: dict[str, type[ModelProviderError]] = {
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

    Falls back to the generic :class:`ModelProviderError` for codes
    without a dedicated subclass; new codes can be added incrementally.
    """
    cls = _ERROR_CODE_TO_CLASS.get(error_code, ModelProviderError)
    return cls(status_code=status_code, error_code=error_code, request_id=request_id)


def classify_status(status: int) -> str:
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
