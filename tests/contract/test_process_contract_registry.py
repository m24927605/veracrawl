from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_process_contracts_registered() -> None:
    for contract in [
        "NormalizationManifest",
        "TextAnchor",
        "AnchorMap",
        "LinkProvenance",
        "PageTypeClassification",
        "SiteModel",
        "ExtractionStrategy",
        "NormalizeExtractReport",
        "ProcessFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_process_commands_events_fixtures_registered() -> None:
    assert {
        "record_normalization_manifest",
        "record_link_provenance",
        "record_extraction_strategy",
        "record_process_report",
    }.issubset(COMMAND_TYPES)
    assert {
        "normalization_manifest_recorded",
        "link_provenance_recorded",
        "extraction_strategy_recorded",
        "process_report_recorded",
    }.issubset(EVENT_TYPES)
    assert "normalize_extract" in TARGET_CONTRACT_AREAS
    assert {
        "process-static-basic",
        "process-link-provenance",
        "process-anchored-candidate",
        "process-missing-raw",
        "process-empty-content",
        "process-anchor-gap",
    }.issubset(FIXTURE_ORACLES)


def test_process_registry_validation_passes() -> None:
    assert validate_registry().ok
