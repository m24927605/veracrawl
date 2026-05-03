"""Live HTTP acquisition runtime composed through production ports."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveHttpAcquisitionFailureType,
    NetworkFailureType,
    TargetWebsitePattern,
)
from veracrawl.contracts.network import LiveHttpAcquisitionReport, NetworkRequest
from veracrawl.contracts.target_runtime import TargetSourceObservationRecord
from veracrawl.control.production_persistence import (
    ProductionPersistenceRuntimeResult,
    ProductionPersistenceStore,
    run_production_persistence_runtime_fixture,
)
from veracrawl.control.runtime import create_runtime_command
from veracrawl.fetch.network_acquisition import (
    NetworkBrowserAcquisitionOutcome,
    build_network_request,
    execute_http_network_acquisition,
)
from veracrawl.ports.network import NetworkClientResult, NetworkSourceAdapterPort


@dataclass(frozen=True)
class LiveHttpAcquisitionRuntimeResult:
    report: LiveHttpAcquisitionReport
    production_persistence: ProductionPersistenceRuntimeResult
    network_outcome: NetworkBrowserAcquisitionOutcome | None = None
    source_observation: TargetSourceObservationRecord | None = None


_DIRECT_FAILURES: dict[str, tuple[LiveHttpAcquisitionFailureType, str]] = {
    "malformed-response": (
        LiveHttpAcquisitionFailureType.MALFORMED_RESPONSE,
        "network_response_ref",
    ),
    "missing-artifact": (
        LiveHttpAcquisitionFailureType.MISSING_ARTIFACT,
        "artifact_refs",
    ),
    "replay-mismatch": (
        LiveHttpAcquisitionFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
    "direct-source-bypass": (
        LiveHttpAcquisitionFailureType.DIRECT_SOURCE_BYPASS,
        "source_adapter_result_refs",
    ),
}

_NETWORK_FAILURE_MAP = {
    NetworkFailureType.EGRESS_DENIED: LiveHttpAcquisitionFailureType.POLICY_DENIED,
    NetworkFailureType.PRIVATE_NETWORK_DENIED: (
        LiveHttpAcquisitionFailureType.PRIVATE_NETWORK_DENIED
    ),
    NetworkFailureType.MISSING_NETWORK_ARTIFACT: (
        LiveHttpAcquisitionFailureType.MISSING_ARTIFACT
    ),
}


def execute_live_http_acquisition(
    *,
    fixture_id: str,
    scenario: str,
    target_url: str,
    store: ProductionPersistenceStore,
    adapter: NetworkSourceAdapterPort | None = None,
    profile: str = "target",
    egress_allowlist: list[str] | None = None,
    allow_private_network: bool = True,
    size_budget_bytes: int = 8192,
    timeout_ms: int = 1000,
) -> LiveHttpAcquisitionRuntimeResult:
    production = run_production_persistence_runtime_fixture(
        fixture_id=fixture_id,
        scenario="success",
        profile=profile,
        store=store,
        policy_decision_refs=[f"policy:{fixture_id}:production-persistence"],
    )
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=size_budget_bytes,
        timeout_ms=timeout_ms,
    )

    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        report = _failure_report(
            fixture_id=fixture_id,
            request=request,
            production=production,
            store=store,
            failure=failure,
            missing_field=missing_field,
            diagnostics=[f"{scenario} did not produce complete adapter-backed live HTTP refs"],
        )
        return LiveHttpAcquisitionRuntimeResult(report=report, production_persistence=production)

    if adapter is None:
        report = _failure_report(
            fixture_id=fixture_id,
            request=request,
            production=production,
            store=store,
            failure=LiveHttpAcquisitionFailureType.ADAPTER_UNAVAILABLE,
            missing_field="source_adapter_result_refs",
            diagnostics=["live HTTP acquisition requires a NetworkSourceAdapterPort"],
        )
        return LiveHttpAcquisitionRuntimeResult(report=report, production_persistence=production)

    network_scenario = "egress-denied" if scenario == "scope-denied" else scenario
    network = execute_http_network_acquisition(
        fixture_id=fixture_id,
        scenario=network_scenario,
        target_url=target_url,
        adapter=adapter,
        egress_allowlist=egress_allowlist or [],
        allow_private_network=allow_private_network,
        size_budget_bytes=size_budget_bytes,
        timeout_ms=timeout_ms,
    )
    if network.report.completion_result != CompletenessResult.PASS:
        failure = _live_failure_from_network(network.report.operator_status)
        report = _failure_report(
            fixture_id=fixture_id,
            request=request,
            production=production,
            store=store,
            failure=failure,
            missing_field=network.report.operator_status,
            diagnostics=network.report.missing_ref_fields or [network.report.operator_status],
            network=network,
        )
        return LiveHttpAcquisitionRuntimeResult(
            report=report,
            production_persistence=production,
            network_outcome=network,
        )

    if network.network_result is None or not network.network_result.artifact_refs:
        report = _failure_report(
            fixture_id=fixture_id,
            request=request,
            production=production,
            store=store,
            failure=LiveHttpAcquisitionFailureType.MISSING_ARTIFACT,
            missing_field="artifact_refs",
            diagnostics=["network adapter did not expose a raw HTTP artifact"],
            network=network,
        )
        return LiveHttpAcquisitionRuntimeResult(
            report=report,
            production_persistence=production,
            network_outcome=network,
        )

    report, observation = _success_report(
        fixture_id=fixture_id,
        target_url=target_url,
        production=production,
        store=store,
        request=request,
        network=network,
        network_result=network.network_result,
    )
    return LiveHttpAcquisitionRuntimeResult(
        report=report,
        production_persistence=production,
        network_outcome=network,
        source_observation=observation,
    )


def _success_report(
    *,
    fixture_id: str,
    target_url: str,
    production: ProductionPersistenceRuntimeResult,
    store: ProductionPersistenceStore,
    request: NetworkRequest,
    network: NetworkBrowserAcquisitionOutcome,
    network_result: NetworkClientResult,
) -> tuple[LiveHttpAcquisitionReport, TargetSourceObservationRecord]:
    production_report = production.report
    production_event_cursor_ref = _required_ref(
        production_report.event_cursor_ref,
        "event_cursor_ref",
    )
    response = network_result.response
    artifact_refs = sorted(set(network.report.artifact_refs + network_result.artifact_refs))
    content_hash_refs = [response.content_digest] if response.content_digest else []
    canonical_url_ref = f"canonical-url:{fixture_id}:{stable_hash(response.final_url)[:12]}"
    replay_bundle_ref = f"replay-bundle:{fixture_id}:live-http"
    for artifact_ref in artifact_refs:
        store.register_artifact_ref(artifact_ref)

    observation = TargetSourceObservationRecord(
        id=f"target-source-observation:{fixture_id}:http",
        run_ref=production_report.run_ref,
        corpus_entry_ref=f"corpus-entry:{fixture_id}:http",
        website_pattern=TargetWebsitePattern.STATIC,
        source_path_ref=target_url,
        content_hash_ref=content_hash_refs[0] if content_hash_refs else None,
        source_observation_ref=response.id,
        artifact_ref=artifact_refs[0],
        extracted_field_refs=[f"field:{fixture_id}:title"],
        evidence_refs=[f"evidence:{fixture_id}:source"],
        graph_refs=[f"graph:{fixture_id}:url"],
        policy_decision_refs=sorted(
            set(network.report.policy_decision_refs + production_report.policy_decision_refs)
        ),
        replay_refs=[replay_bundle_ref],
        result=CompletenessResult.PASS,
    )
    store.save_canonical_model("target_source_observations", observation.id, observation)

    command_record_ref, outbox_ref, event_cursor_ref = _record_live_http_report_event(
        fixture_id=fixture_id,
        production=production,
        store=store,
        output_refs=[
            f"live-http-acquisition-report:{fixture_id}",
            observation.id,
            response.id,
            *artifact_refs,
        ],
        policy_decision_refs=observation.policy_decision_refs,
    )

    report = LiveHttpAcquisitionReport(
        id=f"live-http-acquisition-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=production_report.run_ref,
        run_control_report_ref=production_report.run_control_report_ref,
        production_persistence_report_ref=production_report.id,
        network_request_ref=request.id,
        network_response_ref=response.id,
        redirect_hop_refs=[hop.id for hop in network_result.redirect_hops],
        source_acquisition_report_ref=network.report.source_acquisition_report_ref,
        source_adapter_result_refs=[f"source-result:cmd:{fixture_id}:source"],
        fetch_attempt_refs=[f"fetch-attempt:{fixture_id}:1"],
        fetch_result_refs=[f"fetch-result:{fixture_id}"],
        page_snapshot_refs=[f"page-snapshot:{fixture_id}"],
        source_observation_refs=[observation.id],
        artifact_refs=artifact_refs,
        content_hash_refs=content_hash_refs,
        canonical_url_refs=[canonical_url_ref],
        policy_decision_refs=observation.policy_decision_refs,
        command_record_refs=sorted(
            set(
                production_report.persistence_command_record_refs
                + network.report.command_record_refs
                + [command_record_ref]
            )
        ),
        event_cursor_refs=sorted(
            set(
                [production_event_cursor_ref, event_cursor_ref]
                + network.report.event_cursor_refs
            )
        ),
        outbox_refs=sorted(
            set(production_report.outbox_refs + network.report.outbox_refs + [outbox_ref])
        ),
        replay_bundle_ref=replay_bundle_ref,
        operator_status="live_http_acquisition_completed",
        completion_result=CompletenessResult.PASS,
    )
    store.save_canonical_model("live_http_acquisition_reports", report.id, report)
    return report, observation


def _failure_report(
    *,
    fixture_id: str,
    request: NetworkRequest,
    production: ProductionPersistenceRuntimeResult,
    store: ProductionPersistenceStore,
    failure: LiveHttpAcquisitionFailureType,
    missing_field: str,
    diagnostics: list[str],
    network: NetworkBrowserAcquisitionOutcome | None = None,
) -> LiveHttpAcquisitionReport:
    production_report = production.report
    production_event_cursor_ref = _required_ref(
        production_report.event_cursor_ref,
        "event_cursor_ref",
    )
    command_record_ref, outbox_ref, event_cursor_ref = _record_live_http_report_event(
        fixture_id=fixture_id,
        production=production,
        store=store,
        output_refs=[f"failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=sorted(
            set(production_report.policy_decision_refs + [f"policy:{fixture_id}:network"])
        ),
    )
    report = LiveHttpAcquisitionReport(
        id=f"live-http-acquisition-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=production_report.run_ref,
        run_control_report_ref=production_report.run_control_report_ref,
        production_persistence_report_ref=production_report.id,
        network_request_ref=request.id,
        network_response_ref=network.report.network_response_ref if network else None,
        redirect_hop_refs=network.report.redirect_hop_refs if network else [],
        source_acquisition_report_ref=network.report.source_acquisition_report_ref
        if network
        else None,
        artifact_refs=network.report.artifact_refs if network else [],
        policy_decision_refs=sorted(
            set(
                production_report.policy_decision_refs
                + [f"policy:{fixture_id}:network"]
                + (network.report.policy_decision_refs if network else [])
            )
        ),
        command_record_refs=sorted(
            set(
                production_report.persistence_command_record_refs
                + (network.report.command_record_refs if network else [])
                + [command_record_ref]
            )
        ),
        event_cursor_refs=sorted(
            set(
                [production_event_cursor_ref, event_cursor_ref]
                + (network.report.event_cursor_refs if network else [])
            )
        ),
        outbox_refs=sorted(
            set(
                production_report.outbox_refs
                + (network.report.outbox_refs if network else [])
                + [outbox_ref]
            )
        ),
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=diagnostics,
    )
    store.save_canonical_model("live_http_acquisition_reports", report.id, report)
    return report


def _record_live_http_report_event(
    *,
    fixture_id: str,
    production: ProductionPersistenceRuntimeResult,
    store: ProductionPersistenceStore,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
) -> tuple[Ref, Ref, Ref]:
    production_report = production.report
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:live-http-acquisition",
        command_type="record_live_http_acquisition_report",
        target_aggregate_type="LiveHttpAcquisitionReport",
        target_aggregate_id=f"live-http-acquisition-report:{fixture_id}",
        actor_ref="actor:live-http-acquisition",
        payload_ref=f"payload:{fixture_id}:live-http-acquisition",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=production_report.run_ref,
        objective_ref=production_report.objective_ref,
        plan_ref=production_report.plan_ref,
        event_type="live_http_acquisition_reported",
        output_refs=output_refs,
    )
    dispatched = store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{fixture_id}:live-http-outbox-dispatched",
    )
    cursor = store.build_event_cursor(production_report.run_ref)
    return record.id, dispatched.id, cursor.id


def _required_ref(value: Ref | None, field_name: str) -> Ref:
    if value is None:
        raise ValueError(f"production persistence report missing {field_name}")
    return value


def _live_failure_from_network(operator_status: str) -> LiveHttpAcquisitionFailureType:
    try:
        network_failure = NetworkFailureType(operator_status)
    except ValueError:
        return LiveHttpAcquisitionFailureType.NETWORK_FAILURE
    return _NETWORK_FAILURE_MAP.get(
        network_failure,
        LiveHttpAcquisitionFailureType.NETWORK_FAILURE,
    )
