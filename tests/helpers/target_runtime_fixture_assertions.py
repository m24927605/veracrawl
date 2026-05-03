from __future__ import annotations

from pathlib import Path

from veracrawl.cli.target_runtime import run_fixture
from veracrawl.contracts.enums import TargetRuntimeStatus
from veracrawl.contracts.target_runtime import TargetRuntimeReport


def assert_target_runtime_fixture(
    fixture_dir: Path,
    *,
    out_dir: Path,
) -> TargetRuntimeReport:
    report = run_fixture(fixture_dir, profile="target", out=out_dir)
    assert (out_dir / "run_report.json").exists()
    if report.status == TargetRuntimeStatus.COMPLETE:
        assert len(set(report.covered_patterns)) >= 7
        assert report.accepted_output_refs
        assert report.evidence_refs
        assert report.graph_refs
        assert report.export_receipt_refs
        assert report.replay_bundle_ref
    elif report.status == TargetRuntimeStatus.NEEDS_REVIEW:
        assert report.review_item_refs or report.recovery_action_refs
        assert report.missing_ref_fields
    else:
        assert report.failure_type
        assert report.failure_report_refs
    return report
