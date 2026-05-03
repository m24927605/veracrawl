from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.adapters.session.deterministic import DeterministicCredentialedSessionAdapter
from veracrawl.contracts.enums import CompletenessResult, CredentialedSessionFailureType
from veracrawl.fetch.credentialed_session import (
    CredentialedSessionRuntimeResult,
    run_credentialed_session_runtime,
)


def _run_success(
    fixture_id: str = "credentialed-session-success",
) -> CredentialedSessionRuntimeResult:
    return run_credentialed_session_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        target_origin="http://example.test",
        adapter=DeterministicCredentialedSessionAdapter(),
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        browser_snapshot_runtime_report_ref=(
            f"browser-snapshot-runtime-report:{fixture_id}"
        ),
    )


def test_credentialed_session_success_records_audit_redaction_and_replay_refs() -> None:
    result = _run_success()
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert result.credential_audit is not None
    assert report.live_http_acquisition_report_ref
    assert report.browser_snapshot_runtime_report_ref
    assert report.credential_scope_refs
    assert report.authorized_origin_refs
    assert report.approval_decision_refs
    assert report.credential_use_audit_refs == [result.credential_audit.id]
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


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "credentialed-session-missing-authorization",
            CredentialedSessionFailureType.MISSING_AUTHORIZATION,
        ),
        ("credentialed-session-out-of-scope", CredentialedSessionFailureType.OUT_OF_SCOPE),
        ("credentialed-session-raw-secret-leak", CredentialedSessionFailureType.RAW_SECRET_LEAK),
        (
            "credentialed-session-unsafe-use",
            CredentialedSessionFailureType.UNSAFE_CREDENTIAL_USE,
        ),
        ("credentialed-session-missing-audit", CredentialedSessionFailureType.MISSING_AUDIT),
        (
            "credentialed-session-missing-redacted-replay",
            CredentialedSessionFailureType.MISSING_REDACTED_REPLAY,
        ),
        ("credentialed-session-replay-mismatch", CredentialedSessionFailureType.REPLAY_MISMATCH),
    ],
)
def test_credentialed_session_negative_scenarios_are_typed(
    scenario: str,
    failure: CredentialedSessionFailureType,
) -> None:
    result = run_credentialed_session_runtime(
        fixture_id=scenario,
        scenario=scenario,
        target_origin="http://example.test",
        adapter=DeterministicCredentialedSessionAdapter(),
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{scenario}",
        browser_snapshot_runtime_report_ref=f"browser-snapshot-runtime-report:{scenario}",
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields


def test_credentialed_session_blocks_scope_mismatch() -> None:
    result = run_credentialed_session_runtime(
        fixture_id="credentialed-session-scope-mismatch",
        scenario="credentialed-session-scope-mismatch",
        target_origin="http://example.test",
        adapter=DeterministicCredentialedSessionAdapter(),
        live_http_acquisition_report_ref="live-http-acquisition-report:scope",
        browser_snapshot_runtime_report_ref="browser-snapshot-runtime-report:scope",
        authorized_origin_ref="origin:http://other.test",
    )

    assert result.report.failure_type == CredentialedSessionFailureType.OUT_OF_SCOPE


def test_credentialed_session_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(
        Path("src/veracrawl/fetch/credentialed_session.py").read_text(encoding="utf-8")
    )
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert all(not name.startswith("veracrawl.adapters") for name in imports)
