from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.live_normalization import run_fixture
from veracrawl.contracts.enums import CompletenessResult

LIVE_NORMALIZATION_FIXTURES = [
    "live-normalization-listing-success",
    "live-normalization-detail-success",
    "live-normalization-browser-success",
    "live-normalization-missing-upstream",
    "live-normalization-empty-content",
    "live-normalization-missing-anchor-map",
    "live-normalization-missing-site-model",
    "live-normalization-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", LIVE_NORMALIZATION_FIXTURES)
def test_live_normalization_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.live_http_acquisition_report_ref
        assert report.structured_source_adapters_runtime_report_ref
        assert report.browser_snapshot_runtime_report_ref
        assert report.normalized_document_refs
        assert report.normalization_manifest_refs
        assert report.anchor_map_refs
        assert report.source_anchor_refs
        assert report.link_analysis_refs
        assert report.page_type_classification_refs
        assert report.site_model_refs
        assert report.raw_artifact_refs
        assert report.normalized_artifact_refs
        assert report.artifact_refs
        assert report.policy_decision_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
        assert report.derived_context_refs
        if fixture_id == "live-normalization-listing-success":
            assert report.link_provenance_refs
        else:
            assert report.link_provenance_refs == []
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
