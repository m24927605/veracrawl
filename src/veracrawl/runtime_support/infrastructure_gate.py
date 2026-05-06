"""Core integrated runtime infrastructure gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.artifact_lifecycle.object_store_conformance import ObjectStoreConformanceResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    RuntimeInfrastructureAdapterFamily,
    RuntimeInfrastructureFailureType,
)
from veracrawl.contracts.infrastructure import (
    RuntimeInfrastructureReport,
    RuntimeInfrastructureSpec,
)
from veracrawl.persistence.adapter_conformance import PersistenceAdapterConformanceResult
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)
from veracrawl.scale.broker_conformance import QueueBrokerConformanceResult

_BACKEND = "infrastructure"


def _fail_closed_in_production(gate: str) -> None:
    if current_mode() is RuntimeMode.PRODUCTION:
        raise ProductionRuntimeNotImplemented(backend=_BACKEND, gate=gate)


@dataclass(frozen=True)
class RuntimeInfrastructureGateResult:
    spec: RuntimeInfrastructureSpec
    report: RuntimeInfrastructureReport
    persistence: PersistenceAdapterConformanceResult | None = None
    queue_broker: QueueBrokerConformanceResult | None = None
    object_store: ObjectStoreConformanceResult | None = None


_FAILURES: dict[str, tuple[RuntimeInfrastructureFailureType, str]] = {
    "infrastructure-missing-persistence-refs": (
        RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_PERSISTENCE_REFS,
        "persistence_report_refs",
    ),
    "infrastructure-missing-queue-refs": (
        RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_QUEUE_REFS,
        "queue_broker_report_refs",
    ),
    "infrastructure-missing-object-refs": (
        RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_OBJECT_REFS,
        "object_store_report_refs",
    ),
    "infrastructure-missing-replay-refs": (
        RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
}


def runtime_infrastructure_spec(
    fixture_id: str,
    *,
    persistence_adapter_ref: Ref,
    queue_broker_adapter_ref: Ref,
    object_store_adapter_ref: Ref,
    policy_decision_refs: list[Ref],
) -> RuntimeInfrastructureSpec:
    return RuntimeInfrastructureSpec(
        id=f"runtime-infrastructure-spec:{fixture_id}",
        persistence_adapter_ref=persistence_adapter_ref,
        queue_broker_adapter_ref=queue_broker_adapter_ref,
        object_store_adapter_ref=object_store_adapter_ref,
        required_live_adapter_refs=[
            persistence_adapter_ref,
            queue_broker_adapter_ref,
            object_store_adapter_ref,
        ],
        policy_decision_refs=policy_decision_refs,
    )


def run_runtime_infrastructure_gate(
    *,
    fixture_id: str,
    scenario: str,
    spec: RuntimeInfrastructureSpec,
    persistence: PersistenceAdapterConformanceResult | None,
    queue_broker: QueueBrokerConformanceResult | None,
    object_store: ObjectStoreConformanceResult | None,
) -> RuntimeInfrastructureGateResult:
    _fail_closed_in_production("run_runtime_infrastructure_gate")
    if scenario in _FAILURES:
        failure, missing = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            spec=spec,
            failure=failure,
            missing_field=missing,
        )
    if persistence is None or queue_broker is None or object_store is None:
        return run_runtime_infrastructure_runtime_unavailable_gate(
            fixture_id=fixture_id,
            spec=spec,
        )
    if (
        persistence.report.completion_result != CompletenessResult.PASS
        or queue_broker.report.completion_result != CompletenessResult.PASS
        or object_store.report.completion_result != CompletenessResult.PASS
    ):
        return _partial_runtime_result(
            fixture_id=fixture_id,
            spec=spec,
            persistence=persistence,
            queue_broker=queue_broker,
            object_store=object_store,
        )
    idempotency_deduped = False
    if scenario == "operational-infrastructure-idempotency-success":
        idempotency_deduped = (
            persistence.duplicate_deduped
            and queue_broker.duplicate_deduped
            and object_store.duplicate_deduped
        )
    report = RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        infrastructure_spec_ref=spec.id,
        live_adapter_families=list(RuntimeInfrastructureAdapterFamily),
        persistence_report_refs=[persistence.report.id],
        queue_broker_report_refs=[queue_broker.report.id],
        object_store_report_refs=[object_store.report.id],
        persistence_adapter_refs=[spec.persistence_adapter_ref],
        queue_broker_adapter_refs=[spec.queue_broker_adapter_ref],
        object_store_adapter_refs=[spec.object_store_adapter_ref],
        transaction_refs=persistence.report.transaction_refs,
        command_record_refs=persistence.report.command_record_refs,
        idempotency_record_refs=persistence.report.idempotency_record_refs,
        event_cursor_refs=persistence.report.event_cursor_refs,
        outbox_refs=persistence.report.outbox_refs,
        queue_topology_refs=[queue_broker.report.queue_topology_ref or ""],
        queue_item_refs=queue_broker.report.queue_item_refs,
        broker_operation_refs=queue_broker.report.broker_operation_refs,
        queue_operation_refs=persistence.report.queue_operation_refs,
        lease_refs=_unique(persistence.report.lease_refs + queue_broker.report.lease_refs),
        heartbeat_refs=queue_broker.report.heartbeat_refs,
        ack_refs=queue_broker.report.ack_refs,
        nack_refs=queue_broker.report.nack_refs,
        dead_letter_refs=queue_broker.report.dead_letter_refs,
        fencing_token_refs=queue_broker.report.fencing_token_refs,
        artifact_refs=_unique(persistence.report.artifact_refs + object_store.report.artifact_refs),
        object_operation_refs=object_store.report.object_operation_refs,
        content_digest_refs=object_store.report.content_digest_refs,
        read_result_refs=object_store.report.read_result_refs,
        head_refs=object_store.report.head_refs,
        list_refs=object_store.report.list_refs,
        delete_refs=object_store.report.delete_refs,
        lifecycle_state_refs=object_store.report.lifecycle_state_refs,
        retention_policy_refs=object_store.report.retention_policy_refs,
        privacy_policy_refs=object_store.report.privacy_policy_refs,
        failure_record_refs=_unique(
            persistence.report.failure_record_refs
            + queue_broker.report.failure_record_refs
            + object_store.report.failure_record_refs
        ),
        recovery_action_refs=_unique(
            queue_broker.report.recovery_action_refs + object_store.report.recovery_action_refs
        ),
        policy_decision_refs=_unique(
            spec.policy_decision_refs
            + persistence.report.policy_decision_refs
            + queue_broker.report.policy_decision_refs
            + object_store.report.policy_decision_refs
        ),
        replay_bundle_ref=f"replay-bundle:{fixture_id}:operational-infrastructure",
        idempotency_deduped=idempotency_deduped,
        operator_status="operational_infrastructure_completed",
        completion_result=CompletenessResult.PASS,
    )
    return RuntimeInfrastructureGateResult(
        spec=spec,
        report=report,
        persistence=persistence,
        queue_broker=queue_broker,
        object_store=object_store,
    )


def run_runtime_infrastructure_runtime_unavailable_gate(
    *,
    fixture_id: str,
    spec: RuntimeInfrastructureSpec,
) -> RuntimeInfrastructureGateResult:
    _fail_closed_in_production("run_runtime_infrastructure_runtime_unavailable_gate")
    report = RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        infrastructure_spec_ref=spec.id,
        policy_decision_refs=spec.policy_decision_refs,
        contract_only_refs=[
            "runtime:postgres:dsn-required",
            "runtime:redis:url-required",
            "runtime:s3:endpoint-required",
            "runtime:infrastructure:live-conformance-not-executed",
        ],
        operator_status="operational_infrastructure_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return RuntimeInfrastructureGateResult(spec=spec, report=report)


def _partial_runtime_result(
    *,
    fixture_id: str,
    spec: RuntimeInfrastructureSpec,
    persistence: PersistenceAdapterConformanceResult,
    queue_broker: QueueBrokerConformanceResult,
    object_store: ObjectStoreConformanceResult,
) -> RuntimeInfrastructureGateResult:
    contract_only_refs = _unique(
        persistence.report.contract_only_refs
        + queue_broker.report.contract_only_refs
        + object_store.report.contract_only_refs
    )
    missing = _unique(
        persistence.report.missing_ref_fields
        + queue_broker.report.missing_ref_fields
        + object_store.report.missing_ref_fields
    )
    report = RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        infrastructure_spec_ref=spec.id,
        policy_decision_refs=spec.policy_decision_refs,
        contract_only_refs=contract_only_refs
        or ["runtime:infrastructure:component-not-passing"],
        missing_ref_fields=missing,
        operator_status="operational_infrastructure_needs_review",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return RuntimeInfrastructureGateResult(
        spec=spec,
        report=report,
        persistence=persistence,
        queue_broker=queue_broker,
        object_store=object_store,
    )


def _failure_result(
    *,
    fixture_id: str,
    spec: RuntimeInfrastructureSpec,
    failure: RuntimeInfrastructureFailureType,
    missing_field: str,
) -> RuntimeInfrastructureGateResult:
    report = RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        infrastructure_spec_ref=spec.id,
        failure_record_refs=[f"runtime-infrastructure-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=spec.policy_decision_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return RuntimeInfrastructureGateResult(spec=spec, report=report)


def _unique(values: list[Ref] | list[str]) -> list[Ref]:
    seen: set[str] = set()
    result: list[Ref] = []
    for value in values:
        if not value:
            continue
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
