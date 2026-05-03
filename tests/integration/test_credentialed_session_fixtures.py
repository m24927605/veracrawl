from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.credentialed_session import run_fixture
from veracrawl.contracts.enums import CompletenessResult

CREDENTIALED_SESSION_FIXTURES = [
    "credentialed-session-success",
    "credentialed-session-missing-authorization",
    "credentialed-session-out-of-scope",
    "credentialed-session-raw-secret-leak",
    "credentialed-session-unsafe-use",
    "credentialed-session-missing-audit",
    "credentialed-session-missing-redacted-replay",
    "credentialed-session-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", CREDENTIALED_SESSION_FIXTURES)
def test_credentialed_session_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    assert report.live_http_acquisition_report_ref
    assert report.browser_snapshot_runtime_report_ref
    if report.completion_result == CompletenessResult.PASS:
        assert report.credential_scope_refs
        assert report.authorized_origin_refs
        assert report.approval_decision_refs
        assert report.credential_use_audit_refs
        assert report.session_adapter_result_refs
        assert report.session_state_refs
        assert report.redaction_map_refs
        assert report.redacted_artifact_refs
        assert report.redacted_replay_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
        assert not report.raw_secret_leak_refs
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
