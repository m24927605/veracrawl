"""Deterministic source coverage contract adapters."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AdapterType, CompletenessResult
from veracrawl.contracts.source_coverage import (
    EXPECTED_NATURAL_RESULT_TYPES,
    REQUIRED_SOURCE_ADAPTER_TYPES,
    SourceCoverageAdapterExecutionRecord,
)


def adapter_slug(adapter_type: AdapterType) -> str:
    return adapter_type.value.replace("_", "-")


def build_contract_execution_records(
    fixture_id: str,
    *,
    adapter_types: list[AdapterType] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> list[SourceCoverageAdapterExecutionRecord]:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:source-coverage"]
    return [
        build_contract_execution_record(
            fixture_id,
            adapter_type=adapter_type,
            policy_decision_refs=policy_refs,
        )
        for adapter_type in (adapter_types or list(REQUIRED_SOURCE_ADAPTER_TYPES))
    ]


def build_contract_execution_record(
    fixture_id: str,
    *,
    adapter_type: AdapterType,
    policy_decision_refs: list[Ref],
) -> SourceCoverageAdapterExecutionRecord:
    slug = adapter_slug(adapter_type)
    fetch_refs = [f"fetch-attempt:{fixture_id}:{slug}"] if adapter_type == AdapterType.HTTP else []
    page_refs = (
        [f"page-snapshot:{fixture_id}:{slug}"]
        if adapter_type in {AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT}
        else []
    )
    browser_refs = (
        [f"browser-interaction:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.BROWSER_SNAPSHOT
        else []
    )
    credential_refs = (
        [f"credential-use-audit:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.AUTHORIZED_SESSION
        else []
    )
    document_refs = (
        [f"document-artifact:{fixture_id}:{slug}"]
        if adapter_type in {AdapterType.DOCUMENT_SOURCE, AdapterType.FILE_IMPORT}
        else []
    )
    api_refs = (
        [f"api-payload:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.API_SOURCE
        else []
    )
    return SourceCoverageAdapterExecutionRecord(
        id=f"source-coverage-execution:{fixture_id}:{slug}",
        adapter_type=adapter_type,
        natural_result_type=EXPECTED_NATURAL_RESULT_TYPES[adapter_type],
        source_adapter_spec_ref=f"source-adapter-spec:{fixture_id}:{slug}",
        source_adapter_result_ref=f"source-adapter-result:{fixture_id}:{slug}",
        natural_result_refs=[f"source-natural-result:{fixture_id}:{slug}"],
        fetch_attempt_refs=fetch_refs,
        page_snapshot_refs=page_refs,
        browser_interaction_refs=browser_refs,
        credential_audit_refs=credential_refs,
        document_artifact_refs=document_refs,
        api_payload_refs=api_refs,
        command_result_refs=[f"command-result:{fixture_id}:{slug}:source"],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:source-coverage"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:source-coverage"
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:source-coverage",
        live_runtime_refs=[f"source-runtime:{fixture_id}:{slug}:contract"],
        contract_adapter_refs=[f"source-coverage-contract-adapter:{fixture_id}:{slug}"],
        diagnostic_adapter_state_refs=[f"diagnostic-source-state:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )
