from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.browser import BrowserInteractionStep, BrowserSandboxPolicy
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    BrowserStepStatus,
    CompletenessResult,
)
from veracrawl.contracts.network import (
    NetworkAcquisitionReport,
    NetworkRequest,
    NetworkResponse,
    RedirectHop,
)


def test_network_request_requires_absolute_http_url() -> None:
    with pytest.raises(ValidationError):
        NetworkRequest(
            id="request:bad",
            run_ref="run:1",
            source_ref="source:1",
            url="/relative",
            headers_ref="headers:request",
            policy_decision_refs=["policy:network"],
            egress_policy_ref="policy:egress",
            private_network_policy_ref="policy:private",
            robots_policy_ref="policy:robots",
            rate_budget_ref="budget:rate",
            size_budget_bytes=1,
            timeout_ms=1,
            idempotency_key="bad",
        )


def test_network_response_and_report_accept_success_refs() -> None:
    request = NetworkRequest(
        id="request:ok",
        run_ref="run:1",
        source_ref="source:1",
        url="http://127.0.0.1:1/static",
        headers_ref="headers:request",
        policy_decision_refs=["policy:network"],
        egress_policy_ref="policy:egress",
        private_network_policy_ref="policy:private",
        robots_policy_ref="policy:robots",
        rate_budget_ref="budget:rate",
        size_budget_bytes=100,
        timeout_ms=100,
        idempotency_key="ok",
    )
    response = NetworkResponse(
        id="response:ok",
        request_ref=request.id,
        status_code=200,
        final_url=request.url,
        headers_ref="headers:response",
        raw_artifact_ref="artifact:raw",
        content_digest="digest",
        content_type="text/html",
        body_size_bytes=10,
        timing_ref="timing:response",
    )
    report = NetworkAcquisitionReport(
        id="network-report:ok",
        run_ref="run:1",
        network_request_ref=request.id,
        network_response_ref=response.id,
        source_acquisition_report_ref="source-report:ok",
        artifact_refs=["artifact:raw"],
        policy_decision_refs=["policy:network"],
        command_record_refs=["command:1"],
        event_cursor_refs=["cursor:1"],
        outbox_refs=["outbox:1"],
        recovery_report_refs=["recovery:1"],
        operator_status="network_acquired",
        completion_result=CompletenessResult.PASS,
    )
    assert report.network_response_ref == response.id


def test_redirect_hop_requires_policy_refs() -> None:
    with pytest.raises(ValidationError):
        RedirectHop(
            id="redirect:1",
            request_ref="request:1",
            sequence=1,
            from_url="http://a.test",
            to_url="http://b.test",
            status_code=302,
        )


def test_browser_step_blocks_unsafe_execution() -> None:
    policy = BrowserSandboxPolicy(
        id="sandbox:1",
        allowed_origin_refs=["origin:http://127.0.0.1:1"],
        egress_allowlist=["http://127.0.0.1:1"],
        private_network_denylist=["private"],
        max_runtime_ms=100,
        max_dom_bytes=100,
        max_screenshot_bytes=100,
        max_network_log_bytes=100,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
    )
    assert policy.capture_dom
    with pytest.raises(ValidationError):
        BrowserInteractionStep(
            id="browser-step:bad",
            run_ref="run:1",
            source_ref="source:1",
            target_url="http://127.0.0.1:1/browser",
            step_number=1,
            action_type="click",
            side_effect_class=BrowserSideEffectClass.DELETE,
            sandbox_policy_ref=policy.id,
            policy_decision_refs=["policy:browser"],
            dom_artifact_ref="artifact:dom",
            screenshot_artifact_ref="artifact:screen",
            network_log_ref="artifact:net",
            status=BrowserStepStatus.EXECUTED,
        )
