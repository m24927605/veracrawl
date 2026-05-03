from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_deep_crawl_contracts_are_registered() -> None:
    for name in [
        "DeepCrawlPageSpec",
        "DeepCrawlSiteSpec",
        "FrontierDecisionTrace",
        "DeepCrawlPageObservation",
        "DeepCrawlStopReasonRecord",
        "DeepCrawlQualityReport",
        "DeepCrawlQualityManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {"fetch", "tests"}


def test_deep_crawl_commands_and_events_are_registered() -> None:
    for command in [
        "record_deep_crawl_frontier_decision",
        "record_deep_crawl_page_observation",
        "record_deep_crawl_stop_reason",
        "record_deep_crawl_report",
        "record_deep_crawl_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_deep_crawl_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["deep-crawl-quality-corpus"].negative_case is False
    for fixture_id in [
        "deep-crawl-duplicate-loop",
        "deep-crawl-off-origin-pollution",
        "deep-crawl-robots-denied",
        "deep-crawl-budget-exhausted",
        "deep-crawl-infinite-pagination",
        "deep-crawl-replay-mismatch",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_deep_crawl_ref


def test_deep_crawl_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["deep_crawl_frontier_benchmark"]
    assert "DeepCrawlQualityReport" in area.materialized_contract_refs
    assert "FrontierDecisionTrace" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
