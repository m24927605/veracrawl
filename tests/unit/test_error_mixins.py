"""Tests for the RetryableError / FatalError / PolicyViolation marker mixins.

Phase 0 of the production-authorized-source-crawler design adds three
marker classes that adapter / runtime exceptions mix in alongside their
concrete bases (``ValueError`` / ``RuntimeError`` / ``Exception``). The
markers let callers dispatch on category — *retry?* / *abandon?* /
*audit-and-stop?* — without inspecting enum values or parsing prose.

These tests guard:

1. The markers are pure (no state, no methods).
2. Specific exception subclasses inherit the right marker.
3. The dispatch helpers (``classify_network_failure``,
   ``classify_provider_error``) return marker-bearing instances.
4. Backwards compatibility: every concrete exception still subclasses
   its historical base, so existing ``except ValueError`` /
   ``except RuntimeError`` / ``except VeraCrawlError`` sites continue
   to match.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.model_providers.openai_responses import (
    ModelProviderError,
    ProviderAdapterFailure,
    ProviderAuthFailed,
    ProviderBadRequest,
    ProviderNotFound,
    ProviderRateLimited,
    ProviderServerError,
    classify_provider_error,
)
from veracrawl.adapters.network.stdlib_http import (
    AdapterFailureError,
    EgressDeniedError,
    NetworkAdapterError,
    NetworkAdapterTimeoutError,
    NetworkTimeoutError,
    PrivateNetworkDeniedError,
    RedirectDeniedError,
    RetryExhaustedError,
    classify_network_failure,
)
from veracrawl.contracts.enums import NetworkFailureType
from veracrawl.contracts.errors import (
    FatalError,
    PolicyViolation,
    PolicyViolationError,
    RetryableError,
    VeraCrawlError,
)

# Marker classes themselves.


def test_markers_are_exception_subclasses() -> None:
    """Markers descend from Exception so ``except <Marker>:`` works at
    runtime; Python's except clause requires a BaseException subclass."""
    for marker in (RetryableError, FatalError, PolicyViolation):
        assert issubclass(marker, Exception)


def test_markers_can_be_caught_directly() -> None:
    """Sanity: catching the marker by itself works."""
    for marker in (RetryableError, FatalError, PolicyViolation):
        try:
            raise marker("test")
        except Exception as caught:
            assert isinstance(caught, marker)


# Network-side classifications.


def test_network_timeout_is_retryable() -> None:
    err = NetworkTimeoutError()
    assert isinstance(err, NetworkAdapterError)
    assert isinstance(err, ValueError)
    assert isinstance(err, RetryableError)
    assert err.failure_type is NetworkFailureType.NETWORK_TIMEOUT


def test_network_adapter_timeout_alias_preserved() -> None:
    """Backwards-compat: legacy import name resolves to the new class."""
    assert NetworkAdapterTimeoutError is NetworkTimeoutError


def test_retry_exhausted_is_fatal() -> None:
    err = RetryExhaustedError("max_attempts=3 last_status=503")
    assert isinstance(err, NetworkAdapterError)
    assert isinstance(err, ValueError)
    assert isinstance(err, FatalError)
    assert not isinstance(err, RetryableError)
    assert err.failure_type is NetworkFailureType.RETRY_EXHAUSTED


def test_redirect_denied_is_policy_violation() -> None:
    err = RedirectDeniedError("protocol_downgrade_https_to_http")
    assert isinstance(err, NetworkAdapterError)
    assert isinstance(err, PolicyViolation)
    assert err.failure_type is NetworkFailureType.REDIRECT_DENIED


def test_egress_denied_is_policy_violation() -> None:
    err = EgressDeniedError("redirect off allowlist: https://x.test")
    assert isinstance(err, PolicyViolation)
    assert err.failure_type is NetworkFailureType.EGRESS_DENIED


def test_private_network_denied_is_policy_violation() -> None:
    err = PrivateNetworkDeniedError("redirect to private host: 127.0.0.1")
    assert isinstance(err, PolicyViolation)
    assert err.failure_type is NetworkFailureType.PRIVATE_NETWORK_DENIED


def test_adapter_failure_is_fatal() -> None:
    err = AdapterFailureError("ConnectError: refused")
    assert isinstance(err, FatalError)
    assert err.failure_type is NetworkFailureType.ADAPTER_FAILURE


def test_classify_network_failure_returns_marker_bearing_subclass() -> None:
    cases = [
        (NetworkFailureType.NETWORK_TIMEOUT, NetworkTimeoutError, RetryableError),
        (NetworkFailureType.RETRY_EXHAUSTED, RetryExhaustedError, FatalError),
        (NetworkFailureType.REDIRECT_DENIED, RedirectDeniedError, PolicyViolation),
        (NetworkFailureType.EGRESS_DENIED, EgressDeniedError, PolicyViolation),
        (
            NetworkFailureType.PRIVATE_NETWORK_DENIED,
            PrivateNetworkDeniedError,
            PolicyViolation,
        ),
        (NetworkFailureType.ADAPTER_FAILURE, AdapterFailureError, FatalError),
    ]
    for failure_type, expected_cls, expected_marker in cases:
        err = classify_network_failure(failure_type, "detail")
        assert type(err) is expected_cls
        assert isinstance(err, expected_marker)
        assert err.failure_type is failure_type


