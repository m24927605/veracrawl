from __future__ import annotations

import pytest

from veracrawl.contracts.enums import CompletenessResult, FrontierItemStatus, QueueLeaseStatus
from veracrawl.runtime_support.durable_store import DeterministicDurableStore
from veracrawl.scheduler.runtime import (
    LeaseTokenError,
    complete_frontier_item,
    enqueue_frontier_item,
    expire_lease,
    heartbeat_lease,
    lease_next_frontier_item,
    release_frontier_item,
    scheduler_recovery_report,
)


def test_scheduler_leases_highest_priority_item_and_completes_with_token() -> None:
    store = DeterministicDurableStore()
    enqueue_frontier_item(
        store, item_id="frontier:low", run_ref="run:s", source_ref="s:1", priority=1
    )
    enqueue_frontier_item(
        store, item_id="frontier:high", run_ref="run:s", source_ref="s:2", priority=10
    )
    leased = lease_next_frontier_item(
        store,
        run_ref="run:s",
        holder_ref="worker:1",
        expires_at_ref="clock:lease",
    )
    assert leased is not None
    item, lease = leased
    assert item.id == "frontier:high"
    heartbeat = heartbeat_lease(
        store,
        lease_ref=lease.id,
        lease_token_ref=lease.lease_token_ref,
        heartbeat_ref="heartbeat:1",
    )
    assert heartbeat.heartbeat_ref == "heartbeat:1"
    completed_item, completed_lease = complete_frontier_item(
        store,
        item_ref=item.id,
        lease_ref=lease.id,
        lease_token_ref=lease.lease_token_ref,
        result_refs=["source-result:1"],
    )
    assert completed_item.status == FrontierItemStatus.COMPLETED
    assert completed_lease.status == QueueLeaseStatus.COMPLETED


def test_invalid_lease_token_is_rejected_and_reported() -> None:
    store = DeterministicDurableStore()
    item = enqueue_frontier_item(
        store,
        item_id="frontier:invalid",
        run_ref="run:invalid",
        source_ref="s:invalid",
        priority=1,
    )
    leased = lease_next_frontier_item(
        store,
        run_ref="run:invalid",
        holder_ref="worker:1",
        expires_at_ref="clock:lease",
    )
    assert leased is not None
    _, lease = leased
    with pytest.raises(LeaseTokenError):
        complete_frontier_item(
            store,
            item_ref=item.id,
            lease_ref=lease.id,
            lease_token_ref="wrong",
            result_refs=["source-result:1"],
        )
    report = scheduler_recovery_report(store, run_ref="run:invalid")
    assert report.completeness_result == CompletenessResult.FAIL
    assert report.invalid_lease_refs


def test_expired_lease_retries_then_dead_letters() -> None:
    store = DeterministicDurableStore()
    enqueue_frontier_item(
        store,
        item_id="frontier:expire",
        run_ref="run:expire",
        source_ref="s:expire",
        priority=1,
        max_attempts=1,
    )
    leased = lease_next_frontier_item(
        store,
        run_ref="run:expire",
        holder_ref="worker:1",
        expires_at_ref="clock:lease",
    )
    assert leased is not None
    item, lease = leased
    dead_letter, expired = expire_lease(
        store,
        lease_ref=lease.id,
        reason_ref="lease-expired:test",
    )
    assert item.status == FrontierItemStatus.LEASED
    assert expired.status == QueueLeaseStatus.EXPIRED
    assert dead_letter.status == FrontierItemStatus.DEAD_LETTERED
    report = scheduler_recovery_report(store, run_ref="run:expire")
    assert report.completeness_result == CompletenessResult.FAIL


def test_release_returns_item_to_queue() -> None:
    store = DeterministicDurableStore()
    enqueue_frontier_item(
        store,
        item_id="frontier:release",
        run_ref="run:r",
        source_ref="s:r",
        priority=1,
    )
    leased = lease_next_frontier_item(
        store,
        run_ref="run:r",
        holder_ref="worker:1",
        expires_at_ref="clock:lease",
    )
    assert leased is not None
    item, lease = leased
    released_item, released_lease = release_frontier_item(
        store,
        item_ref=item.id,
        lease_ref=lease.id,
        lease_token_ref=lease.lease_token_ref,
    )
    assert released_item.status == FrontierItemStatus.QUEUED
    assert released_lease.status == QueueLeaseStatus.RELEASED
