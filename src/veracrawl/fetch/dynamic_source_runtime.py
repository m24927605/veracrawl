"""Core dynamic source adapter runtime gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult, DynamicSourceRuntimeFailureType
from veracrawl.contracts.source_runtime import (
    REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS,
    DynamicSourceRuntimeAdapterRecord,
    DynamicSourceRuntimeReport,
)


@dataclass(frozen=True)
class DynamicSourceRuntimeGateResult:
    adapter_records: list[DynamicSourceRuntimeAdapterRecord]
    report: DynamicSourceRuntimeReport


_FAILURES: dict[str, tuple[DynamicSourceRuntimeFailureType, str]] = {
    "dynamic-source-runtime-raw-secret-leak": (
        DynamicSourceRuntimeFailureType.RAW_SECRET_LEAK,
        "raw_secret_leak_refs",
    ),
    "dynamic-source-runtime-adapter-state-canonical": (
        DynamicSourceRuntimeFailureType.ADAPTER_NATIVE_STATE_CANONICAL,
        "adapter_native_state_canonical_refs",
    ),
    "dynamic-source-runtime-missing-credential-audit": (
        DynamicSourceRuntimeFailureType.MISSING_CREDENTIAL_AUDIT,
        "credential_audit_refs",
    ),
    "dynamic-source-runtime-missing-document-artifact": (
        DynamicSourceRuntimeFailureType.MISSING_DOCUMENT_ARTIFACT,
        "document_artifact_refs",
    ),
    "dynamic-source-runtime-missing-api-payload": (
        DynamicSourceRuntimeFailureType.MISSING_API_PAYLOAD,
        "api_payload_refs",
    ),
    "dynamic-source-runtime-missing-replay": (
        DynamicSourceRuntimeFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "dynamic-source-runtime-unsafe-browser-side-effect": (
        DynamicSourceRuntimeFailureType.UNSAFE_BROWSER_SIDE_EFFECT,
        "unsafe_browser_side_effect_refs",
    ),
    "dynamic-source-runtime-unsupported-adapter": (
        DynamicSourceRuntimeFailureType.UNSUPPORTED_ADAPTER,
        "unsupported_adapter_refs",
    ),
}


def run_dynamic_source_runtime_gate(
    *,
    fixture_id: str,
    scenario: str,
    adapter_records: list[DynamicSourceRuntimeAdapterRecord] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> DynamicSourceRuntimeGateResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:dynamic-source-runtime"]
    if scenario == "dynamic-source-runtime-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if not adapter_records:
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    return _success_result(
        fixture_id=fixture_id,
        adapter_records=adapter_records,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    adapter_records: list[DynamicSourceRuntimeAdapterRecord],
    policy_refs: list[Ref],
) -> DynamicSourceRuntimeGateResult:
    policy_decision_refs = _dedupe(
        policy_refs + [ref for record in adapter_records for ref in record.policy_decision_refs]
    )
    report = DynamicSourceRuntimeReport(
        id=f"dynamic-source-runtime-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        adapter_record_refs=[record.id for record in adapter_records],
        required_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
        verified_adapter_types=[record.adapter_type for record in adapter_records],
        source_adapter_result_refs=[
            record.source_adapter_result_ref for record in adapter_records
        ],
        natural_result_refs=[
            ref for record in adapter_records for ref in record.natural_result_refs
        ],
        fetch_attempt_refs=[
            ref for record in adapter_records for ref in record.fetch_attempt_refs
        ],
        page_snapshot_refs=[
            ref for record in adapter_records for ref in record.page_snapshot_refs
        ],
        browser_interaction_refs=[
            ref for record in adapter_records for ref in record.browser_interaction_refs
        ],
        credential_audit_refs=[
            ref for record in adapter_records for ref in record.credential_audit_refs
        ],
        document_artifact_refs=[
            ref for record in adapter_records for ref in record.document_artifact_refs
        ],
        api_payload_refs=[
            ref for record in adapter_records for ref in record.api_payload_refs
        ],
        file_artifact_refs=[
            ref for record in adapter_records for ref in record.file_artifact_refs
        ],
        seed_plan_refs=[ref for record in adapter_records for ref in record.seed_plan_refs],
        prior_snapshot_refs=[
            ref for record in adapter_records for ref in record.prior_snapshot_refs
        ],
        command_record_refs=[
            ref for record in adapter_records for ref in record.command_result_refs
        ],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[
            ref for record in adapter_records for ref in record.observability_report_refs
        ],
        security_privacy_report_refs=[
            ref for record in adapter_records for ref in record.security_privacy_report_refs
        ],
        event_cursor_refs=[
            ref for record in adapter_records for ref in record.event_cursor_refs
        ],
        outbox_refs=[ref for record in adapter_records for ref in record.outbox_refs],
        runtime_adapter_refs=[
            ref for record in adapter_records for ref in record.live_runtime_refs
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dynamic-source-runtime",
        operator_status="dynamic_source_runtime_completed",
        completion_result=CompletenessResult.PASS,
    )
    return DynamicSourceRuntimeGateResult(adapter_records=adapter_records, report=report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> DynamicSourceRuntimeGateResult:
    report = DynamicSourceRuntimeReport(
        id=f"dynamic-source-runtime-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:dynamic-source-runtime"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:{adapter_type.value.replace('_', '-')}"
            for adapter_type in REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="dynamic_source_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return DynamicSourceRuntimeGateResult(adapter_records=[], report=report)


def _failure_result(
    *,
    fixture_id: str,
    failure: DynamicSourceRuntimeFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> DynamicSourceRuntimeGateResult:
    report = DynamicSourceRuntimeReport(
        id=f"dynamic-source-runtime-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
        policy_decision_refs=policy_refs,
        raw_secret_leak_refs=(
            [f"raw-secret-leak:{fixture_id}:dynamic-source-runtime"]
            if missing_field == "raw_secret_leak_refs"
            else []
        ),
        adapter_native_state_canonical_refs=(
            [f"adapter-native-state:{fixture_id}:canonical"]
            if missing_field == "adapter_native_state_canonical_refs"
            else []
        ),
        unsafe_browser_side_effect_refs=(
            [f"unsafe-browser-side-effect:{fixture_id}:dynamic-source-runtime"]
            if missing_field == "unsafe_browser_side_effect_refs"
            else []
        ),
        unsupported_adapter_refs=(
            [f"unsupported-adapter:{fixture_id}:unknown"]
            if missing_field == "unsupported_adapter_refs"
            else []
        ),
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return DynamicSourceRuntimeGateResult(adapter_records=[], report=report)


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
