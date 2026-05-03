from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_quality_metric_contracts_are_registered() -> None:
    for name in [
        "QualityMetricThresholds",
        "FieldConfusionRecord",
        "PrecisionRecallSliceMetric",
        "PrecisionRecallQualityReport",
        "QualityMetricManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {"verify", "tests"}


def test_quality_metric_commands_and_events_are_registered() -> None:
    for command in [
        "record_quality_metric_confusion",
        "record_quality_metric_report",
        "record_quality_metric_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_quality_metric_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["precision-recall-quality"].negative_case is False
    for fixture_id in [
        "precision-recall-low-precision",
        "precision-recall-low-recall",
        "precision-recall-low-f1",
        "precision-recall-hidden-false-positive",
        "precision-recall-llm-true-positive",
        "precision-recall-replay-missing",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_quality_metrics_ref


def test_quality_metric_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["precision_recall_quality_benchmark"]
    assert "PrecisionRecallQualityReport" in area.materialized_contract_refs
    assert "FieldConfusionRecord" in area.materialized_contract_refs
    assert "EvidencePacket" in area.materialized_contract_refs
