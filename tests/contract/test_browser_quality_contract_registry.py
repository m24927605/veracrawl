from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_browser_quality_contracts_are_registered() -> None:
    for name in [
        "BrowserQualityTargetSpec",
        "BrowserQualityObservation",
        "BrowserQualityDeltaRecord",
        "BrowserQualityReport",
        "BrowserQualityCorpusManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {"browser", "tests"}


def test_browser_quality_commands_and_events_are_registered() -> None:
    for command in [
        "record_browser_quality_observation",
        "record_browser_quality_delta",
        "record_browser_quality_report",
        "record_browser_quality_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_browser_quality_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["browser-quality-corpus"].negative_case is False
    for fixture_id in [
        "browser-quality-unsafe-action",
        "browser-quality-prompt-taint",
        "browser-quality-missing-artifact",
        "browser-quality-budget-exceeded",
        "browser-quality-replay-mismatch",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True


def test_browser_quality_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["browser_quality_benchmark"]
    assert "BrowserQualityReport" in area.materialized_contract_refs
    assert "BrowserInteractionStep" in area.materialized_contract_refs
