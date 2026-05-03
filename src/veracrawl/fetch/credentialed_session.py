"""Credentialed session runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    CredentialDeliveryMode,
    CredentialedSessionFailureType,
)
from veracrawl.contracts.security_privacy import (
    CredentialedSessionRuntimeReport,
    CredentialUseAudit,
)
from veracrawl.ports.session import CredentialedSessionAdapterPort


@dataclass(frozen=True)
class CredentialedSessionRuntimeResult:
    report: CredentialedSessionRuntimeReport
    credential_audit: CredentialUseAudit | None = None


_DIRECT_FAILURES: dict[str, tuple[CredentialedSessionFailureType, str]] = {
    "credentialed-session-missing-authorization": (
        CredentialedSessionFailureType.MISSING_AUTHORIZATION,
        "approval_decision_refs",
    ),
    "credentialed-session-out-of-scope": (
        CredentialedSessionFailureType.OUT_OF_SCOPE,
        "authorized_origin_refs",
    ),
    "credentialed-session-raw-secret-leak": (
        CredentialedSessionFailureType.RAW_SECRET_LEAK,
        "raw_secret_leak_refs",
    ),
    "credentialed-session-unsafe-use": (
        CredentialedSessionFailureType.UNSAFE_CREDENTIAL_USE,
        "credential_use_audit_refs",
    ),
    "credentialed-session-missing-audit": (
        CredentialedSessionFailureType.MISSING_AUDIT,
        "credential_use_audit_refs",
    ),
    "credentialed-session-missing-redacted-replay": (
        CredentialedSessionFailureType.MISSING_REDACTED_REPLAY,
        "redacted_replay_refs",
    ),
    "credentialed-session-replay-mismatch": (
        CredentialedSessionFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_credentialed_session_runtime(
    *,
    fixture_id: str,
    scenario: str,
    target_origin: str,
    adapter: CredentialedSessionAdapterPort | None,
    live_http_acquisition_report_ref: Ref,
    browser_snapshot_runtime_report_ref: Ref,
    credential_scope_ref: Ref | None = None,
    authorized_origin_ref: Ref | None = None,
    approval_decision_ref: Ref | None = None,
) -> CredentialedSessionRuntimeResult:
    credential_scope = credential_scope_ref or f"credential-scope:{fixture_id}:readonly"
    authorized_origin = authorized_origin_ref or f"origin:{target_origin}"
    approval_ref = approval_decision_ref or f"approval:{fixture_id}:credential-use"
    policy_refs = [f"policy:{fixture_id}:credentialed-session"]

    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
            credential_scope_refs=[credential_scope],
            authorized_origin_refs=[authorized_origin],
            approval_decision_refs=(
                [] if missing_field == "approval_decision_refs" else [approval_ref]
            ),
        )

    if authorized_origin != f"origin:{target_origin}":
        return _failure_result(
            fixture_id=fixture_id,
            failure=CredentialedSessionFailureType.OUT_OF_SCOPE,
            missing_field="authorized_origin_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
            credential_scope_refs=[credential_scope],
            authorized_origin_refs=[authorized_origin],
            approval_decision_refs=[approval_ref],
        )
    if adapter is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=CredentialedSessionFailureType.ADAPTER_UNAVAILABLE,
            missing_field="session_adapter_result_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
            credential_scope_refs=[credential_scope],
            authorized_origin_refs=[authorized_origin],
            approval_decision_refs=[approval_ref],
        )

    audit = _credential_audit(
        fixture_id=fixture_id,
        credential_scope_ref=credential_scope,
        authorized_origin_ref=authorized_origin,
        approval_decision_ref=approval_ref,
        policy_refs=policy_refs,
    )
    adapter_result = adapter.establish_session(
        fixture_id=fixture_id,
        credential_audit=audit,
        target_origin=target_origin,
    )
    if not adapter_result.redacted_replay_refs:
        return _failure_result(
            fixture_id=fixture_id,
            failure=CredentialedSessionFailureType.MISSING_REDACTED_REPLAY,
            missing_field="redacted_replay_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
            credential_scope_refs=[credential_scope],
            authorized_origin_refs=[authorized_origin],
            approval_decision_refs=[approval_ref],
            audit=audit,
        )

    report = CredentialedSessionRuntimeReport(
        id=f"credentialed-session-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        credential_scope_refs=[credential_scope],
        authorized_origin_refs=[authorized_origin],
        approval_decision_refs=[approval_ref],
        credential_use_audit_refs=[audit.id],
        session_adapter_result_refs=[adapter_result.session_adapter_result_ref],
        session_state_refs=[adapter_result.session_state_ref],
        redaction_map_refs=_dedupe(audit.redaction_map_refs + adapter_result.redaction_map_refs),
        redacted_artifact_refs=adapter_result.redacted_artifact_refs,
        redacted_replay_refs=adapter_result.redacted_replay_refs,
        policy_decision_refs=_dedupe(
            policy_refs + audit.policy_decision_refs + adapter_result.policy_decision_refs
        ),
        command_record_refs=_dedupe(audit.command_refs + adapter_result.command_record_refs),
        event_cursor_refs=adapter_result.event_cursor_refs,
        outbox_refs=adapter_result.outbox_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:credentialed-session",
        operator_status="credentialed_session_completed",
        completion_result=CompletenessResult.PASS,
    )
    return CredentialedSessionRuntimeResult(report=report, credential_audit=audit)


def _credential_audit(
    *,
    fixture_id: str,
    credential_scope_ref: Ref,
    authorized_origin_ref: Ref,
    approval_decision_ref: Ref,
    policy_refs: list[Ref],
) -> CredentialUseAudit:
    return CredentialUseAudit(
        id=f"credential-use-audit:{fixture_id}:session",
        credential_scope_ref=credential_scope_ref,
        authorized_origin_ref=authorized_origin_ref,
        delivery_mode=CredentialDeliveryMode.SCOPED_HEADER,
        policy_decision_refs=policy_refs,
        approval_decision_refs=[approval_decision_ref],
        redaction_map_refs=[f"redaction-map:{fixture_id}:credential"],
        prompt_context_refs=[f"context-redacted:{fixture_id}:credential-use"],
        command_refs=[f"durable-command:{fixture_id}:credential-use"],
        event_refs=[f"event:{fixture_id}:credential-use-audited"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:credentialed-session:redacted",
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: CredentialedSessionFailureType,
    missing_field: str,
    policy_refs: list[Ref],
    live_http_acquisition_report_ref: Ref,
    browser_snapshot_runtime_report_ref: Ref,
    credential_scope_refs: list[Ref],
    authorized_origin_refs: list[Ref],
    approval_decision_refs: list[Ref],
    audit: CredentialUseAudit | None = None,
) -> CredentialedSessionRuntimeResult:
    report = CredentialedSessionRuntimeReport(
        id=f"credentialed-session-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        credential_scope_refs=credential_scope_refs,
        authorized_origin_refs=authorized_origin_refs,
        approval_decision_refs=approval_decision_refs,
        credential_use_audit_refs=[] if missing_field == "credential_use_audit_refs" else (
            [audit.id] if audit else []
        ),
        policy_decision_refs=policy_refs,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        raw_secret_leak_refs=[
            f"raw-secret-leak:{fixture_id}:credential"
        ]
        if missing_field == "raw_secret_leak_refs"
        else [],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=[f"credentialed session runtime failed: {failure.value}"],
    )
    return CredentialedSessionRuntimeResult(report=report, credential_audit=audit)


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
