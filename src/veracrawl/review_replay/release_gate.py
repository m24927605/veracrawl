"""Replay validation for row 054 production benchmark release gate."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.release import ProductionBenchmarkReleaseReport


def missing_production_release_refs(report: ProductionBenchmarkReleaseReport) -> list[str]:
    required = {
        "benchmark_manifest_refs": report.benchmark_manifest_refs,
        "authorized_corpus_refs": report.authorized_corpus_refs,
        "benchmark_scenario_refs": report.benchmark_scenario_refs,
        "target_runtime_report_ref": report.target_runtime_report_ref,
        "source_coverage_report_ref": report.source_coverage_report_ref,
        "product_acceptance_report_ref": report.product_acceptance_report_ref,
        "security_privacy_report_ref": report.security_privacy_report_ref,
        "result_publication_export_report_ref": (
            report.result_publication_export_report_ref
        ),
        "worker_orchestration_runtime_report_ref": (
            report.worker_orchestration_runtime_report_ref
        ),
        "ops_replay_observability_runtime_report_ref": (
            report.ops_replay_observability_runtime_report_ref
        ),
        "source_gate_refs": report.source_gate_refs,
        "processing_gate_refs": report.processing_gate_refs,
        "evidence_gate_refs": report.evidence_gate_refs,
        "verification_gate_refs": report.verification_gate_refs,
        "publication_gate_refs": report.publication_gate_refs,
        "export_gate_refs": report.export_gate_refs,
        "replay_gate_refs": report.replay_gate_refs,
        "ops_gate_refs": report.ops_gate_refs,
        "scale_gate_refs": report.scale_gate_refs,
        "safety_gate_refs": report.safety_gate_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "artifact_refs": report.artifact_refs,
        "redaction_map_refs": report.redaction_map_refs,
        "benchmark_run_refs": report.benchmark_run_refs,
        "slo_metric_refs": report.slo_metric_refs,
        "release_decision_refs": report.release_decision_refs,
        "audit_report_refs": report.audit_report_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def production_release_replay_passes(report: ProductionBenchmarkReleaseReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_production_release_refs(report)
        or report.missing_gate_refs
        or report.slo_violation_refs
        or report.release_blocker_refs
        or report.false_ready_refs
        or report.replay_gap_refs
    )