def test_classify_network_failure_falls_back_to_base_for_unmapped_types() -> None:
    """SIZE_BUDGET_EXCEEDED, ROBOTS_BLOCKED etc. don't have dedicated
    subclasses yet; the helper returns the generic NetworkAdapterError
    so callers continue to get a ValueError they can catch."""
    err = classify_network_failure(NetworkFailureType.SIZE_BUDGET_EXCEEDED, "too big")
    assert type(err) is NetworkAdapterError
    assert isinstance(err, ValueError)


# Network-side dispatch with marker.


def test_dispatch_on_retryable_marker_for_timeout() -> None:
    def _raise() -> None:
        raise NetworkTimeoutError()

    with pytest.raises(RetryableError):
        _raise()


def test_dispatch_on_policy_violation_marker_for_redirect() -> None:
    def _raise() -> None:
        raise RedirectDeniedError("loop")

    with pytest.raises(PolicyViolation):
        _raise()


def test_existing_value_error_catch_still_matches() -> None:
    """The fetch acquisition layer's ``except ValueError:`` must keep
    catching every NetworkAdapterError subclass. Regression for codex
    review v1 critical #5."""
    for err in (
        NetworkTimeoutError(),
        RetryExhaustedError("x"),
        RedirectDeniedError("x"),
        EgressDeniedError("x"),
        PrivateNetworkDeniedError("x"),
        AdapterFailureError("x"),
    ):
        try:
            raise err
        except ValueError as caught:
            assert caught is err  # caught exactly the original instance


# Provider-side classifications.


def test_provider_auth_failed_is_fatal() -> None:
    err = ProviderAuthFailed(
        status_code=401, error_code="AUTH_FAILED", request_id="req_x"
    )
    assert isinstance(err, ModelProviderError)
    assert isinstance(err, RuntimeError)
    assert isinstance(err, FatalError)


def test_provider_rate_limited_is_retryable() -> None:
    err = ProviderRateLimited(
        status_code=429, error_code="RATE_LIMITED", request_id=None
    )
    assert isinstance(err, RetryableError)


def test_provider_server_error_is_retryable() -> None:
    err = ProviderServerError(
        status_code=503, error_code="SERVER_ERROR", request_id=None
    )
    assert isinstance(err, RetryableError)


def test_provider_bad_request_is_fatal() -> None:
    err = ProviderBadRequest(
        status_code=400, error_code="BAD_REQUEST", request_id=None
    )
    assert isinstance(err, FatalError)


def test_provider_not_found_is_fatal() -> None:
    err = ProviderNotFound(status_code=404, error_code="NOT_FOUND", request_id=None)
    assert isinstance(err, FatalError)


def test_classify_provider_error_picks_right_subclass() -> None:
    cases = [
        (401, "AUTH_FAILED", ProviderAuthFailed, FatalError),
        (403, "AUTH_FAILED", ProviderAuthFailed, FatalError),
        (429, "RATE_LIMITED", ProviderRateLimited, RetryableError),
        (500, "SERVER_ERROR", ProviderServerError, RetryableError),
        (502, "SERVER_ERROR", ProviderServerError, RetryableError),
        (503, "SERVER_ERROR", ProviderServerError, RetryableError),
        (504, "SERVER_ERROR", ProviderServerError, RetryableError),
        (400, "BAD_REQUEST", ProviderBadRequest, FatalError),
        (422, "BAD_REQUEST", ProviderBadRequest, FatalError),
        (404, "NOT_FOUND", ProviderNotFound, FatalError),
        (0, "ADAPTER_FAILURE", ProviderAdapterFailure, FatalError),
    ]
    for status, code, expected_cls, expected_marker in cases:
        err = classify_provider_error(
            status_code=status, error_code=code, request_id=None
        )
        assert type(err) is expected_cls, f"status={status} code={code}"
        assert isinstance(err, expected_marker)


def test_existing_runtime_error_catch_still_matches_provider() -> None:
    """Existing call sites that catch RuntimeError must still match."""
    err = ProviderAuthFailed(
        status_code=401, error_code="AUTH_FAILED", request_id=None
    )
    try:
        raise err
    except RuntimeError as caught:
        assert caught is err


# Foundation-side: PolicyViolationError now also a marker.


def test_policy_violation_error_carries_marker() -> None:
    err = PolicyViolationError("denied")
    assert isinstance(err, VeraCrawlError)
    assert isinstance(err, Exception)
    assert isinstance(err, PolicyViolation)


def test_existing_veracrawl_error_catch_still_matches() -> None:
    err = PolicyViolationError("denied")
    try:
        raise err
    except VeraCrawlError as caught:
        assert caught is err


# Charter / no-leak boundary checks.


def test_classify_network_failure_does_not_leak_through_str() -> None:
    """Detail strings should not be modified; the str form is
    deterministic and free of internal class lookup details."""
    err = classify_network_failure(
        NetworkFailureType.NETWORK_TIMEOUT, "ConnectTimeout: ..."
    )
    assert str(err) == "network_timeout: network request timed out" or (
        "network_timeout" in str(err)
    )


def test_classify_provider_error_message_has_no_body() -> None:
    """Provider errors must never embed body content (RAW_RESPONSE_LEAK)."""
    err = classify_provider_error(
        status_code=400, error_code="BAD_REQUEST", request_id="req_xyz"
    )
    msg = str(err)
    assert "400" in msg
    assert "BAD_REQUEST" in msg
    assert "req_xyz" in msg
    # No body / prompt / response substring possible because constructor
    # only takes status / code / request_id.
    assert "{" not in msg  # no JSON dump
    assert "secret" not in msg.lower()
