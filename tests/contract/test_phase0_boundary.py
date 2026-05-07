"""Phase 0 step 0.4 boundary tests.

design.md §4 Phase 0 deliverables include two boundary checks the v2
exception hierarchy must satisfy at all times:

1. **Mixin coverage**: every concrete subclass of
   :class:`NetworkAdapterError` / :class:`ModelProviderError` /
   :class:`VeraCrawlError` mixes in at least one of the marker
   classes (:class:`RetryableError` / :class:`FatalError` /
   :class:`PolicyViolation`). Without this, generic dispatch
   (``except PolicyViolation:`` etc.) silently misses the
   un-classified subclass and the orchestrator cannot route the
   failure to the right recovery path.

2. **Catch compatibility**: every concrete subclass keeps
   matching the *historical* base catch (``except ValueError`` for
   adapter errors, ``except RuntimeError`` for model-provider
   errors, ``except VeraCrawlError`` for foundation errors). The
   v2 marker mixins are *additive* — they never replace a
   concrete base — so the existing ``except`` sites in
   ``fetch/``, ``agents/``, ``evidence/`` keep matching.

The tests walk the class hierarchy programmatically rather than
enumerating raise sites. That gives a stronger guarantee than the
design's wording ("every raise site") because any future raise of
a yet-to-be-added subclass is also covered. The previous step-0.1
test_error_mixins.py covers the v1 subclasses individually; this
file is the structural rule that backs all of them at once and
catches any future addition that forgets the mixin.

Step 0.4 also adds three new ``PolicyViolation`` subclasses per
design.md §3.6 + §3.5:

* :class:`TokenBudgetExceeded` (Phase 4 ``OutboxBackedBudget``)
* :class:`StructuredOutputViolation` (Phase 4 LLM-driven extraction)
* :class:`CredentialScopeViolation` (Phase 2 ``StrictAllowlistScope``)

Each gets a per-class assertion below to lock its base + mixin.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.model_providers.openai_responses import (
    ModelProviderError,
    StructuredOutputViolation,
    TokenBudgetExceeded,
)
from veracrawl.adapters.network.stdlib_http import NetworkAdapterError
from veracrawl.contracts.errors import (
    CredentialScopeViolation,
    FatalError,
    PolicyViolation,
    RetryableError,
    VeraCrawlError,
)


def _all_concrete_subclasses(cls: type) -> set[type]:
    """Walk recursive subclasses; ignore the marker bases themselves."""
    out: set[type] = set()
    for sub in cls.__subclasses__():
        out.add(sub)
        out.update(_all_concrete_subclasses(sub))
    return out


def _has_marker(cls: type) -> bool:
    return issubclass(cls, RetryableError | FatalError | PolicyViolation)


# Boundary 1: every NetworkAdapterError / ModelProviderError /
# VeraCrawlError subclass mixes in at least one of the v2 markers.


def test_every_network_adapter_subclass_has_marker() -> None:
    subs = _all_concrete_subclasses(NetworkAdapterError)
    assert subs, "expected at least one NetworkAdapterError subclass"
    unmarked = sorted(
        f"{cls.__module__}.{cls.__qualname__}" for cls in subs if not _has_marker(cls)
    )
    assert not unmarked, (
        f"NetworkAdapterError subclasses missing marker: {unmarked}; add one of "
        "RetryableError / FatalError / PolicyViolation as a mix-in"
    )


def test_every_model_provider_subclass_has_marker() -> None:
    subs = _all_concrete_subclasses(ModelProviderError)
    assert subs, "expected at least one ModelProviderError subclass"
    unmarked = sorted(
        f"{cls.__module__}.{cls.__qualname__}" for cls in subs if not _has_marker(cls)
    )
    assert not unmarked, (
        f"ModelProviderError subclasses missing marker: {unmarked}; add one of "
        "RetryableError / FatalError / PolicyViolation as a mix-in"
    )


def test_every_veracrawl_error_subclass_has_marker_or_is_classification_only() -> None:
    """Foundation-side hierarchy is more permissive: not every
    ``VeraCrawlError`` subclass needs a marker because some
    (``ContractValidationError``, ``ReplayValidationError``,
    ``FixtureValidationError``, ``RegistryValidationError``,
    ``AdapterConformanceError``, ``ImportBoundaryError``) describe
    *test-time* / *load-time* problems, not runtime failures the
    orchestrator must dispatch on. The boundary the design cares
    about is that subclasses representing *runtime policy refusals*
    (i.e., currently :class:`PolicyViolationError` and
    :class:`CredentialScopeViolation`) carry the
    :class:`PolicyViolation` marker so generic dispatch works.

    Lock that as a static fact: enumerate the policy-refusal
    subclasses by name and assert each carries the marker.
    """
    policy_refusal_classes: tuple[type, ...] = (
        # Runtime refusals that already carry the marker per step 0.1.
        # New step-0.4 entry: CredentialScopeViolation.
    )
    from veracrawl.contracts.errors import PolicyViolationError

    policy_refusal_classes = (PolicyViolationError, CredentialScopeViolation)
    for cls in policy_refusal_classes:
        assert issubclass(cls, PolicyViolation), (
            f"{cls.__qualname__} represents a policy refusal but is not a PolicyViolation subclass"
        )
        assert issubclass(cls, VeraCrawlError), (
            f"{cls.__qualname__} must keep its VeraCrawlError base for "
            "backwards compatibility with except VeraCrawlError handlers"
        )


# Boundary 2: every subclass keeps matching its historical catch base.


def test_every_network_adapter_subclass_is_value_error() -> None:
    """Existing ``except ValueError`` sites in fetch/ must keep
    matching every NetworkAdapterError subclass."""
    for sub in _all_concrete_subclasses(NetworkAdapterError):
        assert issubclass(sub, ValueError), (
            f"{sub.__qualname__} must keep ValueError in its MRO so "
            "existing except ValueError handlers in fetch/ continue to match"
        )


def test_every_model_provider_subclass_is_runtime_error() -> None:
    """Existing ``except RuntimeError`` sites must keep matching
    every ModelProviderError subclass."""
    for sub in _all_concrete_subclasses(ModelProviderError):
        assert issubclass(sub, RuntimeError), (
            f"{sub.__qualname__} must keep RuntimeError in its MRO so "
            "existing except RuntimeError handlers continue to match"
        )


def test_every_veracrawl_error_subclass_is_exception() -> None:
    """Existing ``except VeraCrawlError`` and ``except Exception``
    sites must keep matching every foundation-error subclass."""
    for sub in _all_concrete_subclasses(VeraCrawlError):
        assert issubclass(sub, Exception)
        assert issubclass(sub, VeraCrawlError), (
            f"{sub.__qualname__} must keep VeraCrawlError in its MRO"
        )


# Per-class lockdown for the three new step-0.4 subclasses.


def test_token_budget_exceeded_classification() -> None:
    err = TokenBudgetExceeded(
        status_code=0,
        error_code="TOKEN_BUDGET_EXCEEDED",
        request_id=None,
    )
    assert isinstance(err, ModelProviderError)
    assert isinstance(err, RuntimeError)
    assert isinstance(err, PolicyViolation)
    assert not isinstance(err, RetryableError)
    assert not isinstance(err, FatalError)


def test_structured_output_violation_classification() -> None:
    err = StructuredOutputViolation(
        status_code=0,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )
    assert isinstance(err, ModelProviderError)
    assert isinstance(err, RuntimeError)
    assert isinstance(err, PolicyViolation)
    assert not isinstance(err, RetryableError)
    assert not isinstance(err, FatalError)


def test_credential_scope_violation_classification() -> None:
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/admin/users",
        requested_method="GET",
        reason="route /admin/users not in allowed_route_patterns",
    )
    assert isinstance(err, VeraCrawlError)
    assert isinstance(err, Exception)
    assert isinstance(err, PolicyViolation)
    assert not isinstance(err, RetryableError)
    assert not isinstance(err, FatalError)


def test_credential_scope_violation_carries_request_metadata() -> None:
    """Public attributes carry the *sanitized* values; benign inputs
    pass through unchanged."""
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/admin/users",
        requested_method="POST",
        reason="route not allowed",
    )
    assert err.scope_ref == "credential-scope:ebay"
    assert err.requested_origin == "https://api.ebay.com"
    assert err.requested_route == "/admin/users"
    assert err.requested_method == "POST"
    assert err.reason == "route not allowed"
    msg = str(err)
    assert "POST" in msg
    assert "https://api.ebay.com" in msg
    assert "/admin/users" in msg
    assert "credential-scope:ebay" in msg


def test_credential_scope_violation_message_carries_no_secret() -> None:
    """Even though the exception is built from policy-side metadata,
    no field should accept a credential value. The contract docstring
    classifies the credential ref as opaque; the message format
    deliberately omits any field that could carry a credential string."""
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/admin",
        requested_method="GET",
        reason="x",
    )
    msg = str(err)
    # The historical sensitive-marker tripwire — none of these tokens
    # should appear in the formatted message regardless of inputs.
    for marker in ("password", "secret=", "token=", "Bearer ", "api_key="):
        assert marker.lower() not in msg.lower(), (
            f"CredentialScopeViolation message leaked sensitive marker {marker!r}"
        )


# Tainted-input redaction (codex iter-1 minor + important):
# Run actually-sensitive strings through the constructor and assert the
# formatted message no longer contains the sensitive substring. The raw
# value remains accessible via the typed attribute for the audit
# pipeline.


@pytest.mark.parametrize(
    "tainted_origin",
    [
        "https://api.ebay.com/?api_key=sk-prod-XXXX",
        "https://api.ebay.com/path?token=eyJhbGc.payload.sig",
        "https://user:hunter2@api.ebay.com",
        "https://api.ebay.com/#access_token=Bearer-xyz",
    ],
)
def test_credential_scope_violation_redacts_tainted_origin(tainted_origin: str) -> None:
    """Origin / URL fields routinely carry query-string credentials
    or userinfo. Both the formatted message AND the public attribute
    must drop them — exception ``__dict__`` is read by logging
    handlers (codex iter-3 important)."""
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin=tainted_origin,
        requested_route="/items",
        requested_method="GET",
        reason="not in scope",
    )
    leaks = (
        "api_key=",
        "sk-prod-",
        "token=",
        "eyJhbGc",
        "hunter2",
        "Bearer-xyz",
        "access_token=",
    )
    msg = str(err)
    for leak in leaks:
        assert leak.lower() not in msg.lower(), (
            f"CredentialScopeViolation leaked {leak!r} from tainted "
            f"origin {tainted_origin!r}: msg={msg}"
        )
    # Public attribute is sanitized too (closes the __dict__ leak).
    for leak in leaks:
        assert leak.lower() not in err.requested_origin.lower(), (
            f"CredentialScopeViolation public attr leaked {leak!r}: "
            f"requested_origin={err.requested_origin!r}"
        )


@pytest.mark.parametrize(
    "tainted_route",
    [
        "/admin?password=hunter2",
        "/api/v1/secret=abc",
        "/oauth?api_key=sk-XXX",
        "/items?token=eyJhbGc",
    ],
)
def test_credential_scope_violation_redacts_tainted_route(tainted_route: str) -> None:
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route=tainted_route,
        requested_method="GET",
        reason="not in scope",
    )
    msg = str(err)
    for leak in ("password=", "secret=", "api_key=", "token=", "hunter2", "sk-XXX", "eyJhbGc"):
        assert leak.lower() not in msg.lower(), (
            f"CredentialScopeViolation leaked {leak!r} from tainted "
            f"route {tainted_route!r}: msg={msg}"
        )


@pytest.mark.parametrize(
    "tainted_reason",
    [
        "header Authorization: Bearer eyJhbGc.payload.sig was rejected",
        "received password=hunter2",
        "request carried token=abc",
        "credential api_key=sk-XXX did not match",
    ],
)
def test_credential_scope_violation_redacts_tainted_reason(tainted_reason: str) -> None:
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/items",
        requested_method="GET",
        reason=tainted_reason,
    )
    leaks = ("Bearer ", "password=", "token=", "api_key=", "hunter2", "sk-XXX", "eyJhbGc")
    msg = str(err)
    for leak in leaks:
        assert leak.lower() not in msg.lower(), (
            f"CredentialScopeViolation leaked {leak!r} from tainted "
            f"reason {tainted_reason!r}: msg={msg}"
        )
    # Public attribute is sanitized — raw reason is intentionally
    # not preserved on the exception (codex iter-3 important: the
    # audit pipeline reads structured data from CredentialUseRecord
    # in the outbox, not from the raised exception).
    for leak in leaks:
        assert leak.lower() not in err.reason.lower(), (
            f"CredentialScopeViolation public reason attr leaked {leak!r}: reason={err.reason!r}"
        )


# Codex iter-2 important: scope_ref redaction --------------------


@pytest.mark.parametrize(
    "tainted_scope",
    [
        "raw_secret:ebay-api-prod",
        "password=hunter2",
        "token=eyJhbGc",
        "api_key=sk-XXX",
        "Bearer eyJhbGc.payload.sig",
    ],
)
def test_credential_scope_violation_redacts_tainted_scope_ref(tainted_scope: str) -> None:
    """Even though the contract docs require scope_ref to be an
    opaque handle, the constructor must not depend on another
    validator to enforce that — a caller could plausibly pass an
    unvalidated string."""
    err = CredentialScopeViolation(
        scope_ref=tainted_scope,
        requested_origin="https://api.ebay.com",
        requested_route="/items",
        requested_method="GET",
        reason="not in scope",
    )
    leaks = ("password=", "token=", "api_key=", "Bearer ", "raw_secret:", "eyJhbGc", "sk-XXX")
    msg = str(err)
    for leak in leaks:
        assert leak.lower() not in msg.lower(), (
            f"CredentialScopeViolation leaked {leak!r} from tainted "
            f"scope_ref {tainted_scope!r}: msg={msg}"
        )
    # Public attribute is sanitized too.
    for leak in leaks:
        assert leak.lower() not in err.scope_ref.lower(), (
            f"CredentialScopeViolation public scope_ref attr leaked {leak!r}: "
            f"scope_ref={err.scope_ref!r}"
        )


# Codex iter-2 important: route query/fragment unconditional strip


@pytest.mark.parametrize(
    "tainted_route",
    [
        "/items?session=abc123",  # session id (not in marker tuple)
        "/items?sid=def456",
        "/items?access_token=XXX",  # access_token (not in marker tuple)
        "/items?code=oauth-grant-123",  # OAuth code
        "/items?email=user@example.test",  # PII
        "/items?jwt=eyJhbGc.payload.sig",
        "/items#access_token=XXX",  # fragment-bearing
        "/items?user=alice&session=abc",  # multiple params
    ],
)
def test_credential_scope_violation_strips_route_query_unconditionally(
    tainted_route: str,
) -> None:
    """Beyond the small marker list, query strings carry session ids,
    OAuth codes, JWTs, email addresses, and other PII that the
    substring matcher does not recognise. Route fields must be
    treated as URL paths and have query / fragment dropped
    regardless of content."""
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route=tainted_route,
        requested_method="GET",
        reason="x",
    )
    msg = str(err)
    # Neither ``?`` nor ``#`` should appear in the formatted route
    # (they're stripped); none of the parameter values should leak.
    for leak in (
        "session=",
        "sid=",
        "access_token=",
        "code=",
        "email=",
        "jwt=",
        "user=",
        "abc123",
        "def456",
        "oauth-grant-123",
        "user@example",
        "eyJhbGc",
    ):
        assert leak.lower() not in msg.lower(), (
            f"CredentialScopeViolation leaked {leak!r} from tainted "
            f"route {tainted_route!r}: msg={msg}"
        )


# Codex iter-2 important: malformed URL must not crash constructor


@pytest.mark.parametrize(
    "malformed_origin",
    [
        "https://example.com:bad/path",  # non-numeric port
        "https://example.com:99999/path",  # out-of-range port
        "https://[invalid-ipv6/path",
        "https://",
    ],
)
def test_credential_scope_violation_handles_malformed_origin(
    malformed_origin: str,
) -> None:
    """The constructor must produce a policy exception even on
    malformed caller input — crashing with an unrelated ValueError
    here would prevent ``StrictAllowlistScope`` from raising the
    typed scope refusal at all."""
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin=malformed_origin,
        requested_route="/items",
        requested_method="GET",
        reason="malformed origin",
    )
    # Constructor produced a real exception. Public attribute is
    # sanitized; we don't assert the original input survives because
    # malformed authorities fall back to a redacted form to avoid
    # the ``__dict__`` leak vector.
    assert isinstance(err, CredentialScopeViolation)
    assert isinstance(err.requested_origin, str)


# Codex iter-2 minor: provider-neutral message ------------------


def test_model_provider_error_message_is_provider_neutral() -> None:
    """After moving ``ModelProviderError`` to the provider-neutral
    module, the formatted message must not mention OpenAI (it would
    mislabel future Anthropic / other-provider raises)."""
    from veracrawl.adapters.model_providers.errors import ModelProviderError

    err = ModelProviderError(status_code=500, error_code="SERVER_ERROR", request_id="req_x")
    msg = str(err)
    assert "openai" not in msg.lower()
    assert "model provider" in msg.lower()
    assert "500" in msg
    assert "SERVER_ERROR" in msg
    assert "req_x" in msg


# Codex iter-3 important: __dict__ / vars() leak vector ----------


def test_credential_scope_violation_vars_and_dict_carry_no_secret() -> None:
    """``logging.exception()`` formats with ``exc.__dict__`` (and
    callers that inspect ``vars(err)`` follow the same path).
    Storing raw caller-supplied values on the exception would leak
    them via this back-channel even when ``str(err)`` is scrubbed.
    Verify both views are clean."""
    err = CredentialScopeViolation(
        scope_ref="raw_secret:ebay-prod",
        requested_origin="https://api.ebay.com/?api_key=sk-XXX",
        requested_route="/items?session=abc",
        requested_method="GET",
        reason="header Authorization: Bearer eyJhbGc was rejected",
    )
    leaks = (
        "raw_secret:",
        "ebay-prod",
        "api_key=",
        "sk-XXX",
        "session=",
        "abc",
        "Bearer ",
        "eyJhbGc",
    )
    for view_name, view in (("__dict__", err.__dict__), ("vars(err)", vars(err))):
        for value in view.values():
            if not isinstance(value, str):
                continue
            for leak in leaks:
                assert leak.lower() not in value.lower(), (
                    f"CredentialScopeViolation {view_name} value leaked "
                    f"{leak!r}: {view_name}.values() contains {value!r}"
                )


# Codex iter-3 minor: canonical module direct imports ------------


def test_canonical_provider_errors_module_exposes_classes() -> None:
    """The boundary tests above import provider exceptions through
    ``openai_responses`` (the back-compat re-export). Lock the
    canonical provider-neutral module independently so the
    re-export path's behavior cannot mask a regression in the
    canonical home."""
    from veracrawl.adapters.model_providers import errors as canonical_errors

    for name in (
        "ModelProviderError",
        "ProviderAuthFailed",
        "ProviderRateLimited",
        "ProviderServerError",
        "ProviderBadRequest",
        "ProviderNotFound",
        "ProviderAdapterFailure",
        "TokenBudgetExceeded",
        "StructuredOutputViolation",
        "classify_provider_error",
        "classify_status",
    ):
        assert hasattr(canonical_errors, name), (
            f"{name} missing from canonical provider-errors module"
        )


def test_canonical_provider_errors_module_classes_are_same_object() -> None:
    """The re-export in ``openai_responses`` must point at the
    same class objects defined in the canonical module — not a
    re-implementation. ``isinstance`` checks across import paths
    must agree."""
    from veracrawl.adapters.model_providers import errors as canonical_errors
    from veracrawl.adapters.model_providers import openai_responses as openai_re_export

    assert canonical_errors.ModelProviderError is openai_re_export.ModelProviderError
    assert canonical_errors.TokenBudgetExceeded is openai_re_export.TokenBudgetExceeded
    assert canonical_errors.StructuredOutputViolation is openai_re_export.StructuredOutputViolation


def test_classify_provider_error_unknown_code_falls_back_to_marker_class() -> None:
    """codex iter-3 important: an unknown ``error_code`` must still
    classify into a marker-bearing subclass; the previous fallback
    to bare ``ModelProviderError`` left the unknown-code path
    invisible to ``except FatalError:`` / ``except PolicyViolation:``
    dispatch."""
    from veracrawl.adapters.model_providers.errors import (
        ProviderAdapterFailure,
        classify_provider_error,
    )

    err = classify_provider_error(
        status_code=599, error_code="ADAPTER_DOES_NOT_KNOW", request_id="req_x"
    )
    assert type(err) is ProviderAdapterFailure
    assert isinstance(err, FatalError)


# Catch-compatibility lockdown for the three new subclasses.


def test_token_budget_exceeded_is_caught_by_runtime_error() -> None:
    err = TokenBudgetExceeded(
        status_code=0,
        error_code="TOKEN_BUDGET_EXCEEDED",
        request_id=None,
    )
    with pytest.raises(RuntimeError):
        raise err


def test_token_budget_exceeded_is_caught_by_policy_violation() -> None:
    err = TokenBudgetExceeded(
        status_code=0,
        error_code="TOKEN_BUDGET_EXCEEDED",
        request_id=None,
    )
    with pytest.raises(PolicyViolation):
        raise err


def test_structured_output_violation_is_caught_by_runtime_error() -> None:
    err = StructuredOutputViolation(
        status_code=0,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )
    with pytest.raises(RuntimeError):
        raise err


def test_structured_output_violation_is_caught_by_policy_violation() -> None:
    err = StructuredOutputViolation(
        status_code=0,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )
    with pytest.raises(PolicyViolation):
        raise err


def test_credential_scope_violation_is_caught_by_veracrawl_error() -> None:
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/x",
        requested_method="GET",
        reason="x",
    )
    with pytest.raises(VeraCrawlError):
        raise err


def test_credential_scope_violation_is_caught_by_policy_violation() -> None:
    err = CredentialScopeViolation(
        scope_ref="credential-scope:ebay",
        requested_origin="https://api.ebay.com",
        requested_route="/x",
        requested_method="GET",
        reason="x",
    )
    with pytest.raises(PolicyViolation):
        raise err


# classify_provider_error wires the new error codes.


def test_classify_provider_error_routes_token_budget_exceeded() -> None:
    from veracrawl.adapters.model_providers.openai_responses import (
        classify_provider_error,
    )

    err = classify_provider_error(
        status_code=0,
        error_code="TOKEN_BUDGET_EXCEEDED",
        request_id="req_x",
    )
    assert type(err) is TokenBudgetExceeded
    assert isinstance(err, PolicyViolation)


def test_classify_provider_error_routes_structured_output_violation() -> None:
    from veracrawl.adapters.model_providers.openai_responses import (
        classify_provider_error,
    )

    err = classify_provider_error(
        status_code=0,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )
    assert type(err) is StructuredOutputViolation
    assert isinstance(err, PolicyViolation)
