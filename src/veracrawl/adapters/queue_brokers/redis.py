"""Operational Redis queue broker adapter."""

from __future__ import annotations

import importlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast
from uuid import uuid4

from pydantic import BaseModel

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    QueueBrokerAdapterKind,
    QueueBrokerCapability,
    QueueBrokerOperation,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleShardLeaseStatus,
)
from veracrawl.contracts.scale import (
    QueueBrokerAdapterSpec,
    QueueBrokerOperationRecord,
    QueueItem,
    RetryDeadLetterRecord,
    ShardLease,
)

ModelT = TypeVar("ModelT", bound=BaseModel)

_NAMESPACE_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


class RedisRuntimeUnavailableError(RuntimeError):
    """Raised when the optional Redis runtime dependency or URL is unavailable."""


class RedisQueueBrokerAdapter:
    """Redis-backed queue broker for executable queue conformance."""

    def __init__(
        self,
        redis_url: str,
        *,
        namespace: str = "veracrawl",
        client: Any | None = None,
    ) -> None:
        if not redis_url and client is None:
            raise RedisRuntimeUnavailableError("Redis URL is required")
        if not _NAMESPACE_PATTERN.match(namespace):
            raise ValueError(f"unsafe Redis namespace: {namespace}")
        self.redis_url = redis_url
        self.namespace = namespace
        self._client_provided = client is not None
        if client is not None:
            self._client = client
        else:
            self._client = _load_redis_from_url()(redis_url, decode_responses=True)

    def reopen(self) -> RedisQueueBrokerAdapter:
        return RedisQueueBrokerAdapter(
            self.redis_url,
            namespace=self.namespace,
            client=self._client if self._client_provided else None,
        )

    def reset_namespace(self) -> None:
        keys = list(self._client.scan_iter(match=f"{self.namespace}:*"))
        if keys:
            self._client.delete(*keys)

    def enqueue(
        self,
        item: QueueItem,
        *,
        adapter_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord:
        created = bool(
            self._client.set(
                self._idempotency_key(item.queue_name, item.idempotency_key),
                item.id,
                nx=True,
            )
        )
        if not created:
            duplicate_of = str(
                self._client.get(self._idempotency_key(item.queue_name, item.idempotency_key))
            )
            return self._record_operation(
                adapter_ref=adapter_ref,
                queue_name=item.queue_name,
                operation=QueueBrokerOperation.DUPLICATE_ENQUEUE,
                queue_item_ref=item.id,
                duplicate_of_ref=duplicate_of,
                fairness_scope_refs=fairness_scope_refs,
                backpressure_signal_refs=backpressure_signal_refs,
                policy_decision_refs=policy_decision_refs,
            )

        self._put_model(self._item_key(item.id), item)
        self._client.rpush(self._queue_key(item.queue_name), item.id)
        return self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=item.queue_name,
            operation=QueueBrokerOperation.ENQUEUE,
            queue_item_ref=item.id,
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )

    def lease(
        self,
        queue_name: ScaleQueueName,
        *,
        adapter_ref: Ref,
        worker_id: str,
        visibility_timeout_seconds: int,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> tuple[QueueItem, ShardLease, QueueBrokerOperationRecord]:
        item_ref = self._client.lpop(self._queue_key(queue_name))
        if item_ref is None:
            raise ValueError(f"queue {queue_name.value} is empty")
        item = self._get_model(self._item_key(str(item_ref)), QueueItem)
        if item is None:
            raise ValueError(f"queued item {item_ref} is missing")
        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(seconds=visibility_timeout_seconds)
        token = f"fencing-token:{item.id}:{uuid4().hex}"
        leased_item = item.model_copy(
            update={
                "lease_token": token,
                "lease_expires_at": expires_at,
                "attempts": item.attempts + 1,
                "status": ScaleQueueItemStatus.LEASED,
                "updated_at": now,
            }
        )
        lease = ShardLease(
            id=f"queue-broker-lease:{item.id}:{uuid4().hex}",
            queue_name=queue_name,
            shard_key=item.shard_key,
            worker_id=worker_id,
            lease_token=token,
            acquired_at=now,
            heartbeat_at=now,
            expires_at=expires_at,
            policy_decision_refs=policy_decision_refs,
            status=ScaleShardLeaseStatus.ACTIVE,
        )
        self._put_model(self._item_key(leased_item.id), leased_item)
        self._put_model(self._lease_key(lease.id), lease)
        operation = self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=queue_name,
            operation=QueueBrokerOperation.LEASE,
            queue_item_ref=leased_item.id,
            lease_ref=lease.id,
            fencing_token_ref=token,
            visibility_timeout_ref=f"visibility-timeout:{lease.id}:{visibility_timeout_seconds}",
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )
        return leased_item, lease, operation

    def heartbeat(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        visibility_timeout_seconds: int,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord:
        current = self._validate_lease(lease)
        now = datetime.now(tz=UTC)
        updated = current.model_copy(
            update={
                "heartbeat_at": now,
                "expires_at": now + timedelta(seconds=visibility_timeout_seconds),
                "policy_decision_refs": policy_decision_refs,
            }
        )
        self._put_model(self._lease_key(updated.id), updated)
        heartbeat_ref = f"queue-broker-heartbeat:{updated.id}:{self._next_count('heartbeat')}"
        return self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=updated.queue_name,
            operation=QueueBrokerOperation.HEARTBEAT,
            queue_item_ref=item_ref,
            lease_ref=updated.id,
            fencing_token_ref=updated.lease_token,
            visibility_timeout_ref=f"visibility-timeout:{updated.id}:{visibility_timeout_seconds}",
            heartbeat_ref=heartbeat_ref,
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )

    def ack(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord:
        current_lease = self._validate_lease(lease)
        item = self._get_model(self._item_key(item_ref), QueueItem)
        if item is None or item.lease_token != current_lease.lease_token:
            raise ValueError(f"invalid queue broker ack refs for {item_ref}")
        self._put_model(
            self._item_key(item.id),
            item.model_copy(update={"status": ScaleQueueItemStatus.ACKED}),
        )
        self._put_model(
            self._lease_key(current_lease.id),
            current_lease.model_copy(update={"status": ScaleShardLeaseStatus.RELEASED}),
        )
        return self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=item.queue_name,
            operation=QueueBrokerOperation.ACK,
            queue_item_ref=item.id,
            lease_ref=current_lease.id,
            fencing_token_ref=current_lease.lease_token,
            visibility_timeout_ref=f"visibility-timeout:{current_lease.id}:ack",
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )

    def nack(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        failure_refs: list[Ref],
        recovery_refs: list[Ref],
        retry_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord:
        current_lease = self._validate_lease(lease)
        item = self._get_model(self._item_key(item_ref), QueueItem)
        if item is None or item.lease_token != current_lease.lease_token:
            raise ValueError(f"invalid queue broker nack refs for {item_ref}")
        requeued = item.model_copy(
            update={
                "lease_token": None,
                "lease_expires_at": None,
                "status": ScaleQueueItemStatus.QUEUED,
                "updated_at": datetime.now(tz=UTC),
            }
        )
        self._put_model(self._item_key(requeued.id), requeued)
        self._put_model(
            self._lease_key(current_lease.id),
            current_lease.model_copy(update={"status": ScaleShardLeaseStatus.RELEASED}),
        )
        self._client.rpush(self._queue_key(item.queue_name), requeued.id)
        return self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=item.queue_name,
            operation=QueueBrokerOperation.NACK,
            queue_item_ref=item.id,
            lease_ref=current_lease.id,
            fencing_token_ref=current_lease.lease_token,
            visibility_timeout_ref=f"visibility-timeout:{current_lease.id}:nack",
            retry_ref=retry_ref,
            failure_record_refs=failure_refs,
            recovery_action_refs=recovery_refs,
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )

    def dead_letter(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        dead_letter: RetryDeadLetterRecord,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord:
        current_lease = self._validate_lease(lease)
        item = self._get_model(self._item_key(item_ref), QueueItem)
        if item is None or item.lease_token != current_lease.lease_token:
            raise ValueError(f"invalid queue broker dead-letter refs for {item_ref}")
        updated_item = item.model_copy(
            update={
                "status": ScaleQueueItemStatus.DEAD_LETTERED,
                "attempts": max(item.attempts, dead_letter.attempts),
                "updated_at": datetime.now(tz=UTC),
            }
        )
        self._put_model(self._item_key(updated_item.id), updated_item)
        self._put_model(self._dead_letter_record_key(dead_letter.id), dead_letter)
        self._put_model(
            self._lease_key(current_lease.id),
            current_lease.model_copy(update={"status": ScaleShardLeaseStatus.RELEASED}),
        )
        self._client.rpush(self._dead_letter_key(item.queue_name), dead_letter.id)
        return self._record_operation(
            adapter_ref=adapter_ref,
            queue_name=item.queue_name,
            operation=QueueBrokerOperation.DEAD_LETTER,
            queue_item_ref=item.id,
            lease_ref=current_lease.id,
            fencing_token_ref=current_lease.lease_token,
            visibility_timeout_ref=f"visibility-timeout:{current_lease.id}:dead-letter",
            failure_record_refs=[dead_letter.failure_record_id],
            recovery_action_refs=dead_letter.recovery_action_refs,
            dead_letter_ref=dead_letter.id,
            fairness_scope_refs=fairness_scope_refs,
            backpressure_signal_refs=backpressure_signal_refs,
            policy_decision_refs=policy_decision_refs,
        )

    def queued_count(self, queue_name: ScaleQueueName) -> int:
        return int(self._client.llen(self._queue_key(queue_name)))

    def dead_letter_count(self, queue_name: ScaleQueueName) -> int:
        return int(self._client.llen(self._dead_letter_key(queue_name)))

    def _validate_lease(self, lease: ShardLease) -> ShardLease:
        current = self._get_model(self._lease_key(lease.id), ShardLease)
        if current is None or current.lease_token != lease.lease_token:
            raise ValueError(f"invalid queue broker lease token for {lease.id}")
        return current

    def _record_operation(
        self,
        *,
        adapter_ref: Ref,
        queue_name: ScaleQueueName,
        operation: QueueBrokerOperation,
        queue_item_ref: Ref,
        lease_ref: Ref | None = None,
        fencing_token_ref: Ref | None = None,
        visibility_timeout_ref: Ref | None = None,
        heartbeat_ref: Ref | None = None,
        retry_ref: Ref | None = None,
        failure_record_refs: list[Ref] | None = None,
        recovery_action_refs: list[Ref] | None = None,
        dead_letter_ref: Ref | None = None,
        duplicate_of_ref: Ref | None = None,
        fairness_scope_refs: list[Ref] | None = None,
        backpressure_signal_refs: list[Ref] | None = None,
        policy_decision_refs: list[Ref] | None = None,
    ) -> QueueBrokerOperationRecord:
        count = self._next_count("operations")
        record = QueueBrokerOperationRecord(
            id=f"queue-broker-operation:{queue_item_ref}:{operation.value}:{count}",
            adapter_ref=adapter_ref,
            queue_name=queue_name,
            operation=operation,
            queue_item_ref=queue_item_ref,
            lease_ref=lease_ref,
            fencing_token_ref=fencing_token_ref,
            visibility_timeout_ref=visibility_timeout_ref,
            heartbeat_ref=heartbeat_ref,
            retry_ref=retry_ref,
            failure_record_refs=failure_record_refs or [],
            recovery_action_refs=recovery_action_refs or [],
            dead_letter_ref=dead_letter_ref,
            duplicate_of_ref=duplicate_of_ref,
            fairness_scope_refs=fairness_scope_refs or [],
            backpressure_signal_refs=backpressure_signal_refs or [],
            policy_decision_refs=policy_decision_refs or [],
        )
        self._put_model(self._operation_key(record.id), record)
        self._client.rpush(self._operations_key(), record.id)
        return record

    def _next_count(self, counter: str) -> int:
        return int(self._client.incr(f"{self.namespace}:counter:{counter}"))

    def _put_model(self, key: str, model: BaseModel) -> None:
        self._client.set(key, json.dumps(model.model_dump(mode="json"), sort_keys=True))

    def _get_model(self, key: str, model_type: type[ModelT]) -> ModelT | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        loaded = json.loads(str(raw))
        return model_type.model_validate(loaded)

    def _queue_key(self, queue_name: ScaleQueueName) -> str:
        return f"{self.namespace}:queue:{queue_name.value}"

    def _dead_letter_key(self, queue_name: ScaleQueueName) -> str:
        return f"{self.namespace}:dead-letter:{queue_name.value}"

    def _idempotency_key(self, queue_name: ScaleQueueName, idempotency_key: str) -> str:
        return f"{self.namespace}:idempotency:{queue_name.value}:{idempotency_key}"

    def _item_key(self, item_ref: Ref) -> str:
        return f"{self.namespace}:item:{item_ref}"

    def _lease_key(self, lease_ref: Ref) -> str:
        return f"{self.namespace}:lease:{lease_ref}"

    def _operation_key(self, operation_ref: Ref) -> str:
        return f"{self.namespace}:operation:{operation_ref}"

    def _operations_key(self) -> str:
        return f"{self.namespace}:operations"

    def _dead_letter_record_key(self, dead_letter_ref: Ref) -> str:
        return f"{self.namespace}:dead-letter-record:{dead_letter_ref}"


def redis_queue_broker_adapter_spec(
    fixture_id: str,
    policy_refs: list[Ref],
    *,
    fairness_refs: list[Ref] | None = None,
    backpressure_refs: list[Ref] | None = None,
) -> QueueBrokerAdapterSpec:
    return QueueBrokerAdapterSpec(
        id=f"queue-broker-adapter:{fixture_id}:redis",
        adapter_kind=QueueBrokerAdapterKind.REDIS,
        queue_names=list(ScaleQueueName),
        capability_refs=list(QueueBrokerCapability),
        visibility_timeout_seconds=30,
        fencing_token_supported=True,
        idempotency_supported=True,
        fairness_scope_refs=fairness_refs or [f"fairness-scope:{fixture_id}:site"],
        backpressure_signal_refs=backpressure_refs or [f"backpressure-signal:{fixture_id}:lag"],
        policy_decision_refs=policy_refs,
    )


def _load_redis_from_url() -> Callable[..., Any]:
    try:
        module = importlib.import_module("redis")
    except ImportError as exc:
        raise RedisRuntimeUnavailableError(
            "redis is required for operational queue broker conformance; "
            "install with the queue-redis extra"
        ) from exc
    redis_class = module.__dict__.get("Redis")
    from_url = getattr(redis_class, "from_url", None)
    if not callable(from_url):
        raise RedisRuntimeUnavailableError("redis.Redis.from_url is unavailable")
    return cast(Callable[..., Any], from_url)
