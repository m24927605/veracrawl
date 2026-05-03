from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_website_pattern_coverage_contracts_are_registered() -> None:
    expected = {
        "WebsitePatternCoverageRecord",
        "WebsitePatternCoverageReport",
        "WebsitePatternCoverageFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    for contract in expected:
        assert FOUNDATION_CONTRACTS[contract].test_refs


def test_website_pattern_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_website_pattern_coverage": "website_pattern_coverage_recorded",
        "record_website_pattern_coverage_report": "website_pattern_coverage_reported",
        "record_website_pattern_coverage_fixture_manifest": (
            "website_pattern_coverage_fixture_manifest_recorded"
        ),
    }
    for command, event in expected_commands.items():
        assert command in COMMAND_TYPES
        assert event in COMMAND_TYPES[command].emitted_event_types
        assert event in EVENT_TYPES

    expected_fixtures = {
        "website-pattern-coverage-success",
        "website-pattern-runtime-unavailable",
        "website-pattern-missing-pattern",
        "website-pattern-unsupported-pattern",
        "website-pattern-single-site-assumption",
        "website-pattern-scaffold-only",
        "website-pattern-missing-source-adapter",
        "website-pattern-missing-site-model",
        "website-pattern-missing-output-evidence",
        "website-pattern-missing-pattern-specific-refs",
        "website-pattern-unsafe-interaction",
        "website-pattern-missing-replay",
    }
    assert expected_fixtures.issubset(FIXTURE_ORACLES)


def test_website_pattern_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["website_pattern_coverage_gate"]
    assert area.coverage_status == "materialized"
    assert "WebsitePatternCoverageRecord" in area.materialized_contract_refs
    assert "WebsitePatternCoverageReport" in area.materialized_contract_refs
    assert "WebsitePatternCoverageFixtureManifest" in area.materialized_contract_refs
    assert "BenchmarkFixtureManifest" in area.materialized_contract_refs
