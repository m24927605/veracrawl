from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.product_availability import (
    ProductAvailabilityAgentBinding,
    ProductAvailabilityModelBinding,
)
from veracrawl.benchmarks.product_discovery import (
    ProductDiscoveryBenchmarkResult,
    run_product_discovery_benchmark,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    ProductDiscoveryFailureType,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.product_availability import ProductAvailabilityTargetSpec
from veracrawl.contracts.product_discovery import (
    ProductDiscoveryBenchmarkManifest,
    ProductDiscoverySourceSpec,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class _FakeModelProvider:
    provider_name = "Local model runtime"
    model_id = "veracrawl-local-deterministic"
    model_version = "1"

    def complete(self, request):
        from veracrawl.contracts.agent import ModelResponse

        return ModelResponse(
            id=f"model-response:{request.id}",
            model_request_id=request.id,
            response_ref=f"model-response-payload:{request.id}",
            parsed_output_ref=f"model-parsed-output:{request.id}",
            tool_request_refs=[],
            safety_filter_result_ref=f"safety-filter:{request.id}:pass",
            status="completed",
        )


class _FakeAgentRuntime:
    framework_name = "VeraCrawl Native Runtime"

    def run(self, request):
        from veracrawl.contracts.agent import AgentRunResult
        from veracrawl.contracts.enums import AgentRunStatus

        return AgentRunResult(
            id=f"agent-run-result:{request.run_id}:{request.agent_role.value}",
            agent_run_request_id=request.id,
            agent_action_trace_id=(
                f"agent-action-trace:{request.run_id}:{request.agent_role.value}"
            ),
            output_ref=f"agent-output:{request.run_id}:{request.agent_role.value}",
            proposed_tool_call_refs=[],
            recommendation_refs=[],
            status=AgentRunStatus.COMPLETED,
        )


class _FakeDiscoveryAdapter:
    def __init__(self, source: ProductDiscoverySourceSpec, body: str) -> None:
        self.source = source
        self.body = body
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        self._last_result = _network_result(command, self.source.search_url, self.body)
        return _source_result(command, self._last_result.artifact_refs[0])


class _FakeProductAdapter:
    def __init__(self, target: ProductAvailabilityTargetSpec) -> None:
        self.target = target
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        body = _product_body(self.target.target_url)
        self._last_result = _network_result(command, self.target.target_url, body)
        return _source_result(command, self._last_result.artifact_refs[0])


def _network_result(
    command: SourceAdapterCommand,
    final_url: str,
    body: str,
) -> NetworkClientResult:
    digest = stable_hash({"url": final_url, "body": body})
    artifact_ref = f"artifact:{command.command_envelope_id}:{digest[:12]}"
    response = NetworkResponse(
        id=f"network-response:{command.command_envelope_id}",
        request_ref=f"network-request:{command.command_envelope_id}",
        status_code=200,
        final_url=final_url,
        headers_ref=f"headers:{command.command_envelope_id}:response",
        raw_artifact_ref=artifact_ref,
        content_digest=digest,
        content_type="text/html",
        body_size_bytes=len(body.encode("utf-8")),
        timing_ref=f"timing:{command.command_envelope_id}",
    )
    return NetworkClientResult(
        response=response,
        redirect_hops=[],
        body_text=body,
        artifact_refs=[artifact_ref],
    )


def _source_result(command: SourceAdapterCommand, artifact_ref: str) -> SourceAdapterResult:
    return SourceAdapterResult(
        id=f"source-result:{command.command_envelope_id}",
        run_id="run:fixture",
        adapter_spec_id=command.adapter_spec.id,
        adapter_type=AdapterType.HTTP,
        result_type=SourceAdapterResultType.FETCH_RESULT,
        output_refs=[artifact_ref],
        policy_decision_refs=["policy:fixture"],
        replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
        idempotency_key=f"idempotency:{command.command_envelope_id}",
        status=AdapterResultStatus.SUCCEEDED,
    )


def _manifest(
    scenario: str = "query-product-discovery-success",
) -> ProductDiscoveryBenchmarkManifest:
    return ProductDiscoveryBenchmarkManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["target"],
        product_name="Apple iPhone 17 256G",
        brand="Apple",
        query="iphone 17 256G",
        required_identity_terms=["iPhone", "17", "256G"],
        rejected_identity_terms=["17e", "Pro", "Pro Max"],
        source_specs=[
            ProductDiscoverySourceSpec(
                id="example-search",
                site_name="Example Shop",
                search_url="https://example.com/search?q=iphone%2017%20256G",
                robots_url="https://example.com/robots.txt",
                allowed_origin="https://example.com",
                query="iphone 17 256G",
                required_identity_terms=["iPhone", "17", "256G"],
                rejected_identity_terms=["17e", "Pro", "Pro Max"],
                candidate_url_patterns=[r"/prod/[A-Za-z0-9-]+"],
                exclude_url_patterns=[r"/cart", r"/compare"],
            )
        ],
        provider_names=["Local model runtime"],
        framework_names=["VeraCrawl Native Runtime"],
        expected_completion_result=(
            CompletenessResult.FAIL
            if scenario == "query-product-discovery-no-candidates"
            else CompletenessResult.PASS
        ),
        expected_operator_status=(
            ProductDiscoveryFailureType.NO_CANDIDATES.value
            if scenario == "query-product-discovery-no-candidates"
            else "product_discovery_ranked_offers_completed"
        ),
        expected_failure_type=(
            ProductDiscoveryFailureType.NO_CANDIDATES
            if scenario == "query-product-discovery-no-candidates"
            else None
        ),
        negative_case=scenario == "query-product-discovery-no-candidates",
        required_ref_types=[
            "query_discovery",
            "model_call_trace",
            "agent_action_trace",
            "tool_call_trace",
            "context_bundle_trace",
            "source_anchor",
            "product_availability",
            "offer_projection",
            "command_event_outbox",
            "replay",
        ],
    )


def _model_binding() -> ProductAvailabilityModelBinding:
    return ProductAvailabilityModelBinding(
        provider_name="Local model runtime",
        model_id="veracrawl-local-deterministic",
        model_version="1",
        runtime_ref="model-runtime:local",
        port=_FakeModelProvider(),
    )


def _agent_binding() -> ProductAvailabilityAgentBinding:
    return ProductAvailabilityAgentBinding(
        framework_name="VeraCrawl Native Runtime",
        runtime_spec_id="agent-runtime-spec:local",
        runtime_ref="agent-runtime:local",
        port=_FakeAgentRuntime(),
    )


def _run(
    tmp_path: Path,
    search_body: str,
    scenario: str = "query-product-discovery-success",
) -> ProductDiscoveryBenchmarkResult:
    manifest = _manifest(scenario)
    return run_product_discovery_benchmark(
        manifest=manifest,
        profile="target",
        store=ReferencePersistenceStore(tmp_path / "state"),
        discovery_adapter_factory=lambda _fixture, source: _FakeDiscoveryAdapter(
            source,
            search_body,
        ),
        product_adapter_factory=lambda _fixture, target: _FakeProductAdapter(target),
        discovery_robots_fetcher=lambda _source: RobotsFetchResult(status_code=200, body_text=""),
        product_robots_fetcher=lambda _target: RobotsFetchResult(status_code=200, body_text=""),
        model_binding=_model_binding(),
        agent_binding=_agent_binding(),
    )


def _search_body() -> str:
    return """
    <html><body>
      <a href="/prod/iphone-17-256g">Apple iPhone 17 256G</a>
      <a href="/prod/iphone-17-pro-256g">Apple iPhone 17 Pro 256G</a>
      <a href="/compare">compare</a>
      <script>window.products=["/prod/iphone-17-256g-black"];</script>
    </body></html>
    """


def _product_body(url: str) -> str:
    if "iphone-17-pro" in url:
        return """
        <html><head><title>Apple iPhone 17 Pro 256G</title></head>
        <body>Apple iPhone 17 Pro 256G NT$33900 加入購物車</body></html>
        """
    return """
    <html><head><title>Apple iPhone 17 256G</title>
    <meta name="product:price:amount" content="27980">
    <meta name="product:price:currency" content="TWD">
    <meta name="product:availability" content="in stock">
    </head><body>Apple iPhone 17 256G 24小時到貨 免運 加入購物車</body></html>
    """


def test_product_discovery_discovers_candidates_and_ranks_offers(tmp_path: Path) -> None:
    result = _run(tmp_path, _search_body())

    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.candidates) == 2
    assert all("/prod/" in candidate.candidate_url for candidate in result.candidates)
    assert not any("iphone-17-pro" in candidate.candidate_url for candidate in result.candidates)
    assert result.derived_product_availability_manifest is not None
    assert len(result.derived_product_availability_manifest.target_specs) == 2
    assert result.ranked_offers
    assert result.ranked_offers[0].price_amount == 27980
    assert len(result.model_call_traces) == 1 + 4 * len(result.candidates)
    assert result.report.ranked_offer_refs == [offer.id for offer in result.ranked_offers]


def test_product_discovery_no_candidates_fails_with_typed_diagnostics(
    tmp_path: Path,
) -> None:
    result = _run(
        tmp_path,
        "<html><body><a href=\"/category\">Category</a></body></html>",
        scenario="query-product-discovery-no-candidates",
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == ProductDiscoveryFailureType.NO_CANDIDATES
    assert result.report.missing_ref_fields == ["discovered_candidate_refs"]
