from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.cli import real_benchmark
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.real_world_benchmark import RealWorldBenchmarkSiteSpec
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult


class _FixtureHttpAdapter:
    def __init__(self, site: RealWorldBenchmarkSiteSpec) -> None:
        self.site = site
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        body = _body_for_site(self.site)
        digest = stable_hash({"site": self.site.id, "body": body})
        artifact_ref = f"artifact:{command.command_envelope_id}:{digest[:12]}"
        response = NetworkResponse(
            id=f"network-response:{command.command_envelope_id}",
            request_ref=f"network-request:{command.command_envelope_id}",
            status_code=self.site.expected_status_code,
            final_url=self.site.target_url,
            headers_ref=f"headers:{command.command_envelope_id}:response",
            raw_artifact_ref=artifact_ref,
            content_digest=digest,
            content_type=self.site.expected_content_type,
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


def _body_for_site(site: RealWorldBenchmarkSiteSpec) -> str:
    title = " ".join(site.required_title_fragments) if site.required_title_fragments else site.id
    fragments = " ".join(site.required_body_fragments)
    regex_material = " ".join(
        _materialize_regex(pattern, minimum)
        for pattern, minimum in site.required_regex_counts.items()
    )
    padding = "x" * site.min_body_size_bytes
    return (
        f"<html><head><title>{title}</title></head>"
        f"<body>{fragments} {regex_material} {padding}</body></html>"
    )


def _materialize_regex(pattern: str, minimum: int) -> str:
    if pattern == "class=\"product_pod\"":
        return " ".join(["<article class=\"product_pod\"></article>"] * minimum)
    if pattern == "class=\"quote\"":
        return " ".join(["<div class=\"quote\"></div>"] * minimum)
    if pattern == "\"title\"":
        return " ".join(["\"title\""] * minimum)
    return " ".join([pattern] * minimum)


def test_real_world_benchmark_cli_fixture_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        real_benchmark,
        "_fetch_robots",
        lambda site: RobotsFetchResult(
            status_code=site.allowed_robots_status_codes[0],
            body_text="",
        ),
    )
    monkeypatch.setattr(
        real_benchmark,
        "_adapter_factory",
        lambda _fixture_id, site: _FixtureHttpAdapter(site),
    )

    result = real_benchmark.run_fixture(
        Path("tests/fixtures/real-world-public-corpus"),
        profile="target",
        out=tmp_path,
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.observations) == 4
    assert (tmp_path / "run_report.json").exists()
    assert (tmp_path / "site_observations.json").exists()
