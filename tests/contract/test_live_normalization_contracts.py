from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, LiveNormalizationFailureType
from veracrawl.contracts.processing import (
    LiveNormalizationFixtureManifest,
    LiveNormalizationRuntimeReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> LiveNormalizationRuntimeReport:
    return LiveNormalizationRuntimeReport(
        id="live-normalization-runtime-report:test",
        fixture_id="live-normalization-listing-success",
        run_ref="run:test",
        live_http_acquisition_report_ref="live-http-acquisition-report:test",
        structured_source_adapters_runtime_report_ref=(
            "structured-source-adapters-runtime-report:test"
        ),
        browser_snapshot_runtime_report_ref="browser-snapshot-runtime-report:test",
        normalized_document_refs=["normalized:test"],
        normalization_manifest_refs=["normalization-manifest:test"],
        anchor_map_refs=["anchor-map:test"],
        source_anchor_refs=["text-anchor:test:1"],
        link_provenance_refs=["link-provenance:test:1"],
        link_analysis_refs=["link-analysis:test:discovered:1"],
        page_type_classification_refs=["page-type:test"],
        site_model_refs=["site-model:test"],
        raw_artifact_refs=["artifact:test:raw"],
        normalized_artifact_refs=["artifact:test:normalized"],
        artifact_refs=["artifact:test:raw", "artifact:test:normalized", "anchor-map:test"],
        policy_decision_refs=["policy:test:live-normalization"],
        command_record_refs=["durable-command:test:live-normalization"],
        event_cursor_refs=["event-cursor:test:live-normalization"],
        outbox_refs=["outbox:test:live-normalization"],
        replay_bundle_ref="replay-bundle:test:live-normalization",
        derived_context_refs=["page-type:test", "site-model:test"],
        operator_status="live_normalization_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_live_normalization_report_requires_upstream_anchors_and_replay() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        LiveNormalizationRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"browser_snapshot_runtime_report_ref": None}
        )
    with pytest.raises(ValidationError):
        LiveNormalizationRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"source_anchor_refs": []}
        )
    with pytest.raises(ValidationError):
        LiveNormalizationRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"link_analysis_refs": []}
        )


def test_linkless_live_normalization_pass_uses_link_analysis_without_fake_provenance() -> None:
    report = _passing_report().model_copy(
        update={
            "link_provenance_refs": [],
            "link_analysis_refs": ["link-analysis:test:no-outbound-links"],
        }
    )
    assert report.completion_result == CompletenessResult.PASS
    assert report.link_provenance_refs == []


def test_live_normalization_failure_requires_typed_diagnostics() -> None:
    failure = LiveNormalizationRuntimeReport(
        id="live-normalization-runtime-report:failure",
        fixture_id="live-normalization-replay-mismatch",
        run_ref="run:failure",
        policy_decision_refs=["policy:failure:live-normalization"],
        failure_report_refs=["failure:live-normalization-replay-mismatch"],
        missing_ref_fields=["replay_bundle_ref"],
        failure_type=LiveNormalizationFailureType.REPLAY_MISMATCH,
        operator_status=LiveNormalizationFailureType.REPLAY_MISMATCH.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == LiveNormalizationFailureType.REPLAY_MISMATCH
    with pytest.raises(ValidationError):
        LiveNormalizationRuntimeReport(
            id="live-normalization-runtime-report:bad",
            fixture_id="live-normalization-bad",
            run_ref="run:bad",
            operator_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_live_normalization_manifest_requires_target_and_failure_type() -> None:
    manifest = LiveNormalizationFixtureManifest(
        id="live-normalization-listing-success",
        scenario="live-normalization-listing-success",
        path="/static/basic",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="live_normalization_completed",
        required_ref_types=["normalized_document", "anchor_map", "site_model"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        LiveNormalizationFixtureManifest(
            id="live-normalization-missing-upstream",
            scenario="live-normalization-missing-upstream",
            path="/static/basic",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=LiveNormalizationFailureType.MISSING_UPSTREAM.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_live_normalization_registry_is_materialized() -> None:
    assert "LiveNormalizationRuntimeReport" in FOUNDATION_CONTRACTS
    assert "LiveNormalizationFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_live_normalization_runtime_report" in COMMAND_TYPES
    assert "record_live_normalization_fixture_manifest" in COMMAND_TYPES
    assert "live_normalization_runtime_reported" in EVENT_TYPES
    assert "live-normalization-listing-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["live_normalization_site_understanding"]
    assert area.coverage_status == "materialized"
    assert "LiveNormalizationRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
