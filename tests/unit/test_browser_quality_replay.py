from __future__ import annotations

from veracrawl.contracts.browser_quality import BrowserQualityObservation
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.review_replay.browser_quality import (
    browser_quality_observation_replay_passes,
    missing_browser_quality_observation_replay_refs,
)


def _observation() -> BrowserQualityObservation:
    return BrowserQualityObservation(
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


def test_browser_quality_observation_replay_passes_with_required_refs() -> None:
    assert browser_quality_observation_replay_passes(_observation())


def test_browser_quality_observation_replay_reports_missing_refs() -> None:
    observation = _observation().model_copy(update={"replay_bundle_ref": None})

    assert browser_quality_observation_replay_passes(observation) is False
    assert missing_browser_quality_observation_replay_refs(observation) == [
        "replay_bundle_ref"
    ]
