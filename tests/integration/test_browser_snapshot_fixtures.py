from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.browser_snapshot import run_fixture
from veracrawl.contracts.enums import CompletenessResult

BROWSER_SNAPSHOT_FIXTURES = [
    "browser-snapshot-success",
    "browser-snapshot-egress-denied",
    "browser-snapshot-unsafe-interaction",
    "browser-snapshot-budget-exceeded",
    "browser-snapshot-prompt-tainted-content",
    "browser-snapshot-missing-artifact",
    "browser-snapshot-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", BROWSER_SNAPSHOT_FIXTURES)
def test_browser_snapshot_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    assert report.live_http_acquisition_report_ref
    assert report.structured_source_adapters_runtime_report_ref
    if report.completion_result == CompletenessResult.PASS:
        assert report.browser_step_ref
        assert report.dom_artifact_refs
        assert report.screenshot_artifact_refs
        assert report.network_trace_refs
        assert report.console_log_refs
        assert report.timing_refs
        assert report.browser_budget_refs
        assert report.prompt_taint_boundary_refs
        assert report.artifact_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
