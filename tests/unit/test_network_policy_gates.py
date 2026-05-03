from __future__ import annotations

from veracrawl.contracts.enums import NetworkFailureType
from veracrawl.contracts.network import NetworkRequest
from veracrawl.fetch.network_acquisition import (
    build_network_request,
    is_private_network_url,
    network_policy_failure,
    url_origin,
)


def _request(url: str, scenario: str = "http-success") -> NetworkRequest:
    return build_network_request(
        fixture_id=f"fixture:{scenario}",
        target_url=url,
        policy_decision_refs=["policy:network"],
        size_budget_bytes=100,
        timeout_ms=100,
    )


def test_private_network_detection() -> None:
    assert is_private_network_url("http://127.0.0.1:1/static")
    assert is_private_network_url("http://localhost:1/static")
    assert not is_private_network_url("http://example.com/static")


def test_egress_denied_before_private_network() -> None:
    request = _request("http://example.invalid/blocked", "egress-denied")
    assert (
        network_policy_failure(
            request,
            scenario="http-success",
            egress_allowlist=["http://allowed.invalid"],
            allow_private_network=False,
        )
        == NetworkFailureType.EGRESS_DENIED
    )


def test_private_network_denied_when_not_allowed() -> None:
    request = _request("http://127.0.0.1:1/private", "private-denied")
    assert (
        network_policy_failure(
            request,
            scenario="http-success",
            egress_allowlist=[url_origin(request.url)],
            allow_private_network=False,
        )
        == NetworkFailureType.PRIVATE_NETWORK_DENIED
    )


def test_robots_rate_redirect_and_timeout_failures() -> None:
    request = _request("http://127.0.0.1:1/static")
    allowlist = [url_origin(request.url)]
    assert (
        network_policy_failure(
            request,
            scenario="robots-blocked",
            egress_allowlist=allowlist,
            allow_private_network=True,
        )
        == NetworkFailureType.ROBOTS_BLOCKED
    )
    assert (
        network_policy_failure(
            request,
            scenario="rate-budget",
            egress_allowlist=allowlist,
            allow_private_network=True,
        )
        == NetworkFailureType.RATE_BUDGET_EXCEEDED
    )
    assert (
        network_policy_failure(
            request,
            scenario="redirect-denied",
            egress_allowlist=allowlist,
            allow_private_network=True,
        )
        == NetworkFailureType.REDIRECT_DENIED
    )
    assert (
        network_policy_failure(
            request,
            scenario="timeout",
            egress_allowlist=allowlist,
            allow_private_network=True,
        )
        == NetworkFailureType.NETWORK_TIMEOUT
    )
