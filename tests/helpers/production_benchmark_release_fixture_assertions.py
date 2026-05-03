from __future__ import annotations

from veracrawl.cli.release_gate import ProductionBenchmarkReleaseFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_release_success(report: ProductionBenchmarkReleaseFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.release_status == "production_release_ready"
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
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.redaction_map_refs
    assert report.benchmark_run_refs
    assert report.slo_metric_refs
    assert report.release_decision_refs
    assert report.audit_report_refs
    assert report.failure_type is None


def assert_release_negative(
    report: ProductionBenchmarkReleaseFixtureRunReport,
    *,
    release_status: str,
    failure_type: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.release_status == release_status
    assert report.failure_type == failure_type
    assert report.failure_report_refs
    assert report.missing_ref_fields
