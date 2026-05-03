"""Deterministic production benchmark and release gate aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    ProductionBenchmarkReleaseFailureType,
)
from veracrawl.contracts.release import ProductionBenchmarkReleaseReport
from veracrawl.contracts.source_coverage import (
    EXPECTED_NATURAL_RESULT_TYPES,
    REQUIRED_SOURCE_ADAPTER_TYPES,
    SourceCoverageAdapterExecutionRecord,
)
from veracrawl.fetch.source_coverage_gate import (
    SourceCoverageAdapterGateResult,
    run_source_coverage_adapter_gate,
)
from veracrawl.ops.replay_observability_runtime import (
    OpsReplayObservabilityRuntimeResult,
    run_ops_replay_observability_runtime,
)
from veracrawl.product_acceptance.gate import (
    ProductAcceptanceRuntimeResult,
    run_product_acceptance_gate,
)
from veracrawl.runtime_support.security_privacy import (
    SecurityPrivacyGateResult,
    run_security_privacy_gate,
)
from veracrawl.target_runtime.runner import TargetRuntimeResult, run_target_runtime_fixture


@dataclass(frozen=True)
class ProductionBenchmarkReleaseResult:
    report: ProductionBenchmarkReleaseReport
    target_runtime: TargetRuntimeResult | None = None
    source_coverage: SourceCoverageAdapterGateResult | None = None
    product_acceptance: ProductAcceptanceRuntimeResult | None = None
    security_privacy: SecurityPrivacyGateResult | None = None
    ops_runtime: OpsReplayObservabilityRuntimeResult | None = None


@dataclass(frozen=True)
class _ReleaseDependencies:
    target_runtime: TargetRuntimeResult | None
    source_coverage: SourceCoverageAdapterGateResult | None
    product_acceptance: ProductAcceptanceRuntimeResult | None
    security_privacy: SecurityPrivacyGateResult | None
    ops_runtime: OpsReplayObservabilityRuntimeResult | None


_MISSING_DEPENDENCIES: dict[
    str,
    tuple[ProductionBenchmarkReleaseFailureType, str],
] = {
    "production-release-missing-target-runtime": (
        ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME,
        "target_runtime_report_ref",
    ),
    "production-release-missing-source-coverage": (
        ProductionBenchmarkReleaseFailureType.MISSING_SOURCE_COVERAGE,
        "source_coverage_report_ref",
    ),
    "production-release-missing-product-acceptance": (
        ProductionBenchmarkReleaseFailureType.MISSING_PRODUCT_ACCEPTANCE,
        "product_acceptance_report_ref",
    ),
    "production-release-missing-security-privacy": (
        ProductionBenchmarkReleaseFailureType.MISSING_SECURITY_PRIVACY,
        "security_privacy_report_ref",
    ),
    "production-release-missing-ops-runtime": (
        ProductionBenchmarkReleaseFailureType.MISSING_OPS_RUNTIME,
        "ops_replay_observability_runtime_report_ref",
    ),
}


def run_production_benchmark_release_gate(
    *,
    fixture_id: str,
    scenario: str,
    telemetry_backend_ref: Ref | None = None,
    collector_handoff_ref: Ref | None = None,
) -> ProductionBenchmarkReleaseResult:
    backend_ref = telemetry_backend_ref or f"telemetry-backend:{fixture_id}:release"
    handoff_ref = collector_handoff_ref or f"collector-handoff:{fixture_id}:release"

    if scenario in _MISSING_DEPENDENCIES:
        failure, missing_field = _MISSING_DEPENDENCIES[scenario]
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            include_target=failure
            != ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME,
            include_source=failure
            != ProductionBenchmarkReleaseFailureType.MISSING_SOURCE_COVERAGE,
            include_product=failure
            != ProductionBenchmarkReleaseFailureType.MISSING_PRODUCT_ACCEPTANCE,
            include_security=failure
            != ProductionBenchmarkReleaseFailureType.MISSING_SECURITY_PRIVACY,
            include_ops=failure != ProductionBenchmarkReleaseFailureType.MISSING_OPS_RUNTIME,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=failure,
            missing_ref_fields=[missing_field],
            missing_gate_refs=[f"missing-gate:{fixture_id}:{missing_field}"],
        )

    if scenario == "production-release-missing-publication":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            ops_scenario="ops-runtime-missing-publication",
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.MISSING_PUBLICATION,
            missing_ref_fields=["result_publication_export_report_ref"],
            missing_gate_refs=[f"missing-gate:{fixture_id}:publication"],
        )

    if scenario == "production-release-missing-worker-orchestration":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            ops_scenario="ops-runtime-missing-worker-orchestration",
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.MISSING_WORKER_ORCHESTRATION,
            missing_ref_fields=["worker_orchestration_runtime_report_ref"],
            missing_gate_refs=[f"missing-gate:{fixture_id}:worker-orchestration"],
        )

    if scenario == "production-release-slo-violation":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.SLO_VIOLATION,
            missing_ref_fields=["slo_metric_refs"],
            slo_violation_refs=[f"slo-violation:{fixture_id}:projection-lag"],
        )

    if scenario == "production-release-blocker-present":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.RELEASE_BLOCKER_PRESENT,
            missing_ref_fields=["release_blocker_refs"],
            release_blocker_refs=[f"release-blocker:{fixture_id}:operator-recovery"],
        )

    if scenario == "production-release-false-ready":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.FALSE_READY,
            missing_ref_fields=["release_decision_refs"],
            false_ready_refs=[f"false-ready:{fixture_id}:degraded-operational"],
        )

    if scenario == "production-release-replay-mismatch":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH,
            missing_ref_fields=["replay_gate_refs"],
            replay_gap_refs=[f"replay-gap:{fixture_id}:release"],
        )

    deps = _collect_dependencies(
        fixture_id=fixture_id,
        telemetry_backend_ref=backend_ref,
        collector_handoff_ref=handoff_ref,
    )
    return ProductionBenchmarkReleaseResult(
        report=_pass_report(fixture_id=fixture_id, scenario=scenario, deps=deps),
        target_runtime=deps.target_runtime,
        source_coverage=deps.source_coverage,
        product_acceptance=deps.product_acceptance,
        security_privacy=deps.security_privacy,
        ops_runtime=deps.ops_runtime,
    )


def _collect_dependencies(
    *,
    fixture_id: str,
    include_target: bool = True,
    include_source: bool = True,
    include_product: bool = True,
    include_security: bool = True,
    include_ops: bool = True,
    ops_scenario: str = "ops-runtime-review-replay-success",
    telemetry_backend_ref: Ref,
    collector_handoff_ref: Ref,
) -> _ReleaseDependencies:
    target = (
        run_target_runtime_fixture(
            fixture_id=fixture_id,
            scenario="target-runtime-success",
            profile="target",
        )
        if include_target
        else None
    )
    source = (
        run_source_coverage_adapter_gate(
            fixture_id=fixture_id,
            scenario="source-coverage-adapter-success",
            execution_records=_source_coverage_records(fixture_id),
            policy_decision_refs=[f"policy:{fixture_id}:source-coverage"],
        )
        if include_source
        else None
    )
    product = (
        run_product_acceptance_gate(
            fixture_id=fixture_id,
            scenario="product-acceptance-success",
            policy_decision_refs=[f"policy:{fixture_id}:product-acceptance"],
        )
        if include_product
        else None
    )
    security = (
        run_security_privacy_gate(
            fixture_id=fixture_id,
            scenario="security-privacy-success",
        )
        if include_security
        else None
    )
    ops = (
        run_ops_replay_observability_runtime(
            fixture_id=fixture_id,
            scenario=ops_scenario,
            telemetry_backend_ref=telemetry_backend_ref,
            collector_handoff_ref=collector_handoff_ref,
        )
        if include_ops
        else None
    )
    return _ReleaseDependencies(
        target_runtime=target,
        source_coverage=source,
        product_acceptance=product,
        security_privacy=security,
        ops_runtime=ops,
    )


def _source_coverage_records(fixture_id: str) -> list[SourceCoverageAdapterExecutionRecord]:
    return [
        _source_coverage_record(fixture_id=fixture_id, adapter_type=adapter_type)
        for adapter_type in REQUIRED_SOURCE_ADAPTER_TYPES
    ]


def _source_coverage_record(
    *,
    fixture_id: str,
    adapter_type: AdapterType,
) -> SourceCoverageAdapterExecutionRecord:
    slug = adapter_type.value.replace("_", "-")
    return SourceCoverageAdapterExecutionRecord(
        id=f"source-coverage-execution:{fixture_id}:{slug}:release",
        adapter_type=adapter_type,
        natural_result_type=EXPECTED_NATURAL_RESULT_TYPES[adapter_type],
        source_adapter_spec_ref=f"source-adapter-spec:{fixture_id}:{slug}",
        source_adapter_result_ref=f"source-adapter-result:{fixture_id}:{slug}",
        natural_result_refs=[f"source-natural-result:{fixture_id}:{slug}"],
        fetch_attempt_refs=(
            [f"fetch-attempt:{fixture_id}:{slug}"]
            if adapter_type == AdapterType.HTTP
            else []
        ),
        page_snapshot_refs=(
            [f"page-snapshot:{fixture_id}:{slug}"]
            if adapter_type in {AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT}
            else []
        ),
        browser_interaction_refs=(
            [f"browser-interaction:{fixture_id}:{slug}"]
            if adapter_type == AdapterType.BROWSER_SNAPSHOT
            else []
        ),
        credential_audit_refs=(
            [f"credential-use-audit:{fixture_id}:{slug}"]
            if adapter_type == AdapterType.AUTHORIZED_SESSION
            else []
        ),
        document_artifact_refs=(
            [f"document-artifact:{fixture_id}:{slug}"]
            if adapter_type in {AdapterType.DOCUMENT_SOURCE, AdapterType.FILE_IMPORT}
            else []
        ),
        api_payload_refs=(
            [f"api-payload:{fixture_id}:{slug}"]
            if adapter_type == AdapterType.API_SOURCE
            else []
        ),
        command_result_refs=[f"command-result:{fixture_id}:{slug}:source-release"],
        policy_decision_refs=[f"policy:{fixture_id}:source-coverage"],
        observability_report_refs=[f"observability-report:{fixture_id}:source-release"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:source-release"
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:source-release",
        contract_adapter_refs=[f"source-coverage-contract-adapter:{fixture_id}:{slug}"],
        diagnostic_adapter_state_refs=[f"diagnostic-source-state:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )


def _pass_report(
    *,
    fixture_id: str,
    scenario: str,
    deps: _ReleaseDependencies,
) -> ProductionBenchmarkReleaseReport:
    if not (
        deps.target_runtime
        and deps.source_coverage
        and deps.product_acceptance
        and deps.security_privacy
        and deps.ops_runtime
        and deps.ops_runtime.publication
        and deps.ops_runtime.worker_orchestration
    ):
        raise ValueError("passing production release requires all dependencies")

    target = deps.target_runtime.report
    source = deps.source_coverage.report
    product = deps.product_acceptance.report
    security = deps.security_privacy.report
    ops = deps.ops_runtime.report
    publication = deps.ops_runtime.publication.report
    worker = deps.ops_runtime.worker_orchestration.report

    return ProductionBenchmarkReleaseReport(
        id=f"production-benchmark-release-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        benchmark_manifest_refs=[f"benchmark-manifest:{fixture_id}:target-release"],
        authorized_corpus_refs=[f"authorized-corpus:{fixture_id}:deterministic-local"],
        benchmark_scenario_refs=[
            f"benchmark-scenario:{fixture_id}:target",
            f"benchmark-scenario:{fixture_id}:{scenario}",
        ],
        target_runtime_report_ref=target.id,
        source_coverage_report_ref=source.id,
        product_acceptance_report_ref=product.id,
        security_privacy_report_ref=security.id,
        result_publication_export_report_ref=publication.id,
        worker_orchestration_runtime_report_ref=worker.id,
        ops_replay_observability_runtime_report_ref=ops.id,
        source_gate_refs=_dedupe(
            [
                source.id,
                *source.source_adapter_result_refs,
                *worker.worker_pool_refs,
                *target.pattern_record_refs,
            ]
        ),
        processing_gate_refs=_dedupe(
            [
                *publication.extraction_candidate_refs,
                *target.processing_evidence_refs,
                *target.normalized_document_refs,
                f"processing-gate:{fixture_id}:normalization-extraction",
            ]
        ),
        evidence_gate_refs=_dedupe(
            [
                publication.live_evidence_runtime_report_ref or "",
                *publication.evidence_packet_refs,
                *publication.evidence_coverage_refs,
                *target.evidence_refs,
                *product.evidence_refs,
            ]
        ),
        verification_gate_refs=_dedupe(
            [
                *publication.verification_decision_refs,
                *publication.review_decision_refs,
                *target.verification_refs,
            ]
        ),
        publication_gate_refs=_dedupe(
            [
                publication.id,
                *publication.publication_report_refs,
                *publication.published_output_refs,
                *publication.output_manifest_refs,
            ]
        ),
        export_gate_refs=_dedupe(
            [
                *publication.export_target_spec_refs,
                *publication.export_job_refs,
                *publication.export_attempt_refs,
                *publication.delivery_receipt_refs,
                *publication.withdrawal_job_refs,
                *publication.withdrawal_attempt_refs,
                *publication.correction_record_refs,
                *product.export_reconciliation_refs,
            ]
        ),
        replay_gate_refs=_dedupe(
            [
                target.replay_bundle_ref or "",
                source.replay_bundle_ref or "",
                publication.replay_bundle_ref or "",
                worker.replay_bundle_ref or "",
                ops.replay_bundle_ref or "",
                security.replay_bundle_ref or "",
                *product.replay_refs,
            ]
        ),
        ops_gate_refs=_dedupe(
            [
                ops.id,
                *ops.run_control_action_refs,
                *ops.review_item_refs,
                *ops.replay_audit_view_refs,
                *ops.recovery_action_refs,
                *ops.dashboard_snapshot_refs,
                *ops.alert_record_refs,
            ]
        ),
        scale_gate_refs=_dedupe(
            [
                worker.id,
                worker.queue_topology_ref or "",
                *worker.queue_item_refs,
                *worker.shard_lease_refs,
                *worker.backpressure_signal_refs,
                *worker.autoscaling_decision_refs,
            ]
        ),
        safety_gate_refs=_dedupe(
            [
                security.id,
                *security.security_policy_check_refs,
                *security.credential_use_audit_refs,
                *security.prompt_taint_boundary_refs,
                *security.artifact_lifecycle_action_refs,
                *security.projection_cleanup_refs,
            ]
        ),
        policy_decision_refs=_dedupe(
            [
                *target.policy_decision_refs,
                *source.policy_decision_refs,
                *product.policy_decision_refs,
                *security.policy_decision_refs,
                *publication.policy_decision_refs,
                *worker.policy_decision_refs,
                *ops.policy_decision_refs,
                f"policy:{fixture_id}:release",
            ]
        ),
        command_record_refs=_dedupe(
            [
                *target.command_record_refs,
                *source.command_record_refs,
                *product.command_record_refs,
                *security.command_record_refs,
                *publication.command_record_refs,
                *worker.command_record_refs,
                *ops.command_record_refs,
            ]
        ),
        event_cursor_refs=_dedupe(
            [
                *target.event_cursor_refs,
                *source.event_cursor_refs,
                *product.event_cursor_refs,
                *security.event_cursor_refs,
                *publication.event_cursor_refs,
                *worker.event_cursor_refs,
                *ops.event_cursor_refs,
            ]
        ),
        outbox_refs=_dedupe(
            [
                *target.outbox_refs,
                *source.outbox_refs,
                *product.outbox_refs,
                *security.outbox_refs,
                *publication.outbox_refs,
                *worker.outbox_refs,
                *ops.outbox_refs,
            ]
        ),
        artifact_refs=_dedupe(
            [
                *target.artifact_refs,
                *product.artifact_refs,
                f"artifact:{fixture_id}:release-benchmark-summary",
            ]
        ),
        redaction_map_refs=_dedupe([*ops.redaction_map_refs, *security.redaction_map_refs]),
        benchmark_run_refs=[f"benchmark-run:{fixture_id}:target-release"],
        slo_metric_refs=[
            f"slo-metric:{fixture_id}:runtime-completion",
            f"slo-metric:{fixture_id}:operator-recovery",
            f"slo-metric:{fixture_id}:replay-closure",
        ],
        release_decision_refs=[f"release-decision:{fixture_id}:approved"],
        audit_report_refs=[f"release-audit:{fixture_id}:complete"],
        release_status="production_release_ready",
        completion_result=CompletenessResult.PASS,
    )


def _failure_result(
    *,
    fixture_id: str,
    deps: _ReleaseDependencies,
    failure: ProductionBenchmarkReleaseFailureType,
    missing_ref_fields: list[str] | None = None,
    missing_gate_refs: list[Ref] | None = None,
    slo_violation_refs: list[Ref] | None = None,
    release_blocker_refs: list[Ref] | None = None,
    false_ready_refs: list[Ref] | None = None,
    replay_gap_refs: list[Ref] | None = None,
) -> ProductionBenchmarkReleaseResult:
    target = deps.target_runtime.report if deps.target_runtime else None
    source = deps.source_coverage.report if deps.source_coverage else None
    product = deps.product_acceptance.report if deps.product_acceptance else None
    security = deps.security_privacy.report if deps.security_privacy else None
    ops = deps.ops_runtime.report if deps.ops_runtime else None
    publication = (
        deps.ops_runtime.publication.report
        if deps.ops_runtime and deps.ops_runtime.publication
        else None
    )
    worker = (
        deps.ops_runtime.worker_orchestration.report
        if deps.ops_runtime and deps.ops_runtime.worker_orchestration
        else None
    )
    replay_mismatch = failure == ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH
    command_refs = [] if replay_mismatch else [f"command-record:{fixture_id}:release"]
    event_refs = [] if replay_mismatch else [f"event-cursor:{fixture_id}:release"]
    outbox_refs = [] if replay_mismatch else [f"outbox:{fixture_id}:release"]
    report = ProductionBenchmarkReleaseReport(
        id=f"production-benchmark-release-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        benchmark_manifest_refs=[f"benchmark-manifest:{fixture_id}:target-release"],
        authorized_corpus_refs=[f"authorized-corpus:{fixture_id}:deterministic-local"],
        benchmark_scenario_refs=[f"benchmark-scenario:{fixture_id}:failure"],
        target_runtime_report_ref=target.id if target else None,
        source_coverage_report_ref=source.id if source else None,
        product_acceptance_report_ref=product.id if product else None,
        security_privacy_report_ref=security.id if security else None,
        result_publication_export_report_ref=publication.id if publication else None,
        worker_orchestration_runtime_report_ref=worker.id if worker else None,
        ops_replay_observability_runtime_report_ref=ops.id if ops else None,
        policy_decision_refs=[f"policy:{fixture_id}:release"],
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        failure_type=failure,
        failure_report_refs=[f"failure-report:{fixture_id}:{failure.value}"],
        missing_gate_refs=missing_gate_refs or [],
        slo_violation_refs=slo_violation_refs or [],
        release_blocker_refs=release_blocker_refs or [],
        false_ready_refs=false_ready_refs or [],
        replay_gap_refs=replay_gap_refs or [],
        missing_ref_fields=missing_ref_fields or [failure.value],
        diagnostics=[failure.value],
        release_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return ProductionBenchmarkReleaseResult(
        report=report,
        target_runtime=deps.target_runtime,
        source_coverage=deps.source_coverage,
        product_acceptance=deps.product_acceptance,
        security_privacy=deps.security_privacy,
        ops_runtime=deps.ops_runtime,
    )


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return [ref for ref in dict.fromkeys(refs) if ref]
