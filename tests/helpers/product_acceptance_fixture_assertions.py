from __future__ import annotations

from pathlib import Path

from veracrawl.cli.product_acceptance import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def assert_product_acceptance_fixture(
    fixture_dir: Path,
    *,
    out_dir: Path,
) -> None:
    report = run_fixture(fixture_dir, profile="target", out=out_dir)
    assert report.fixture_id == fixture_dir.name
    assert (out_dir / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.workflow_record_refs
        assert report.covered_workflows
        assert report.minimum_gate_refs
        assert report.evidence_refs
        assert report.replay_refs
        assert report.operator_visible_result_refs
        assert report.status_accuracy_refs
    elif report.completion_result == CompletenessResult.NEEDS_REVIEW:
        assert report.missing_runtime_refs or report.contract_only_refs
    else:
        assert report.failure_type
        assert report.failure_report_refs or report.missing_ref_fields
