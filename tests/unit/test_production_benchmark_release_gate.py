from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionBenchmarkReleaseFailureType,
)
from veracrawl.release.benchmark_gate import run_production_benchmark_release_gate


def test_production_release_success_composes_all_target_gates() -> None:
    result = run_production_benchmark_release_gate(
        fixture_id="unit-production-release",
        scenario="production-release-benchmark-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert result.target_runtime is not None
    assert result.source_coverage is not None
    assert result.product_acceptance is not None
    assert result.security_privacy is not None
    assert result.ops_runtime is not None
    assert result.ops_runtime.publication is not None
    assert result.ops_runtime.worker_orchestration is not None
    assert report.target_runtime_report_ref
    assert report.source_coverage_report_ref
    assert report.product_acceptance_report_ref
    assert report.security_privacy_report_ref
    assert report.result_publication_export_report_ref
    assert report.worker_orchestration_runtime_report_ref
    assert report.ops_replay_observability_runtime_report_ref
    assert report.source_gate_refs
    assert report.processing_gate_refs
    assert report.evidence_gate_refs
    assert report.verification_gate_refs
    assert report.publication_gate_refs
    assert report.export_gate_refs
    assert report.replay_gate_refs
    assert report.ops_gate_refs
    assert report.scale_gate_refs
    assert report.safety_gate_refs
    assert report.release_status == "production_release_ready"


def test_production_release_missing_dependency_failures_are_typed() -> None:
    expectations = {
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
    for scenario, (failure, missing) in expectations.items():
        report = run_production_benchmark_release_gate(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert missing in report.missing_ref_fields


def test_production_release_lower_runtime_failures_are_typed() -> None:
    expectations = {
        "production-release-missing-publication": (
            ProductionBenchmarkReleaseFailureType.MISSING_PUBLICATION,
            "result_publication_export_report_ref",
        ),
        "production-release-missing-worker-orchestration": (
            ProductionBenchmarkReleaseFailureType.MISSING_WORKER_ORCHESTRATION,
            "worker_orchestration_runtime_report_ref",
        ),
    }
    for scenario, (failure, missing) in expectations.items():
        report = run_production_benchmark_release_gate(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert missing in report.missing_ref_fields


def test_production_release_blocker_failures_are_typed() -> None:
    expectations = {
        "production-release-slo-violation": (
            ProductionBenchmarkReleaseFailureType.SLO_VIOLATION,
            "slo_violation_refs",
        ),
        "production-release-blocker-present": (
            ProductionBenchmarkReleaseFailureType.RELEASE_BLOCKER_PRESENT,
            "release_blocker_refs",
        ),
        "production-release-false-ready": (
            ProductionBenchmarkReleaseFailureType.FALSE_READY,
            "false_ready_refs",
        ),
        "production-release-replay-mismatch": (
            ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH,
            "replay_gap_refs",
        ),
    }
    for scenario, (failure, attr) in expectations.items():
        report = run_production_benchmark_release_gate(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert getattr(report, attr)
