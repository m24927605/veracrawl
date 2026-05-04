from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.cli import product_availability_benchmark
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.product_availability import ProductAvailabilityTargetSpec
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult


class _FixtureHttpAdapter:
    def __init__(self, target: ProductAvailabilityTargetSpec) -> None:
        self.target = target
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        if self.target.expected_site_result == CompletenessResult.NEEDS_REVIEW:
            raise ValueError("fixture source access denied")
        body = _body_for_target(self.target)
        digest = stable_hash({"target": self.target.id, "body": body})
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


def _body_for_target(target: ProductAvailabilityTargetSpec) -> str:
    identity = " ".join(
        dict.fromkeys([*target.required_identity_terms, "SanDisk", "256GB", "Extreme", "microSDXC"])
    )
    return f"""
    <html><head><title>{identity}</title>
    <script type="application/ld+json">
    {{"@context":"https://schema.org","@type":"Product","name":"{identity}","offers":{{"@type":"Offer","priceCurrency":"USD","price":82.68,"availability":"https://schema.org/InStock"}}}}
    </script></head><body>{identity} In Stock $82.68</body></html>
    """


@pytest.mark.parametrize(
    ("fixture_path", "expected_result", "expected_passing", "expected_blocked"),
    [
        (
            Path("tests/fixtures/us-top-ecommerce-product-availability"),
            CompletenessResult.NEEDS_REVIEW,
            2,
            1,
        ),
        (
            Path("tests/fixtures/product-availability-wrong-identity"),
            CompletenessResult.FAIL,
            0,
            1,
        ),
        (
            Path("tests/fixtures/product-availability-missing-price"),
            CompletenessResult.FAIL,
            0,
            1,
        ),
        (
            Path("tests/fixtures/product-availability-missing-availability"),
            CompletenessResult.FAIL,
            0,
            1,
        ),
        (
            Path("tests/fixtures/product-availability-llm-output-as-evidence"),
            CompletenessResult.FAIL,
            0,
            1,
        ),
        (
            Path("tests/fixtures/product-availability-missing-replay"),
            CompletenessResult.FAIL,
            0,
            1,
        ),
    ],
)
def test_product_availability_cli_fixture_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_path: Path,
    expected_result: CompletenessResult,
    expected_passing: int,
    expected_blocked: int,
) -> None:
    monkeypatch.setattr(
        product_availability_benchmark,
        "_fetch_robots",
        lambda target: RobotsFetchResult(
            status_code=target.allowed_robots_status_codes[0],
            body_text="",
        ),
    )
    monkeypatch.setattr(
        product_availability_benchmark,
        "_adapter_factory",
        lambda _fixture_id, target: _FixtureHttpAdapter(target),
    )

    result = product_availability_benchmark.run_fixture(
        fixture_path,
        profile="target",
        out=tmp_path,
    )

    assert result.report.completion_result == expected_result
    assert len(result.report.passing_site_result_refs) == expected_passing
    assert len(result.report.blocked_site_result_refs) == expected_blocked
    assert (tmp_path / "run_report.json").exists()
    assert (tmp_path / "site_results.json").exists()
    assert (tmp_path / "field_evidence.json").exists()
