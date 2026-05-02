from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    BackpressureSignalType,
    OpsSeverity,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
    WorkerPool,
)
from veracrawl.contracts.scale import (
    AutoscalingDecision,
    BackpressureSignal,
    RetryDeadLetterRecord,
    ShardLease,
)


def test_backpressure_threshold_breach_requires_policy_refs() -> None:
    with pytest.raises(ValidationError):
        BackpressureSignal(
            id="backpressure:bad",
            project_id="project:bad",
            site_id="site:bad",
            signal_type=BackpressureSignalType.QUEUE_LAG,
            value=100,
            threshold=50,
            severity=OpsSeverity.HIGH,
        )


def test_autoscaling_capacity_change_requires_policy_refs() -> None:
    with pytest.raises(ValidationError):
        AutoscalingDecision(
            id="autoscaling:bad",
            worker_pool=WorkerPool.FETCH,
            reason_signal_refs=["backpressure:bad"],
            from_capacity=1,
            to_capacity=3,
            cooldown_seconds=60,
        )


def test_dead_letter_requires_failure_and_recovery_refs() -> None:
    with pytest.raises(ValidationError):
        RetryDeadLetterRecord(
            id="dead-letter:bad",
            queue_item_id="queue-item:bad",
            run_id="run:bad",
            retry_class=ScaleRetryClass.WORKER_CRASH,
            attempts=3,
            final_reason="worker_crash",
            failure_record_id="failure:bad",
        )


def test_active_lease_requires_policy_refs() -> None:
    now = datetime.now(tz=UTC)
    with pytest.raises(ValidationError):
        ShardLease(
            id="shard-lease:bad",
            queue_name=ScaleQueueName.FRONTIER,
            shard_key="project|site|http|p1",
            worker_id="worker:bad",
            lease_token="lease-token:bad",
            acquired_at=now,
            heartbeat_at=now + timedelta(seconds=10),
            expires_at=now + timedelta(minutes=5),
            status=ScaleShardLeaseStatus.ACTIVE,
        )
