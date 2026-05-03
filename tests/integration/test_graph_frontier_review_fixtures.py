from __future__ import annotations

from pathlib import Path

from tests.helpers.graph_frontier_review_fixture_assertions import (
    assert_graph_frontier_review_needs_review,
    assert_graph_frontier_review_negative,
    assert_graph_frontier_review_success,
)
from veracrawl.cli.graph_frontier_review import run_fixture
from veracrawl.contracts.enums import GraphFrontierReviewFailureType


def test_graph_frontier_review_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "graph-frontier-review-success",
        profile="target",
        out=tmp_path / "graph-frontier-review-success",
    )
    assert_graph_frontier_review_success(report)


def test_graph_frontier_review_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "graph-frontier-review-runtime-unavailable",
        profile="target",
        out=tmp_path / "graph-frontier-review-runtime-unavailable",
    )
    assert_graph_frontier_review_needs_review(report)


def test_graph_frontier_review_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "graph-frontier-review-signal-as-evidence": (
            GraphFrontierReviewFailureType.GRAPH_SIGNAL_AS_EVIDENCE.value,
            "graph_signal_as_evidence_refs",
        ),
        "graph-frontier-review-missing-source-graph": (
            GraphFrontierReviewFailureType.MISSING_SOURCE_GRAPH_REFS.value,
            "source_graph_refs",
        ),
        "graph-frontier-review-missing-explanation": (
            GraphFrontierReviewFailureType.MISSING_EXPLANATION_REF.value,
            "explanation_ref",
        ),
        "graph-frontier-review-unauthorized-frontier-mutation": (
            GraphFrontierReviewFailureType.UNAUTHORIZED_FRONTIER_MUTATION.value,
            "unauthorized_frontier_mutation_refs",
        ),
        "graph-frontier-review-missing-review-route": (
            GraphFrontierReviewFailureType.MISSING_REVIEW_ROUTE.value,
            "review_route_decision_refs",
        ),
        "graph-frontier-review-missing-replay": (
            GraphFrontierReviewFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "graph-frontier-review-unsupported-signal": (
            GraphFrontierReviewFailureType.UNSUPPORTED_SIGNAL.value,
            "unsupported_signal_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_graph_frontier_review_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
