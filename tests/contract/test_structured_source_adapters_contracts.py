from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    StructuredSourceAdapterFailureType,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)
from veracrawl.contracts.source_runtime import (
    REQUIRED_STRUCTURED_SOURCE_ADAPTERS,
    StructuredSourceAdapterRecord,
    StructuredSourceAdaptersFixtureManifest,
    StructuredSourceAdaptersRuntimeReport,
)


def _record(adapter_type: AdapterType = AdapterType.SITEMAP) -> StructuredSourceAdapterRecord:
    kwargs = {
        "id": f"structured-source-adapter-record:{adapter_type.value}",
        "adapter_type": adapter_type,
        "source_adapter_result_ref": f"source-result:{adapter_type.value}",
        "natural_result_refs": [f"natural:{adapter_type.value}"],
        "artifact_refs": [f"artifact:{adapter_type.value}"],
        "metadata_refs": [f"metadata:{adapter_type.value}"],
        "evidence_seed_refs": [f"evidence-seed:{adapter_type.value}"],
        "fetch_attempt_refs": [f"fetch-attempt:{adapter_type.value}:1"],
        "fetch_result_refs": [f"fetch-result:{adapter_type.value}"],
        "page_snapshot_refs": [f"page-snapshot:{adapter_type.value}"],
        "policy_decision_refs": [f"policy:{adapter_type.value}"],
        "command_record_refs": [f"durable-command:{adapter_type.value}"],
        "event_cursor_refs": [f"event-cursor:{adapter_type.value}"],
        "outbox_refs": [f"outbox:{adapter_type.value}"],
        "replay_refs": [f"replay:{adapter_type.value}"],
        "content_hash_refs": [f"hash:{adapter_type.value}"],
        "result": CompletenessResult.PASS,
    }
    if adapter_type in {AdapterType.SITEMAP, AdapterType.RSS}:
        kwargs["discovered_url_refs"] = [f"url-ref:{adapter_type.value}"]
    if adapter_type == AdapterType.API_SOURCE:
        kwargs["api_payload_refs"] = ["api-payload:test"]
    if adapter_type == AdapterType.DOCUMENT_SOURCE:
        kwargs["document_artifact_refs"] = ["document-artifact:test"]
    if adapter_type == AdapterType.FILE_IMPORT:
        kwargs["file_artifact_refs"] = ["file-artifact:test"]
    return StructuredSourceAdapterRecord(**kwargs)


def test_structured_source_record_requires_family_specific_refs() -> None:
    assert _record(AdapterType.API_SOURCE).api_payload_refs
    with pytest.raises(ValidationError):
        StructuredSourceAdapterRecord.model_validate(
            _record(AdapterType.API_SOURCE).model_dump(mode="json") | {"api_payload_refs": []}
        )


def test_structured_source_failure_requires_typed_diagnostics() -> None:
    failure = StructuredSourceAdapterRecord(
        id="structured-source-adapter-record:failure",
        adapter_type=AdapterType.SITEMAP,
        failure_report_refs=["failure:malformed"],
        missing_ref_fields=["natural_result_refs"],
        failure_type=StructuredSourceAdapterFailureType.MALFORMED_SOURCE,
        result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == StructuredSourceAdapterFailureType.MALFORMED_SOURCE
    with pytest.raises(ValidationError):
        StructuredSourceAdapterRecord(
            id="structured-source-adapter-record:bad",
            adapter_type=AdapterType.SITEMAP,
            result=CompletenessResult.FAIL,
        )


def test_structured_source_report_requires_all_adapter_families() -> None:
    records = [_record(adapter_type) for adapter_type in REQUIRED_STRUCTURED_SOURCE_ADAPTERS]
    report = StructuredSourceAdaptersRuntimeReport(
        id="structured-source-adapters-runtime-report:test",
        fixture_id="structured-source-adapters-success",
        run_ref="run:test",
        verified_adapter_types=list(REQUIRED_STRUCTURED_SOURCE_ADAPTERS),
        source_adapter_record_refs=[record.id for record in records],
        source_adapter_result_refs=[
            record.source_adapter_result_ref or "" for record in records
        ],
        natural_result_refs=[ref for record in records for ref in record.natural_result_refs],
        artifact_refs=[ref for record in records for ref in record.artifact_refs],
        evidence_seed_refs=[ref for record in records for ref in record.evidence_seed_refs],
        discovered_url_refs=[ref for record in records for ref in record.discovered_url_refs],
        api_payload_refs=[ref for record in records for ref in record.api_payload_refs],
        document_artifact_refs=[
            ref for record in records for ref in record.document_artifact_refs
        ],
        file_artifact_refs=[ref for record in records for ref in record.file_artifact_refs],
        fetch_attempt_refs=[ref for record in records for ref in record.fetch_attempt_refs],
        fetch_result_refs=[ref for record in records for ref in record.fetch_result_refs],
        page_snapshot_refs=[ref for record in records for ref in record.page_snapshot_refs],
        policy_decision_refs=[ref for record in records for ref in record.policy_decision_refs],
        command_record_refs=[ref for record in records for ref in record.command_record_refs],
        event_cursor_refs=[ref for record in records for ref in record.event_cursor_refs],
        outbox_refs=[ref for record in records for ref in record.outbox_refs],
        replay_bundle_ref="replay-bundle:test",
        operator_status="structured_source_adapters_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        StructuredSourceAdaptersRuntimeReport.model_validate(
            report.model_dump(mode="json")
            | {"verified_adapter_types": [AdapterType.SITEMAP.value]}
        )


def test_structured_source_manifest_requires_target_and_failure_type() -> None:
    manifest = StructuredSourceAdaptersFixtureManifest(
        id="structured-source-adapters-success",
        scenario="structured-source-adapters-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="structured_source_adapters_completed",
        required_ref_types=["sitemap", "rss", "api", "document", "file"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        StructuredSourceAdaptersFixtureManifest(
            id="structured-source-adapters-policy-denied",
            scenario="structured-source-adapters-policy-denied",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=StructuredSourceAdapterFailureType.POLICY_DENIED.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_structured_source_registry_is_materialized() -> None:
    assert "StructuredSourceAdapterRecord" in FOUNDATION_CONTRACTS
    assert "StructuredSourceAdaptersRuntimeReport" in FOUNDATION_CONTRACTS
    assert "StructuredSourceAdaptersFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_structured_source_adapters_runtime_report" in COMMAND_TYPES
    assert "structured_source_adapters_runtime_reported" in EVENT_TYPES
    assert "structured-source-adapters-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["structured_source_adapters_runtime"]
    assert area.coverage_status == "materialized"
    assert "StructuredSourceAdaptersRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
