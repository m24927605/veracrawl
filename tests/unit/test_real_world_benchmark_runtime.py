from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.real_world import (
    RobotsFetchResult,
    run_real_world_benchmark_corpus,
)
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    RealWorldBenchmarkFailureType,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkCorpusManifest,
    RealWorldBenchmarkSiteSpec,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class _FakeHttpAdapter:
    def __init__(
        self,
        *,
        body: str,
        final_url: str,
        content_type: str = "text/html",
    ) -> None:
        self.body = body
        self.final_url = final_url
        self.content_type = content_type
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        digest = stable_hash({"body": self.body, "source": command.source_ref})
        artifact_ref = f"artifact:{command.command_envelope_id}:{digest[:12]}"
        response = NetworkResponse(
            id=f"network-response:{command.command_envelope_id}",
            request_ref=f"network-request:{command.command_envelope_id}",
            status_code=200,
            final_url=self.final_url,
            headers_ref=f"headers:{command.command_envelope_id}:response",
            raw_artifact_ref=artifact_ref,
            content_digest=digest,
            content_type=self.content_type,
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
            run_id="run:fake",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=["policy:fake"],
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"idempotency:{command.command_envelope_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def _site(**overrides: object) -> RealWorldBenchmarkSiteSpec:
    data: dict[str, object] = {
        "id": "example-static",
        "target_url": "https://example.com/",
        "robots_url": "https://example.com/robots.txt",
        "allowed_origin": "https://example.com",
        "expected_status_code": 200,
        "expected_content_type": "text/html",
        "min_body_size_bytes": 20,
        "required_title_fragments": ["Example Domain"],
        "required_body_fragments": ["documentation examples"],
        "allowed_robots_status_codes": [404],
        "pattern_refs": ["pattern:static"],
    }
    data.update(overrides)
    return RealWorldBenchmarkSiteSpec(**data)


def _manifest(site: RealWorldBenchmarkSiteSpec) -> RealWorldBenchmarkCorpusManifest:
    return RealWorldBenchmarkCorpusManifest(
        id="real-world-public-corpus",
        scenario="success",
        profile_refs=["target"],
        site_specs=[site],
        allowed_origin_refs=[site.allowed_origin],
        rate_budget_ref="budget:real-world",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="real_world_benchmark_completed",
        required_ref_types=["artifact_refs", "replay_bundle_refs"],
    )


def test_real_world_benchmark_passes_with_fake_live_http(tmp_path: Path) -> None:
    body = (
        "<html><head><title>Example Domain</title></head>"
        "<body>documentation examples</body></html>"
    )
    result = run_real_world_benchmark_corpus(
        manifest=_manifest(_site()),
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
        adapter_factory=lambda _fixture_id, site: _FakeHttpAdapter(
            body=body,
            final_url=site.target_url,
        ),
        robots_fetcher=lambda _site_spec: RobotsFetchResult(status_code=404, body_text=""),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.artifact_refs
    assert result.report.replay_bundle_refs
    assert result.observations[0].matched_observation_refs


def test_real_world_benchmark_fails_on_observation_mismatch(tmp_path: Path) -> None:
    result = run_real_world_benchmark_corpus(
        manifest=_manifest(_site()),
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
        adapter_factory=lambda _fixture_id, _site_spec: _FakeHttpAdapter(
            body="<html><head><title>Other</title></head><body>missing</body></html>",
            final_url=_site_spec.target_url,
        ),
        robots_fetcher=lambda _site_spec: RobotsFetchResult(status_code=404, body_text=""),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH


def test_real_world_benchmark_fails_before_fetch_when_robots_denies(tmp_path: Path) -> None:
    result = run_real_world_benchmark_corpus(
        manifest=_manifest(_site(allowed_robots_status_codes=[200])),
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
        adapter_factory=lambda _fixture_id, site: _FakeHttpAdapter(
            body="unused",
            final_url=site.target_url,
        ),
        robots_fetcher=lambda _site_spec: RobotsFetchResult(
            status_code=200,
            body_text="User-agent: *\nDisallow: /\n",
        ),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == RealWorldBenchmarkFailureType.ROBOTS_DENIED
    assert not result.live_http_results


def test_real_world_benchmark_reports_robots_network_unavailable(tmp_path: Path) -> None:
    def _raise(_site_spec: RealWorldBenchmarkSiteSpec) -> RobotsFetchResult:
        raise OSError("dns unavailable")

    result = run_real_world_benchmark_corpus(
        manifest=_manifest(_site()),
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
        adapter_factory=lambda _fixture_id, site: _FakeHttpAdapter(
            body="unused",
            final_url=site.target_url,
        ),
        robots_fetcher=_raise,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == RealWorldBenchmarkFailureType.NETWORK_UNAVAILABLE
