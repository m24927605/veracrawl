from __future__ import annotations

import json
from pathlib import Path

from veracrawl.benchmarks.production_grade import run_production_grade_gate
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    ProductionGateReport,
    ProductionGradeClosureManifest,
)


def _manifest(fixture_name: str) -> ProductionGradeClosureManifest:
    path = Path("tests/fixtures") / fixture_name / "manifest.yaml"
    return ProductionGradeClosureManifest.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _report_for(fixture_name: str) -> ProductionGateReport:
    result = run_production_grade_gate(
        manifest=_manifest(fixture_name),
        profile="production",
    )
    assert result.report.completion_result == CompletenessResult.PASS
    return result.report


def test_discovery_planning_records_ai_decision_and_replay_refs() -> None:
    result = run_production_grade_gate(
        manifest=_manifest("production-discovery-planning-success"),
        profile="production",
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.discovery_plans
    assert result.discovery_entry_points
    assert result.candidate_targets
    assert result.discovery_approval_decisions
    plan = result.discovery_plans[0]
    assert plan.model_call_trace_refs
    assert plan.agent_action_trace_refs
    assert plan.tool_call_trace_refs
    assert plan.context_bundle_trace_refs
    assert plan.replay_bundle_ref


def test_acquisition_source_limited_blocks_publication_with_limitation_refs() -> None:
    result = run_production_grade_gate(
        manifest=_manifest("production-acquisition-source-limited"),
        profile="production",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.release_blocker_refs
    assert result.acquisition_attempts
    assert all(attempt.source_limitation_ref for attempt in result.acquisition_attempts)


def test_release_gate_requires_actual_lower_gate_report_data() -> None:
    result = run_production_grade_gate(
        manifest=_manifest("production-grade-release-ready"),
        profile="production",
        input_report_refs=[
            "production-gate-report:discovery",
            "production-gate-report:acquisition",
            "production-gate-report:authorized",
            "production-gate-report:deep-crawl",
            "production-gate-report:quality",
            "production-gate-report:ops",
        ],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert "missing-lower-gate-report-data" in result.report.release_blocker_refs[0]


def test_release_gate_passes_only_with_all_passing_lower_gate_reports() -> None:
    lower_reports = [
        _report_for("production-discovery-planning-success"),
        _report_for("production-acquisition-escalation-success"),
        _report_for("production-authorized-source-success"),
        _report_for("production-deep-crawl-success"),
        _report_for("production-extraction-quality-success"),
        _report_for("production-operations-success"),
    ]
    result = run_production_grade_gate(
        manifest=_manifest("production-grade-release-ready"),
        profile="production",
        lower_gate_reports=lower_reports,
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.report.lower_gate_report_refs) == 6
    assert result.capability_matrices
    assert result.release_decisions[0].decision == "pass"
    assert result.release_reports[0].completion_result == CompletenessResult.PASS
    assert not result.release_blockers


def test_release_gate_fails_when_a_required_gate_report_is_missing() -> None:
    lower_reports = [
        _report_for("production-discovery-planning-success"),
        _report_for("production-acquisition-escalation-success"),
        _report_for("production-authorized-source-success"),
        _report_for("production-deep-crawl-success"),
        _report_for("production-extraction-quality-success"),
    ]
    result = run_production_grade_gate(
        manifest=_manifest("production-grade-release-missing-gate"),
        profile="production",
        lower_gate_reports=lower_reports,
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.release_blocker_refs
    assert result.release_blockers
    assert result.false_ready_guards
    assert result.release_decisions[0].decision == "blocked"
