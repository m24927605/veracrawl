"""Structured source adapter runtime aggregate gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    StructuredSourceAdapterFailureType,
)
from veracrawl.contracts.source_runtime import (
    REQUIRED_STRUCTURED_SOURCE_ADAPTERS,
    StructuredSourceAdapterRecord,
    StructuredSourceAdaptersRuntimeReport,
)


@dataclass(frozen=True)
class StructuredSourceAdaptersRuntimeResult:
    adapter_records: list[StructuredSourceAdapterRecord]
    report: StructuredSourceAdaptersRuntimeReport


_FAILURES: dict[str, tuple[StructuredSourceAdapterFailureType, str]] = {
    "structured-source-adapters-policy-denied": (
        StructuredSourceAdapterFailureType.POLICY_DENIED,
        "policy_decision_refs",
    ),
    "structured-source-adapters-malformed-source": (
        StructuredSourceAdapterFailureType.MALFORMED_SOURCE,
        "natural_result_refs",
    ),
    "structured-source-adapters-unsupported-adapter": (
        StructuredSourceAdapterFailureType.UNSUPPORTED_ADAPTER,
        "adapter_type",
    ),
    "structured-source-adapters-replay-mismatch": (
        StructuredSourceAdapterFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_structured_source_adapters_runtime(
    *,
    fixture_id: str,
    scenario: str,
    adapter_records: list[StructuredSourceAdapterRecord] | None,
    policy_decision_refs: list[Ref] | None = None,
) -> StructuredSourceAdaptersRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:structured-source"]
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if not adapter_records:
        return _failure_result(
            fixture_id=fixture_id,
            failure=StructuredSourceAdapterFailureType.UNSUPPORTED_ADAPTER,
            missing_field="adapter_records",
            policy_refs=policy_refs,
        )
    return _success_result(
        fixture_id=fixture_id,
        adapter_records=adapter_records,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    adapter_records: list[StructuredSourceAdapterRecord],
    policy_refs: list[Ref],
) -> StructuredSourceAdaptersRuntimeResult:
    policy_decision_refs = _dedupe(
        policy_refs + [ref for record in adapter_records for ref in record.policy_decision_refs]
    )
    report = StructuredSourceAdaptersRuntimeReport(
        id=f"structured-source-adapters-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_STRUCTURED_SOURCE_ADAPTERS),
        verified_adapter_types=[record.adapter_type for record in adapter_records],
        source_adapter_record_refs=[record.id for record in adapter_records],
        source_adapter_result_refs=[
            _required_ref(record.source_adapter_result_ref, "source_adapter_result_ref")
            for record in adapter_records
        ],
        natural_result_refs=[
            ref for record in adapter_records for ref in record.natural_result_refs
        ],
        artifact_refs=[ref for record in adapter_records for ref in record.artifact_refs],
        evidence_seed_refs=[
            ref for record in adapter_records for ref in record.evidence_seed_refs
        ],
        discovered_url_refs=[
            ref for record in adapter_records for ref in record.discovered_url_refs
        ],
        api_payload_refs=[
            ref for record in adapter_records for ref in record.api_payload_refs
        ],
        document_artifact_refs=[
            ref for record in adapter_records for ref in record.document_artifact_refs
        ],
        file_artifact_refs=[
            ref for record in adapter_records for ref in record.file_artifact_refs
        ],
        fetch_attempt_refs=[
            ref for record in adapter_records for ref in record.fetch_attempt_refs
        ],
        fetch_result_refs=[
            ref for record in adapter_records for ref in record.fetch_result_refs
        ],
        page_snapshot_refs=[
            ref for record in adapter_records for ref in record.page_snapshot_refs
        ],
        policy_decision_refs=policy_decision_refs,
        command_record_refs=[
            ref for record in adapter_records for ref in record.command_record_refs
        ],
        event_cursor_refs=[
            ref for record in adapter_records for ref in record.event_cursor_refs
        ],
        outbox_refs=[ref for record in adapter_records for ref in record.outbox_refs],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:structured-source-adapters",
        operator_status="structured_source_adapters_completed",
        completion_result=CompletenessResult.PASS,
    )
    return StructuredSourceAdaptersRuntimeResult(
        adapter_records=adapter_records,
        report=report,
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: StructuredSourceAdapterFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> StructuredSourceAdaptersRuntimeResult:
    report = StructuredSourceAdaptersRuntimeReport(
        id=f"structured-source-adapters-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        required_adapter_types=list(REQUIRED_STRUCTURED_SOURCE_ADAPTERS),
        policy_decision_refs=policy_refs,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=[f"structured source adapter runtime failed: {failure.value}"],
    )
    return StructuredSourceAdaptersRuntimeResult(adapter_records=[], report=report)


def _required_ref(value: Ref | None, field_name: str) -> Ref:
    if value is None:
        raise ValueError(f"structured source adapter record missing {field_name}")
    return value


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
