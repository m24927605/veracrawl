from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.adapters.browser.deterministic import DeterministicBrowserObservationAdapter
from veracrawl.cli import browser_quality
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.browser_quality import BrowserQualityTargetSpec
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    BrowserQualityFailureType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkClientResult


class _FixtureHttpAdapter:
    def __init__(self, target: BrowserQualityTargetSpec) -> None:
        self.target = target
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        body = "<html><body><div id='app'>Loading quotes</div></body></html>"
        digest = stable_hash({"url": self.target.target_url, "body": body})
        artifact_ref = f"artifact:{command.command_envelope_id}:raw-html:{digest[:12]}"
        response = NetworkResponse(
            id=f"network-response:{command.command_envelope_id}",
            request_ref=f"network-request:{command.command_envelope_id}",
            status_code=200,
            final_url=self.target.target_url,
            headers_ref=f"headers:{command.command_envelope_id}:response",
            raw_artifact_ref=artifact_ref,
            content_digest=digest,
            content_type="text/html",
            body_size_bytes=len(body.encode("utf-8")),
            timing_ref=f"timing:{command.command_envelope_id}",
        )
        self._last_result = NetworkClientResult(
            response=response,
            redirect_hops=[],
            body_text=body,
            artifact_refs=[artifact_ref],
        )
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:browser-quality-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=["policy:browser-quality-fixture:http"],
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"idempotency:{command.command_envelope_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def _browser_adapter(
    adapter_kind: str,
    fixture_ref: str,
    target: BrowserQualityTargetSpec,
    sandbox: BrowserSandboxPolicy,
) -> BrowserSourceAdapterPort:
    del adapter_kind
    return DeterministicBrowserObservationAdapter(
        fixture_id=fixture_ref,
        target_url=target.target_url,
        sandbox_policy=sandbox,
        rendered_text=" ".join(target.browser_required_fragments),
    )


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("browser-quality-corpus", CompletenessResult.PASS, None),
        (
            "browser-quality-unsafe-action",
            CompletenessResult.FAIL,
            BrowserQualityFailureType.UNSAFE_ACTION,
        ),
        (
            "browser-quality-prompt-taint",
            CompletenessResult.FAIL,
            BrowserQualityFailureType.PROMPT_TAINT_BYPASS,
        ),
        (
            "browser-quality-missing-artifact",
            CompletenessResult.FAIL,
            BrowserQualityFailureType.MISSING_ARTIFACT,
        ),
        (
            "browser-quality-budget-exceeded",
            CompletenessResult.FAIL,
            BrowserQualityFailureType.BUDGET_EXCEEDED,
        ),
        (
            "browser-quality-replay-mismatch",
            CompletenessResult.FAIL,
            BrowserQualityFailureType.REPLAY_MISMATCH,
        ),
    ],
)
def test_browser_quality_fixture_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: BrowserQualityFailureType | None,
) -> None:
    monkeypatch.setattr(
        browser_quality,
        "_http_adapter_factory",
        lambda _fixture_ref, target: _FixtureHttpAdapter(target),
    )
    monkeypatch.setattr(browser_quality, "_browser_adapter_factory", _browser_adapter)

    result = browser_quality.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        browser_adapter="deterministic",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "browser_quality_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
