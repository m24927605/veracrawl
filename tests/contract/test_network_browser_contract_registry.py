from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_network_browser_contracts_registered() -> None:
    for contract in [
        "NetworkRequest",
        "NetworkResponse",
        "RedirectHop",
        "NetworkAcquisitionReport",
        "NetworkFixtureManifest",
        "BrowserSandboxPolicy",
        "BrowserInteractionStep",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_network_browser_commands_events_and_target_area_registered() -> None:
    expected_commands = {
        "execute_http_fetch",
        "record_network_acquisition",
        "capture_browser_snapshot",
    }
    assert expected_commands.issubset(COMMAND_TYPES)
    assert {
        "network_request_recorded",
        "network_response_recorded",
        "network_acquisition_reported",
        "browser_step_executed",
        "snapshot_written",
    }.issubset(EVENT_TYPES)
    assert "network_browser_acquisition" in TARGET_CONTRACT_AREAS


def test_network_browser_fixtures_registered() -> None:
    expected = {
        "network-http-success",
        "network-http-redirect",
        "network-browser-readonly",
        "network-robots-blocked",
        "network-private-denied",
        "network-egress-denied",
        "network-rate-budget",
        "network-size-budget",
        "network-redirect-denied",
        "network-timeout",
        "network-browser-unsafe-side-effect",
    }
    assert expected.issubset(FIXTURE_ORACLES)


def test_registry_validation_includes_network_browser_contracts() -> None:
    assert validate_registry().ok
