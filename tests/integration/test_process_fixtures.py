from __future__ import annotations

from pathlib import Path

from tests.helpers.process_fixture_assertions import assert_process_negative, assert_process_success
from veracrawl.cli.process import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_process_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "process-static-basic",
        "process-link-provenance",
        "process-anchored-candidate",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_process_success(report)
    link_report = run_fixture(
        fixtures_root / "process-link-provenance",
        profile="target",
        out=tmp_path / "process-link-provenance-2",
    )
    assert link_report.link_provenance_refs


def test_process_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "process-missing-raw": ("missing_raw_artifact", CompletenessResult.FAIL),
        "process-empty-content": ("empty_normalized_content", CompletenessResult.NEEDS_REVIEW),
        "process-anchor-gap": ("candidate_anchor_gap", CompletenessResult.FAIL),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_process_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
