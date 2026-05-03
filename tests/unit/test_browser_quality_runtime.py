from __future__ import annotations

from pathlib import Path

from veracrawl.adapters.browser.deterministic import DeterministicBrowserObservationAdapter
from veracrawl.benchmarks.browser_quality import run_browser_quality_corpus
from veracrawl.contracts.browser_quality import (
    BrowserQualityCorpusManifest,
    BrowserQualityTargetSpec,
)
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
from veracrawl.ports.network import NetworkClientResult
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class _HttpOnlyMissingAdapter:
    def __init__(self, target: BrowserQualityTargetSpec, *, body: str = "HTTP shell") -> None:
        self.target = target
        self.body = body
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        digest = stable_hash({"url": self.target.target_url, "body": self.body})
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
            body_size_bytes=len(self.body.encode("utf-8")),
            timing_ref=f"timing:{command.command_envelope_id}",
        )
        self._last_result = NetworkClientResult(
            response=response,
            redirect_hops=[],
            body_text=self.body,
            artifact_refs=[artifact_ref],
        )
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:browser-quality",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=["policy:browser-quality:http"],
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"idempotency:{command.command_envelope_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def _target(index: int, fragment: str = "Rendered Ready") -> BrowserQualityTargetSpec:
    return BrowserQualityTargetSpec(
        id=f"target:{index}",
        target_url=f"https://example.com/scroll?target={index}",
        allowed_origin="https://example.com",
        http_absent_fragments=[fragment],
        browser_required_fragments=[fragment],
        pattern_refs=["pattern:javascript-rendered"],
        sandbox_policy_ref=f"browser-sandbox:target:{index}",
        browser_budget_ref=f"budget:target:{index}:browser",
    )


def _manifest(targets: list[BrowserQualityTargetSpec]) -> BrowserQualityCorpusManifest:
    return BrowserQualityCorpusManifest(
        id="browser-quality-corpus",
        scenario="browser-quality-corpus",
        profile_refs=["quality"],
        target_specs=targets,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="browser_quality_completed",
        required_ref_types=["dom", "screenshot", "replay"],
    )


def test_browser_quality_runtime_passes_with_browser_recovered_evidence(
    tmp_path: Path,
) -> None:
    targets = [_target(index, f"Rendered {index}") for index in range(1, 9)]
    result = run_browser_quality_corpus(
        manifest=_manifest(targets),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
        http_adapter_factory=lambda _fixture, target: _HttpOnlyMissingAdapter(target),
        browser_adapter_factory=lambda fixture, target, sandbox: (
            DeterministicBrowserObservationAdapter(
                fixture_id=fixture,
                target_url=target.target_url,
                sandbox_policy=sandbox,
                rendered_text=" ".join(target.browser_required_fragments),
            )
        ),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.browser_required_pass_count == 8
    assert result.report.recovered_fragment_count == 8
    assert all(item.replay_bundle_ref for item in result.observations)


def test_browser_quality_runtime_fails_when_http_already_contains_oracle(
    tmp_path: Path,
) -> None:
    targets = [_target(index, "Rendered Ready") for index in range(1, 9)]
    result = run_browser_quality_corpus(
        manifest=_manifest(targets),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
        http_adapter_factory=lambda _fixture, target: _HttpOnlyMissingAdapter(
            target,
            body="Rendered Ready",
        ),
        browser_adapter_factory=lambda fixture, target, sandbox: (
            DeterministicBrowserObservationAdapter(
                fixture_id=fixture,
                target_url=target.target_url,
                sandbox_policy=sandbox,
                rendered_text="Rendered Ready",
            )
        ),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == BrowserQualityFailureType.HTTP_ORACLE_NOT_MISSING


def test_browser_quality_runtime_maps_direct_unsafe_action_failure(tmp_path: Path) -> None:
    targets = [_target(index, f"Rendered {index}") for index in range(1, 9)]
    manifest = _manifest(targets).model_copy(
        update={
            "scenario": "browser-quality-unsafe-action",
            "expected_completion_result": CompletenessResult.FAIL,
            "expected_operator_status": "browser_quality_unsafe_action",
            "expected_failure_type": BrowserQualityFailureType.UNSAFE_ACTION,
            "negative_case": True,
        }
    )
    result = run_browser_quality_corpus(
        manifest=manifest,
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
        http_adapter_factory=lambda _fixture, target: _HttpOnlyMissingAdapter(target),
        browser_adapter_factory=lambda fixture, target, sandbox: (
            DeterministicBrowserObservationAdapter(
                fixture_id=fixture,
                target_url=target.target_url,
                sandbox_policy=sandbox,
                rendered_text=" ".join(target.browser_required_fragments),
            )
        ),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == BrowserQualityFailureType.UNSAFE_ACTION
