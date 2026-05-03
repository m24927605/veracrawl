from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.live_http import run_fixture
from veracrawl.contracts.enums import CompletenessResult

LIVE_HTTP_FIXTURES = [
    "live-http-success",
    "live-http-redirect",
    "live-http-scope-denied",
    "live-http-private-denied",
    "live-http-malformed-response",
    "live-http-missing-artifact",
    "live-http-replay-mismatch",
    "live-http-direct-source-bypass",
]


@pytest.mark.parametrize("fixture_id", LIVE_HTTP_FIXTURES)
def test_live_http_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    assert report.run_control_report_ref
    assert report.production_persistence_report_ref
    if report.completion_result == CompletenessResult.PASS:
        assert report.network_response_ref
        assert report.source_observation_refs
        assert report.artifact_refs
        assert report.content_hash_refs
        assert report.replay_bundle_ref
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields


def test_live_http_redirect_fixture_records_redirect_lineage(tmp_path: Path) -> None:
    report = run_fixture(
        Path("tests/fixtures/live-http-redirect"),
        profile="target",
        out=tmp_path / "redirect",
    )

    assert report.completion_result == CompletenessResult.PASS
    assert report.redirect_hop_refs
    assert report.canonical_url_refs
