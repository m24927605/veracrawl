"""Deterministic/local dynamic source runtime adapter records."""

from __future__ import annotations

from veracrawl.adapters.browser.deterministic import DeterministicBrowserObservationAdapter
from veracrawl.adapters.sources.deterministic import DeterministicSourceAdapter
from veracrawl.browser.observation import build_browser_sandbox_policy
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AdapterType, CompletenessResult
from veracrawl.contracts.source_runtime import (
    REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS,
    DynamicSourceRuntimeAdapterRecord,
)
from veracrawl.fetch.acquisition import SourceAcquisitionOutcome, execute_source_acquisition


def adapter_slug(adapter_type: AdapterType) -> str:
    return adapter_type.value.replace("_", "-")


def build_dynamic_source_runtime_records(
    fixture_id: str,
    *,
    adapter_types: list[AdapterType] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> list[DynamicSourceRuntimeAdapterRecord]:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:dynamic-source-runtime"]
    return [
        build_dynamic_source_runtime_record(
            fixture_id,
            adapter_type=adapter_type,
            policy_decision_refs=policy_refs,
        )
        for adapter_type in (adapter_types or list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS))
    ]


def build_dynamic_source_runtime_record(
    fixture_id: str,
    *,
    adapter_type: AdapterType,
    policy_decision_refs: list[Ref],
) -> DynamicSourceRuntimeAdapterRecord:
    if adapter_type in {
        AdapterType.HTTP,
        AdapterType.SITEMAP,
        AdapterType.RSS,
        AdapterType.API_SOURCE,
        AdapterType.DOCUMENT_SOURCE,
    }:
        return _fetch_like_record(
            fixture_id,
            adapter_type=adapter_type,
            policy_decision_refs=policy_decision_refs,
        )
    if adapter_type == AdapterType.BROWSER_SNAPSHOT:
        return _browser_record(fixture_id, policy_decision_refs=policy_decision_refs)
    return _native_non_fetch_record(
        fixture_id,
        adapter_type=adapter_type,
        policy_decision_refs=policy_decision_refs,
    )


