from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.cli import product_discovery
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.product_availability import ProductAvailabilityTargetSpec
from veracrawl.contracts.product_discovery import ProductDiscoverySourceSpec
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult


class _FixtureDiscoveryAdapter:
    def __init__(self, source: ProductDiscoverySourceSpec) -> None:
        self.source = source
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        body = _search_body(self.source)
        self._last_result = _network_result(command, self.source.search_url, body)
        return _source_result(command, self._last_result.artifact_refs[0])


class _FixtureProductAdapter:
    def __init__(self, target: ProductAvailabilityTargetSpec) -> None:
        self.target = target
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        self._last_result = _network_result(command, self.target.target_url, _product_body())
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


def _search_body(source: ProductDiscoverySourceSpec) -> str:
    if "no-candidates" in source.id:
        return "<html><body><a href=\"/category\">Category</a></body></html>"
    return """
    <html><body>
      <a href="/prod/iphone-17-256g">Apple iPhone 17 256G</a>
      <a href="/prod/iphone-17-pro-256g">Apple iPhone 17 Pro 256G</a>
      <a href="/cart">Cart</a>
    </body></html>
    """


def _product_body() -> str:
    return """
    <html><head><title>Apple iPhone 17 256G</title>
    <meta name="product:price:amount" content="27980">
    <meta name="product:price:currency" content="TWD">
    <meta name="product:availability" content="in stock">
    </head><body>Apple iPhone 17 256G 24小時到貨 免運 加入購物車</body></html>
    """


@pytest.mark.parametrize(
    ("fixture_path", "expected_result"),
    [
        (Path("tests/fixtures/query-product-discovery-success"), CompletenessResult.PASS),
        (Path("tests/fixtures/query-product-discovery-no-candidates"), CompletenessResult.FAIL),
    ],
)
def test_product_discovery_cli_fixture_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_path: Path,
    expected_result: CompletenessResult,
) -> None:
    monkeypatch.setattr(
        product_discovery,
        "_fetch_discovery_robots",
        lambda source: RobotsFetchResult(
            status_code=source.allowed_robots_status_codes[0],
            body_text="",
        ),
    )
    monkeypatch.setattr(
        product_discovery,
        "_fetch_product_robots",
        lambda target: RobotsFetchResult(
            status_code=target.allowed_robots_status_codes[0],
            body_text="",
        ),
    )
    monkeypatch.setattr(
        product_discovery,
        "_discovery_adapter_factory",
        lambda _fixture_id, source: _FixtureDiscoveryAdapter(source),
    )
    monkeypatch.setattr(
        product_discovery,
        "_product_adapter_factory",
        lambda _fixture_id, target: _FixtureProductAdapter(target),
    )

    result = product_discovery.run_fixture(
        fixture_path,
        profile="target",
        out=tmp_path,
    )

    assert result.report.completion_result == expected_result
    assert (tmp_path / "discovery_report.json").exists()
    assert (tmp_path / "discovered_candidates.json").exists()
    assert (tmp_path / "ranked_offers.json").exists()
