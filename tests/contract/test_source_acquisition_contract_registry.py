from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_source_acquisition_contracts_are_registered() -> None:
    report = validate_registry()
    assert report.ok, report.errors
    for contract in [
        "FetchAttempt",
        "FetchResult",
        "PageSnapshot",
        "DocumentArtifact",
        "RateLimitDecision",
        "SourceFailureReport",
        "SourceAcquisitionReport",
        "SourceFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[contract].test_refs


def test_source_commands_and_events_are_registered() -> None:
    for command_name in [
        "record_fetch_attempt",
        "record_fetch_result",
        "record_source_acquisition",
    ]:
        command = COMMAND_TYPES[command_name]
        assert command.payload_schema_ref in FOUNDATION_CONTRACTS
        for event_type in command.emitted_event_types:
            assert event_type in EVENT_TYPES


def test_source_fixtures_and_target_area_are_registered() -> None:
    for fixture_id in [
        "source-http-success",
        "source-sitemap-success",
        "source-rss-success",
        "source-api-success",
        "source-document-success",
        "source-blocked",
        "source-rate-limited",
        "source-adapter-mismatch",
        "source-malformed-response",
        "source-retry-exhausted",
        "source-missing-artifact",
    ]:
        assert FIXTURE_ORACLES[fixture_id].expected_replay_ref
    area = TARGET_CONTRACT_AREAS["source_acquisition"]
    assert area.coverage_status == "materialized"
    assert "SourceAcquisitionReport" in area.materialized_contract_refs
