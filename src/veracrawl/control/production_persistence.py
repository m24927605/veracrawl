"""Production run-control persistence wiring through port-shaped stores."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, TypeVar

from pydantic import BaseModel

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import DurableCommandRecord, EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import (
    CompletenessResult,
    PersistenceAdapterKind,
    PersistenceCapability,
    ProductionPersistenceFailureType,
    RunStatus,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
)
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.objective import (
    CrawlObjective,
    CrawlPlan,
    CrawlRun,
    ProductionPersistenceRuntimeReport,
    ProductionProject,
    ProductionRunControlReport,
    ProductionSiteScope,
    RunApprovalRecord,
    RunBudget,
    RunLifecycleRecord,
    RunPlanSnapshot,
    RunPolicySnapshot,
)
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceAdapterSpec,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.scale import QueueItem, RetryDeadLetterRecord, ShardLease
from veracrawl.control.run_control import (
    ProductionRunControlFixtureExecution,
    execute_production_run_control_fixture,
)
from veracrawl.control.runtime import create_runtime_command

ModelT = TypeVar("ModelT", bound=BaseModel)


class ProductionPersistenceStore(Protocol):
    def reopen(self) -> ProductionPersistenceStore: ...

    def save_canonical_model(self, collection: str, key: Ref, model: BaseModel) -> Ref: ...

    def load_canonical_model(
        self,
        collection: str,
        key: Ref,
        model_type: type[ModelT],
    ) -> ModelT | None: ...

    def begin_transaction(
        self,
        *,
        run_ref: Ref,
        unit_of_work_ref: Ref,
        adapter_ref: Ref = ...,
    ) -> PersistenceTransactionRecord: ...

    def commit_transaction(
        self,
        record: PersistenceTransactionRecord,
    ) -> PersistenceTransactionRecord: ...

    def register_artifact_ref(self, artifact_ref: Ref) -> Ref: ...

    def has_artifact_ref(self, artifact_ref: Ref) -> bool: ...

    def append_event(self, event: CrawlRunEvent) -> Ref: ...

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]: ...

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord: ...

    def mark_outbox_dispatched(self, outbox_ref: Ref, *, dispatched_at_ref: Ref) -> OutboxRecord:
        ...

    def list_outbox(self, run_ref: Ref | None = None) -> list[OutboxRecord]: ...

    def handle_command_once(
        self,
        command: CommandEnvelope,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        plan_ref: Ref,
        event_type: str,
        output_refs: list[Ref],
    ) -> tuple[
        DurableCommandRecord,
        CommandResult,
        OutboxRecord,
        IdempotencyPersistenceRecord,
        bool,
    ]: ...

    def enqueue_queue_item(self, item: QueueItem) -> PersistentQueueOperationRecord: ...

    def acquire_queue_lease(
        self,
        item: QueueItem,
        lease: ShardLease,
    ) -> PersistentQueueOperationRecord: ...

    def heartbeat_queue_lease(
        self,
        lease_ref: Ref,
        *,
        lease_token_ref: Ref,
        heartbeat_ref: Ref,
    ) -> PersistentQueueOperationRecord: ...

    def ack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        command_result_ref: Ref,
    ) -> PersistentQueueOperationRecord: ...

    def nack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        failure_refs: list[Ref],
        recovery_refs: list[Ref],
    ) -> PersistentQueueOperationRecord: ...

    def dead_letter_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        dead_letter: RetryDeadLetterRecord,
    ) -> PersistentQueueOperationRecord: ...


@dataclass(frozen=True)
class CanonicalDocumentRef:
    collection: str
    key: Ref
    model_type: type[BaseModel]

    @property
    def ref(self) -> Ref:
        return f"canonical:{self.collection}:{self.key}"


@dataclass(frozen=True)
class ProductionPersistenceRuntimeResult:
    report: ProductionPersistenceRuntimeReport
    run_control_report: ProductionRunControlReport | None = None
    transaction: PersistenceTransactionRecord | None = None
    command_records: list[DurableCommandRecord] | None = None
    idempotency_records: list[IdempotencyPersistenceRecord] | None = None
    outbox_records: list[OutboxRecord] | None = None
    queue_operations: list[PersistentQueueOperationRecord] | None = None
    duplicate_deduped: bool = False
    event_count: int = 0
    outbox_count: int = 0
    pre_duplicate_event_count: int = 0
    pre_duplicate_outbox_count: int = 0
    reloaded: bool = False


_SCENARIO_ALIASES = {
    "production-persistence-wiring-success": "success",
    "production-persistence-idempotent-replay": "idempotent-replay",
    "production-persistence-queue-recovery": "queue-recovery",
    "production-persistence-non-atomic-commit": "non-atomic-commit",
    "production-persistence-canonical-state-missing": "canonical-state-missing",
    "production-persistence-idempotency-missing": "idempotency-missing",
    "production-persistence-event-gap": "event-gap",
    "production-persistence-outbox-missing": "outbox-missing",
    "production-persistence-artifact-index-missing": "artifact-index-missing",
    "production-persistence-lease-heartbeat-missing": "lease-heartbeat-missing",
    "production-persistence-replay-missing": "replay-missing",
}

_FAILURES: dict[str, tuple[ProductionPersistenceFailureType, str]] = {
    "non-atomic-commit": (
        ProductionPersistenceFailureType.NON_ATOMIC_COMMIT,
        "transaction_ref",
    ),
    "canonical-state-missing": (
        ProductionPersistenceFailureType.CANONICAL_STATE_MISSING,
        "canonical_state_refs",
    ),
    "idempotency-missing": (
        ProductionPersistenceFailureType.IDEMPOTENCY_MISSING,
        "idempotency_record_refs",
    ),
    "event-gap": (
        ProductionPersistenceFailureType.EVENT_GAP,
        "event_cursor_ref",
    ),
    "outbox-missing": (
        ProductionPersistenceFailureType.OUTBOX_MISSING,
        "outbox_refs",
    ),
    "artifact-index-missing": (
        ProductionPersistenceFailureType.ARTIFACT_INDEX_MISSING,
        "artifact_refs",
    ),
    "lease-heartbeat-missing": (
        ProductionPersistenceFailureType.LEASE_HEARTBEAT_MISSING,
        "queue_operation_refs",
    ),
    "replay-missing": (
        ProductionPersistenceFailureType.REPLAY_MISSING,
        "replay_bundle_ref",
    ),
}


def run_production_persistence_runtime_fixture(
    *,
    fixture_id: str,
    scenario: str | None,
    profile: str,
    store: ProductionPersistenceStore,
    adapter: PersistenceAdapterSpec | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> ProductionPersistenceRuntimeResult:
    runtime_scenario = _scenario_from_fixture(fixture_id, scenario)
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:production-persistence"]
    if runtime_scenario in _FAILURES:
        failure, missing_field = _FAILURES[runtime_scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    execution = execute_production_run_control_fixture(
        fixture_id=fixture_id,
        scenario="success",
        profile=profile,
    )
    adapter_spec = adapter or production_persistence_adapter_spec(fixture_id, policy_refs)
    return _success_result(
        fixture_id=fixture_id,
        scenario=runtime_scenario,
        store=store,
        adapter=adapter_spec,
        policy_refs=policy_refs,
        execution=execution,
    )


def production_persistence_adapter_spec(
    fixture_id: str,
    policy_refs: list[Ref],
) -> PersistenceAdapterSpec:
    return PersistenceAdapterSpec(
        id=f"persistence-adapter:{fixture_id}:production-reference",
        adapter_kind=PersistenceAdapterKind.REFERENCE_FILESYSTEM,
        capability_refs=list(PersistenceCapability),
        port_refs=[
            "port:canonical-metadata-persistence",
            "port:event-log-persistence",
            "port:outbox-persistence",
            "port:artifact-index-persistence",
            "port:queue-persistence",
        ],
        transaction_supported=True,
        idempotency_supported=True,
        lease_supported=True,
        policy_decision_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    store: ProductionPersistenceStore,
    adapter: PersistenceAdapterSpec,
    policy_refs: list[Ref],
    execution: ProductionRunControlFixtureExecution,
) -> ProductionPersistenceRuntimeResult:
    run_ref = execution.report.run_ref
    transaction = store.begin_transaction(
        run_ref=run_ref,
        unit_of_work_ref=f"uow:{fixture_id}:production-persistence",
        adapter_ref=adapter.id,
    )
    canonical_docs = _persist_canonical_state(store, execution)
    artifact_refs = [
        f"artifact:{fixture_id}:run-control-report",
        f"artifact:{fixture_id}:replay-bundle",
    ]
    for artifact_ref in artifact_refs:
        store.register_artifact_ref(artifact_ref)
    _persist_run_control_events(store, execution.report)
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:production-persistence",
        command_type="record_production_persistence_runtime_report",
        target_aggregate_type="ProductionPersistenceRuntimeReport",
        target_aggregate_id=f"production-persistence-runtime-report:{fixture_id}",
        actor_ref="actor:production-persistence",
        payload_ref=f"payload:{fixture_id}:production-persistence",
        policy_decision_refs=policy_refs,
    )
    command_record, command_result, outbox, idempotency, duplicate = store.handle_command_once(
        command,
        run_ref=run_ref,
        objective_ref=execution.report.objective_ref,
        plan_ref=execution.report.plan_ref,
        event_type="production_persistence_runtime_reported",
        output_refs=[execution.report.id, *artifact_refs],
    )
    command_records = [command_record]
    idempotency_records = [idempotency]
    pre_duplicate_event_count = len(store.stream_events(run_ref))
    pre_duplicate_outbox_count = len(store.list_outbox(run_ref))
    if scenario == "idempotent-replay":
        store = store.reopen()
        duplicate_record, _, _, duplicate_idempotency, duplicate = store.handle_command_once(
            command.model_copy(update={"id": f"cmd:{fixture_id}:production-persistence:retry"}),
            run_ref=run_ref,
            objective_ref=execution.report.objective_ref,
            plan_ref=execution.report.plan_ref,
            event_type="production_persistence_runtime_reported",
            output_refs=[execution.report.id, *artifact_refs],
        )
        command_records.append(duplicate_record)
        idempotency_records.append(duplicate_idempotency)
    dispatched = store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{fixture_id}:production-persistence-outbox-dispatched",
    )
    queue_operations, lease_refs, failure_refs, recovery_refs = _queue_operations(
        store,
        fixture_id=fixture_id,
        run_ref=run_ref,
        command_result_ref=command_result.id,
        policy_refs=policy_refs,
        include_dead_letter=scenario == "queue-recovery",
    )
    cursor = store.build_event_cursor(run_ref)
    transaction = PersistenceTransactionRecord.model_validate(
        transaction.model_copy(
            update={
                "command_record_refs": [record.id for record in command_records],
                "event_refs": cursor.event_refs,
                "outbox_refs": [dispatched.id],
                "artifact_refs": artifact_refs,
                "idempotency_record_refs": [record.id for record in idempotency_records],
                "queue_operation_refs": [operation.id for operation in queue_operations],
                "policy_decision_refs": policy_refs,
            }
        ).model_dump(mode="json")
    )
    committed = store.commit_transaction(transaction)
    reopened = store.reopen()
    reloaded_missing = _validate_reopened_state(
        reopened,
        canonical_docs=canonical_docs,
        artifact_refs=artifact_refs,
        run_ref=run_ref,
    )
    if reloaded_missing:
        failure = ProductionPersistenceFailureType.CANONICAL_STATE_MISSING
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field="canonical_state_refs",
            policy_refs=policy_refs,
            diagnostics=reloaded_missing,
        )
    report = ProductionPersistenceRuntimeReport(
        id=f"production-persistence-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        project_ref=execution.report.project_ref,
        site_scope_ref=execution.report.site_scope_ref,
        objective_ref=execution.report.objective_ref,
        plan_ref=execution.report.plan_ref,
        run_control_report_ref=execution.report.id,
        status=execution.report.status,
        completion_result=CompletenessResult.PASS,
        operator_status=_operator_status(scenario),
        adapter_ref=adapter.id,
        transaction_ref=committed.id,
        canonical_state_refs=[doc.ref for doc in canonical_docs],
        run_control_command_result_refs=execution.report.command_result_refs,
        persistence_command_record_refs=[record.id for record in command_records],
        idempotency_record_refs=[record.id for record in idempotency_records],
        event_refs=cursor.event_refs,
        event_cursor_ref=cursor.id,
        outbox_refs=[dispatched.id],
        artifact_refs=artifact_refs,
        queue_operation_refs=[operation.id for operation in queue_operations],
        lease_refs=lease_refs,
        failure_record_refs=failure_refs,
        recovery_action_refs=recovery_refs,
        policy_decision_refs=policy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:production-persistence",
        duplicate_deduped=duplicate,
        reloaded=True,
    )
    event_count = len(reopened.stream_events(run_ref))
    outbox_count = len(reopened.list_outbox(run_ref))
    return ProductionPersistenceRuntimeResult(
        report=report,
        run_control_report=execution.report,
        transaction=committed,
        command_records=command_records,
        idempotency_records=idempotency_records,
        outbox_records=[dispatched],
        queue_operations=queue_operations,
        duplicate_deduped=duplicate,
        event_count=event_count,
        outbox_count=outbox_count,
        pre_duplicate_event_count=pre_duplicate_event_count,
        pre_duplicate_outbox_count=pre_duplicate_outbox_count,
        reloaded=True,
    )


def _persist_canonical_state(
    store: ProductionPersistenceStore,
    execution: ProductionRunControlFixtureExecution,
) -> list[CanonicalDocumentRef]:
    records: list[tuple[str, Ref, BaseModel, type[BaseModel]]] = [
        ("production_projects", execution.project.id, execution.project, ProductionProject),
        (
            "production_site_scopes",
            execution.site_scope.id,
            execution.site_scope,
            ProductionSiteScope,
        ),
        ("crawl_objectives", execution.objective.id, execution.objective, CrawlObjective),
        ("crawl_plans", execution.plan.id, execution.plan, CrawlPlan),
        (
            "run_plan_snapshots",
            execution.run_plan_snapshot.id,
            execution.run_plan_snapshot,
            RunPlanSnapshot,
        ),
        ("crawl_runs", execution.run.id, execution.run, CrawlRun),
        (
            "production_run_control_reports",
            execution.report.id,
            execution.report,
            ProductionRunControlReport,
        ),
    ]
    if execution.budget is not None:
        records.append(("run_budgets", execution.budget.id, execution.budget, RunBudget))
    if execution.policy_snapshot is not None:
        records.append(
            (
                "run_policy_snapshots",
                execution.policy_snapshot.id,
                execution.policy_snapshot,
                RunPolicySnapshot,
            )
        )
    if execution.approval is not None:
        records.append(
            ("run_approval_records", execution.approval.id, execution.approval, RunApprovalRecord)
        )
    for policy in execution.policies:
        records.append(("policy_decisions", policy.id, policy, PolicyDecision))
    for lifecycle in execution.lifecycle_records:
        records.append(("run_lifecycle_records", lifecycle.id, lifecycle, RunLifecycleRecord))
    canonical_docs: list[CanonicalDocumentRef] = []
    for collection, key, model, model_type in records:
        store.save_canonical_model(collection, key, model)
        canonical_docs.append(CanonicalDocumentRef(collection, key, model_type))
    return canonical_docs


def _persist_run_control_events(
    store: ProductionPersistenceStore,
    report: ProductionRunControlReport,
) -> None:
    for sequence, event_ref in enumerate(report.event_refs, start=1):
        command_result_ref = report.command_result_refs[
            min(sequence - 1, len(report.command_result_refs) - 1)
        ]
        store.append_event(
            CrawlRunEvent(
                id=event_ref,
                run_id=report.run_ref,
                objective_id=report.objective_ref,
                crawl_plan_id=report.plan_ref,
                sequence=sequence,
                event_type="production_run_control_event_persisted",
                event_type_spec_id="event-type:production_run_control_event_persisted",
                payload_ref=f"payload:{event_ref}",
                causation_id=command_result_ref,
                correlation_id=f"corr:{report.run_ref}",
                trace_id=f"trace:{report.run_ref}:{sequence}",
                output_refs=[report.id],
                policy_decision_refs=report.policy_decision_refs,
                idempotency_key=f"idempotency:{event_ref}",
                state_before={"status": "run_control_recorded"},
                state_after={"status": "persisted", "event_ref": event_ref},
            )
        )


def _queue_operations(
    store: ProductionPersistenceStore,
    *,
    fixture_id: str,
    run_ref: Ref,
    command_result_ref: Ref,
    policy_refs: list[Ref],
    include_dead_letter: bool,
) -> tuple[list[PersistentQueueOperationRecord], list[Ref], list[Ref], list[Ref]]:
    now = datetime.now(tz=UTC)
    queued = QueueItem(
        id=f"queue-item:{fixture_id}:frontier",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=f"project:{fixture_id}|site:{fixture_id}|production|p1",
        run_id=run_ref,
        aggregate_type="FrontierItem",
        aggregate_id=f"frontier-item:{fixture_id}",
        command_ref=f"command:{fixture_id}:frontier",
        priority=10,
        retry_class=ScaleRetryClass.TRANSIENT,
        idempotency_key=f"idempotency:{fixture_id}:frontier",
        expected_version_ref=f"expected-version:{fixture_id}:frontier",
        attempts=0,
        deadline_at=now + timedelta(minutes=30),
        status=ScaleQueueItemStatus.QUEUED,
    )
    lease = ShardLease(
        id=f"shard-lease:{fixture_id}:frontier",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=queued.shard_key,
        worker_id=f"worker:{fixture_id}:production",
        lease_token=f"lease-token:{fixture_id}",
        acquired_at=now,
        heartbeat_at=now + timedelta(seconds=30),
        expires_at=now + timedelta(minutes=5),
        policy_decision_refs=policy_refs,
        status=ScaleShardLeaseStatus.ACTIVE,
    )
    leased = QueueItem.model_validate(
        queued.model_copy(
            update={
                "status": ScaleQueueItemStatus.LEASED,
                "lease_token": lease.lease_token,
                "lease_expires_at": lease.expires_at,
                "attempts": 1,
            }
        ).model_dump(mode="json")
    )
    operations = [
        store.enqueue_queue_item(queued),
        store.acquire_queue_lease(leased, lease),
        store.heartbeat_queue_lease(
            lease.id,
            lease_token_ref=lease.lease_token,
            heartbeat_ref=f"heartbeat:{fixture_id}:frontier",
        ),
    ]
    failure_refs: list[Ref] = []
    recovery_refs: list[Ref] = []
    if include_dead_letter:
        failure_refs = [f"failure-record:{fixture_id}:queue"]
        recovery_refs = [f"recovery-action:{fixture_id}:queue"]
        operations.append(
            store.nack_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                failure_refs=failure_refs,
                recovery_refs=recovery_refs,
            )
        )
        dead_letter = RetryDeadLetterRecord(
            id=f"retry-dead-letter:{fixture_id}:frontier",
            queue_item_id=queued.id,
            run_id=run_ref,
            retry_class=ScaleRetryClass.WORKER_CRASH,
            attempts=3,
            final_reason="production_persistence_worker_retry_exhausted",
            failure_record_id=failure_refs[0],
            recovery_action_refs=recovery_refs,
        )
        operations.append(
            store.dead_letter_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                dead_letter=dead_letter,
            )
        )
    else:
        operations.append(
            store.ack_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                command_result_ref=command_result_ref,
            )
        )
    return operations, [lease.id], failure_refs, recovery_refs


def _validate_reopened_state(
    store: ProductionPersistenceStore,
    *,
    canonical_docs: list[CanonicalDocumentRef],
    artifact_refs: list[Ref],
    run_ref: Ref,
) -> list[str]:
    missing: list[str] = []
    for document in canonical_docs:
        loaded = store.load_canonical_model(
            document.collection,
            document.key,
            document.model_type,
        )
        if loaded is None:
            missing.append(document.ref)
    for artifact_ref in artifact_refs:
        if not store.has_artifact_ref(artifact_ref):
            missing.append(artifact_ref)
    if not store.stream_events(run_ref):
        missing.append(f"events:{run_ref}")
    return missing


def _failure_result(
    *,
    fixture_id: str,
    failure: ProductionPersistenceFailureType,
    missing_field: str,
    policy_refs: list[Ref],
    diagnostics: list[str] | None = None,
) -> ProductionPersistenceRuntimeResult:
    report = ProductionPersistenceRuntimeReport(
        id=f"production-persistence-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        project_ref=f"project:{fixture_id}",
        site_scope_ref=f"site-scope:{fixture_id}",
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=RunStatus.FAILED,
        completion_result=CompletenessResult.FAIL,
        operator_status=failure.value,
        failure_record_refs=[f"failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=policy_refs,
        missing_ref_fields=[missing_field],
        failure_type=failure,
        diagnostics=diagnostics
        or [f"missing required production persistence ref: {missing_field}"],
    )
    return ProductionPersistenceRuntimeResult(report=report)


def _scenario_from_fixture(fixture_id: str, scenario: str | None) -> str:
    if scenario:
        return scenario
    return _SCENARIO_ALIASES.get(fixture_id, fixture_id.removeprefix("production-persistence-"))


def _operator_status(scenario: str) -> str:
    if scenario == "idempotent-replay":
        return "production_persistence_idempotent_replay_completed"
    if scenario == "queue-recovery":
        return "production_persistence_queue_recovery_completed"
    return "production_persistence_runtime_completed"
