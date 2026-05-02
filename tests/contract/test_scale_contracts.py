from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
)
from veracrawl.contracts.scale import QueueItem, QueueTopologySpec


def test_queue_topology_requires_all_target_queues() -> None:
    topology = QueueTopologySpec(
        id="queue-topology:unit",
        project_id="project:unit",
        queue_names=list(ScaleQueueName),
        shard_key_parts=["project_id", "site_id", "adapter_type", "priority_band"],
        fairness_scope_refs=["fairness:project", "fairness:site"],
        per_project_concurrency_limit=10,
        per_site_concurrency_limit=2,
        policy_decision_refs=["policy:unit:scale"],
    )
    assert len(topology.queue_names) == len(ScaleQueueName)
    with pytest.raises(ValidationError):
        QueueTopologySpec(
            id="queue-topology:bad",
            project_id="project:bad",
            queue_names=[ScaleQueueName.FRONTIER],
            shard_key_parts=["project_id"],
            fairness_scope_refs=["fairness:bad"],
            per_project_concurrency_limit=1,
            per_site_concurrency_limit=1,
            policy_decision_refs=["policy:bad:scale"],
        )


def test_leased_queue_item_requires_token_and_expiry() -> None:
    now = datetime.now(tz=UTC)
    with pytest.raises(ValidationError):
        QueueItem(
            id="queue-item:bad",
            queue_name=ScaleQueueName.FRONTIER,
            shard_key="project|site|http|p1",
            run_id="run:bad",
            aggregate_type="FrontierItem",
            aggregate_id="frontier:bad",
            command_ref="command:bad",
            priority=1,
            retry_class=ScaleRetryClass.TRANSIENT,
            idempotency_key="idempotency:bad",
            expected_version_ref="expected-version:bad",
            attempts=1,
            deadline_at=now + timedelta(minutes=5),
            status=ScaleQueueItemStatus.LEASED,
        )
