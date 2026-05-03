"""Deterministic target crawl runtime runner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentRecommendationSubject,
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
    TargetWebsitePattern,
)
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
    TargetAIRecommendationRecord,
    TargetCrawlPatternRecord,
    TargetRuntimeReport,
    TargetSourceCorpusEntry,
    TargetSourceCorpusManifest,
    TargetSourceObservationRecord,
)


@dataclass(frozen=True)
class TargetRuntimeResult:
    pattern_records: list[TargetCrawlPatternRecord]
    ai_recommendations: list[TargetAIRecommendationRecord]
    report: TargetRuntimeReport
    source_observations: list[TargetSourceObservationRecord]
    adapter_backed_records: list[TargetAdapterBackedSourceRecord] = field(default_factory=list)


_TARGET_PATTERNS: tuple[TargetWebsitePattern, ...] = (
    TargetWebsitePattern.STATIC,
    TargetWebsitePattern.SITEMAP_RSS_FEED,
    TargetWebsitePattern.LISTING_DETAIL,
    TargetWebsitePattern.API_LIKE_ENDPOINTS,
    TargetWebsitePattern.DOCUMENTS,
    TargetWebsitePattern.DRIFTED_SITES,
    TargetWebsitePattern.JAVASCRIPT_PAGES,
)

_FAILURES: dict[str, tuple[TargetRuntimeStatus, TargetRuntimeFailureType, str]] = {
    "target-runtime-policy-denied": (
        TargetRuntimeStatus.BLOCKED,
        TargetRuntimeFailureType.POLICY_DENIED,
        "source access denied by target runtime policy",
    ),
    "target-runtime-prompt-injection": (
        TargetRuntimeStatus.BLOCKED,
        TargetRuntimeFailureType.PROMPT_INJECTION,
        "untrusted source content attempted to override trusted crawl policy",
    ),
    "target-runtime-missing-evidence": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.MISSING_EVIDENCE,
        "accepted output cannot be linked to required source evidence",
    ),
    "target-runtime-replay-mismatch": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.REPLAY_MISMATCH,
        "replay event sequence does not match target runtime oracle",
    ),
    "target-runtime-partial-export": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.PARTIAL_EXPORT,
        "export receipt set is incomplete for accepted outputs",
    ),
    "target-runtime-false-complete": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.FALSE_COMPLETE,
        "run attempted to mark degraded capability complete",
    ),
}


def run_target_runtime_fixture(
    *,
    fixture_id: str,
    scenario: str,
    profile: str = "target",
    fixture_dir: Path | None = None,
    source_corpus_ref: Ref | None = None,
    adapter_manifest: TargetAdapterBackedSourceManifest | None = None,
    adapter_records: list[TargetAdapterBackedSourceRecord] | None = None,
) -> TargetRuntimeResult:
    if profile != "target":
        raise ValueError(f"unsupported target runtime profile: {profile}")
    if source_corpus_ref is not None:
        if fixture_dir is None:
            raise ValueError("source-backed target runtime requires fixture_dir")
        return _source_backed_result(
            fixture_id=fixture_id,
            scenario=scenario,
            fixture_dir=fixture_dir,
            source_corpus_ref=source_corpus_ref,
            adapter_manifest=adapter_manifest,
            adapter_records=adapter_records,
        )
    if scenario == "target-runtime-needs-review":
        return _needs_review_result(fixture_id)
    if scenario in _FAILURES:
        status, failure, diagnostic = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            status=status,
            failure=failure,
            diagnostic=diagnostic,
        )
    repaired = scenario == "target-runtime-drift-repair"
    return _success_result(fixture_id=fixture_id, repaired=repaired)


def _success_result(*, fixture_id: str, repaired: bool) -> TargetRuntimeResult:
    run_ref = _run_ref(fixture_id)
    policy_refs = _policy_refs(fixture_id)
    command_refs = _command_refs(fixture_id)
    event_refs = _event_refs(fixture_id)
    outbox_refs = _outbox_refs(fixture_id)
    replay_ref = _replay_ref(fixture_id)
    pattern_records = [
        _pattern_record(
            fixture_id=fixture_id,
            pattern=pattern,
            policy_refs=policy_refs,
            command_refs=command_refs,
            event_refs=event_refs,
            outbox_refs=outbox_refs,
            replay_ref=replay_ref,
        )
        for pattern in _TARGET_PATTERNS
    ]
    ai = _accepted_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if repaired
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        repair_refs=(
            [f"frontier:{fixture_id}:drifted_sites:repair-retry"] if repaired else []
        ),
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=TargetRuntimeStatus.COMPLETE,
        completion_result=CompletenessResult.PASS,
        covered_patterns=[record.website_pattern for record in pattern_records],
        pattern_record_refs=[record.id for record in pattern_records],
        accepted_output_refs=_collect(pattern_records, "accepted_output_refs"),
        evidence_refs=_collect(pattern_records, "evidence_refs"),
        verification_refs=_collect(pattern_records, "verification_refs"),
        graph_refs=_collect(pattern_records, "graph_refs"),
        export_receipt_refs=[f"export-receipt:{fixture_id}:target"],
        output_manifest_refs=[f"output-manifest:{fixture_id}:target"],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=_collect(pattern_records, "artifact_refs"),
        ai_recommendation_refs=[ai.id],
        repair_action_refs=(
            [f"repair-action:{fixture_id}:drifted-sites"] if repaired else []
        ),
        recovery_action_refs=[f"recovery-action:{fixture_id}:operator-visible"],
        privacy_lifecycle_refs=[f"privacy:{fixture_id}:retention-redaction"],
        replay_bundle_ref=replay_ref,
        operator_status=(
            "target_runtime_drift_repaired" if repaired else "target_runtime_completed"
        ),
    )
    return TargetRuntimeResult(pattern_records, [ai], report, [])


def _needs_review_result(fixture_id: str) -> TargetRuntimeResult:
    policy_refs = _policy_refs(fixture_id)
    ai = _accepted_ai_recommendation(
        fixture_id=fixture_id,
        subject=AgentRecommendationSubject.REPAIR,
        repair_refs=[f"frontier:{fixture_id}:needs-review"],
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=TargetRuntimeStatus.NEEDS_REVIEW,
        completion_result=CompletenessResult.NEEDS_REVIEW,
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        ai_recommendation_refs=[ai.id],
        review_item_refs=[f"review:{fixture_id}:evidence-gap"],
        recovery_action_refs=[f"recovery-action:{fixture_id}:rerun-frontier"],
        missing_ref_fields=["accepted_output_refs"],
        diagnostics=["recoverable evidence gap requires operator review"],
        operator_status="target_runtime_needs_review",
    )
    return TargetRuntimeResult([], [ai], report, [])


def _failure_result(
    *,
    fixture_id: str,
    status: TargetRuntimeStatus,
    failure: TargetRuntimeFailureType,
    diagnostic: str,
) -> TargetRuntimeResult:
    policy_refs = _policy_refs(fixture_id)
    ai = _blocked_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if failure == TargetRuntimeFailureType.PROMPT_INJECTION
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        blocked_ref=f"blocked-action:{fixture_id}:{failure.value}",
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=status,
        completion_result=CompletenessResult.FAIL,
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        ai_recommendation_refs=[ai.id],
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=_missing_fields_for(failure),
        diagnostics=[diagnostic],
        operator_status=failure.value,
    )
    return TargetRuntimeResult([], [ai], report, [])


def _source_backed_result(
    *,
    fixture_id: str,
    scenario: str,
    fixture_dir: Path,
    source_corpus_ref: Ref,
    adapter_manifest: TargetAdapterBackedSourceManifest | None = None,
    adapter_records: list[TargetAdapterBackedSourceRecord] | None = None,
) -> TargetRuntimeResult:
    corpus = TargetSourceCorpusManifest.model_validate(
        json.loads((fixture_dir / source_corpus_ref).read_text(encoding="utf-8"))
    )
    observations: list[TargetSourceObservationRecord] = []
    repaired_fields: list[Ref] = []
    replay_mismatches: list[Ref] = []
    missing_fields: list[Ref] = []
    prompt_injections: list[Ref] = []
    policy_denials: list[Ref] = []

    for entry in corpus.entries:
        source_path = fixture_dir / entry.source_path
        if not entry.allowed:
            policy_denials.append(entry.policy_decision_ref)
            continue
        content = source_path.read_text(encoding="utf-8")
        if entry.contains_prompt_injection or "PROMPT_INJECTION" in content:
            prompt_injections.append(f"prompt-injection:{fixture_id}:{entry.id}")
            continue
        observation, repaired, replay_mismatch, missing = _observe_source_entry(
            fixture_id=fixture_id,
            entry=entry,
            content=content,
        )
        observations.append(observation)
        repaired_fields.extend(repaired)
        replay_mismatches.extend(replay_mismatch)
        missing_fields.extend(missing)

    if policy_denials:
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=TargetRuntimeFailureType.POLICY_DENIED,
            status=TargetRuntimeStatus.BLOCKED,
            diagnostics=["source corpus entry denied by policy"],
            missing_ref_fields=["source_policy_refs"],
            extra_policy_refs=corpus.policy_decision_refs + policy_denials,
            observations=observations,
            adapter_records=adapter_records or [],
        )
    if prompt_injections:
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=TargetRuntimeFailureType.PROMPT_INJECTION,
            status=TargetRuntimeStatus.BLOCKED,
            diagnostics=["source corpus contains prompt-injection-tainted content"],
            missing_ref_fields=["trusted_prompt_boundary_ref"],
            extra_policy_refs=corpus.policy_decision_refs,
            observations=observations,
            adapter_records=adapter_records or [],
        )
    if missing_fields:
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=TargetRuntimeFailureType.MISSING_EVIDENCE,
            status=TargetRuntimeStatus.FAILED,
            diagnostics=["source-backed corpus missing required evidence markers"],
            missing_ref_fields=["evidence_refs"],
            extra_policy_refs=corpus.policy_decision_refs,
            observations=observations,
            adapter_records=adapter_records or [],
        )
    adapter_failure = _adapter_backed_failure(
        adapter_manifest=adapter_manifest,
        adapter_records=adapter_records or [],
        observations=observations,
    )
    if adapter_failure is not None:
        failure, status, missing_ref_fields, diagnostics = adapter_failure
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=failure,
            status=status,
            diagnostics=diagnostics,
            missing_ref_fields=missing_ref_fields,
            extra_policy_refs=_adapter_policy_refs(
                corpus.policy_decision_refs,
                adapter_records or [],
                adapter_manifest,
            ),
            observations=observations,
            adapter_records=adapter_records or [],
        )
    if replay_mismatches or scenario == "source-backed-target-replay-mismatch":
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=TargetRuntimeFailureType.REPLAY_MISMATCH,
            status=TargetRuntimeStatus.FAILED,
            diagnostics=["source-backed content hash does not match replay oracle"],
            missing_ref_fields=["replay_bundle_ref"],
            extra_policy_refs=corpus.policy_decision_refs,
            observations=observations,
            adapter_records=adapter_records or [],
        )
    if not corpus.export_complete or scenario == "source-backed-target-partial-export":
        return _source_backed_failure(
            fixture_id=fixture_id,
            failure=TargetRuntimeFailureType.PARTIAL_EXPORT,
            status=TargetRuntimeStatus.FAILED,
            diagnostics=["source-backed export receipt set is incomplete"],
            missing_ref_fields=["export_receipt_refs"],
            extra_policy_refs=corpus.policy_decision_refs,
            observations=observations,
            adapter_records=adapter_records or [],
        )

    return _source_backed_success(
        fixture_id=fixture_id,
        observations=observations,
        repaired_fields=repaired_fields,
        policy_refs=_adapter_policy_refs(
            corpus.policy_decision_refs,
            adapter_records or [],
            adapter_manifest,
        ),
        adapter_records=adapter_records or [],
    )


def _adapter_backed_failure(
    *,
    adapter_manifest: TargetAdapterBackedSourceManifest | None,
    adapter_records: list[TargetAdapterBackedSourceRecord],
    observations: list[TargetSourceObservationRecord],
) -> tuple[TargetRuntimeFailureType, TargetRuntimeStatus, list[str], list[str]] | None:
    if adapter_manifest is None:
        return None
    record_by_entry = {record.corpus_entry_ref: record for record in adapter_records}
    observation_by_entry = {
        observation.corpus_entry_ref: observation for observation in observations
    }
    missing_entries = [
        entry.corpus_entry_ref
        for entry in adapter_manifest.entries
        if entry.corpus_entry_ref not in record_by_entry
    ]
    passing_records = [
        record for record in adapter_records if record.result == CompletenessResult.PASS
    ]
    for record in adapter_records:
        observation = observation_by_entry.get(record.corpus_entry_ref)
        if record.direct_source_bypass_refs:
            return (
                TargetRuntimeFailureType.DIRECT_SOURCE_BYPASS,
                TargetRuntimeStatus.FAILED,
                ["source_adapter_result_refs"],
                ["adapter-backed target runtime detected direct source bypass"],
            )
        if record.missing_adapter_result_refs:
            return (
                TargetRuntimeFailureType.ADAPTER_RESULT_MISSING,
                TargetRuntimeStatus.FAILED,
                ["source_adapter_result_refs"],
                ["adapter-backed target runtime missing source adapter result refs"],
            )
        if record.policy_denied_refs:
            return (
                TargetRuntimeFailureType.POLICY_DENIED,
                TargetRuntimeStatus.BLOCKED,
                ["source_policy_refs"],
                ["adapter-backed source adapter output denied by policy"],
            )
        if record.adapter_output_mismatch_refs:
            return (
                TargetRuntimeFailureType.ADAPTER_OUTPUT_MISMATCH,
                TargetRuntimeStatus.FAILED,
                ["adapter_output_refs"],
                ["adapter-backed source adapter output did not match oracle"],
            )
        if record.replay_mismatch_refs:
            return (
                TargetRuntimeFailureType.REPLAY_MISMATCH,
                TargetRuntimeStatus.FAILED,
                ["replay_bundle_ref"],
                ["adapter-backed source adapter replay refs did not match oracle"],
            )
        if observation is None:
            return (
                TargetRuntimeFailureType.ADAPTER_RESULT_MISSING,
                TargetRuntimeStatus.FAILED,
                ["source_observation_refs"],
                ["adapter-backed source record has no matching source observation"],
            )
        if (
            record.source_observation_ref != observation.source_observation_ref
            or record.content_hash_ref != observation.content_hash_ref
        ):
            return (
                TargetRuntimeFailureType.REPLAY_MISMATCH,
                TargetRuntimeStatus.FAILED,
                ["content_hash_refs"],
                ["adapter-backed source content hash does not match observation"],
            )
    if missing_entries or len(passing_records) < adapter_manifest.expected_adapter_result_count:
        return (
            TargetRuntimeFailureType.ADAPTER_RESULT_MISSING,
            TargetRuntimeStatus.FAILED,
            ["source_adapter_result_refs"],
            ["adapter-backed target runtime missing source adapter result refs"],
        )
    required_types = set(adapter_manifest.required_adapter_types)
    covered_types = {record.adapter_type for record in passing_records}
    if required_types - covered_types:
        return (
            TargetRuntimeFailureType.ADAPTER_RESULT_MISSING,
            TargetRuntimeStatus.FAILED,
            ["source_adapter_result_refs"],
            ["adapter-backed target runtime missing required adapter type refs"],
        )
    return None


def _adapter_policy_refs(
    policy_refs: list[Ref],
    adapter_records: list[TargetAdapterBackedSourceRecord],
    adapter_manifest: TargetAdapterBackedSourceManifest | None,
) -> list[Ref]:
    refs = list(policy_refs)
    if adapter_manifest is not None:
        refs.extend(adapter_manifest.policy_decision_refs)
    for record in adapter_records:
        refs.extend(record.adapter_policy_decision_refs)
    return sorted(set(refs))


def _observe_source_entry(
    *,
    fixture_id: str,
    entry: TargetSourceCorpusEntry,
    content: str,
) -> tuple[TargetSourceObservationRecord, list[Ref], list[Ref], list[Ref]]:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    content_hash_ref = f"sha256:{digest}"
    extracted: list[Ref] = []
    evidence: list[Ref] = []
    repaired: list[Ref] = []
    missing: list[Ref] = []
    replay_mismatch: list[Ref] = []
    for field_name, expected_value in entry.expected_fields.items():
        marker = entry.evidence_markers.get(field_name, expected_value)
        if marker in content or expected_value in content:
            extracted.append(f"field:{fixture_id}:{entry.id}:{field_name}:{digest[:12]}")
            evidence.append(f"evidence:{fixture_id}:{entry.id}:{field_name}:{digest[:12]}")
            continue
        alias = entry.drift_aliases.get(field_name)
        if alias and alias in content:
            extracted.append(f"field:{fixture_id}:{entry.id}:{field_name}:{digest[:12]}")
            evidence.append(f"evidence:{fixture_id}:{entry.id}:{field_name}:alias:{digest[:12]}")
            repaired.append(f"repair-alias:{fixture_id}:{entry.id}:{field_name}")
            continue
        missing.append(f"missing-field:{fixture_id}:{entry.id}:{field_name}")
    if entry.expected_content_hash_ref and entry.expected_content_hash_ref != content_hash_ref:
        replay_mismatch.append(f"replay-mismatch:{fixture_id}:{entry.id}")
    observation = TargetSourceObservationRecord(
        id=f"source-observation-record:{fixture_id}:{entry.id}",
        run_ref=_run_ref(fixture_id),
        corpus_entry_ref=entry.id,
        website_pattern=entry.website_pattern,
        source_path_ref=f"source-path:{fixture_id}:{entry.source_path}",
        content_hash_ref=content_hash_ref,
        source_observation_ref=f"source-observation:{fixture_id}:{entry.id}:{digest[:12]}",
        artifact_ref=f"artifact:{fixture_id}:{entry.id}:{digest[:12]}",
        extracted_field_refs=extracted,
        evidence_refs=evidence,
        graph_refs=[f"graph:{fixture_id}:{entry.id}:{entry.website_pattern.value}"],
        policy_decision_refs=[entry.policy_decision_ref],
        replay_refs=[f"replay:{fixture_id}:{entry.id}:{digest[:12]}"],
        missing_field_refs=missing,
        failure_report_refs=replay_mismatch,
        result=CompletenessResult.FAIL if (missing or replay_mismatch) else CompletenessResult.PASS,
    )
    return observation, repaired, replay_mismatch, missing


def _source_backed_success(
    *,
    fixture_id: str,
    observations: list[TargetSourceObservationRecord],
    repaired_fields: list[Ref],
    policy_refs: list[Ref],
    adapter_records: list[TargetAdapterBackedSourceRecord] | None = None,
) -> TargetRuntimeResult:
    command_refs = _command_refs(fixture_id)
    event_refs = _event_refs(fixture_id) + [f"event-cursor:{fixture_id}:source-backed"]
    outbox_refs = _outbox_refs(fixture_id)
    replay_ref = _replay_ref(fixture_id)
    adapter_record_by_entry = {
        record.corpus_entry_ref: record for record in (adapter_records or [])
    }
    pattern_records = [
        _pattern_record_from_observation(
            fixture_id=fixture_id,
            observation=observation,
            adapter_record=adapter_record_by_entry.get(observation.corpus_entry_ref),
            command_refs=command_refs,
            event_refs=event_refs,
            outbox_refs=outbox_refs,
            replay_ref=replay_ref,
        )
        for observation in observations
    ]
    ai = _accepted_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if repaired_fields
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        repair_refs=repaired_fields,
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=TargetRuntimeStatus.COMPLETE,
        completion_result=CompletenessResult.PASS,
        covered_patterns=[record.website_pattern for record in pattern_records],
        pattern_record_refs=[record.id for record in pattern_records],
        source_observation_refs=[
            observation.source_observation_ref or observation.id
            for observation in observations
        ],
        content_hash_refs=[
            observation.content_hash_ref
            for observation in observations
            if observation.content_hash_ref is not None
        ],
        adapter_backed_source_refs=[record.id for record in adapter_records or []],
        source_adapter_result_refs=[
            record.source_adapter_result_ref
            for record in adapter_records or []
            if record.source_adapter_result_ref is not None
        ],
        adapter_output_refs=[
            output_ref
            for record in adapter_records or []
            for output_ref in record.adapter_output_refs
        ],
        accepted_output_refs=_collect(pattern_records, "accepted_output_refs"),
        evidence_refs=_collect(pattern_records, "evidence_refs"),
        verification_refs=_collect(pattern_records, "verification_refs"),
        graph_refs=_collect(pattern_records, "graph_refs"),
        export_receipt_refs=[f"export-receipt:{fixture_id}:source-backed"],
        output_manifest_refs=[f"output-manifest:{fixture_id}:source-backed"],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=_collect(pattern_records, "artifact_refs"),
        ai_recommendation_refs=[ai.id],
        repair_action_refs=repaired_fields,
        recovery_action_refs=[f"recovery-action:{fixture_id}:source-backed"],
        privacy_lifecycle_refs=[f"privacy:{fixture_id}:source-backed"],
        replay_bundle_ref=replay_ref,
        operator_status=(
            "adapter_backed_target_runtime_completed"
            if adapter_records
            else "source_backed_target_runtime_completed"
        ),
    )
    return TargetRuntimeResult(pattern_records, [ai], report, observations, adapter_records or [])


def _source_backed_failure(
    *,
    fixture_id: str,
    failure: TargetRuntimeFailureType,
    status: TargetRuntimeStatus,
    diagnostics: list[str],
    missing_ref_fields: list[str],
    extra_policy_refs: list[Ref],
    observations: list[TargetSourceObservationRecord],
    adapter_records: list[TargetAdapterBackedSourceRecord] | None = None,
) -> TargetRuntimeResult:
    ai = _blocked_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if failure == TargetRuntimeFailureType.PROMPT_INJECTION
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        blocked_ref=f"blocked-action:{fixture_id}:{failure.value}",
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=status,
        completion_result=CompletenessResult.FAIL,
        source_observation_refs=[
            observation.source_observation_ref or observation.id for observation in observations
        ],
        content_hash_refs=[
            observation.content_hash_ref
            for observation in observations
            if observation.content_hash_ref is not None
        ],
        adapter_backed_source_refs=[record.id for record in adapter_records or []],
        source_adapter_result_refs=[
            record.source_adapter_result_ref
            for record in adapter_records or []
            if record.source_adapter_result_ref is not None
        ],
        adapter_output_refs=[
            output_ref
            for record in adapter_records or []
            for output_ref in record.adapter_output_refs
        ],
        policy_decision_refs=extra_policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        ai_recommendation_refs=[ai.id],
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=missing_ref_fields,
        diagnostics=diagnostics,
        operator_status=failure.value,
    )
    return TargetRuntimeResult([], [ai], report, observations, adapter_records or [])


def _pattern_record_from_observation(
    *,
    fixture_id: str,
    observation: TargetSourceObservationRecord,
    adapter_record: TargetAdapterBackedSourceRecord | None,
    command_refs: list[Ref],
    event_refs: list[Ref],
    outbox_refs: list[Ref],
    replay_ref: Ref,
) -> TargetCrawlPatternRecord:
    suffix = observation.website_pattern.value
    digest_part = (observation.content_hash_ref or "sha256:unknown").removeprefix("sha256:")[:12]
    source_adapter_result_refs = (
        [adapter_record.source_adapter_result_ref]
        if adapter_record is not None and adapter_record.source_adapter_result_ref is not None
        else [f"source-result:{fixture_id}:{observation.corpus_entry_ref}"]
    )
    adapter_output_refs = adapter_record.adapter_output_refs if adapter_record is not None else []
    policy_refs = list(observation.policy_decision_refs)
    replay_refs = [replay_ref, *observation.replay_refs]
    pattern_specific_refs: dict[str, Ref] = {
        "source_path_ref": observation.source_path_ref,
        "content_hash_ref": observation.content_hash_ref or f"hash-missing:{fixture_id}",
        "general_pattern_ref": f"pattern:{suffix}",
    }
    if adapter_record is not None:
        policy_refs = sorted(set(policy_refs + adapter_record.adapter_policy_decision_refs))
        replay_refs.extend(adapter_record.adapter_replay_refs)
        pattern_specific_refs["adapter_backed_source_ref"] = adapter_record.id
        if adapter_record.source_adapter_result_ref is not None:
            pattern_specific_refs["source_adapter_result_ref"] = (
                adapter_record.source_adapter_result_ref
            )
    return TargetCrawlPatternRecord(
        id=f"target-pattern:{fixture_id}:{observation.corpus_entry_ref}:{digest_part}",
        run_ref=_run_ref(fixture_id),
        website_pattern=observation.website_pattern,
        frontier_item_refs=[f"frontier:{fixture_id}:{observation.corpus_entry_ref}"],
        source_observation_refs=[observation.source_observation_ref or observation.id],
        source_adapter_result_refs=source_adapter_result_refs,
        extraction_result_refs=observation.extracted_field_refs,
        accepted_output_refs=[
            f"accepted-output:{fixture_id}:{observation.corpus_entry_ref}:{digest_part}"
        ],
        evidence_refs=observation.evidence_refs,
        verification_refs=[f"verification:{fixture_id}:{observation.corpus_entry_ref}:{digest_part}"],
        graph_refs=observation.graph_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=(
            ([observation.artifact_ref] if observation.artifact_ref else [])
            + adapter_output_refs
        ),
        replay_refs=replay_refs,
        operator_visible_refs=[f"operator-result:{fixture_id}:{observation.corpus_entry_ref}"],
        pattern_specific_refs=pattern_specific_refs,
        result=CompletenessResult.PASS,
    )


def _pattern_record(
    *,
    fixture_id: str,
    pattern: TargetWebsitePattern,
    policy_refs: list[Ref],
    command_refs: list[Ref],
    event_refs: list[Ref],
    outbox_refs: list[Ref],
    replay_ref: Ref,
) -> TargetCrawlPatternRecord:
    suffix = pattern.value
    return TargetCrawlPatternRecord(
        id=f"target-pattern:{fixture_id}:{suffix}",
        run_ref=_run_ref(fixture_id),
        website_pattern=pattern,
        frontier_item_refs=[f"frontier:{fixture_id}:{suffix}"],
        source_observation_refs=[f"source-observation:{fixture_id}:{suffix}"],
        source_adapter_result_refs=[f"source-result:{fixture_id}:{suffix}"],
        extraction_result_refs=[f"extraction:{fixture_id}:{suffix}"],
        accepted_output_refs=[f"accepted-output:{fixture_id}:{suffix}"],
        evidence_refs=[f"evidence:{fixture_id}:{suffix}"],
        verification_refs=[f"verification:{fixture_id}:{suffix}"],
        graph_refs=[f"graph:{fixture_id}:{suffix}"],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=[f"artifact:{fixture_id}:{suffix}:raw"],
        replay_refs=[replay_ref, f"replay:{fixture_id}:{suffix}"],
        operator_visible_refs=[f"operator-result:{fixture_id}:{suffix}"],
        pattern_specific_refs=_pattern_specific_refs(fixture_id, pattern),
        result=CompletenessResult.PASS,
    )


def _accepted_ai_recommendation(
    *,
    fixture_id: str,
    subject: AgentRecommendationSubject,
    repair_refs: list[Ref],
) -> TargetAIRecommendationRecord:
    return TargetAIRecommendationRecord(
        id=f"target-ai:{fixture_id}:{subject.value}",
        run_ref=_run_ref(fixture_id),
        subject=subject,
        recommendation_ref=f"agent-recommendation:{fixture_id}:{subject.value}",
        accepted=True,
        policy_decision_refs=[f"policy:{fixture_id}:agent-tool"],
        tool_call_refs=[f"tool-call:{fixture_id}:{subject.value}"],
        trace_refs=[f"agent-trace:{fixture_id}:{subject.value}"],
        repair_frontier_refs=repair_refs,
        result=CompletenessResult.PASS,
    )


def _blocked_ai_recommendation(
    *,
    fixture_id: str,
    subject: AgentRecommendationSubject,
    blocked_ref: Ref,
) -> TargetAIRecommendationRecord:
    return TargetAIRecommendationRecord(
        id=f"target-ai:{fixture_id}:{subject.value}:blocked",
        run_ref=_run_ref(fixture_id),
        subject=subject,
        recommendation_ref=f"agent-recommendation:{fixture_id}:{subject.value}:blocked",
        accepted=False,
        policy_decision_refs=[f"policy:{fixture_id}:agent-tool-denied"],
        blocked_action_refs=[blocked_ref],
        result=CompletenessResult.FAIL,
    )


def _pattern_specific_refs(
    fixture_id: str,
    pattern: TargetWebsitePattern,
) -> dict[str, Ref]:
    suffix = pattern.value
    return {
        "fixture_ref": f"fixture:{fixture_id}:{suffix}",
        "oracle_ref": f"oracle:{fixture_id}:{suffix}",
        "general_pattern_ref": f"pattern:{suffix}",
    }


def _collect(records: list[TargetCrawlPatternRecord], field_name: str) -> list[Ref]:
    values: list[Ref] = []
    for record in records:
        field_value = getattr(record, field_name)
        if isinstance(field_value, list):
            values.extend(field_value)
    return values


def _missing_fields_for(failure: TargetRuntimeFailureType) -> list[str]:
    return {
        TargetRuntimeFailureType.POLICY_DENIED: ["source_policy_refs"],
        TargetRuntimeFailureType.PROMPT_INJECTION: ["trusted_prompt_boundary_ref"],
        TargetRuntimeFailureType.MISSING_EVIDENCE: ["evidence_refs"],
        TargetRuntimeFailureType.REPLAY_MISMATCH: ["replay_bundle_ref"],
        TargetRuntimeFailureType.PARTIAL_EXPORT: ["export_receipt_refs"],
        TargetRuntimeFailureType.FALSE_COMPLETE: ["status_accuracy_refs"],
        TargetRuntimeFailureType.DRIFT_REPAIR_REQUIRED: ["repair_action_refs"],
        TargetRuntimeFailureType.ORACLE_MISMATCH: ["oracle_refs"],
        TargetRuntimeFailureType.ADAPTER_RESULT_MISSING: ["source_adapter_result_refs"],
        TargetRuntimeFailureType.ADAPTER_OUTPUT_MISMATCH: ["adapter_output_refs"],
        TargetRuntimeFailureType.DIRECT_SOURCE_BYPASS: ["source_adapter_result_refs"],
    }[failure]


def _run_ref(fixture_id: str) -> Ref:
    return f"run:{fixture_id}"


def _policy_refs(fixture_id: str) -> list[Ref]:
    return [
        f"policy:{fixture_id}:source",
        f"policy:{fixture_id}:prompt-boundary",
        f"policy:{fixture_id}:publication",
        f"policy:{fixture_id}:export",
    ]


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:target-runtime"]


def _event_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:target-runtime"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:target-runtime"]


def _replay_ref(fixture_id: str) -> Ref:
    return f"replay-bundle:{fixture_id}:target-runtime"