def _fetch_like_record(
    fixture_id: str,
    *,
    adapter_type: AdapterType,
    policy_decision_refs: list[Ref],
) -> DynamicSourceRuntimeAdapterRecord:
    slug = adapter_slug(adapter_type)
    outcome = execute_source_acquisition(
        fixture_id=f"{fixture_id}-{slug}",
        adapter_type=adapter_type,
        scenario="dynamic-source-runtime-success",
        adapter=DeterministicSourceAdapter(adapter_type=adapter_type),
    )
    return _record_from_outcome(
        fixture_id,
        adapter_type=adapter_type,
        outcome=outcome,
        policy_decision_refs=policy_decision_refs,
        api_payload_refs=[f"api-payload:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.API_SOURCE
        else [],
    )


def _browser_record(
    fixture_id: str,
    *,
    policy_decision_refs: list[Ref],
) -> DynamicSourceRuntimeAdapterRecord:
    slug = adapter_slug(AdapterType.BROWSER_SNAPSHOT)
    origin = "https://example.test"
    sandbox_policy = build_browser_sandbox_policy(fixture_id=f"{fixture_id}-{slug}", origin=origin)
    adapter = DeterministicBrowserObservationAdapter(
        fixture_id=f"{fixture_id}-{slug}",
        target_url=f"{origin}/dynamic-source",
        sandbox_policy=sandbox_policy,
    )
    outcome = execute_source_acquisition(
        fixture_id=f"{fixture_id}-{slug}",
        adapter_type=AdapterType.BROWSER_SNAPSHOT,
        scenario="dynamic-source-runtime-browser",
        adapter=adapter,
    )
    browser_result = adapter.last_result
    browser_refs = [browser_result.step.id] if browser_result else []
    return _record_from_outcome(
        fixture_id,
        adapter_type=AdapterType.BROWSER_SNAPSHOT,
        outcome=outcome,
        policy_decision_refs=policy_decision_refs,
        browser_interaction_refs=browser_refs,
    )


def _record_from_outcome(
    fixture_id: str,
    *,
    adapter_type: AdapterType,
    outcome: SourceAcquisitionOutcome,
    policy_decision_refs: list[Ref],
    browser_interaction_refs: list[Ref] | None = None,
    api_payload_refs: list[Ref] | None = None,
) -> DynamicSourceRuntimeAdapterRecord:
    slug = adapter_slug(adapter_type)
    if outcome.source_result is None:
        raise ValueError(f"{adapter_type.value} dynamic source runtime missing source result")
    return DynamicSourceRuntimeAdapterRecord(
        id=f"dynamic-source-runtime-record:{fixture_id}:{slug}",
        adapter_type=adapter_type,
        source_adapter_result_ref=outcome.source_result.id,
        natural_result_refs=outcome.source_result.output_refs,
        fetch_attempt_refs=outcome.report.fetch_attempt_refs,
        page_snapshot_refs=[outcome.page_snapshot.id] if outcome.page_snapshot else [],
        browser_interaction_refs=browser_interaction_refs or [],
        credential_audit_refs=[],
        document_artifact_refs=[outcome.document_artifact.id] if outcome.document_artifact else [],
        api_payload_refs=api_payload_refs or [],
        command_result_refs=outcome.report.command_record_refs,
        policy_decision_refs=sorted(
            set(policy_decision_refs + outcome.report.policy_decision_refs)
        ),
        observability_report_refs=[f"observability-report:{fixture_id}:dynamic-source-runtime"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:dynamic-source-runtime"
        ],
        event_cursor_refs=outcome.report.event_cursor_refs,
        outbox_refs=outcome.report.outbox_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dynamic-source-runtime",
        live_runtime_refs=[f"dynamic-source-runtime:{fixture_id}:{slug}:deterministic"],
        contract_adapter_refs=[f"dynamic-source-contract-adapter:{fixture_id}:{slug}"],
        diagnostic_adapter_state_refs=[f"diagnostic-dynamic-source:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )


def _native_non_fetch_record(
    fixture_id: str,
    *,
    adapter_type: AdapterType,
    policy_decision_refs: list[Ref],
) -> DynamicSourceRuntimeAdapterRecord:
    slug = adapter_slug(adapter_type)
    credential_refs = (
        [f"credential-use-audit:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.AUTHORIZED_SESSION
        else []
    )
    file_refs = (
        [f"file-artifact:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.FILE_IMPORT
        else []
    )
    seed_refs = (
        [f"seed-plan:{fixture_id}:{slug}"] if adapter_type == AdapterType.MANUAL_SEED else []
    )
    prior_refs = (
        [f"prior-snapshot:{fixture_id}:{slug}"]
        if adapter_type == AdapterType.PRIOR_SNAPSHOT
        else []
    )
    natural_refs = credential_refs + file_refs + seed_refs + prior_refs
    return DynamicSourceRuntimeAdapterRecord(
        id=f"dynamic-source-runtime-record:{fixture_id}:{slug}",
        adapter_type=adapter_type,
        source_adapter_result_ref=f"source-adapter-result:{fixture_id}:{slug}",
        natural_result_refs=natural_refs,
        credential_audit_refs=credential_refs,
        file_artifact_refs=file_refs,
        seed_plan_refs=seed_refs,
        prior_snapshot_refs=prior_refs,
        command_result_refs=[f"command-result:{fixture_id}:{slug}:dynamic-source-runtime"],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:dynamic-source-runtime"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:dynamic-source-runtime"
        ],
        event_cursor_refs=[f"event-cursor:{fixture_id}:{slug}:dynamic-source-runtime"],
        outbox_refs=[f"outbox:{fixture_id}:{slug}:dynamic-source-runtime"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dynamic-source-runtime",
        live_runtime_refs=[f"dynamic-source-runtime:{fixture_id}:{slug}:deterministic"],
        contract_adapter_refs=[f"dynamic-source-contract-adapter:{fixture_id}:{slug}"],
        diagnostic_adapter_state_refs=[f"diagnostic-dynamic-source:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )
