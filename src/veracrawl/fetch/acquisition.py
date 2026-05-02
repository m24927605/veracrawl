"""Generic source acquisition runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    FetchAttemptStatus,
    FetchResultStatus,
    PolicyDecisionValue,
    RateLimitDecisionValue,
    SourceAdapterResultType,
    SourceFailureType,
)
from veracrawl.contracts.fetch import DocumentArtifact, FetchAttempt, FetchResult, PageSnapshot
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.source_adapter import (
    SourceAdapterCommand,
    SourceAdapterResult,
    SourceAdapterSpec,
)
from veracrawl.contracts.source_runtime import (
    RateLimitDecision,
    SourceAcquisitionReport,
    SourceFailureReport,
)
from veracrawl.control.runtime import create_runtime_command
from veracrawl.policy.gates import decision_for
from veracrawl.ports.source_adapter import SourceAdapterPort
from veracrawl.review_replay.durable import validate_durable_recovery
from veracrawl.runtime_support.durable_store import DeterministicDurableStore
from veracrawl.scheduler.runtime import (
    complete_frontier_item,
    enqueue_frontier_item,
    lease_next_frontier_item,
    scheduler_recovery_report,
)


@dataclass(frozen=True)
class SourceAcquisitionOutcome:
    report: SourceAcquisitionReport
    source_result: SourceAdapterResult | None
    fetch_attempt: FetchAttempt
    fetch_result: FetchResult | None
    page_snapshot: PageSnapshot | None
    document_artifact: DocumentArtifact | None
    failure_report: SourceFailureReport | None
    rate_limit_decision: RateLimitDecision | None
    durable_recovery_ref: Ref


def source_adapter_spec(adapter_type: AdapterType) -> SourceAdapterSpec:
    return SourceAdapterSpec(
        id=f"adapter:{adapter_type.value}:deterministic",
        name=f"deterministic {adapter_type.value}",
        version="1",
        adapter_type=adapter_type,
        supported_source_types=["fixture"],
        metadata_schema_ref="schema:source-metadata",
        transformation_schema_ref="schema:source-transform",
        policy_refs=["policy:source"],
        idempotency_key_template="{adapter}:{source}",
        freshness_semantics={"deterministic": True},
    )


def _failure(
    *,
    run_ref: Ref,
    source_ref: Ref,
    failure_type: SourceFailureType,
    policy_decision_refs: list[Ref] | None = None,
    retry_refs: list[Ref] | None = None,
) -> SourceFailureReport:
    return SourceFailureReport(
        id=f"source-failure:{run_ref}:{failure_type.value}",
        run_ref=run_ref,
        source_ref=source_ref,
        failure_type=failure_type,
        operator_status=failure_type.value,
        policy_decision_refs=policy_decision_refs or [],
        retry_refs=retry_refs or [],
        diagnostic_refs=[f"diagnostic:{run_ref}:{failure_type.value}"],
    )


def _policy(run_ref: Ref, source_ref: Ref, *, allow: bool) -> PolicyDecision:
    return decision_for(
        decision_id=f"policy:{run_ref}:source",
        run_id=run_ref,
        objective_id=f"objective:{run_ref}",
        decision_type="runtime_source",
        subject_ref=source_ref,
        allow=allow,
        reasons=[] if allow else ["source blocked by deterministic policy"],
    )


def _result_status_for_failure(failure_type: SourceFailureType) -> FetchResultStatus:
    if failure_type == SourceFailureType.SOURCE_BLOCKED:
        return FetchResultStatus.BLOCKED
    if failure_type == SourceFailureType.SOURCE_RATE_LIMITED:
        return FetchResultStatus.RATE_LIMITED
    if failure_type == SourceFailureType.MALFORMED_RESPONSE:
        return FetchResultStatus.MALFORMED
    return FetchResultStatus.FAILED


def _attempt_status_for_failure(failure_type: SourceFailureType) -> FetchAttemptStatus:
    if failure_type == SourceFailureType.SOURCE_BLOCKED:
        return FetchAttemptStatus.BLOCKED
    if failure_type == SourceFailureType.SOURCE_RATE_LIMITED:
        return FetchAttemptStatus.RATE_LIMITED
    if failure_type == SourceFailureType.MALFORMED_RESPONSE:
        return FetchAttemptStatus.MALFORMED
    if failure_type == SourceFailureType.RETRY_EXHAUSTED:
        return FetchAttemptStatus.RETRY_EXHAUSTED
    return FetchAttemptStatus.FAILED


def _build_non_success_report(
    *,
    run_ref: Ref,
    frontier_item_ref: Ref,
    lease_ref: Ref,
    attempt: FetchAttempt,
    failure: SourceFailureReport,
    policy_decision_refs: list[Ref],
    completion_result: CompletenessResult,
    command_record_refs: list[Ref],
    event_cursor_refs: list[Ref],
    outbox_refs: list[Ref],
    recovery_report_refs: list[Ref],
    fetch_result_ref: Ref | None = None,
    missing_ref_fields: list[str] | None = None,
) -> SourceAcquisitionReport:
    return SourceAcquisitionReport(
        id=f"source-acquisition:{run_ref}",
        run_ref=run_ref,
        fetch_attempt_refs=[attempt.id],
        fetch_result_refs=[fetch_result_ref] if fetch_result_ref else [],
        policy_decision_refs=policy_decision_refs,
        frontier_item_ref=frontier_item_ref,
        lease_ref=lease_ref,
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
        recovery_report_refs=recovery_report_refs,
        failure_report_refs=[failure.id],
        missing_ref_fields=missing_ref_fields or [failure.failure_type.value],
        operator_status=failure.operator_status,
        completion_result=completion_result,
    )


def execute_source_acquisition(
    *,
    fixture_id: str,
    adapter_type: AdapterType,
    scenario: str,
    adapter: SourceAdapterPort,
    store: DeterministicDurableStore | None = None,
) -> SourceAcquisitionOutcome:
    durable = store or DeterministicDurableStore()
    run_ref = f"run:{fixture_id}"
    source_ref = f"source:{fixture_id}"
    objective_ref = f"objective:{fixture_id}"
    plan_ref = f"plan:{fixture_id}"
    policy = _policy(run_ref, source_ref, allow=scenario != "blocked")
    item = enqueue_frontier_item(
        durable,
        item_id=f"frontier:{fixture_id}:source",
        run_ref=run_ref,
        source_ref=source_ref,
        priority=10,
        policy_decision_refs=[policy.id],
    )
    leased = lease_next_frontier_item(
        durable,
        run_ref=run_ref,
        holder_ref="worker:source-fixture",
        expires_at_ref=f"clock:{fixture_id}:lease-expiry",
    )
    if leased is None:
        raise ValueError("source acquisition could not lease frontier item")
    leased_item, lease = leased
    adapter_spec = source_adapter_spec(adapter_type)
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:source",
        command_type="execute_source_adapter",
        target_aggregate_type="SourceAdapterResult",
        target_aggregate_id=f"source-result:{fixture_id}",
        payload_ref=f"payload:{fixture_id}:source-command",
        policy_decision_refs=[policy.id],
    )
    source_command = SourceAdapterCommand(
        command_envelope_id=command.id,
        adapter_spec=adapter_spec,
        source_ref=source_ref,
        policy_snapshot_ref=f"policy-snapshot:{fixture_id}",
        deterministic_clock_ref=f"clock:{fixture_id}:fixed",
        randomness_seed_ref=f"random:{fixture_id}:fixed",
    )
    record, result, outbox, _ = durable.handle_command(
        command,
        run_ref=run_ref,
        objective_ref=objective_ref,
        plan_ref=plan_ref,
        event_type="source_adapter_command_committed",
        output_refs=[f"source-result:{fixture_id}"],
    )
    durable.mark_outbox_dispatched(outbox.id, dispatched_at_ref=f"clock:{outbox.id}:dispatched")
    cursor = durable.build_event_cursor(run_ref)

    def recovery_refs(expected_artifacts: list[Ref]) -> tuple[list[Ref], list[Ref], Ref]:
        sched = scheduler_recovery_report(durable, run_ref=run_ref)
        recovery = validate_durable_recovery(
            run_ref=run_ref,
            command_record_refs=[record.id],
            event_cursors=[cursor],
            outbox_records=durable.list_outbox(run_ref),
            artifact_refs=sorted(durable.backing.artifact_refs),
            expected_artifact_refs=expected_artifacts,
            frontier_item_refs=[item.id],
            lease_refs=[lease.id],
            scheduler_report=sched,
            report_id=f"durable-recovery:{fixture_id}",
        )
        return [sched.id], [recovery.id], recovery.id

    failure_type: SourceFailureType | None = None
    rate_limit: RateLimitDecision | None = None
    if policy.decision != PolicyDecisionValue.ALLOW:
        failure_type = SourceFailureType.SOURCE_BLOCKED
    elif scenario == "rate-limited":
        failure_type = SourceFailureType.SOURCE_RATE_LIMITED
        rate_limit = RateLimitDecision(
            id=f"rate-limit:{fixture_id}",
            run_ref=run_ref,
            source_ref=source_ref,
            decision=RateLimitDecisionValue.RATE_LIMIT,
            rate_limit_policy_ref=f"rate-policy:{fixture_id}",
            retry_after_ref=f"retry-after:{fixture_id}",
            reason_refs=[f"rate-limit-reason:{fixture_id}"],
        )
    elif scenario == "retry-exhausted":
        failure_type = SourceFailureType.RETRY_EXHAUSTED
    elif scenario == "malformed-response":
        failure_type = SourceFailureType.MALFORMED_RESPONSE

    attempt_status = (
        FetchAttemptStatus.SUCCEEDED
        if failure_type is None
        else _attempt_status_for_failure(failure_type)
    )
    attempt = FetchAttempt(
        id=f"fetch-attempt:{fixture_id}:1",
        run_ref=run_ref,
        frontier_item_ref=leased_item.id,
        lease_ref=lease.id,
        adapter_spec_ref=adapter_spec.id,
        source_ref=source_ref,
        policy_decision_refs=[policy.id],
        attempt_number=3 if scenario == "retry-exhausted" else 1,
        status=attempt_status,
        retry_after_ref=rate_limit.retry_after_ref if rate_limit else None,
        failure_report_ref=f"source-failure:{run_ref}:{failure_type.value}"
        if failure_type
        else None,
    )
    if failure_type is not None:
        failure = _failure(
            run_ref=run_ref,
            source_ref=source_ref,
            failure_type=failure_type,
            policy_decision_refs=[policy.id],
            retry_refs=[rate_limit.id] if rate_limit else [f"retry-exhausted:{fixture_id}"]
            if failure_type == SourceFailureType.RETRY_EXHAUSTED
            else [],
        )
        fetch_result = FetchResult(
            id=f"fetch-result:{fixture_id}",
            attempt_ref=attempt.id,
            source_ref=source_ref,
            status=_result_status_for_failure(failure_type),
            result_type=SourceAdapterResultType.BLOCKED_SOURCE
            if failure_type == SourceFailureType.SOURCE_BLOCKED
            else SourceAdapterResultType.FETCH_RESULT,
            failure_report_ref=failure.id,
        )
        scheduler_refs, recovery_report_refs, durable_recovery_ref = recovery_refs([])
        report = _build_non_success_report(
            run_ref=run_ref,
            frontier_item_ref=leased_item.id,
            lease_ref=lease.id,
            attempt=attempt,
            failure=failure,
            policy_decision_refs=[policy.id],
            completion_result=CompletenessResult.NEEDS_REVIEW
            if failure_type == SourceFailureType.SOURCE_RATE_LIMITED
            else CompletenessResult.FAIL,
            command_record_refs=[record.id],
            event_cursor_refs=[cursor.id],
            outbox_refs=[outbox.id],
            recovery_report_refs=recovery_report_refs + scheduler_refs,
            fetch_result_ref=fetch_result.id,
        )
        return SourceAcquisitionOutcome(
            report=report,
            source_result=None,
            fetch_attempt=attempt,
            fetch_result=fetch_result,
            page_snapshot=None,
            document_artifact=None,
            failure_report=failure,
            rate_limit_decision=rate_limit,
            durable_recovery_ref=durable_recovery_ref,
        )

    try:
        source_result = adapter.execute(source_command)
    except ValueError:
        source_result = None
    if scenario == "adapter-mismatch" or source_result is None:
        failure = _failure(
            run_ref=run_ref,
            source_ref=source_ref,
            failure_type=SourceFailureType.ADAPTER_MISMATCH,
            policy_decision_refs=[policy.id],
        )
        failed_attempt = attempt.model_copy(
            update={"status": FetchAttemptStatus.FAILED, "failure_report_ref": failure.id}
        )
        scheduler_refs, recovery_report_refs, durable_recovery_ref = recovery_refs([])
        report = _build_non_success_report(
            run_ref=run_ref,
            frontier_item_ref=leased_item.id,
            lease_ref=lease.id,
            attempt=failed_attempt,
            failure=failure,
            policy_decision_refs=[policy.id],
            completion_result=CompletenessResult.FAIL,
            command_record_refs=[record.id],
            event_cursor_refs=[cursor.id],
            outbox_refs=[outbox.id],
            recovery_report_refs=recovery_report_refs + scheduler_refs,
        )
        return SourceAcquisitionOutcome(
            report=report,
            source_result=source_result,
            fetch_attempt=failed_attempt,
            fetch_result=None,
            page_snapshot=None,
            document_artifact=None,
            failure_report=failure,
            rate_limit_decision=None,
            durable_recovery_ref=durable_recovery_ref,
        )

    raw_artifact_ref = source_result.output_refs[0]
    durable.register_artifact_ref(raw_artifact_ref)
    if scenario == "missing-artifact":
        durable.remove_artifact_ref_for_fixture(raw_artifact_ref)
    fetch_result = FetchResult(
        id=f"fetch-result:{fixture_id}",
        attempt_ref=attempt.id,
        source_ref=source_ref,
        status=FetchResultStatus.SUCCEEDED,
        result_type=source_result.result_type,
        raw_artifact_refs=[raw_artifact_ref],
        metadata_refs=[f"metadata:{fixture_id}:{adapter_type.value}"],
    )
    digest = stable_hash(f"{adapter_type.value}:{source_ref}:{raw_artifact_ref}")
    page_snapshot = None
    document_artifact = None
    if adapter_type == AdapterType.DOCUMENT_SOURCE:
        document_artifact = DocumentArtifact(
            id=f"document-artifact:{fixture_id}",
            fetch_result_ref=fetch_result.id,
            source_ref=source_ref,
            raw_artifact_ref=raw_artifact_ref,
            document_type="fixture-document",
            content_digest=digest,
            metadata_refs=[f"metadata:{fixture_id}:{adapter_type.value}"],
        )
    else:
        page_snapshot = PageSnapshot(
            id=f"page-snapshot:{fixture_id}",
            fetch_result_ref=fetch_result.id,
            source_ref=source_ref,
            raw_artifact_ref=raw_artifact_ref,
            content_digest=digest,
            content_type=(
                "application/json"
                if adapter_type == AdapterType.API_SOURCE
                else "application/xml"
                if adapter_type in {AdapterType.SITEMAP, AdapterType.RSS}
                else "text/html"
            ),
            canonical_ref=f"canonical:{source_ref}",
            privacy_classification_ref="privacy:internal",
        )
    complete_frontier_item(
        durable,
        item_ref=leased_item.id,
        lease_ref=lease.id,
        lease_token_ref=lease.lease_token_ref,
        result_refs=[source_result.id, fetch_result.id],
    )
    scheduler_refs, recovery_report_refs, durable_recovery_ref = recovery_refs([raw_artifact_ref])
    completion = (
        CompletenessResult.FAIL
        if scenario == "missing-artifact"
        else CompletenessResult.PASS
    )
    missing = ["artifact_refs"] if scenario == "missing-artifact" else []
    missing_failure = (
        _failure(
            run_ref=run_ref,
            source_ref=source_ref,
            failure_type=SourceFailureType.MISSING_RAW_ARTIFACT,
            policy_decision_refs=[policy.id],
        )
        if scenario == "missing-artifact"
        else None
    )
    report = SourceAcquisitionReport(
        id=f"source-acquisition:{fixture_id}",
        run_ref=run_ref,
        source_adapter_result_ref=source_result.id,
        fetch_attempt_refs=[attempt.id],
        fetch_result_refs=[fetch_result.id],
        artifact_refs=[] if scenario == "missing-artifact" else [raw_artifact_ref],
        policy_decision_refs=[policy.id],
        frontier_item_ref=leased_item.id,
        lease_ref=lease.id,
        command_record_refs=[record.id],
        event_cursor_refs=[cursor.id],
        outbox_refs=[outbox.id],
        recovery_report_refs=recovery_report_refs + scheduler_refs,
        failure_report_refs=[missing_failure.id] if missing_failure else [],
        missing_ref_fields=missing,
        operator_status="missing_raw_artifact" if missing_failure else "source_acquired",
        completion_result=completion,
    )
    return SourceAcquisitionOutcome(
        report=report,
        source_result=source_result,
        fetch_attempt=attempt,
        fetch_result=fetch_result,
        page_snapshot=page_snapshot,
        document_artifact=document_artifact,
        failure_report=missing_failure,
        rate_limit_decision=None,
        durable_recovery_ref=durable_recovery_ref,
    )
