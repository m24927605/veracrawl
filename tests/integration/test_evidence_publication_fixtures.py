from __future__ import annotations

from pathlib import Path

from tests.helpers.evidence_fixture_assertions import (
    assert_evidence_negative,
    assert_evidence_success,
    assert_publication_success,
)
from veracrawl.cli.evidence import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_evidence_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    coverage_report = run_fixture(
        fixtures_root / "evidence-field-coverage",
        profile="target",
        out=tmp_path / "evidence-field-coverage",
    )
    assert_evidence_success(coverage_report)
    review_report = run_fixture(
        fixtures_root / "evidence-verification-review",
        profile="target",
        out=tmp_path / "evidence-verification-review",
    )
    assert_evidence_success(review_report)
    assert review_report.verification_decision_ref
    assert review_report.review_decision_ref
    publication_report = run_fixture(
        fixtures_root / "evidence-publication-success",
        profile="target",
        out=tmp_path / "evidence-publication-success",
    )
    assert_publication_success(publication_report)


def test_evidence_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "evidence-missing-anchor": (
            "missing_evidence_anchor",
            CompletenessResult.NEEDS_REVIEW,
        ),
        "evidence-verification-conflict": (
            "verification_conflict",
            CompletenessResult.FAIL,
        ),
        "evidence-policy-denied": (
            "publication_policy_denied",
            CompletenessResult.FAIL,
        ),
        "evidence-replay-gap": ("replay_gap", CompletenessResult.FAIL),
        "evidence-candidate-direct-publication": (
            "candidate_direct_publication",
            CompletenessResult.FAIL,
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_evidence_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
