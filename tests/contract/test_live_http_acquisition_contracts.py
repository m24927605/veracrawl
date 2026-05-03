from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, LiveHttpAcquisitionFailureType
from veracrawl.contracts.network import (
    LiveHttpAcquisitionFixtureManifest,
    LiveHttpAcquisitionReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> LiveHttpAcquisitionReport:
    return LiveHttpAcquisitionReport(
        id="live-http-acquisition-report:test",
        fixture_id="live-http-success",
        run_ref="run:test",
        run_control_report_ref="production-run-control-report:test",
        production_persistence_report_ref="production-persistence-runtime-report:test",
        network_request_ref="network-request:test",
        network_response_ref="network-response:test",
        source_acquisition_report_ref="source-acquisition:test",
        source_adapter_result_refs=["source-result:test"],
        fetch_attempt_refs=["fetch-attempt:test:1"],
        fetch_result_refs=["fetch-result:test"],
        page_snapshot_refs=["page-snapshot:test"],
        source_observation_refs=["target-source-observation:test:http"],
        artifact_refs=["artifact:test:raw"],
        content_hash_refs=["hash:test"],
        canonical_url_refs=["canonical-url:test"],
        policy_decision_refs=["policy:test"],
        command_record_refs=["durable-command:test"],
        event_cursor_refs=["event-cursor:test"],
        outbox_refs=["outbox:test"],
        replay_bundle_ref="replay-bundle:test",
        operator_status="live_http_acquisition_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_live_http_report_requires_production_and_source_refs() -> None:
    assert _passing_report().completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        LiveHttpAcquisitionReport.model_validate(
            _passing_report().model_dump(mode="json") | {"source_observation_refs": []}
        )


def test_live_http_failure_requires_typed_diagnostics() -> None:
    failure = LiveHttpAcquisitionReport(
        id="live-http-acquisition-report:failure",
        fixture_id="live-http-replay-mismatch",
        run_ref="run:test",
        failure_report_refs=["failure:replay"],
        missing_ref_fields=["replay_bundle_ref"],
        failure_type=LiveHttpAcquisitionFailureType.REPLAY_MISMATCH,
        operator_status=LiveHttpAcquisitionFailureType.REPLAY_MISMATCH.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == LiveHttpAcquisitionFailureType.REPLAY_MISMATCH

    with pytest.raises(ValidationError):
        LiveHttpAcquisitionReport(
            id="live-http-acquisition-report:bad-failure",
            fixture_id="live-http-replay-mismatch",
            run_ref="run:test",
            operator_status=LiveHttpAcquisitionFailureType.REPLAY_MISMATCH.value,
            completion_result=CompletenessResult.FAIL,
        )


def test_live_http_manifest_requires_target_and_failure_type() -> None:
    manifest = LiveHttpAcquisitionFixtureManifest(
        id="live-http-success",
        scenario="success",
        path="/static/basic",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="live_http_acquisition_completed",
        required_ref_types=["run_control", "network_response", "source_observation"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        LiveHttpAcquisitionFixtureManifest(
            id="live-http-private-denied",
            scenario="private-denied",
            path="/private",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=LiveHttpAcquisitionFailureType.PRIVATE_NETWORK_DENIED.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_live_http_registry_is_materialized() -> None:
    assert "LiveHttpAcquisitionReport" in FOUNDATION_CONTRACTS
    assert "LiveHttpAcquisitionFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_live_http_acquisition_report" in COMMAND_TYPES
    assert "live_http_acquisition_reported" in EVENT_TYPES
    assert "live-http-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["live_http_acquisition_runtime"]
    assert area.coverage_status == "materialized"
    assert "LiveHttpAcquisitionReport" in area.materialized_contract_refs
    assert validate_registry().ok
