from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionBenchmarkReleaseFailureType,
)
from veracrawl.contracts.release import (
    ProductionBenchmarkReleaseFixtureManifest,
    ProductionBenchmarkReleaseReport,
)


def _complete_report(**overrides: object) -> ProductionBenchmarkReleaseReport:
    data: dict[str, object] = {
        "id": "production-benchmark-release-report:unit",
        "fixture_id": "production-release-benchmark-success",
        "run_ref": "run:unit",
        "benchmark_manifest_refs": ["benchmark-manifest:unit"],
        "authorized_corpus_refs": ["authorized-corpus:unit"],
        "benchmark_scenario_refs": ["benchmark-scenario:unit"],
        "target_runtime_report_ref": "target-runtime-report:unit",
        "source_coverage_report_ref": "source-coverage-report:unit",
        "product_acceptance_report_ref": "product-acceptance-report:unit",
        "security_privacy_report_ref": "security-privacy-report:unit",
        "result_publication_export_report_ref": "result-publication-report:unit",
        "worker_orchestration_runtime_report_ref": "worker-orchestration-report:unit",
        "ops_replay_observability_runtime_report_ref": "ops-runtime-report:unit",
        "source_gate_refs": ["source-gate:unit"],
        "processing_gate_refs": ["processing-gate:unit"],
        "evidence_gate_refs": ["evidence-gate:unit"],
        "verification_gate_refs": ["verification-gate:unit"],
        "publication_gate_refs": ["publication-gate:unit"],
        "export_gate_refs": ["export-gate:unit"],
        "replay_gate_refs": ["replay-gate:unit"],
        "ops_gate_refs": ["ops-gate:unit"],
        "scale_gate_refs": ["scale-gate:unit"],
        "safety_gate_refs": ["safety-gate:unit"],
        "policy_decision_refs": ["policy:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "artifact_refs": ["artifact:unit"],
        "redaction_map_refs": ["redaction-map:unit"],
        "benchmark_run_refs": ["benchmark-run:unit"],
        "slo_metric_refs": ["slo:unit"],
        "release_decision_refs": ["release-decision:unit"],
        "audit_report_refs": ["release-audit:unit"],
        "release_status": "production_release_ready",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return ProductionBenchmarkReleaseReport(**data)


def test_release_report_requires_all_release_gate_refs() -> None:
    report = _complete_report()
    assert report.completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        _complete_report(target_runtime_report_ref=None)

    with pytest.raises(ValidationError):
        _complete_report(safety_gate_refs=[])


def test_release_report_rejects_hidden_blockers_on_pass() -> None:
    with pytest.raises(ValidationError):
        _complete_report(slo_violation_refs=["slo-violation:unit"])

    with pytest.raises(ValidationError):
        _complete_report(false_ready_refs=["false-ready:unit"])

    with pytest.raises(ValidationError):
        _complete_report(replay_gap_refs=["replay-gap:unit"])


def test_release_failure_requires_typed_diagnostics() -> None:
    report = ProductionBenchmarkReleaseReport(
        id="production-benchmark-release-report:failure",
        fixture_id="production-release-missing-target-runtime",
        run_ref="run:failure",
        failure_type=ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME,
        failure_report_refs=["failure:missing-target"],
        missing_ref_fields=["target_runtime_report_ref"],
        release_status=(
            ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME.value
        ),
        completion_result=CompletenessResult.FAIL,
    )
    assert report.failure_type == ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME

    with pytest.raises(ValidationError):
        ProductionBenchmarkReleaseReport(
            id="production-benchmark-release-report:bad",
            fixture_id="bad",
            run_ref="run:bad",
            release_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_release_fixture_manifest_validates_negative_cases() -> None:
    manifest = ProductionBenchmarkReleaseFixtureManifest(
        id="production-release-benchmark-success",
        scenario="production-release-benchmark-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_release_status="production_release_ready",
        required_gate_refs=["target_runtime_report_ref"],
    )
    assert manifest.id == "production-release-benchmark-success"

    with pytest.raises(ValidationError):
        ProductionBenchmarkReleaseFixtureManifest(
            id="production-release-negative-pass",
            scenario="production-release-negative-pass",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_release_status="bad",
            expected_failure_type=ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH,
            negative_case=True,
            required_gate_refs=["replay_gate_refs"],
        )

    with pytest.raises(ValidationError):
        ProductionBenchmarkReleaseFixtureManifest(
            id="production-release-missing-required-gates",
            scenario="production-release-missing-required-gates",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_release_status="bad",
            expected_failure_type=ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH,
            negative_case=True,
        )
