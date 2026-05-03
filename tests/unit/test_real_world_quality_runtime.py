from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.benchmarks.real_world_quality import (
    RealWorldQualityCorpusResult,
    run_real_world_quality_corpus,
)
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    RealWorldQualityCorpusFailureType,
    SourceAdapterResultType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.real_world_benchmark import RealWorldBenchmarkSiteSpec
from veracrawl.contracts.real_world_quality import (
    RealWorldQualityCorpusManifest,
    RealWorldQualityTargetSpec,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class _QualityHttpAdapter:
    def __init__(self, site: RealWorldBenchmarkSiteSpec, *, drift: bool = False) -> None:
        self.site = site
        self.drift = drift
        self._last_result: NetworkClientResult | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        body = "<html><head><title>Drift</title></head><body>missing</body></html>"
        if not self.drift:
            body = (
                f"<html><head><title>{self.site.required_title_fragments[0]}</title></head>"
                f"<body>{' '.join(self.site.required_body_fragments)} "
                f"{'x' * self.site.min_body_size_bytes}</body></html>"
            )
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
            run_id="run:quality",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=["policy:quality"],
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"idempotency:{command.command_envelope_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def _target(index: int, *, origin_index: int, pattern_index: int) -> RealWorldQualityTargetSpec:
    origin = f"https://quality-{origin_index:02d}.example"
    pattern = f"pattern:family-{pattern_index:02d}"
    return RealWorldQualityTargetSpec(
        id=f"target-{index:02d}",
        target_url=f"{origin}/page-{index:02d}",
        robots_url=f"{origin}/robots.txt",
        allowed_origin=origin,
        expected_status_code=200,
        expected_content_type="text/html",
        min_body_size_bytes=20,
        required_title_fragments=[f"Quality Target {index:02d}"],
        required_body_fragments=[f"quality body {index:02d}"],
        allowed_robots_status_codes=[404],
        pattern_refs=[pattern],
        pattern_family_refs=[pattern],
    )


def _manifest(
    *,
    target_count: int = 40,
    origin_count: int = 15,
    pattern_count: int = 10,
    scenario: str = "success",
) -> RealWorldQualityCorpusManifest:
    targets = [
        _target(
            index,
            origin_index=index % origin_count,
            pattern_index=index % pattern_count,
        )
        for index in range(target_count)
    ]
    return RealWorldQualityCorpusManifest(
        id=f"real-world-quality-{scenario}",
        scenario=scenario,
        profile_refs=["target", "quality"],
        target_specs=targets,
        allowed_origin_refs=sorted({target.allowed_origin for target in targets}),
        rate_budget_ref="budget:quality",
        minimum_target_count=40,
        minimum_origin_count=15,
        minimum_pattern_family_count=10,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="real_world_quality_completed",
        required_ref_types=["quality_observation_refs", "replay_bundle_refs"],
    )


def _run(
    tmp_path: Path,
    manifest: RealWorldQualityCorpusManifest,
    *,
    drift_target: str | None = None,
) -> RealWorldQualityCorpusResult:
    return run_real_world_quality_corpus(
        manifest=manifest,
        profile="quality",
        store=ReferencePersistenceStore(tmp_path),
        adapter_factory=lambda _fixture_id, site: _QualityHttpAdapter(
            site,
            drift=site.id == drift_target,
        ),
        robots_fetcher=lambda _site: RobotsFetchResult(status_code=404, body_text=""),
    )


def test_quality_corpus_passes_thresholds(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest())

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.passing_target_count == 40
    assert result.report.origin_count == 15
    assert result.report.pattern_family_count == 10
    assert len(result.quality_observations) == 40
    assert result.pattern_coverage


def test_quality_corpus_fails_insufficient_targets(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest(target_count=39, scenario="insufficient-targets"))

    assert result.report.completion_result == CompletenessResult.FAIL
    assert (
        result.report.failure_type
        == RealWorldQualityCorpusFailureType.INSUFFICIENT_TARGET_COVERAGE
    )


def test_quality_corpus_fails_insufficient_origins(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest(origin_count=14, scenario="insufficient-origins"))

    assert result.report.completion_result == CompletenessResult.FAIL
    assert (
        result.report.failure_type
        == RealWorldQualityCorpusFailureType.INSUFFICIENT_ORIGIN_COVERAGE
    )


def test_quality_corpus_fails_insufficient_patterns(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest(pattern_count=9, scenario="insufficient-patterns"))

    assert result.report.completion_result == CompletenessResult.FAIL
    assert (
        result.report.failure_type
        == RealWorldQualityCorpusFailureType.INSUFFICIENT_PATTERN_COVERAGE
    )


def test_quality_corpus_fails_target_drift(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest(scenario="target-drift"), drift_target="target-00")

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == RealWorldQualityCorpusFailureType.TARGET_DRIFT
    assert result.report.drift_count == 1


def test_quality_corpus_fails_missing_replay(tmp_path: Path) -> None:
    result = _run(tmp_path, _manifest(scenario="missing-replay"))

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == RealWorldQualityCorpusFailureType.MISSING_REPLAY_REFS
    assert result.report.replay_missing_count == 1
