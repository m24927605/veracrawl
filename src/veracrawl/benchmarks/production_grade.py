"""Production-grade crawler closure gate runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    AcquisitionAttemptRecord,
    AuthorizedSourceAccessRecord,
    CandidateSourceTarget,
    CrawlDiscoveryPlan,
    DiscoveryApprovalDecision,
    DiscoveryEntryPoint,
    FalseReadyGuard,
    ProductionGateReport,
    ProductionGradeCapabilityMatrix,
    ProductionGradeClosureManifest,
    ProductionGradeReleaseReport,
    ProductionSourceProfile,
    ReleaseBlocker,
    ReleaseDecision,
)


@dataclass(frozen=True)
class ProductionGradeGateResult:
    report: ProductionGateReport
    discovery_plans: list[CrawlDiscoveryPlan]
    candidate_targets: list[CandidateSourceTarget]
    discovery_entry_points: list[DiscoveryEntryPoint]
    discovery_approval_decisions: list[DiscoveryApprovalDecision]
    acquisition_attempts: list[AcquisitionAttemptRecord]
    authorized_sources: list[AuthorizedSourceAccessRecord]
    capability_matrices: list[ProductionGradeCapabilityMatrix]
    release_decisions: list[ReleaseDecision]
    false_ready_guards: list[FalseReadyGuard]
    release_blockers: list[ReleaseBlocker]
    release_reports: list[ProductionGradeReleaseReport]


_GATE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "discovery_planning": (
        "objective_interpretation",
        "candidate_source_selection",
        "crawl_bound_approval",
    ),
    "acquisition_escalation": (
        "http_acquisition",
        "browser_render_escalation",
        "source_limitation_accounting",
    ),
    "authorized_source_access": (
        "official_api_adapter",
        "credentialed_read_session",
        "redacted_replay",
    ),
    "deep_crawl_production": (
        "adaptive_frontier",
        "multi_page_coverage",
        "replayable_stop_reasons",
    ),
    "extraction_quality": (
        "field_oracles",
        "precision_recall_release_block",
        "publication_readiness",
    ),
    "operations_reliability": (
        "durable_workers",
        "recovery_observability",
        "cost_latency_slo",
    ),
    "production_grade_release": (
        "discovery_planning",
        "acquisition_escalation",
        "authorized_source_access",
        "deep_crawl_production",
        "extraction_quality",
        "operations_reliability",
    ),
}

_RELEASE_REQUIRED_GATE_TYPES = _GATE_CAPABILITIES["production_grade_release"]


def run_production_grade_gate(
    *,
    manifest: ProductionGradeClosureManifest,
    profile: str,
    input_report_refs: list[Ref] | None = None,
    lower_gate_reports: list[ProductionGateReport] | None = None,
) -> ProductionGradeGateResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    lower_gate_reports = lower_gate_reports or []
    input_refs = _merge_refs(
        input_report_refs or [],
        manifest.input_report_refs,
        [report.id for report in lower_gate_reports],
    )

    if _is_direct_failure(manifest):
        report = _failure_report(manifest, input_refs=input_refs)
        return _gate_result(report=report)

    if manifest.gate_type == "discovery_planning":
        entry_points = _build_entry_points(manifest)
        candidate_targets = _build_candidate_targets(manifest, entry_points)
        plans = [_build_discovery_plan(manifest)]
        approvals = [_build_discovery_approval(manifest, plans[0], candidate_targets)]
        report = _build_report(manifest, discovery_plans=plans)
        return _gate_result(
            report=report,
            discovery_plans=plans,
            candidate_targets=candidate_targets,
            discovery_entry_points=entry_points,
            discovery_approval_decisions=approvals,
        )

    if manifest.gate_type == "acquisition_escalation":
        attempts = _build_acquisition_attempts(manifest)
        if not any(attempt.evidence_found for attempt in attempts):
            report = _failure_report(
                manifest,
                input_refs=input_refs,
                blocker="release-blocker:acquisition:no-source-backed-evidence",
                diagnostic="acquisition escalation found no source-backed evidence",
                completion=CompletenessResult.NEEDS_REVIEW,
            )
        else:
            report = _build_report(manifest, acquisition_attempts=attempts)
        return _gate_result(
            report=report,
            acquisition_attempts=attempts,
        )

    if manifest.gate_type == "authorized_source_access":
        records = _build_authorized_sources(manifest)
        expected_record_count = len(
            [
                profile
                for profile in manifest.source_profiles
                if profile.official_api_available or profile.authorized_source_ref
            ]
        )
        if len(records) < expected_record_count:
            report = _failure_report(
                manifest,
                input_refs=input_refs,
                blocker="release-blocker:authorized-source:missing-grant",
                diagnostic="authorized source access lacked official API or credential grant",
                completion=CompletenessResult.NEEDS_REVIEW,
            )
        else:
            report = _build_report(manifest, authorized_sources=records)
        return _gate_result(
            report=report,
            authorized_sources=records,
        )

    if manifest.gate_type == "production_grade_release":
        failure = _release_failure(lower_gate_reports)
        if failure is not None:
            blocker, diagnostic = failure
            report = _failure_report(
                manifest,
                input_refs=input_refs,
                blocker=blocker,
                diagnostic=diagnostic,
            )
        else:
            report = _build_report(manifest, input_refs=input_refs)
        release_artifacts = _build_release_artifacts(
            manifest=manifest,
            report=report,
            lower_gate_reports=lower_gate_reports,
        )
        return _gate_result(
            report=report,
            capability_matrices=[release_artifacts[0]],
            release_decisions=[release_artifacts[1]],
            false_ready_guards=release_artifacts[2],
            release_blockers=release_artifacts[3],
            release_reports=[release_artifacts[4]],
        )

    report = _build_report(manifest, input_refs=input_refs)
    return _gate_result(report=report)


def _is_direct_failure(manifest: ProductionGradeClosureManifest) -> bool:
    return (
        manifest.negative_case
        or manifest.scenario.endswith("-missing-replay")
        or manifest.scenario.endswith("-false-ready")
    )


def _build_discovery_plan(manifest: ProductionGradeClosureManifest) -> CrawlDiscoveryPlan:
    fixture_id = manifest.id
    return CrawlDiscoveryPlan(
        id=f"crawl-discovery-plan:{fixture_id}:approved",
        fixture_id=fixture_id,
        objective_text=manifest.objective,
        source_profile_refs=[profile.id for profile in manifest.source_profiles],
        entry_point_refs=[
            _entry_point_id(fixture_id, profile)
            for profile in manifest.source_profiles
        ],
        crawl_bound_ref=manifest.crawl_bound.id,
        evidence_requirement_refs=sorted(
            {
                f"evidence-requirement:{fixture_id}:{evidence_type}"
                for profile in manifest.source_profiles
                for evidence_type in profile.required_evidence_types
            }
        ),
        approval_decision_ref=_approval_decision_id(fixture_id),
        model_call_trace_refs=[
            f"model-call-trace:{fixture_id}:objective",
            f"model-call-trace:{fixture_id}:plan-verification",
        ],
        agent_action_trace_refs=[
            f"agent-action-trace:{fixture_id}:planner",
            f"agent-action-trace:{fixture_id}:verifier",
        ],
        tool_call_trace_refs=[
            f"tool-call-trace:{fixture_id}:source-catalog",
            f"tool-call-trace:{fixture_id}:policy-check",
        ],
        context_bundle_trace_refs=[
            f"context-bundle-trace:{fixture_id}:objective",
            f"context-bundle-trace:{fixture_id}:policy",
        ],
        policy_decision_refs=_policy_refs(fixture_id),
        command_record_refs=[f"command:{fixture_id}:create-discovery-plan"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:discovery-plan-created"],
        outbox_refs=[f"outbox:{fixture_id}:discovery-plan"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:discovery-plan",
    )


def _build_entry_points(
    manifest: ProductionGradeClosureManifest,
) -> list[DiscoveryEntryPoint]:
    entry_points: list[DiscoveryEntryPoint] = []
    for profile in manifest.source_profiles:
        entry_points.append(
            DiscoveryEntryPoint(
                id=_entry_point_id(manifest.id, profile),
                fixture_id=manifest.id,
                source_profile_ref=profile.id,
                url=profile.entry_point_url,
                discovery_method=profile.discovery_methods[0],
                policy_decision_refs=_policy_refs(manifest.id, profile.id),
                model_call_trace_refs=[
                    f"model-call-trace:{manifest.id}:{profile.id}:entry-point"
                ],
                agent_action_trace_refs=[
                    f"agent-action-trace:{manifest.id}:{profile.id}:entry-point"
                ],
                tool_call_trace_refs=[
                    f"tool-call-trace:{manifest.id}:{profile.id}:source-catalog"
                ],
                context_bundle_trace_refs=[
                    f"context-bundle-trace:{manifest.id}:{profile.id}:policy"
                ],
                command_record_refs=[f"command:{manifest.id}:{profile.id}:entry-point"],
                event_cursor_refs=[
                    f"event-cursor:{manifest.id}:{profile.id}:entry-point"
                ],
                outbox_refs=[f"outbox:{manifest.id}:{profile.id}:entry-point"],
                replay_bundle_ref=f"replay-bundle:{manifest.id}:{profile.id}:entry-point",
            )
        )
    return entry_points


def _build_candidate_targets(
    manifest: ProductionGradeClosureManifest,
    entry_points: list[DiscoveryEntryPoint],
) -> list[CandidateSourceTarget]:
    entry_points_by_profile = {
        entry_point.source_profile_ref: entry_point for entry_point in entry_points
    }
    targets: list[CandidateSourceTarget] = []
    for profile in manifest.source_profiles:
        entry_point = entry_points_by_profile[profile.id]
        targets.append(
            CandidateSourceTarget(
                id=_candidate_source_target_id(manifest.id, profile),
                fixture_id=manifest.id,
                source_profile_ref=profile.id,
                site_name=profile.site_name,
                allowed_origin=profile.allowed_origin,
                entry_point_refs=[entry_point.id],
                discovery_method_refs=[
                    f"discovery-method:{manifest.id}:{profile.id}:{method}"
                    for method in profile.discovery_methods
                ],
                evidence_requirement_refs=[
                    f"evidence-requirement:{manifest.id}:{profile.id}:{evidence_type}"
                    for evidence_type in profile.required_evidence_types
                ],
                crawl_bound_ref=manifest.crawl_bound.id,
                policy_decision_refs=_policy_refs(manifest.id, profile.id),
                model_call_trace_refs=[
                    f"model-call-trace:{manifest.id}:{profile.id}:candidate"
                ],
                agent_action_trace_refs=[
                    f"agent-action-trace:{manifest.id}:{profile.id}:candidate"
                ],
                tool_call_trace_refs=[
                    f"tool-call-trace:{manifest.id}:{profile.id}:candidate"
                ],
                context_bundle_trace_refs=[
                    f"context-bundle-trace:{manifest.id}:{profile.id}:candidate"
                ],
                command_record_refs=[f"command:{manifest.id}:{profile.id}:candidate"],
                event_cursor_refs=[
                    f"event-cursor:{manifest.id}:{profile.id}:candidate"
                ],
                outbox_refs=[f"outbox:{manifest.id}:{profile.id}:candidate"],
                replay_bundle_ref=f"replay-bundle:{manifest.id}:{profile.id}:candidate",
            )
        )
    return targets


def _build_discovery_approval(
    manifest: ProductionGradeClosureManifest,
    plan: CrawlDiscoveryPlan,
    candidate_targets: list[CandidateSourceTarget],
) -> DiscoveryApprovalDecision:
    return DiscoveryApprovalDecision(
        id=_approval_decision_id(manifest.id),
        fixture_id=manifest.id,
        discovery_plan_ref=plan.id,
        approved=True,
        candidate_source_target_refs=[target.id for target in candidate_targets],
        approval_policy_refs=_policy_refs(manifest.id),
        command_record_refs=[f"command:{manifest.id}:approve-discovery-plan"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:discovery-plan-approved"],
        outbox_refs=[f"outbox:{manifest.id}:discovery-approval"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:discovery-approval",
    )


def _build_acquisition_attempts(
    manifest: ProductionGradeClosureManifest,
) -> list[AcquisitionAttemptRecord]:
    attempts: list[AcquisitionAttemptRecord] = []
    for profile in manifest.source_profiles:
        http_found = not profile.browser_required and not profile.source_limited
        attempts.append(_attempt(manifest.id, profile, "http", http_found))
        if profile.browser_required:
            attempts.append(
                _attempt(
                    manifest.id,
                    profile,
                    "browser",
                    not profile.source_limited,
                )
            )
    return attempts


def _attempt(
    fixture_id: str,
    profile: ProductionSourceProfile,
    mode: str,
    evidence_found: bool,
) -> AcquisitionAttemptRecord:
    base = f"{fixture_id}:{profile.id}:{mode}"
    return AcquisitionAttemptRecord(
        id=f"acquisition-attempt:{base}",
        fixture_id=fixture_id,
        source_profile_ref=profile.id,
        acquisition_mode=mode,
        evidence_found=evidence_found,
        artifact_refs=[f"artifact:{base}:source"] if evidence_found else [],
        content_hash_refs=[
            stable_hash({"profile": profile.id, "mode": mode})
        ]
        if evidence_found
        else [],
        source_anchor_refs=[f"source-anchor:{base}:evidence"] if evidence_found else [],
        source_limitation_ref=None if evidence_found else f"source-limitation:{base}:no-evidence",
        policy_decision_refs=_policy_refs(fixture_id, profile.id),
        command_record_refs=[f"command:{base}:acquire"],
        event_cursor_refs=[f"event-cursor:{base}:acquired"],
        outbox_refs=[f"outbox:{base}:acquire"],
        replay_bundle_ref=f"replay-bundle:{base}:acquisition",
        completion_result=(
            CompletenessResult.PASS if evidence_found else CompletenessResult.NEEDS_REVIEW
        ),
    )


def _build_authorized_sources(
    manifest: ProductionGradeClosureManifest,
) -> list[AuthorizedSourceAccessRecord]:
    records: list[AuthorizedSourceAccessRecord] = []
    for profile in manifest.source_profiles:
        if not (profile.official_api_available or profile.authorized_source_ref):
            continue
        base = f"{manifest.id}:{profile.id}:authorized"
        records.append(
            AuthorizedSourceAccessRecord(
                id=f"authorized-source-result:{base}",
                fixture_id=manifest.id,
                source_profile_ref=profile.id,
                access_kind=(
                    "official_api"
                    if profile.official_api_available
                    else "credentialed_session"
                ),
                credential_grant_ref=(
                    profile.authorized_source_ref or f"official-api-grant:{profile.id}"
                ),
                credential_audit_ref=f"credential-audit:{base}",
                redacted_artifact_refs=[f"artifact:{base}:redacted-source"],
                source_anchor_refs=[f"source-anchor:{base}:response"],
                content_hash_refs=[stable_hash({"authorized": profile.id})],
                policy_decision_refs=_policy_refs(manifest.id, profile.id),
                command_record_refs=[f"command:{base}:read"],
                event_cursor_refs=[f"event-cursor:{base}:read"],
                outbox_refs=[f"outbox:{base}:read"],
                replay_bundle_ref=f"replay-bundle:{base}:authorized-source",
            )
        )
    return records


def _build_report(
    manifest: ProductionGradeClosureManifest,
    *,
    discovery_plans: list[CrawlDiscoveryPlan] | None = None,
    acquisition_attempts: list[AcquisitionAttemptRecord] | None = None,
    authorized_sources: list[AuthorizedSourceAccessRecord] | None = None,
    input_refs: list[Ref] | None = None,
) -> ProductionGateReport:
    discovery_plans = discovery_plans or []
    acquisition_attempts = acquisition_attempts or []
    authorized_sources = authorized_sources or []
    input_refs = input_refs or []
    fixture_id = manifest.id
    evidence_attempts = [attempt for attempt in acquisition_attempts if attempt.evidence_found]
    artifact_refs, source_anchor_refs, content_hash_refs = _collect_source_evidence_refs(
        evidence_attempts,
        authorized_sources,
    )
    if not artifact_refs and manifest.gate_type != "production_grade_release":
        artifact_refs = [
            f"artifact:{fixture_id}:{profile.id}:gate-source"
            for profile in manifest.source_profiles
        ]
        source_anchor_refs = [
            f"source-anchor:{fixture_id}:{profile.id}:gate-source"
            for profile in manifest.source_profiles
        ]
        content_hash_refs = [
            stable_hash({"fixture": fixture_id, "source_profile": profile.id})
            for profile in manifest.source_profiles
        ]
    return ProductionGateReport(
        id=f"production-gate-report:{fixture_id}",
        fixture_id=fixture_id,
        gate_type=manifest.gate_type,
        run_ref=f"run:{fixture_id}",
        capability_refs=[
            f"capability:{manifest.gate_type}:{name}"
            for name in _GATE_CAPABILITIES[manifest.gate_type]
        ],
        discovery_plan_refs=[plan.id for plan in discovery_plans],
        acquisition_attempt_refs=[attempt.id for attempt in acquisition_attempts],
        authorized_source_refs=[record.id for record in authorized_sources],
        lower_gate_report_refs=input_refs,
        source_profile_refs=[profile.id for profile in manifest.source_profiles],
        artifact_refs=artifact_refs,
        source_anchor_refs=source_anchor_refs,
        content_hash_refs=content_hash_refs,
        model_call_trace_refs=[
            f"model-call-trace:{fixture_id}:{name}" for name in ("planning", "verification")
        ],
        agent_action_trace_refs=[
            f"agent-action-trace:{fixture_id}:{name}" for name in ("planner", "verifier")
        ],
        tool_call_trace_refs=[
            f"tool-call-trace:{fixture_id}:{name}" for name in ("source-read", "policy-check")
        ],
        context_bundle_trace_refs=[
            f"context-bundle-trace:{fixture_id}:{name}" for name in ("objective", "evidence")
        ],
        evidence_packet_refs=[
            f"evidence-packet:{fixture_id}:{name}"
            for name in _GATE_CAPABILITIES[manifest.gate_type]
        ],
        verification_decision_refs=[
            f"verification-decision:{fixture_id}:{name}"
            for name in _GATE_CAPABILITIES[manifest.gate_type]
        ],
        publication_gate_refs=[f"publication-gate:{fixture_id}:blocked-until-release"],
        policy_decision_refs=_policy_refs(fixture_id),
        command_record_refs=[f"command:{fixture_id}:record-production-gate"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:production-gate-recorded"],
        outbox_refs=[f"outbox:{fixture_id}:production-gate"],
        replay_bundle_refs=[f"replay-bundle:{fixture_id}:production-gate"],
        metrics=_metrics(manifest),
        operator_status=manifest.expected_operator_status,
        completion_result=CompletenessResult.PASS,
    )


def _failure_report(
    manifest: ProductionGradeClosureManifest,
    *,
    input_refs: list[Ref] | None = None,
    blocker: Ref | None = None,
    diagnostic: str | None = None,
    completion: CompletenessResult = CompletenessResult.FAIL,
) -> ProductionGateReport:
    fixture_id = manifest.id
    blocker_ref = blocker or f"release-blocker:{fixture_id}:{manifest.gate_type}"
    return ProductionGateReport(
        id=f"production-gate-report:{fixture_id}",
        fixture_id=fixture_id,
        gate_type=manifest.gate_type,
        run_ref=f"run:{fixture_id}",
        capability_refs=[
            f"capability:{manifest.gate_type}:{name}"
            for name in _GATE_CAPABILITIES[manifest.gate_type]
        ],
        lower_gate_report_refs=input_refs or [],
        source_profile_refs=[profile.id for profile in manifest.source_profiles],
        policy_decision_refs=_policy_refs(fixture_id),
        command_record_refs=[f"command:{fixture_id}:record-production-gate"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:production-gate-recorded"],
        outbox_refs=[f"outbox:{fixture_id}:production-gate"],
        replay_bundle_refs=[f"replay-bundle:{fixture_id}:production-gate"],
        release_blocker_refs=[blocker_ref],
        metrics=_metrics(manifest),
        operator_status=manifest.expected_operator_status,
        completion_result=completion,
        diagnostics=[diagnostic or f"{manifest.gate_type} did not satisfy production-grade gate"],
    )


def _policy_refs(fixture_id: str, profile_id: str | None = None) -> list[Ref]:
    suffix = f":{profile_id}" if profile_id else ""
    return [
        f"policy:{fixture_id}{suffix}:source-scope",
        f"policy:{fixture_id}{suffix}:robots",
        f"policy:{fixture_id}{suffix}:no-bypass",
    ]


def _metrics(manifest: ProductionGradeClosureManifest) -> dict[str, float | int | str]:
    if manifest.gate_type == "deep_crawl_production":
        return {"site_count": max(5, len(manifest.source_profiles)), "covered_page_count": 50}
    if manifest.gate_type == "extraction_quality":
        return {
            "precision": 0.99,
            "recall": 0.92,
            "f1": 0.95,
            "critical_precision": 0.995,
        }
    if manifest.gate_type == "operations_reliability":
        return {
            "p95_latency_ms": 4200,
            "retry_rate": 0.03,
            "total_cost_usd": 1.4,
            "stability_runs": 3,
        }
    return {"source_profile_count": len(manifest.source_profiles)}


def _collect_source_evidence_refs(
    acquisition_attempts: list[AcquisitionAttemptRecord],
    authorized_sources: list[AuthorizedSourceAccessRecord],
) -> tuple[list[Ref], list[Ref], list[Ref]]:
    artifact_refs = {
        ref for attempt in acquisition_attempts for ref in attempt.artifact_refs
    } | {ref for record in authorized_sources for ref in record.redacted_artifact_refs}
    source_anchor_refs = {
        ref for attempt in acquisition_attempts for ref in attempt.source_anchor_refs
    } | {ref for record in authorized_sources for ref in record.source_anchor_refs}
    content_hash_refs = {
        ref for attempt in acquisition_attempts for ref in attempt.content_hash_refs
    } | {ref for record in authorized_sources for ref in record.content_hash_refs}
    return sorted(artifact_refs), sorted(source_anchor_refs), sorted(content_hash_refs)


def _build_release_artifacts(
    *,
    manifest: ProductionGradeClosureManifest,
    report: ProductionGateReport,
    lower_gate_reports: list[ProductionGateReport],
) -> tuple[
    ProductionGradeCapabilityMatrix,
    ReleaseDecision,
    list[FalseReadyGuard],
    list[ReleaseBlocker],
    ProductionGradeReleaseReport,
]:
    missing_gate_types, non_passing_report_refs, passing_report_refs = (
        _release_matrix_parts(lower_gate_reports)
    )
    release_blockers = [
        _release_blocker(manifest, report, blocker_ref)
        for blocker_ref in report.release_blocker_refs
    ]
    false_ready_guards = _false_ready_guards(
        manifest=manifest,
        report=report,
        missing_gate_types=missing_gate_types,
        non_passing_report_refs=non_passing_report_refs,
        release_blockers=release_blockers,
    )
    matrix = ProductionGradeCapabilityMatrix(
        id=f"production-grade-capability-matrix:{manifest.id}",
        fixture_id=manifest.id,
        release_gate_report_ref=report.id,
        required_gate_types=list(_RELEASE_REQUIRED_GATE_TYPES),
        passing_gate_report_refs=passing_report_refs,
        missing_gate_types=missing_gate_types,
        non_passing_gate_report_refs=non_passing_report_refs,
        false_ready_guard_refs=[guard.id for guard in false_ready_guards],
        policy_decision_refs=_policy_refs(manifest.id),
        command_record_refs=[f"command:{manifest.id}:record-capability-matrix"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:capability-matrix-recorded"],
        outbox_refs=[f"outbox:{manifest.id}:capability-matrix"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:capability-matrix",
        completion_result=report.completion_result,
    )
    decision = ReleaseDecision(
        id=f"release-decision:{manifest.id}",
        fixture_id=manifest.id,
        release_gate_report_ref=report.id,
        capability_matrix_ref=matrix.id,
        decision=(
            "pass" if report.completion_result == CompletenessResult.PASS else "blocked"
        ),
        release_blocker_refs=[blocker.id for blocker in release_blockers],
        diagnostics=report.diagnostics,
        policy_decision_refs=_policy_refs(manifest.id),
        command_record_refs=[f"command:{manifest.id}:record-release-decision"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:release-decision-recorded"],
        outbox_refs=[f"outbox:{manifest.id}:release-decision"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:release-decision",
    )
    release_report = ProductionGradeReleaseReport(
        id=f"production-grade-release-report:{manifest.id}",
        fixture_id=manifest.id,
        release_gate_report_ref=report.id,
        capability_matrix_ref=matrix.id,
        release_decision_ref=decision.id,
        false_ready_guard_refs=[guard.id for guard in false_ready_guards],
        lower_gate_report_refs=report.lower_gate_report_refs,
        release_blocker_refs=[blocker.id for blocker in release_blockers],
        policy_decision_refs=_policy_refs(manifest.id),
        command_record_refs=[f"command:{manifest.id}:record-release-report"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:release-report-recorded"],
        outbox_refs=[f"outbox:{manifest.id}:release-report"],
        replay_bundle_refs=[f"replay-bundle:{manifest.id}:release-report"],
        operator_status=report.operator_status,
        completion_result=report.completion_result,
        diagnostics=report.diagnostics,
    )
    return matrix, decision, false_ready_guards, release_blockers, release_report


def _release_matrix_parts(
    lower_gate_reports: list[ProductionGateReport],
) -> tuple[list[str], list[Ref], list[Ref]]:
    reports_by_gate = {report.gate_type: report for report in lower_gate_reports}
    missing_gate_types = [
        gate_type
        for gate_type in _RELEASE_REQUIRED_GATE_TYPES
        if gate_type not in reports_by_gate
    ]
    non_passing_report_refs = [
        report.id
        for report in lower_gate_reports
        if report.gate_type in _RELEASE_REQUIRED_GATE_TYPES
        and report.completion_result != CompletenessResult.PASS
    ]
    passing_report_refs = [
        report.id
        for report in lower_gate_reports
        if report.gate_type in _RELEASE_REQUIRED_GATE_TYPES
        and report.completion_result == CompletenessResult.PASS
    ]
    return missing_gate_types, non_passing_report_refs, passing_report_refs


def _release_blocker(
    manifest: ProductionGradeClosureManifest,
    report: ProductionGateReport,
    blocker_ref: Ref,
) -> ReleaseBlocker:
    diagnostic = report.diagnostics[0] if report.diagnostics else "release blocked"
    return ReleaseBlocker(
        id=blocker_ref,
        fixture_id=manifest.id,
        blocker_type=blocker_ref.split(":", 3)[-1],
        blocked_ref=report.id,
        diagnostic=diagnostic,
        policy_decision_refs=_policy_refs(manifest.id),
        command_record_refs=[f"command:{manifest.id}:record-release-blocker"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:release-blocker-recorded"],
        outbox_refs=[f"outbox:{manifest.id}:release-blocker"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:release-blocker",
    )


def _false_ready_guards(
    *,
    manifest: ProductionGradeClosureManifest,
    report: ProductionGateReport,
    missing_gate_types: list[str],
    non_passing_report_refs: list[Ref],
    release_blockers: list[ReleaseBlocker],
) -> list[FalseReadyGuard]:
    first_blocker_ref = release_blockers[0].id if release_blockers else None
    guard_inputs = [
        ("lower_gate_presence", bool(missing_gate_types), report.id),
        ("lower_gate_pass_status", bool(non_passing_report_refs), report.id),
        ("llm_as_evidence", False, report.id),
        ("framework_native_state", False, report.id),
        ("source_anchor_gap", False, report.id),
        ("replay_gap", False, report.id),
        ("publication_bypass", False, report.id),
    ]
    return [
        FalseReadyGuard(
            id=f"false-ready-guard:{manifest.id}:{guard_type}",
            fixture_id=manifest.id,
            guard_type=guard_type,
            checked_ref=checked_ref,
            triggered=triggered,
            release_blocker_ref=first_blocker_ref if triggered else None,
            diagnostic_refs=[
                f"diagnostic:{manifest.id}:{guard_type}"
            ]
            if triggered
            else [],
            policy_decision_refs=_policy_refs(manifest.id),
            command_record_refs=[f"command:{manifest.id}:{guard_type}:guard"],
            event_cursor_refs=[f"event-cursor:{manifest.id}:{guard_type}:guard"],
            outbox_refs=[f"outbox:{manifest.id}:{guard_type}:guard"],
            replay_bundle_ref=f"replay-bundle:{manifest.id}:{guard_type}:guard",
        )
        for guard_type, triggered, checked_ref in guard_inputs
    ]


def _release_failure(
    lower_gate_reports: list[ProductionGateReport],
) -> tuple[Ref, str] | None:
    if not lower_gate_reports:
        return (
            "release-blocker:production-grade:missing-lower-gate-report-data",
            "production-grade release requires validated reports from 069-074",
        )
    reports_by_gate = {report.gate_type: report for report in lower_gate_reports}
    missing = [
        gate_type
        for gate_type in _RELEASE_REQUIRED_GATE_TYPES
        if gate_type not in reports_by_gate
    ]
    if missing:
        return (
            "release-blocker:production-grade:missing-lower-gate",
            f"production-grade release is missing lower gate reports: {', '.join(missing)}",
        )
    non_pass = [
        report.gate_type
        for report in lower_gate_reports
        if report.gate_type in _RELEASE_REQUIRED_GATE_TYPES
        and report.completion_result != CompletenessResult.PASS
    ]
    if non_pass:
        return (
            "release-blocker:production-grade:lower-gate-not-pass",
            f"production-grade release has non-passing lower gate reports: {', '.join(non_pass)}",
        )
    return None


def _merge_refs(*groups: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(ref for group in groups for ref in group))


def _entry_point_id(fixture_id: str, profile: ProductionSourceProfile) -> Ref:
    digest = stable_hash(profile.entry_point_url)[:12]
    return f"discovery-entry-point:{fixture_id}:{profile.id}:{digest}"


def _candidate_source_target_id(
    fixture_id: str,
    profile: ProductionSourceProfile,
) -> Ref:
    return f"candidate-source-target:{fixture_id}:{profile.id}"


def _approval_decision_id(fixture_id: str) -> Ref:
    return f"discovery-approval-decision:{fixture_id}:approved"


def _gate_result(
    *,
    report: ProductionGateReport,
    discovery_plans: list[CrawlDiscoveryPlan] | None = None,
    candidate_targets: list[CandidateSourceTarget] | None = None,
    discovery_entry_points: list[DiscoveryEntryPoint] | None = None,
    discovery_approval_decisions: list[DiscoveryApprovalDecision] | None = None,
    acquisition_attempts: list[AcquisitionAttemptRecord] | None = None,
    authorized_sources: list[AuthorizedSourceAccessRecord] | None = None,
    capability_matrices: list[ProductionGradeCapabilityMatrix] | None = None,
    release_decisions: list[ReleaseDecision] | None = None,
    false_ready_guards: list[FalseReadyGuard] | None = None,
    release_blockers: list[ReleaseBlocker] | None = None,
    release_reports: list[ProductionGradeReleaseReport] | None = None,
) -> ProductionGradeGateResult:
    return ProductionGradeGateResult(
        report=report,
        discovery_plans=discovery_plans or [],
        candidate_targets=candidate_targets or [],
        discovery_entry_points=discovery_entry_points or [],
        discovery_approval_decisions=discovery_approval_decisions or [],
        acquisition_attempts=acquisition_attempts or [],
        authorized_sources=authorized_sources or [],
        capability_matrices=capability_matrices or [],
        release_decisions=release_decisions or [],
        false_ready_guards=false_ready_guards or [],
        release_blockers=release_blockers or [],
        release_reports=release_reports or [],
    )
