from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    DynamicSourceRuntimeFailureType,
)
from veracrawl.contracts.source_runtime import (
    REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS,
    DynamicSourceRuntimeAdapterRecord,
    DynamicSourceRuntimeFixtureManifest,
    DynamicSourceRuntimeReport,
)


def _record(adapter_type: AdapterType = AdapterType.HTTP) -> DynamicSourceRuntimeAdapterRecord:
    return DynamicSourceRuntimeAdapterRecord(
        id=f"dynamic-source-runtime-record:{adapter_type.value}",
        adapter_type=adapter_type,
        source_adapter_result_ref=f"source-result:{adapter_type.value}",
        natural_result_refs=[f"natural:{adapter_type.value}"],
        fetch_attempt_refs=(
            [f"fetch-attempt:{adapter_type.value}"]
            if adapter_type == AdapterType.HTTP
            else []
        ),
        page_snapshot_refs=(
            [f"page-snapshot:{adapter_type.value}"]
            if adapter_type in {AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT}
            else []
        ),
        browser_interaction_refs=(
            [f"browser-step:{adapter_type.value}"]
            if adapter_type == AdapterType.BROWSER_SNAPSHOT
            else []
        ),
        credential_audit_refs=(
            [f"credential-use:{adapter_type.value}"]
            if adapter_type == AdapterType.AUTHORIZED_SESSION
            else []
        ),
        document_artifact_refs=(
            [f"document-artifact:{adapter_type.value}"]
            if adapter_type == AdapterType.DOCUMENT_SOURCE
            else []
        ),
        api_payload_refs=(
            [f"api-payload:{adapter_type.value}"]
            if adapter_type == AdapterType.API_SOURCE
            else []
        ),
        file_artifact_refs=(
            [f"file-artifact:{adapter_type.value}"]
            if adapter_type == AdapterType.FILE_IMPORT
            else []
        ),
        seed_plan_refs=(
            [f"seed-plan:{adapter_type.value}"]
            if adapter_type == AdapterType.MANUAL_SEED
            else []
        ),
        prior_snapshot_refs=(
            [f"prior-snapshot:{adapter_type.value}"]
            if adapter_type == AdapterType.PRIOR_SNAPSHOT
            else []
        ),
        command_result_refs=[f"command:{adapter_type.value}"],
        policy_decision_refs=[f"policy:{adapter_type.value}"],
        observability_report_refs=[f"observability:{adapter_type.value}"],
        security_privacy_report_refs=[f"security:{adapter_type.value}"],
        event_cursor_refs=[f"event-cursor:{adapter_type.value}"],
        outbox_refs=[f"outbox:{adapter_type.value}"],
        replay_bundle_ref=f"replay:{adapter_type.value}",
        live_runtime_refs=[f"runtime:{adapter_type.value}"],
        result=CompletenessResult.PASS,
    )


def test_dynamic_source_runtime_rejects_raw_secret_and_native_state() -> None:
    payload = _record().model_dump()
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(**(payload | {"raw_secret_persisted": True}))
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(payload | {"adapter_native_state_canonical": True})
        )


def test_dynamic_source_runtime_requires_adapter_specific_refs() -> None:
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(
                _record(AdapterType.BROWSER_SNAPSHOT).model_dump()
                | {"browser_interaction_refs": []}
            )
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(
                _record(AdapterType.AUTHORIZED_SESSION).model_dump()
                | {"credential_audit_refs": []}
            )
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(
                _record(AdapterType.DOCUMENT_SOURCE).model_dump()
                | {"document_artifact_refs": []}
            )
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(_record(AdapterType.API_SOURCE).model_dump() | {"api_payload_refs": []})
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(_record(AdapterType.FILE_IMPORT).model_dump() | {"file_artifact_refs": []})
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(_record(AdapterType.MANUAL_SEED).model_dump() | {"seed_plan_refs": []})
        )
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(_record(AdapterType.PRIOR_SNAPSHOT).model_dump() | {"prior_snapshot_refs": []})
        )


def test_dynamic_source_runtime_non_fetch_adapters_cannot_fake_fetch_refs() -> None:
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeAdapterRecord(
            **(
                _record(AdapterType.MANUAL_SEED).model_dump()
                | {"fetch_attempt_refs": ["fetch-attempt:bad"]}
            )
        )


def test_dynamic_source_runtime_report_requires_all_adapters() -> None:
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeReport(
            id="dynamic-source-runtime-report:bad",
            run_ref="run:bad",
            adapter_record_refs=["dynamic-source-runtime-record:http"],
            required_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
            verified_adapter_types=[AdapterType.HTTP],
            source_adapter_result_refs=["source-result:http"],
            natural_result_refs=["natural:http"],
            fetch_attempt_refs=["fetch-attempt:http"],
            page_snapshot_refs=["page-snapshot:http"],
            browser_interaction_refs=["browser-step:browser"],
            credential_audit_refs=["credential:auth"],
            document_artifact_refs=["document:doc"],
            api_payload_refs=["api:payload"],
            file_artifact_refs=["file:artifact"],
            seed_plan_refs=["seed:plan"],
            prior_snapshot_refs=["prior:snapshot"],
            command_record_refs=["command:bad"],
            policy_decision_refs=["policy:bad"],
            observability_report_refs=["observability:bad"],
            security_privacy_report_refs=["security:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            runtime_adapter_refs=["runtime:bad"],
            replay_bundle_ref="replay:bad",
            operator_status="dynamic_source_runtime_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_dynamic_source_runtime_report_accepts_complete_pass() -> None:
    report = DynamicSourceRuntimeReport(
        id="dynamic-source-runtime-report:ok",
        run_ref="run:ok",
        adapter_record_refs=[
            f"dynamic-source-runtime-record:{adapter_type.value}"
            for adapter_type in REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS
        ],
        required_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
        verified_adapter_types=list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS),
        source_adapter_result_refs=["source-result:ok"],
        natural_result_refs=["natural:ok"],
        fetch_attempt_refs=["fetch-attempt:ok"],
        page_snapshot_refs=["page-snapshot:ok"],
        browser_interaction_refs=["browser-step:ok"],
        credential_audit_refs=["credential-use:ok"],
        document_artifact_refs=["document-artifact:ok"],
        api_payload_refs=["api-payload:ok"],
        file_artifact_refs=["file-artifact:ok"],
        seed_plan_refs=["seed-plan:ok"],
        prior_snapshot_refs=["prior-snapshot:ok"],
        command_record_refs=["command:ok"],
        policy_decision_refs=["policy:ok"],
        observability_report_refs=["observability:ok"],
        security_privacy_report_refs=["security:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        runtime_adapter_refs=["runtime:ok"],
        replay_bundle_ref="replay:ok",
        operator_status="dynamic_source_runtime_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.verified_adapter_types == list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS)


def test_dynamic_source_runtime_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        DynamicSourceRuntimeFixtureManifest(
            id="dynamic-source-runtime-bad",
            scenario="dynamic-source-runtime-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=DynamicSourceRuntimeFailureType.RAW_SECRET_LEAK,
            negative_case=True,
        )
