from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.browser import (
    BrowserSnapshotFixtureManifest,
    BrowserSnapshotRuntimeReport,
)
from veracrawl.contracts.enums import BrowserSnapshotFailureType, CompletenessResult
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> BrowserSnapshotRuntimeReport:
    return BrowserSnapshotRuntimeReport(
        id="browser-snapshot-runtime-report:test",
        fixture_id="browser-snapshot-success",
        run_ref="run:test",
        live_http_acquisition_report_ref="live-http-acquisition-report:test",
        structured_source_adapters_runtime_report_ref=(
            "structured-source-adapters-runtime-report:test"
        ),
        network_acquisition_report_ref="network-acquisition:test",
        source_acquisition_report_ref="source-acquisition:test",
        sandbox_policy_ref="browser-sandbox:test",
        browser_step_ref="browser-step:test:1",
        dom_artifact_refs=["artifact:test:dom"],
        screenshot_artifact_refs=["artifact:test:screenshot"],
        network_trace_refs=["artifact:test:network"],
        console_log_refs=["artifact:test:console"],
        timing_refs=["artifact:test:timing"],
        browser_budget_refs=["budget:test:browser-runtime"],
        prompt_taint_boundary_refs=["prompt-taint-boundary:test:rendered-content"],
        artifact_refs=[
            "artifact:test:dom",
            "artifact:test:screenshot",
            "artifact:test:network",
            "artifact:test:console",
            "artifact:test:timing",
        ],
        policy_decision_refs=["policy:test:browser-snapshot"],
        command_record_refs=["durable-command:test"],
        event_cursor_refs=["event-cursor:test"],
        outbox_refs=["outbox:test"],
        replay_bundle_ref="replay-bundle:test:browser-snapshot",
        operator_status="browser_snapshot_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_browser_snapshot_report_requires_all_browser_artifact_refs() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        BrowserSnapshotRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"console_log_refs": []}
        )


def test_browser_snapshot_failure_requires_typed_diagnostics() -> None:
    failure = BrowserSnapshotRuntimeReport(
        id="browser-snapshot-runtime-report:failure",
        fixture_id="browser-snapshot-replay-mismatch",
        run_ref="run:failure",
        failure_report_refs=["failure:browser-snapshot-replay-mismatch"],
        missing_ref_fields=["replay_bundle_ref"],
        failure_type=BrowserSnapshotFailureType.REPLAY_MISMATCH,
        operator_status=BrowserSnapshotFailureType.REPLAY_MISMATCH.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == BrowserSnapshotFailureType.REPLAY_MISMATCH
    with pytest.raises(ValidationError):
        BrowserSnapshotRuntimeReport(
            id="browser-snapshot-runtime-report:bad",
            fixture_id="browser-snapshot-bad",
            run_ref="run:bad",
            operator_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_browser_snapshot_manifest_requires_target_and_failure_type() -> None:
    manifest = BrowserSnapshotFixtureManifest(
        id="browser-snapshot-success",
        scenario="browser-snapshot-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="browser_snapshot_completed",
        required_ref_types=["dom", "screenshot", "network_trace", "console", "timing"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        BrowserSnapshotFixtureManifest(
            id="browser-snapshot-egress-denied",
            scenario="browser-snapshot-egress-denied",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=BrowserSnapshotFailureType.EGRESS_DENIED.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_browser_snapshot_registry_is_materialized() -> None:
    assert "BrowserSnapshotRuntimeReport" in FOUNDATION_CONTRACTS
    assert "BrowserSnapshotFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_browser_snapshot_runtime_report" in COMMAND_TYPES
    assert "record_browser_snapshot_fixture_manifest" in COMMAND_TYPES
    assert "browser_snapshot_runtime_reported" in EVENT_TYPES
    assert "browser-snapshot-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["browser_snapshot_runtime"]
    assert area.coverage_status == "materialized"
    assert "BrowserSnapshotRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
