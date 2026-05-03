"""Expanded real-world public corpus quality benchmark runtime."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from veracrawl.benchmarks.real_world import (
    NetworkAdapterFactory,
    RealWorldBenchmarkResult,
    RobotsFetcher,
    run_real_world_benchmark_corpus,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldBenchmarkFailureType,
    RealWorldQualityCorpusFailureType,
)
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkCorpusManifest,
    RealWorldBenchmarkSiteObservation,
    RealWorldBenchmarkSiteSpec,
)
from veracrawl.contracts.real_world_quality import (
    RealWorldQualityCorpusManifest,
    RealWorldQualityCorpusReport,
    RealWorldQualityPatternCoverageRecord,
    RealWorldQualitySiteObservation,
    RealWorldQualityTargetSpec,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class RealWorldQualityCorpusResult:
    report: RealWorldQualityCorpusReport
    quality_observations: list[RealWorldQualitySiteObservation]
    pattern_coverage: list[RealWorldQualityPatternCoverageRecord]
    real_world_result: RealWorldBenchmarkResult


def run_real_world_quality_corpus(
    *,
    manifest: RealWorldQualityCorpusManifest,
    profile: str,
    store: ProductionPersistenceStore,
    adapter_factory: NetworkAdapterFactory,
    robots_fetcher: RobotsFetcher,
) -> RealWorldQualityCorpusResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"real-world quality corpus {manifest.id} does not support {profile}")

    real_world_manifest = _real_world_manifest_from_quality(manifest, profile)
    real_world_result = run_real_world_benchmark_corpus(
        manifest=real_world_manifest,
        profile=profile,
        store=store,
        adapter_factory=adapter_factory,
        robots_fetcher=robots_fetcher,
    )
    observations_by_site = {
        observation.site_spec_ref: observation
        for observation in real_world_result.observations
    }
    quality_observations = [
        _quality_observation_from_real_world(
            manifest=manifest,
            target=target,
            observation=observations_by_site.get(target.id),
        )
        for target in manifest.target_specs
    ]
    if manifest.scenario == "missing-replay":
        quality_observations = _inject_missing_replay(quality_observations)

    recorded_observations = [
        _record_quality_observation_event(manifest.id, observation, store)
        for observation in quality_observations
    ]
    pattern_coverage = _build_pattern_coverage(manifest, recorded_observations)
    recorded_patterns = [
        _record_pattern_coverage_event(manifest.id, coverage, store)
        for coverage in pattern_coverage
    ]
    report = _build_quality_report(
        manifest=manifest,
        real_world_result=real_world_result,
        observations=recorded_observations,
        pattern_coverage=recorded_patterns,
    )
    store.save_canonical_model("real_world_quality_corpus_reports", report.id, report)
    report = _record_quality_report_event(manifest.id, report, store)
    store.save_canonical_model("real_world_quality_corpus_reports", report.id, report)

    return RealWorldQualityCorpusResult(
        report=report,
        quality_observations=recorded_observations,
        pattern_coverage=recorded_patterns,
        real_world_result=real_world_result,
    )


def _real_world_manifest_from_quality(
    manifest: RealWorldQualityCorpusManifest,
    profile: str,
) -> RealWorldBenchmarkCorpusManifest:
    profile_refs = sorted(set(manifest.profile_refs + ["target", profile]))
    return RealWorldBenchmarkCorpusManifest(
        id=f"{manifest.id}:row055",
        scenario=manifest.scenario,
        profile_refs=profile_refs,
        site_specs=[_site_spec_from_quality_target(target) for target in manifest.target_specs],
        allowed_origin_refs=manifest.allowed_origin_refs,
        rate_budget_ref=manifest.rate_budget_ref,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="real_world_benchmark_completed",
        required_ref_types=[
            "site_observation_refs",
            "live_http_report_refs",
            "network_response_refs",
            "artifact_refs",
            "content_hash_refs",
            "canonical_url_refs",
            "command_record_refs",
            "event_cursor_refs",
            "outbox_refs",
            "replay_bundle_refs",
        ],
    )


def _site_spec_from_quality_target(
    target: RealWorldQualityTargetSpec,
) -> RealWorldBenchmarkSiteSpec:
    return RealWorldBenchmarkSiteSpec(
        id=target.id,
        target_url=target.target_url,
        robots_url=target.robots_url,
        allowed_origin=target.allowed_origin,
        expected_status_code=target.expected_status_code,
        expected_content_type=target.expected_content_type,
        min_body_size_bytes=target.min_body_size_bytes,
        required_title_fragments=target.required_title_fragments,
        required_body_fragments=target.required_body_fragments,
        required_regex_counts=target.required_regex_counts,
        allowed_robots_status_codes=target.allowed_robots_status_codes,
        timeout_ms=target.timeout_ms,
        size_budget_bytes=target.size_budget_bytes,
        pattern_refs=target.pattern_refs,
    )


def _quality_observation_from_real_world(
    *,
    manifest: RealWorldQualityCorpusManifest,
    target: RealWorldQualityTargetSpec,
    observation: RealWorldBenchmarkSiteObservation | None,
) -> RealWorldQualitySiteObservation:
    if observation is None:
        return _failure_observation(
            manifest_id=manifest.id,
            target=target,
            failure=RealWorldQualityCorpusFailureType.MISSING_REAL_WORLD_REPORT,
            diagnostics=[f"missing row 055 observation for {target.id}"],
            missing_ref_fields=["site_observation_ref"],
        )
    if observation.completion_result != CompletenessResult.PASS:
        failure = _quality_failure_from_real_world(observation.failure_type)
        return _failure_observation(
            manifest_id=manifest.id,
            target=target,
            failure=failure,
            diagnostics=observation.diagnostics
            or [f"row 055 observation did not pass for {target.id}"],
            missing_ref_fields=observation.missing_ref_fields or ["site_observation_ref"],
            site_observation_ref=observation.id,
            failure_report_refs=observation.failure_report_refs,
        )
    return RealWorldQualitySiteObservation(
        id=f"real-world-quality-site-observation:{manifest.id}:{target.id}",
        target_spec_ref=target.id,
        site_observation_ref=observation.id,
        target_url=target.target_url,
        pattern_family_refs=target.pattern_family_refs,
        matched_observation_refs=observation.matched_observation_refs,
        policy_decision_refs=observation.policy_decision_refs,
        artifact_refs=observation.artifact_refs,
        content_hash_refs=observation.content_hash_refs,
        canonical_url_refs=observation.canonical_url_refs,
        command_record_refs=observation.command_record_refs,
        event_cursor_refs=observation.event_cursor_refs,
        outbox_refs=observation.outbox_refs,
        replay_bundle_ref=observation.replay_bundle_ref,
        completion_result=CompletenessResult.PASS,
    )


def _failure_observation(
    *,
    manifest_id: str,
    target: RealWorldQualityTargetSpec,
    failure: RealWorldQualityCorpusFailureType,
    diagnostics: list[str],
    missing_ref_fields: list[str],
    site_observation_ref: Ref | None = None,
    failure_report_refs: list[Ref] | None = None,
) -> RealWorldQualitySiteObservation:
    return RealWorldQualitySiteObservation(
        id=f"real-world-quality-site-observation:{manifest_id}:{target.id}",
        target_spec_ref=target.id,
        site_observation_ref=site_observation_ref,
        target_url=target.target_url,
        pattern_family_refs=target.pattern_family_refs,
        failure_report_refs=failure_report_refs
        or [f"failure:{manifest_id}:{target.id}:{failure.value}"],
        missing_ref_fields=missing_ref_fields,
        failure_type=failure,
        diagnostics=diagnostics,
        completion_result=CompletenessResult.FAIL,
    )


def _quality_failure_from_real_world(
    failure: RealWorldBenchmarkFailureType | None,
) -> RealWorldQualityCorpusFailureType:
    if failure in {
        RealWorldBenchmarkFailureType.SCOPE_DENIED,
        RealWorldBenchmarkFailureType.PRIVATE_NETWORK_DENIED,
        RealWorldBenchmarkFailureType.ROBOTS_DENIED,
    }:
        return RealWorldQualityCorpusFailureType.POLICY_DENIED_TARGET
    if failure in {
        RealWorldBenchmarkFailureType.NETWORK_UNAVAILABLE,
        RealWorldBenchmarkFailureType.LIVE_HTTP_FAILED,
    }:
        return RealWorldQualityCorpusFailureType.NETWORK_UNAVAILABLE_TARGET
    if failure == RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH:
        return RealWorldQualityCorpusFailureType.TARGET_DRIFT
    if failure == RealWorldBenchmarkFailureType.REPLAY_MISMATCH:
        return RealWorldQualityCorpusFailureType.MISSING_REPLAY_REFS
    return RealWorldQualityCorpusFailureType.MISSING_EVIDENCE_REFS


def _inject_missing_replay(
    observations: list[RealWorldQualitySiteObservation],
) -> list[RealWorldQualitySiteObservation]:
    injected = False
    updated: list[RealWorldQualitySiteObservation] = []
    for observation in observations:
        if not injected and observation.completion_result == CompletenessResult.PASS:
            injected = True
            updated.append(
                observation.model_copy(
                    update={
                        "replay_bundle_ref": None,
                        "failure_type": RealWorldQualityCorpusFailureType.MISSING_REPLAY_REFS,
                        "failure_report_refs": [
                            f"failure:{observation.id}:missing-replay"
                        ],
                        "missing_ref_fields": ["replay_bundle_ref"],
                        "diagnostics": ["quality observation replay refs intentionally missing"],
                        "completion_result": CompletenessResult.FAIL,
                    }
                )
            )
        else:
            updated.append(observation)
    return updated


def _build_pattern_coverage(
    manifest: RealWorldQualityCorpusManifest,
    observations: list[RealWorldQualitySiteObservation],
) -> list[RealWorldQualityPatternCoverageRecord]:
    declared: dict[Ref, list[Ref]] = defaultdict(list)
    for target in manifest.target_specs:
        for pattern in target.pattern_family_refs:
            declared[pattern].append(target.id)

    by_target = {observation.target_spec_ref: observation for observation in observations}
    records: list[RealWorldQualityPatternCoverageRecord] = []
    for pattern, target_refs in sorted(declared.items()):
        passing: list[Ref] = []
        failed: list[Ref] = []
        site_refs: list[Ref] = []
        quality_refs: list[Ref] = []
        for target_ref in target_refs:
            observation = by_target[target_ref]
            quality_refs.append(observation.id)
            if observation.site_observation_ref:
                site_refs.append(observation.site_observation_ref)
            if observation.completion_result == CompletenessResult.PASS:
                passing.append(target_ref)
            else:
                failed.append(target_ref)
        result = CompletenessResult.PASS if passing else CompletenessResult.FAIL
        records.append(
            RealWorldQualityPatternCoverageRecord(
                id=f"real-world-quality-pattern-coverage:{manifest.id}:{pattern}",
                pattern_family_ref=pattern,
                declared_target_refs=sorted(target_refs),
                passing_target_refs=sorted(passing),
                failed_target_refs=sorted(failed),
                site_observation_refs=sorted(site_refs),
                quality_observation_refs=sorted(quality_refs),
                diagnostics=[] if passing else [f"no passing targets for {pattern}"],
                completion_result=result,
            )
        )
    return records


def _build_quality_report(
    *,
    manifest: RealWorldQualityCorpusManifest,
    real_world_result: RealWorldBenchmarkResult,
    observations: list[RealWorldQualitySiteObservation],
    pattern_coverage: list[RealWorldQualityPatternCoverageRecord],
) -> RealWorldQualityCorpusReport:
    passing = [item for item in observations if item.completion_result == CompletenessResult.PASS]
    passing_target_refs = {item.target_spec_ref for item in passing}
    target_by_id = {target.id: target for target in manifest.target_specs}
    passing_origins = {
        target_by_id[item.target_spec_ref].allowed_origin for item in passing
    }
    passing_patterns = {
        pattern.pattern_family_ref
        for pattern in pattern_coverage
        if pattern.completion_result == CompletenessResult.PASS
    }
    failure_type, diagnostics, missing = _quality_gate_failure(
        manifest=manifest,
        observations=observations,
        passing_target_count=len(passing_target_refs),
        passing_origin_count=len(passing_origins),
        passing_pattern_count=len(passing_patterns),
    )
    completion = CompletenessResult.FAIL if failure_type else CompletenessResult.PASS
    return RealWorldQualityCorpusReport(
        id=f"real-world-quality-corpus-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        real_world_benchmark_run_report_ref=real_world_result.report.id,
        quality_observation_refs=[item.id for item in observations],
        pattern_coverage_refs=[item.id for item in pattern_coverage],
        site_observation_refs=[
            item.site_observation_ref for item in observations if item.site_observation_ref
        ],
        passing_target_count=len(passing_target_refs),
        declared_target_count=len(manifest.target_specs),
        origin_count=len(passing_origins),
        pattern_family_count=len(passing_patterns),
        policy_denied_count=_count_failure(
            observations, RealWorldQualityCorpusFailureType.POLICY_DENIED_TARGET
        ),
        network_unavailable_count=_count_failure(
            observations, RealWorldQualityCorpusFailureType.NETWORK_UNAVAILABLE_TARGET
        ),
        drift_count=_count_failure(observations, RealWorldQualityCorpusFailureType.TARGET_DRIFT),
        replay_missing_count=_count_failure(
            observations, RealWorldQualityCorpusFailureType.MISSING_REPLAY_REFS
        ),
        policy_decision_refs=_collect("policy_decision_refs", observations),
        artifact_refs=_collect("artifact_refs", observations),
        content_hash_refs=_collect("content_hash_refs", observations),
        canonical_url_refs=_collect("canonical_url_refs", observations),
        command_record_refs=_collect("command_record_refs", observations),
        event_cursor_refs=_collect("event_cursor_refs", observations),
        outbox_refs=_collect("outbox_refs", observations),
        replay_bundle_refs=sorted(
            {item.replay_bundle_ref for item in observations if item.replay_bundle_ref}
        ),
        failure_report_refs=sorted(
            {ref for item in observations for ref in item.failure_report_refs}
        )
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "real_world_quality_completed",
        completion_result=completion,
    )


def _quality_gate_failure(
    *,
    manifest: RealWorldQualityCorpusManifest,
    observations: list[RealWorldQualitySiteObservation],
    passing_target_count: int,
    passing_origin_count: int,
    passing_pattern_count: int,
) -> tuple[RealWorldQualityCorpusFailureType | None, list[str], list[str]]:
    failed = [item for item in observations if item.completion_result != CompletenessResult.PASS]
    if failed:
        first = failed[0].failure_type or RealWorldQualityCorpusFailureType.MISSING_EVIDENCE_REFS
        diagnostics = [diagnostic for item in failed for diagnostic in item.diagnostics]
        missing = sorted({field for item in failed for field in item.missing_ref_fields})
        return first, diagnostics, missing
    if passing_target_count < manifest.minimum_target_count:
        return (
            RealWorldQualityCorpusFailureType.INSUFFICIENT_TARGET_COVERAGE,
            [
                f"passing targets {passing_target_count} below minimum "
                f"{manifest.minimum_target_count}"
            ],
            ["passing_target_count"],
        )
    if passing_origin_count < manifest.minimum_origin_count:
        return (
            RealWorldQualityCorpusFailureType.INSUFFICIENT_ORIGIN_COVERAGE,
            [
                f"passing origins {passing_origin_count} below minimum "
                f"{manifest.minimum_origin_count}"
            ],
            ["origin_count"],
        )
    if passing_pattern_count < manifest.minimum_pattern_family_count:
        return (
            RealWorldQualityCorpusFailureType.INSUFFICIENT_PATTERN_COVERAGE,
            [
                f"passing pattern families {passing_pattern_count} below minimum "
                f"{manifest.minimum_pattern_family_count}"
            ],
            ["pattern_family_count"],
        )
    return None, [], []


def _count_failure(
    observations: Iterable[RealWorldQualitySiteObservation],
    failure_type: RealWorldQualityCorpusFailureType,
) -> int:
    return sum(1 for item in observations if item.failure_type == failure_type)


def _collect(
    field_name: str,
    observations: Iterable[RealWorldQualitySiteObservation],
) -> list[Ref]:
    refs: list[Ref] = []
    for observation in observations:
        refs.extend(getattr(observation, field_name))
    return sorted(set(refs))


def _record_quality_observation_event(
    manifest_id: str,
    observation: RealWorldQualitySiteObservation,
    store: ProductionPersistenceStore,
) -> RealWorldQualitySiteObservation:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:{observation.target_spec_ref}:quality-observation",
        command_type="record_real_world_quality_site_observation",
        target_aggregate_type="RealWorldQualitySiteObservation",
        target_aggregate_id=observation.id,
        event_type="real_world_quality_site_observed",
        output_refs=[observation.id],
        policy_decision_refs=observation.policy_decision_refs,
        store=store,
    )
    updated = observation.model_copy(
        update={
            "command_record_refs": sorted(set(observation.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(observation.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(observation.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("real_world_quality_site_observations", updated.id, updated)
    return updated


def _record_pattern_coverage_event(
    manifest_id: str,
    coverage: RealWorldQualityPatternCoverageRecord,
    store: ProductionPersistenceStore,
) -> RealWorldQualityPatternCoverageRecord:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:{coverage.pattern_family_ref}:pattern-coverage",
        command_type="record_real_world_quality_pattern_coverage",
        target_aggregate_type="RealWorldQualityPatternCoverageRecord",
        target_aggregate_id=coverage.id,
        event_type="real_world_quality_pattern_coverage_recorded",
        output_refs=[coverage.id],
        policy_decision_refs=[],
        store=store,
    )
    del command_ref, event_ref, outbox_ref
    store.save_canonical_model("real_world_quality_pattern_coverage", coverage.id, coverage)
    return coverage


def _record_quality_report_event(
    manifest_id: str,
    report: RealWorldQualityCorpusReport,
    store: ProductionPersistenceStore,
) -> RealWorldQualityCorpusReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:quality-report",
        command_type="record_real_world_quality_corpus_report",
        target_aggregate_type="RealWorldQualityCorpusReport",
        target_aggregate_id=report.id,
        event_type="real_world_quality_corpus_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:real-world-quality-benchmark",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{command_id}:dispatched",
    )
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id
