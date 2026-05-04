from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import production_grade
from veracrawl.contracts.enums import CompletenessResult

_LOWER_GATE_FIXTURES = [
    "production-discovery-planning-success",
    "production-acquisition-escalation-success",
    "production-authorized-source-success",
    "production-deep-crawl-success",
    "production-extraction-quality-success",
    "production-operations-success",
]


@pytest.mark.parametrize(
    ("fixture_name", "expected_result", "expected_lower_report_count"),
    [
        ("production-discovery-planning-success", CompletenessResult.PASS, 0),
        ("production-acquisition-escalation-success", CompletenessResult.PASS, 0),
        ("production-acquisition-source-limited", CompletenessResult.NEEDS_REVIEW, 0),
        ("production-authorized-source-success", CompletenessResult.PASS, 0),
        ("production-deep-crawl-success", CompletenessResult.PASS, 0),
        ("production-extraction-quality-success", CompletenessResult.PASS, 0),
        ("production-operations-success", CompletenessResult.PASS, 0),
        ("production-grade-release-ready", CompletenessResult.PASS, 6),
        ("production-grade-release-missing-gate", CompletenessResult.FAIL, 0),
    ],
)
def test_production_grade_fixture_contracts(
    tmp_path: Path,
    fixture_name: str,
    expected_result: CompletenessResult,
    expected_lower_report_count: int,
) -> None:
    input_reports = (
        _run_lower_gate_reports(tmp_path)
        if fixture_name == "production-grade-release-ready"
        else []
    )
    result = production_grade.run_fixture(
        Path("tests/fixtures") / fixture_name,
        profile="production",
        out=tmp_path / fixture_name,
        input_reports=input_reports,
    )

    assert result.report.completion_result == expected_result
    assert len(result.report.lower_gate_report_refs) == expected_lower_report_count
    assert result.report.policy_decision_refs
    assert result.report.command_record_refs
    assert result.report.event_cursor_refs
    assert result.report.outbox_refs
    assert result.report.replay_bundle_refs
    assert (tmp_path / fixture_name / "production_gate_report.json").exists()
    assert (tmp_path / fixture_name / "summary.json").exists()
    assert (tmp_path / fixture_name / "candidate_targets.json").exists()
    assert (tmp_path / fixture_name / "production_grade_release_reports.json").exists()
    if fixture_name == "production-grade-release-ready":
        assert result.release_reports
        assert result.capability_matrices
        assert result.release_decisions[0].decision == "pass"


def _run_lower_gate_reports(tmp_path: Path) -> list[Path]:
    report_paths: list[Path] = []
    for fixture_name in _LOWER_GATE_FIXTURES:
        out = tmp_path / "lower" / fixture_name
        production_grade.run_fixture(
            Path("tests/fixtures") / fixture_name,
            profile="production",
            out=out,
        )
        report_paths.append(out / "production_gate_report.json")
    return report_paths
