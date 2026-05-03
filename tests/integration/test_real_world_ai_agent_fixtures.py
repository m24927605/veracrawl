from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.real_world import RealWorldBenchmarkResult
from veracrawl.cli import real_ai_benchmark
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkRunReport,
    RealWorldBenchmarkSiteObservation,
)


def _real_world_result(
    fixture_id: str = "real-world-public-corpus",
    site_count: int = 4,
) -> RealWorldBenchmarkResult:
    observations = [_observation(index) for index in range(site_count)]
    report = RealWorldBenchmarkRunReport(
        id=f"real-world-benchmark-run-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        benchmark_corpus_ref="real-world-benchmark-corpus:fixture",
        benchmark_run_refs=[f"benchmark-run:site-{index}" for index in range(site_count)],
        site_observation_refs=[item.id for item in observations],
        live_http_report_refs=[item.live_http_report_ref or "" for item in observations],
        network_response_refs=[item.network_response_ref or "" for item in observations],
        source_observation_refs=[
            ref for item in observations for ref in item.source_observation_refs
        ],
        artifact_refs=[ref for item in observations for ref in item.artifact_refs],
        content_hash_refs=[ref for item in observations for ref in item.content_hash_refs],
        canonical_url_refs=[ref for item in observations for ref in item.canonical_url_refs],
        policy_decision_refs=[ref for item in observations for ref in item.policy_decision_refs],
        command_record_refs=[ref for item in observations for ref in item.command_record_refs],
        event_cursor_refs=[ref for item in observations for ref in item.event_cursor_refs],
        outbox_refs=[ref for item in observations for ref in item.outbox_refs],
        replay_bundle_refs=[item.replay_bundle_ref or "" for item in observations],
        observation_summary_refs=[
            f"observation-summary:site-{index}" for index in range(site_count)
        ],
        operator_status="real_world_benchmark_completed",
        completion_result=CompletenessResult.PASS,
    )
    return RealWorldBenchmarkResult(
        report=report,
        observations=observations,
        live_http_results=[],
    )


def _observation(index: int) -> RealWorldBenchmarkSiteObservation:
    return RealWorldBenchmarkSiteObservation(
        id=f"real-world-site-observation:site-{index}",
        site_spec_ref=f"site-{index}",
        target_url=f"https://example.com/{index}",
        robots_policy_ref=f"policy:site-{index}:robots",
        live_http_report_ref=f"live-http-report:site-{index}",
        network_response_ref=f"network-response:site-{index}",
        source_observation_refs=[f"source-observation:site-{index}"],
        artifact_refs=[f"artifact:site-{index}"],
        content_hash_refs=[f"content-hash:site-{index}"],
        canonical_url_refs=[f"canonical-url:site-{index}"],
        policy_decision_refs=[f"policy:site-{index}"],
        command_record_refs=[f"command:site-{index}"],
        event_cursor_refs=[f"event-cursor:site-{index}"],
        outbox_refs=[f"outbox:site-{index}"],
        replay_bundle_ref=f"replay-bundle:site-{index}",
        status_code=200,
        content_type="text/html",
        body_size_bytes=128,
        content_digest=f"digest-{index}",
        matched_observation_refs=[f"observation:site-{index}:title"],
        completion_result=CompletenessResult.PASS,
    )


@pytest.mark.parametrize(
    ("fixture_path", "corpus_fixture_id", "site_count", "expected_traces"),
    [
        (
            Path("tests/fixtures/real-world-ai-agent-public-corpus"),
            "real-world-public-corpus",
            4,
            16,
        ),
        (
            Path("tests/fixtures/top-ecommerce-ai-agent-corpus"),
            "top-ecommerce-public-corpus",
            6,
            24,
        ),
    ],
)
def test_real_world_ai_agent_cli_success_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_path: Path,
    corpus_fixture_id: str,
    site_count: int,
    expected_traces: int,
) -> None:
    monkeypatch.setattr(
        real_ai_benchmark,
        "_run_real_world_corpus",
        lambda _manifest, profile, out: _real_world_result(
            corpus_fixture_id,
            site_count,
        ),
    )

    result = real_ai_benchmark.run_fixture(
        fixture_path,
        profile="target",
        out=tmp_path,
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.report.model_call_trace_refs) == expected_traces
    assert (tmp_path / "run_report.json").exists()
    assert (tmp_path / "decision_traces.json").exists()
    assert (tmp_path / "model_call_traces.json").exists()


def test_real_world_ai_agent_negative_fixture_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        real_ai_benchmark,
        "_run_real_world_corpus",
        lambda _manifest, profile, out: _real_world_result(),
    )

    result = real_ai_benchmark.run_fixture(
        Path("tests/fixtures/real-world-ai-agent-publication-bypass"),
        profile="target",
        out=tmp_path,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.direct_publication_refs
