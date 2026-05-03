from __future__ import annotations

from pathlib import Path

from tests.helpers.output_type_coverage_fixture_assertions import (
    assert_output_type_coverage_needs_review,
    assert_output_type_coverage_negative,
    assert_output_type_coverage_success,
)
from veracrawl.cli.output_coverage import run_fixture
from veracrawl.contracts.enums import OutputTypeCoverageFailureType


def test_output_type_coverage_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "output-type-coverage-success",
        profile="target",
        out=tmp_path / "output-type-coverage-success",
    )
    assert_output_type_coverage_success(report)


def test_output_type_coverage_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "output-type-coverage-runtime-unavailable",
        profile="target",
        out=tmp_path / "output-type-coverage-runtime-unavailable",
    )
    assert_output_type_coverage_needs_review(report)


def test_output_type_coverage_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "output-type-coverage-missing-output-type": (
            OutputTypeCoverageFailureType.MISSING_OUTPUT_TYPE.value,
            "covered_output_types",
        ),
        "output-type-coverage-unsupported-output-type": (
            OutputTypeCoverageFailureType.UNSUPPORTED_OUTPUT_TYPE.value,
            "unsupported_output_type",
        ),
        "output-type-coverage-derived-context-as-evidence": (
            OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-candidate-as-evidence": (
            OutputTypeCoverageFailureType.CANDIDATE_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-graph-as-evidence": (
            OutputTypeCoverageFailureType.GRAPH_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-memory-as-evidence": (
            OutputTypeCoverageFailureType.MEMORY_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-agent-reasoning-as-evidence": (
            OutputTypeCoverageFailureType.AGENT_REASONING_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-temporal-kg-as-evidence": (
            OutputTypeCoverageFailureType.TEMPORAL_KG_AS_EVIDENCE.value,
            "source_evidence_refs",
        ),
        "output-type-coverage-missing-table-cell-evidence": (
            OutputTypeCoverageFailureType.MISSING_TABLE_CELL_EVIDENCE.value,
            "cell_anchor_refs",
        ),
        "output-type-coverage-missing-file-lifecycle": (
            OutputTypeCoverageFailureType.MISSING_FILE_LIFECYCLE.value,
            "file_artifact_hash_ref",
        ),
        "output-type-coverage-missing-dataset-item-evidence": (
            OutputTypeCoverageFailureType.MISSING_DATASET_ITEM_EVIDENCE.value,
            "dataset_item_evidence_refs",
        ),
        "output-type-coverage-missing-fact-verification": (
            OutputTypeCoverageFailureType.MISSING_FACT_VERIFICATION.value,
            "fact_verification_ref",
        ),
        "output-type-coverage-missing-replay": (
            OutputTypeCoverageFailureType.MISSING_REPLAY_REFS.value,
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
        assert_output_type_coverage_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
