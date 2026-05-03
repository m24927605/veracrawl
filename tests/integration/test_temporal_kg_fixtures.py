from __future__ import annotations

from pathlib import Path

from tests.helpers.temporal_kg_fixture_assertions import (
    assert_temporal_kg_false_merge_success,
    assert_temporal_kg_false_split_success,
    assert_temporal_kg_needs_review,
    assert_temporal_kg_negative,
    assert_temporal_kg_projection_success,
)
from veracrawl.cli.temporal_kg import run_fixture
from veracrawl.contracts.enums import TemporalKGFailureType


def test_temporal_kg_projection_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "temporal-kg-projection-success",
        profile="target",
        out=tmp_path / "temporal-kg-projection-success",
    )
    assert_temporal_kg_projection_success(report)


def test_temporal_kg_false_merge_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "temporal-kg-false-merge-adjudicated",
        profile="target",
        out=tmp_path / "temporal-kg-false-merge-adjudicated",
    )
    assert_temporal_kg_false_merge_success(report)


def test_temporal_kg_false_split_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "temporal-kg-false-split-superseded",
        profile="target",
        out=tmp_path / "temporal-kg-false-split-superseded",
    )
    assert_temporal_kg_false_split_success(report)


def test_temporal_kg_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "temporal-kg-runtime-unavailable",
        profile="target",
        out=tmp_path / "temporal-kg-runtime-unavailable",
    )
    assert_temporal_kg_needs_review(report)


def test_temporal_kg_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "temporal-kg-provisional-identity": (
            TemporalKGFailureType.PROVISIONAL_IDENTITY.value,
            "provisional_graph_identity_refs",
        ),
        "temporal-kg-projection-as-evidence": (
            TemporalKGFailureType.PROJECTION_AS_EVIDENCE.value,
            "temporal_kg_projection_ref",
        ),
        "temporal-kg-missing-canonical-source": (
            TemporalKGFailureType.MISSING_CANONICAL_SOURCES.value,
            "source_verified_fact_refs",
        ),
        "temporal-kg-missing-bitemporal-refs": (
            TemporalKGFailureType.MISSING_BITEMPORAL_REFS.value,
            "valid_time_and_transaction_time_refs",
        ),
        "temporal-kg-false-merge-without-adjudication": (
            TemporalKGFailureType.FALSE_MERGE_WITHOUT_ADJUDICATION.value,
            "adjudication_record_refs",
        ),
        "temporal-kg-false-split-without-supersession": (
            TemporalKGFailureType.FALSE_SPLIT_WITHOUT_SUPERSESSION.value,
            "supersession_refs",
        ),
        "temporal-kg-missing-replay": (
            TemporalKGFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_temporal_kg_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
