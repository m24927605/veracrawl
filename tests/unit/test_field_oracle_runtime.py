from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.field_oracle import run_field_oracle_benchmark
from veracrawl.contracts.enums import CompletenessResult, FieldOracleFailureType
from veracrawl.contracts.field_oracle import FieldOracleBenchmarkManifest
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest(
    *,
    scenario: str = "field-oracle-quality-corpus",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: FieldOracleFailureType | None = None,
) -> FieldOracleBenchmarkManifest:
    return FieldOracleBenchmarkManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["quality"],
        generated_schema_count=8,
        generated_fields_per_schema=25,
        expected_completion_result=expected_result,
        expected_operator_status=(
            expected_failure.value if expected_failure else "field_oracle_completed"
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_ref_types=["schema", "field", "replay"],
    )


def test_field_oracle_runtime_evaluates_8_schemas_and_200_fields(tmp_path: Path) -> None:
    result = run_field_oracle_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.schema_count == 8
    assert result.report.expected_field_count == 200
    assert result.report.evaluated_field_count == 200
    assert result.report.accepted_field_count == 200
    assert result.report.exact_match_count > 0
    assert result.report.normalized_match_count > 0
    assert result.report.acceptable_partial_count > 0
    assert all(item.source_anchor_refs for item in result.evaluations)
    assert all(item.evidence_packet_refs for item in result.evaluations)
    assert all(item.verification_decision_refs for item in result.evaluations)


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("field-oracle-wrong-value", FieldOracleFailureType.WRONG_VALUE),
        ("field-oracle-missing-anchor", FieldOracleFailureType.MISSING_ANCHOR),
        ("field-oracle-schema-violation", FieldOracleFailureType.SCHEMA_VIOLATION),
        ("field-oracle-stale-evidence", FieldOracleFailureType.STALE_EVIDENCE),
        ("field-oracle-publication-bypass", FieldOracleFailureType.PUBLICATION_BYPASS),
        ("field-oracle-llm-as-evidence", FieldOracleFailureType.LLM_AS_EVIDENCE),
    ],
)
def test_field_oracle_runtime_maps_negative_fixtures(
    tmp_path: Path,
    scenario: str,
    failure: FieldOracleFailureType,
) -> None:
    result = run_field_oracle_benchmark(
        manifest=_manifest(
            scenario=scenario,
            expected_result=CompletenessResult.FAIL,
            expected_failure=failure,
        ),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
