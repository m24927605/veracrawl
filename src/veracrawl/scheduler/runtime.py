"""Scheduler frontier and queue lease owner service."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    FrontierItemStatus,
    QueueLeaseStatus,
)
from veracrawl.contracts.scheduler import FrontierItem, QueueLease, SchedulerRecoveryReport
from veracrawl.ports.scheduler import SchedulerStatePort
from veracrawl.runtime_support.durable_store import (
    DeterministicDurableStore,
    mark_frontier_item_status,
    mark_queue_lease_status,
)


class LeaseTokenError(ValueError):
    """Raised when a leased frontier mutation uses an invalid token."""


def enqueue_frontier_item(
    store: SchedulerStatePort,
    *,
    item_id: str,
    run_ref: Ref,
    source_ref: Ref,
    priority: int,
    max_attempts: int = 3,
    policy_decision_refs: list[Ref] | None = None,
) -> FrontierItem:
    item = FrontierItem(
        id=item_id,
        run_ref=run_ref,
        source_ref=source_ref,
        priority=priority,
        max_attempts=max_attempts,
        policy_decision_refs=policy_decision_refs or [],
    )
    store.save_frontier_item(item)
    return item


def lease_next_frontier_item(
    store: DeterministicDurableStore,
    *,
    run_ref: Ref,
    holder_ref: Ref,
    expires_at_ref: Ref,
) -> tuple[FrontierItem, QueueLease] | None:
    eligible = [
        item
        for item in store.list_frontier_items(run_ref)
        if item.status in {FrontierItemStatus.QUEUED, FrontierItemStatus.RETRYING}
    ]
    if not eligible:
        return None
    item = sorted(eligible, key=lambda current: (-current.priority, current.id))[0]
    lease = QueueLease(
        id=f"lease:{item.id}:{item.attempt_count + 1}",
        frontier_item_ref=item.id,
        run_ref=run_ref,
        lease_token_ref=f"lease-token:{item.id}:{item.attempt_count + 1}",
        holder_ref=holder_ref,
        expires_at_ref=expires_at_ref,
    )
    store.save_queue_lease(lease)
    leased_item = mark_frontier_item_status(
        store,
        item,
        status=FrontierItemStatus.LEASED,
        lease_ref=lease.id,
        attempt_count=item.attempt_count + 1,
    )
    return leased_item, lease


def _require_active_lease(
    store: DeterministicDurableStore,
    *,
    lease_ref: Ref,
    lease_token_ref: Ref,
) -> QueueLease:
    lease = store.get_queue_lease(lease_ref)
    if lease is None or lease.lease_token_ref != lease_token_ref:
        invalid_ref = f"invalid-lease:{lease_ref}:{lease_token_ref}"
        store.record_invalid_lease_ref(invalid_ref)
        raise LeaseTokenError(f"invalid lease token for {lease_ref}")
    if lease.status != QueueLeaseStatus.ACTIVE:
        invalid_ref = f"invalid-lease:{lease_ref}:{lease.status.value}"
        store.record_invalid_lease_ref(invalid_ref)
        raise LeaseTokenError(f"lease {lease_ref} is not active")
    return lease


def heartbeat_lease(
    store: DeterministicDurableStore,
    *,
    lease_ref: Ref,
    lease_token_ref: Ref,
    heartbeat_ref: Ref,
) -> QueueLease:
    lease = _require_active_lease(store, lease_ref=lease_ref, lease_token_ref=lease_token_ref)
    heartbeated = mark_queue_lease_status(
        store,
        lease,
        status=QueueLeaseStatus.HEARTBEAT_RECORDED,
        heartbeat_ref=heartbeat_ref,
    )
    active = heartbeated.model_copy(update={"status": QueueLeaseStatus.ACTIVE})
    store.save_queue_lease(active)
    return active


def complete_frontier_item(
    store: DeterministicDurableStore,
    *,
    item_ref: Ref,
    lease_ref: Ref,
    lease_token_ref: Ref,
    result_refs: list[Ref],
) -> tuple[FrontierItem, QueueLease]:
    lease = _require_active_lease(store, lease_ref=lease_ref, lease_token_ref=lease_token_ref)
    item = store.get_frontier_item(item_ref)
    if item is None:
        raise ValueError(f"unknown frontier item: {item_ref}")
    completed_lease = mark_queue_lease_status(
        store,
        lease,
        status=QueueLeaseStatus.COMPLETED,
        completed_at_ref=f"clock:{lease.id}:completed",
    )
    completed_item = mark_frontier_item_status(
        store,
        item,
        status=FrontierItemStatus.COMPLETED,
        result_refs=result_refs,
    )
    return completed_item, completed_lease


def release_frontier_item(
    store: DeterministicDurableStore,
    *,
    item_ref: Ref,
    lease_ref: Ref,
    lease_token_ref: Ref,
) -> tuple[FrontierItem, QueueLease]:
    lease = _require_active_lease(store, lease_ref=lease_ref, lease_token_ref=lease_token_ref)
    item = store.get_frontier_item(item_ref)
    if item is None:
        raise ValueError(f"unknown frontier item: {item_ref}")
    released_lease = mark_queue_lease_status(
        store,
        lease,
        status=QueueLeaseStatus.RELEASED,
        released_at_ref=f"clock:{lease.id}:released",
    )
    released_item = mark_frontier_item_status(
        store,
        item,
        status=FrontierItemStatus.QUEUED,
        lease_ref=lease.id,
    )
    return released_item, released_lease


def expire_lease(
    store: DeterministicDurableStore,
    *,
    lease_ref: Ref,
    reason_ref: Ref,
) -> tuple[FrontierItem, QueueLease]:
    lease = store.get_queue_lease(lease_ref)
    if lease is None:
        raise ValueError(f"unknown lease: {lease_ref}")
    item = store.get_frontier_item(lease.frontier_item_ref)
    if item is None:
        raise ValueError(f"unknown frontier item: {lease.frontier_item_ref}")
    expired = mark_queue_lease_status(
        store,
        lease,
        status=QueueLeaseStatus.EXPIRED,
        expiry_reason_ref=reason_ref,
    )
    next_status = (
        FrontierItemStatus.RETRYING
        if item.attempt_count < item.max_attempts
        else FrontierItemStatus.DEAD_LETTERED
    )
    updated_item = mark_frontier_item_status(
        store,
        item,
        status=next_status,
        failure_refs=[reason_ref] if next_status == FrontierItemStatus.DEAD_LETTERED else [],
        last_error_ref=reason_ref,
    )
    return updated_item, expired


def scheduler_recovery_report(
    store: DeterministicDurableStore,
    *,
    run_ref: Ref,
    report_id: str = "scheduler-recovery:durable",
) -> SchedulerRecoveryReport:
    expired = [
        lease.id
        for lease in store.list_queue_leases(run_ref)
        if lease.status == QueueLeaseStatus.EXPIRED
    ]
    retry_items = [
        item.id
        for item in store.list_frontier_items(run_ref)
        if item.status == FrontierItemStatus.RETRYING
    ]
    dead_letters = [
        item.id
        for item in store.list_frontier_items(run_ref)
        if item.status == FrontierItemStatus.DEAD_LETTERED
    ]
    invalid = store.list_invalid_lease_refs()
    if invalid or dead_letters:
        result = CompletenessResult.FAIL
        operator_status = "invalid_lease" if invalid else "dead_letter"
    elif expired or retry_items:
        result = CompletenessResult.NEEDS_REVIEW
        operator_status = "stale_lease"
    else:
        result = CompletenessResult.PASS
        operator_status = "scheduler_recovered"
    return SchedulerRecoveryReport(
        id=report_id,
        run_ref=run_ref,
        expired_lease_refs=expired,
        retry_frontier_item_refs=retry_items,
        dead_letter_refs=dead_letters,
        invalid_lease_refs=invalid,
        operator_status=operator_status,
        completeness_result=result,
    )
