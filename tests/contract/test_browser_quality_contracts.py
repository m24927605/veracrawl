from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.browser_quality import (
    BrowserQualityCorpusManifest,
    BrowserQualityDeltaRecord,
    BrowserQualityObservation,
    BrowserQualityReport,
    BrowserQualityTargetSpec,
)
from veracrawl.contracts.enums import (
    BrowserQualityFailureType,
    CompletenessResult,
)


def _target() -> BrowserQualityTargetSpec:
    return BrowserQualityTargetSpec(
        id="target:js",
        target_url="https://example.com/scroll",
        allowed_origin="https://example.com",
        http_absent_fragments=["Rendered"],
        browser_required_fragments=["Rendered"],
        pattern_refs=["pattern:javascript-rendered"],
        sandbox_policy_ref="browser-sandbox:target",
        browser_budget_ref="budget:target:browser",
    )


def test_browser_quality_target_requires_browser_oracles() -> None:
    with pytest.raises(ValidationError):
        BrowserQualityTargetSpec(
            id="target:bad",
            target_url="https://example.com",
            allowed_origin="https://example.com",
            http_absent_fragments=[],
            browser_required_fragments=["Rendered"],
            pattern_refs=["pattern:javascript-rendered"],
            sandbox_policy_ref="browser-sandbox:target",
            browser_budget_ref="budget:target:browser",
        )


def test_browser_quality_manifest_requires_quality_profile() -> None:
    manifest = BrowserQualityCorpusManifest(
        id="browser-quality-corpus",
        scenario="browser-quality-corpus",
        profile_refs=["quality"],
        target_specs=[_target()] * 8,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="browser_quality_completed",
        required_ref_types=["dom", "screenshot", "replay"],
    )

    assert manifest.minimum_browser_required_count == 8


def test_passing_delta_requires_recovered_refs() -> None:
    with pytest.raises(ValidationError):
        BrowserQualityDeltaRecord(
            id="delta:bad",
            target_spec_ref="target:js",
            completion_result=CompletenessResult.PASS,
        )


def test_passing_observation_requires_browser_lineage_refs() -> None:
    observation = BrowserQualityObservation(
        id="browser-quality-observation:ok",
        target_spec_ref="target:js",
        target_url="https://example.com/scroll",
        live_http_acquisition_report_ref="live-http:target",
        network_response_ref="network-response:target",
        http_artifact_refs=["artifact:http"],
        http_content_hash_refs=["hash:http"],
        browser_step_ref="browser-step:target",
        dom_artifact_refs=["artifact:dom"],
        screenshot_artifact_refs=["artifact:screenshot"],
        network_trace_refs=["artifact:network"],
        console_log_refs=["artifact:console"],
        timing_refs=["artifact:timing"],
        rendered_content_hash_refs=["hash:dom"],
        browser_artifact_refs=["artifact:dom", "artifact:screenshot"],
        http_missing_fragment_refs=["fragment:http-missing"],
        recovered_fragment_refs=["fragment:browser-recovered"],
        source_anchor_refs=["source-anchor:fragment"],
        delta_record_ref="delta:target",
        sandbox_policy_ref="browser-sandbox:target",
        browser_budget_ref="budget:target",
        prompt_taint_boundary_refs=["prompt-taint-boundary:target"],
        policy_decision_refs=["policy:target"],
        command_record_refs=["command:target"],
        event_cursor_refs=["cursor:target"],
        outbox_refs=["outbox:target"],
        replay_bundle_ref="replay:target",
        browser_wall_time_ms=10,
        browser_network_request_count=1,
        browser_cost_units=1,
        completion_result=CompletenessResult.PASS,
    )

    assert observation.completion_result == CompletenessResult.PASS


def test_failed_observation_requires_typed_diagnostics() -> None:
    observation = BrowserQualityObservation(
        id="browser-quality-observation:fail",
        target_spec_ref="target:js",
        target_url="https://example.com/scroll",
        failure_report_refs=["failure:target"],
        missing_ref_fields=["dom_artifact_refs"],
        failure_type=BrowserQualityFailureType.MISSING_ARTIFACT,
        diagnostics=["missing DOM"],
        completion_result=CompletenessResult.FAIL,
    )

    assert observation.failure_type == BrowserQualityFailureType.MISSING_ARTIFACT


def test_passing_report_requires_replay_and_artifacts() -> None:
    report = BrowserQualityReport(
        id="browser-quality-report:ok",
        fixture_id="browser-quality-corpus",
        run_ref="run:browser-quality-corpus",
        observation_refs=["observation:1"],
        delta_record_refs=["delta:1"],
        target_count=8,
        browser_required_pass_count=8,
        recovered_fragment_count=8,
        http_only_missing_count=8,
        dom_artifact_refs=["artifact:dom"],
        screenshot_artifact_refs=["artifact:screenshot"],
        network_trace_refs=["artifact:network"],
        console_log_refs=["artifact:console"],
        timing_refs=["artifact:timing"],
        content_hash_refs=["hash:dom"],
        source_anchor_refs=["source-anchor:fragment"],
        browser_budget_refs=["budget:browser"],
        prompt_taint_boundary_refs=["prompt-taint-boundary:rendered"],
        policy_decision_refs=["policy:browser"],
        command_record_refs=["command:browser"],
        event_cursor_refs=["cursor:browser"],
        outbox_refs=["outbox:browser"],
        replay_bundle_refs=["replay:browser"],
        operator_status="browser_quality_completed",
        completion_result=CompletenessResult.PASS,
    )

    assert report.browser_required_pass_count == 8
