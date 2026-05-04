from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.product_availability import (
    ProductAvailabilityAgentBinding,
    ProductAvailabilityBenchmarkResult,
    ProductAvailabilityModelBinding,
    run_product_availability_benchmark,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    ProductAvailabilityFailureType,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkManifest,
    ProductAvailabilityTargetSpec,
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


class _FakeHttpAdapter:
    def __init__(self, target: ProductAvailabilityTargetSpec, body: str | None = None) -> None:
        self.target = target
        self.body = body or _product_body()
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        digest = stable_hash({"target": self.target.id, "body": self.body})
        artifact_ref = f"artifact:{command.command_envelope_id}:{digest[:12]}"
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


def _manifest(scenario: str = "success") -> ProductAvailabilityBenchmarkManifest:
    return ProductAvailabilityBenchmarkManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["target"],
        product_name="SanDisk 256GB Extreme microSDXC UHS-I Memory Card",
        brand="SanDisk",
        required_identity_terms=["SanDisk", "256GB", "Extreme", "microSDXC"],
        target_specs=[
            ProductAvailabilityTargetSpec(
                id="target",
                site_name="Example",
                target_url="https://example.com/product",
                robots_url="https://example.com/robots.txt",
                allowed_origin="https://example.com",
                required_identity_terms=["SanDisk", "256GB", "Extreme", "microSDXC"],
            )
        ],
        provider_names=["Local model runtime"],
        framework_names=["VeraCrawl Native Runtime"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="product_availability_benchmark_completed",
        required_ref_types=["live_http", "replay"],
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
    scenario: str = "success",
    body: str | None = None,
) -> ProductAvailabilityBenchmarkResult:
    manifest = _manifest(scenario)
    return run_product_availability_benchmark(
        manifest=manifest,
        profile="target",
        store=ReferencePersistenceStore(tmp_path / "state"),
        adapter_factory=lambda _fixture_id, target: _FakeHttpAdapter(target, body=body),
        robots_fetcher=lambda _target: RobotsFetchResult(status_code=200, body_text=""),
        model_binding=_model_binding(),
        agent_binding=_agent_binding(),
    )


def _product_body() -> str:
    return """
    <html><head><title>SanDisk 256GB Extreme microSDXC</title>
    <script type="application/ld+json">
    {
      "@context":"https://schema.org",
      "@type":"Product",
      "name":"SanDisk 256GB Extreme microSDXC UHS-I Memory Card",
      "offers":{
        "@type":"Offer",
        "priceCurrency":"USD",
        "price":82.68,
        "availability":"https://schema.org/InStock"
      }
    }
    </script></head><body>SanDisk 256GB Extreme microSDXC Memory Card</body></html>
    """


def test_product_availability_extracts_source_backed_price_and_availability(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path)

    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.site_results) == 1
    assert result.site_results[0].price_amount == 82.68
    assert result.site_results[0].availability_status == "in_stock"
    assert len(result.model_call_traces) == 4
    assert len(result.field_evidence) == 3


def test_product_availability_extracts_product_meta_price_and_availability(
    tmp_path: Path,
) -> None:
    body = """
    <html><head><title>SanDisk 256GB Extreme microSDXC</title>
    <meta name="product:price:amount" content="1,879">
    <meta name="product:price:currency" content="TWD">
    <meta name="product:availability" content="in stock">
    </head><body>SanDisk 256GB Extreme microSDXC 記憶卡 可訂購</body></html>
    """
    result = _run(tmp_path, body=body)

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.site_results[0].price_raw_text == "TWD 1,879"
    assert result.site_results[0].price_amount == 1879.0
    assert result.site_results[0].price_currency == "TWD"
    assert result.site_results[0].availability_status == "in_stock"


def test_product_availability_extracts_chinese_availability_fallback(
    tmp_path: Path,
) -> None:
    body = """
    <html><head><title>SanDisk 256GB Extreme microSDXC</title>
    <script type="application/ld+json">
    {
      "@context":"https://schema.org",
      "@type":"Product",
      "name":"SanDisk 256GB Extreme microSDXC",
      "offers":{"@type":"Offer","priceCurrency":"TWD","price":1999}
    }
    </script></head><body>SanDisk 256GB Extreme microSDXC 記憶卡 加入購物車</body></html>
    """
    result = _run(tmp_path, body=body)

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.site_results[0].price_currency == "TWD"
    assert result.site_results[0].availability_status == "in_stock"


def test_product_availability_javascript_shell_without_identity_needs_review(
    tmp_path: Path,
) -> None:
    body = """
    <html><head><title>Product app shell</title></head>
    <body><noscript>Please enable JavaScript on your browser.</noscript>
    <div id="main"></div><script src="/assets/app.js"></script></body></html>
    """
    result = _run(tmp_path, body=body)

    assert result.site_results[0].completion_result == CompletenessResult.NEEDS_REVIEW
    assert (
        result.site_results[0].failure_type
        == ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED
    )
    assert result.site_results[0].missing_ref_fields == ["source_backed_product_identity"]


def test_product_availability_wrong_identity_fails(tmp_path: Path) -> None:
    result = _run(tmp_path, scenario="product-availability-wrong-identity")

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == ProductAvailabilityFailureType.PRODUCT_IDENTITY_MISMATCH


def test_product_availability_missing_price_fails(tmp_path: Path) -> None:
    body = "<html><body>SanDisk 256GB Extreme microSDXC In Stock</body></html>"
    result = _run(tmp_path, body=body)

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == ProductAvailabilityFailureType.PRICE_NOT_FOUND
