from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.infrastructure import RuntimeInfrastructureSpec
from veracrawl.runtime_support.infrastructure_gate import (
    run_runtime_infrastructure_gate,
    run_runtime_infrastructure_runtime_unavailable_gate,
    runtime_infrastructure_spec,
)


def _spec() -> RuntimeInfrastructureSpec:
    return runtime_infrastructure_spec(
        "unit",
        persistence_adapter_ref="persistence-adapter:unit:postgres",
        queue_broker_adapter_ref="queue-broker-adapter:unit:redis",
        object_store_adapter_ref="object-store-adapter:unit:s3",
        policy_decision_refs=["policy:unit:infrastructure"],
    )


def test_runtime_infrastructure_unavailable_reports_needs_review() -> None:
    result = run_runtime_infrastructure_runtime_unavailable_gate(
        fixture_id="operational-infrastructure-runtime-unavailable",
        spec=_spec(),
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.operator_status == "operational_infrastructure_runtime_unavailable"
    assert result.report.contract_only_refs


def test_runtime_infrastructure_negative_scenarios_emit_failures() -> None:
    expectations = {
        "infrastructure-missing-persistence-refs": "infrastructure_missing_persistence_refs",
        "infrastructure-missing-queue-refs": "infrastructure_missing_queue_refs",
        "infrastructure-missing-object-refs": "infrastructure_missing_object_refs",
        "infrastructure-missing-replay-refs": "infrastructure_missing_replay_refs",
    }
    for scenario, operator_status in expectations.items():
        result = run_runtime_infrastructure_gate(
            fixture_id=scenario,
            scenario=scenario,
            spec=_spec(),
            persistence=None,
            queue_broker=None,
            object_store=None,
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.missing_ref_fields
