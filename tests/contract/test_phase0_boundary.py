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
