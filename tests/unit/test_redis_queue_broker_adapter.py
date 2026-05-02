from __future__ import annotations

import pytest

from veracrawl.adapters.queue_brokers.redis import (
    RedisQueueBrokerAdapter,
    RedisRuntimeUnavailableError,
    redis_queue_broker_adapter_spec,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    QueueBrokerAdapterKind,
    QueueBrokerCapability,
)
from veracrawl.scale.broker_conformance import (
    run_queue_broker_conformance,
    run_queue_broker_runtime_unavailable_conformance,
)


def test_redis_queue_broker_spec_declares_operational_kind() -> None:
    spec = redis_queue_broker_adapter_spec("unit", ["policy:unit:queue-broker"])
    assert spec.adapter_kind == QueueBrokerAdapterKind.REDIS
    assert set(spec.capability_refs) == set(QueueBrokerCapability)
    assert spec.fencing_token_supported is True
    assert spec.idempotency_supported is True


def test_redis_queue_broker_requires_url() -> None:
    with pytest.raises(RedisRuntimeUnavailableError):
        RedisQueueBrokerAdapter("")


def test_redis_queue_broker_rejects_unsafe_namespace() -> None:
    with pytest.raises(ValueError):
        RedisQueueBrokerAdapter("redis://example.invalid/0", namespace="bad namespace")


def test_redis_runtime_unavailable_reports_needs_review() -> None:
    spec = redis_queue_broker_adapter_spec("redis-broker-runtime-unavailable", ["policy:unit"])
    result = run_queue_broker_runtime_unavailable_conformance(
        fixture_id="redis-broker-runtime-unavailable",
        adapter_spec=spec,
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.operator_status == "redis_broker_runtime_unavailable"
    assert result.report.contract_only_refs


def test_queue_broker_negative_scenarios_emit_failures() -> None:
    expectations = {
        "broker-missing-fencing-token": "broker_missing_fencing_token",
        "broker-missing-heartbeat": "broker_missing_heartbeat",
        "broker-missing-dead-letter": "broker_missing_dead_letter",
    }
    for scenario, operator_status in expectations.items():
        spec = redis_queue_broker_adapter_spec(scenario, [f"policy:{scenario}:queue-broker"])
        result = run_queue_broker_conformance(
            fixture_id=scenario,
            scenario=scenario,
            broker=None,
            adapter_spec=spec,
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.missing_ref_fields
