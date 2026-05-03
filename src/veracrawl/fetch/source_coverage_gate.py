"""Core source coverage adapter operational gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult, SourceCoverageFailureType
from veracrawl.contracts.source_coverage import (
    REQUIRED_SOURCE_ADAPTER_TYPES,
    SourceCoverageAdapterExecutionRecord,
    SourceCoverageAdapterReport,
)


@dataclass(frozen=True)
class SourceCoverageAdapterGateResult:
    execution_records: list[SourceCoverageAdapterExecutionRecord]
    report: SourceCoverageAdapterReport


_FAILURES: dict[str, tuple[SourceCoverageFailureType, str]] = {
    "source-coverage-adapter-native-state-canonical": (
        SourceCoverageFailureType.ADAPTER_NATIVE_STATE_CANONICAL,
        "adapter_native_state_canonical_refs",
    ),
    "source-coverage-adapter-raw-secret-leak": (
        SourceCoverageFailureType.RAW_SECRET_LEAK,
        "raw_secret_leak_refs",
    ),
    "source-coverage-adapter-missing-browser-refs": (
        SourceCoverageFailureType.MISSING_BROWSER_REFS,
        "browser_interaction_refs",
    ),
    "source-coverage-adapter-missing-credential-audit": (
        SourceCoverageFailureType.MISSING_CREDENTIAL_AUDIT,
        "credential_audit_refs",
    ),
    "source-coverage-adapter-missing-document-artifact": (
        SourceCoverageFailureType.MISSING_DOCUMENT_ARTIFACT,
        "document_artifact_refs",
    ),
    "source-coverage-adapter-missing-api-payload": (
        SourceCoverageFailureType.MISSING_API_PAYLOAD,
        "api_payload_refs",
    ),
    "source-coverage-adapter-missing-replay": (
        SourceCoverageFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "source-coverage-adapter-unsafe-browser-side-effect": (
        SourceCoverageFailureType.UNSAFE_BROWSER_SIDE_EFFECT,
        "unsafe_browser_side_effect_refs",
    ),
    "source-coverage-adapter-unsupported-adapter": (
        SourceCoverageFailureType.UNSUPPORTED_ADAPTER,
        "unsupported_adapter_refs",
    ),
}


def run_source_coverage_adapter_gate(
    *,
    fixture_id: str,
    scenario: str,
    execution_records: list[SourceCoverageAdapterExecutionRecord] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> SourceCoverageAdapterGateResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:source-coverage"]
    if scenario == "source-coverage-adapter-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if not execution_records:
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    return _success_result(
        fixture_id=fixture_id,
        execution_records=execution_records,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    execution_records: list[SourceCoverageAdapterExecutionRecord],
    policy_refs: list[Ref],
) -> SourceCoverageAdapterGateResult:
    policy_decision_refs = _dedupe(
        policy_refs
        + [ref for record in execution_records for ref in record.policy_decision_refs]
    )
    report = SourceCoverageAdapterReport(
        id=f"source-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        adapter_execution_refs=[record.id for record in execution_records],
        required_adapter_types=list(REQUIRED_SOURCE_ADAPTER_TYPES),
        verified_adapter_types=[record.adapter_type for record in execution_records],
        source_adapter_result_refs=[
            record.source_adapter_result_ref for record in execution_records
        ],
        natural_result_refs=[
            ref for record in execution_records for ref in record.natural_result_refs
        ],
        fetch_attempt_refs=[
            ref for record in execution_records for ref in record.fetch_attempt_refs
        ],
        page_snapshot_refs=[
            ref for record in execution_records for ref in record.page_snapshot_refs
        ],
        browser_interaction_refs=[
            ref for record in execution_records for ref in record.browser_interaction_refs
        ],
        credential_audit_refs=[
            ref for record in execution_records for ref in record.credential_audit_refs
        ],
        document_artifact_refs=[
            ref for record in execution_records for ref in record.document_artifact_refs
        ],
        api_payload_refs=[
            ref for record in execution_records for ref in record.api_payload_refs
        ],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[
            ref for record in execution_records for ref in record.observability_report_refs
        ],
        security_privacy_report_refs=[
            ref for record in execution_records for ref in record.security_privacy_report_refs
        ],
        command_record_refs=[
            ref for record in execution_records for ref in record.command_result_refs
        ],
        event_cursor_refs=[f"event-cursor:{fixture_id}:source-coverage"],
        outbox_refs=[f"outbox:{fixture_id}:source-coverage"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:source-coverage",
        operator_status="source_coverage_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    return SourceCoverageAdapterGateResult(execution_records=execution_records, report=report)


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> SourceCoverageAdapterGateResult:
    report = SourceCoverageAdapterReport(
        id=f"source-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_SOURCE_ADAPTER_TYPES),
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:source-coverage"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:{adapter_type.value.replace('_', '-')}"
            for adapter_type in REQUIRED_SOURCE_ADAPTER_TYPES
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="source_coverage_adapter_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return SourceCoverageAdapterGateResult(execution_records=[], report=report)


def _failure_result(
    *,
    fixture_id: str,
    failure: SourceCoverageFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> SourceCoverageAdapterGateResult:
    report = SourceCoverageAdapterReport(
        id=f"source-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_SOURCE_ADAPTER_TYPES),
        verified_adapter_types=[],
        policy_decision_refs=policy_refs,
        raw_secret_leak_refs=(
            [f"raw-secret-leak:{fixture_id}:source-coverage"]
            if missing_field == "raw_secret_leak_refs"
            else []
        ),
        adapter_native_state_canonical_refs=(
            [f"adapter-native-state:{fixture_id}:canonical"]
            if missing_field == "adapter_native_state_canonical_refs"
            else []
        ),
        unsafe_browser_side_effect_refs=(
            [f"unsafe-browser-side-effect:{fixture_id}:source-coverage"]
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
    return SourceCoverageAdapterGateResult(execution_records=[], report=report)
