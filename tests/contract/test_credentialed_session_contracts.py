from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, CredentialedSessionFailureType
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)
from veracrawl.contracts.security_privacy import (
    CredentialedSessionFixtureManifest,
    CredentialedSessionRuntimeReport,
)


def _passing_report() -> CredentialedSessionRuntimeReport:
    return CredentialedSessionRuntimeReport(
        id="credentialed-session-runtime-report:test",
        fixture_id="credentialed-session-success",
        run_ref="run:test",
        live_http_acquisition_report_ref="live-http-acquisition-report:test",
        browser_snapshot_runtime_report_ref="browser-snapshot-runtime-report:test",
        credential_scope_refs=["credential-scope:test:readonly"],
        authorized_origin_refs=["origin:http://example.test"],
        approval_decision_refs=["approval:test:credential-use"],
        credential_use_audit_refs=["credential-use-audit:test:session"],
        session_adapter_result_refs=["source-result:test:authorized-session"],
        session_state_refs=["session-state-redacted:test:scoped"],
        redaction_map_refs=["redaction-map:test:credential"],
        redacted_artifact_refs=["artifact-redacted:test:session"],
        redacted_replay_refs=["replay-bundle:test:redacted"],
        policy_decision_refs=["policy:test:credentialed-session"],
        command_record_refs=["durable-command:test"],
        event_cursor_refs=["event-cursor:test"],
        outbox_refs=["outbox:test"],
        replay_bundle_ref="replay-bundle:test:credentialed-session",
        operator_status="credentialed_session_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_credentialed_session_report_requires_audit_and_redacted_replay() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        CredentialedSessionRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"credential_use_audit_refs": []}
        )
    with pytest.raises(ValidationError):
        CredentialedSessionRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"redacted_replay_refs": []}
        )


def test_credentialed_session_report_rejects_raw_secret_canonical_pass() -> None:
    report = _passing_report()
    with pytest.raises(ValidationError):
        CredentialedSessionRuntimeReport.model_validate(
            report.model_dump(mode="json")
            | {"raw_secret_leak_refs": ["raw-secret-leak:test:credential"]}
        )


def test_credentialed_session_failure_requires_typed_diagnostics() -> None:
    failure = CredentialedSessionRuntimeReport(
        id="credentialed-session-runtime-report:failure",
        fixture_id="credentialed-session-raw-secret-leak",
        run_ref="run:failure",
        raw_secret_leak_refs=["raw-secret-leak:failure:credential"],
        failure_report_refs=["failure:credentialed-session-raw-secret-leak"],
        missing_ref_fields=["raw_secret_leak_refs"],
        failure_type=CredentialedSessionFailureType.RAW_SECRET_LEAK,
        operator_status=CredentialedSessionFailureType.RAW_SECRET_LEAK.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == CredentialedSessionFailureType.RAW_SECRET_LEAK
    with pytest.raises(ValidationError):
        CredentialedSessionRuntimeReport(
            id="credentialed-session-runtime-report:bad",
            fixture_id="credentialed-session-bad",
            run_ref="run:bad",
            operator_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_credentialed_session_manifest_requires_target_and_failure_type() -> None:
    manifest = CredentialedSessionFixtureManifest(
        id="credentialed-session-success",
        scenario="credentialed-session-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="credentialed_session_completed",
        required_ref_types=["credential_audit", "redacted_replay"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        CredentialedSessionFixtureManifest(
            id="credentialed-session-missing-authorization",
            scenario="credentialed-session-missing-authorization",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=CredentialedSessionFailureType.MISSING_AUTHORIZATION.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_credentialed_session_registry_is_materialized() -> None:
    assert "CredentialedSessionRuntimeReport" in FOUNDATION_CONTRACTS
    assert "CredentialedSessionFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_credentialed_session_runtime_report" in COMMAND_TYPES
    assert "record_credentialed_session_fixture_manifest" in COMMAND_TYPES
    assert "credentialed_session_runtime_reported" in EVENT_TYPES
    assert "credentialed-session-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["credentialed_session_runtime"]
    assert area.coverage_status == "materialized"
    assert "CredentialedSessionRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
