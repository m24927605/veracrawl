from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    WorkerOrchestrationFailureType,
    WorkerPool,
)
from veracrawl.contracts.scale import (
    WorkerOrchestrationFixtureManifest,
    WorkerOrchestrationRuntimeReport,
)


def _complete_report(**overrides: object) -> WorkerOrchestrationRuntimeReport:
    data: dict[str, object] = {
        "id": "worker-orchestration-report:unit",
        "fixture_id": "unit-worker-orchestration",
        "run_ref": "run:unit",
        "production_persistence_runtime_report_ref": "production-persistence:unit",
        "queue_broker_conformance_report_ref": "queue-broker:unit",
        "live_http_acquisition_report_ref": "live-http:unit",
        "live_normalization_runtime_report_ref": "live-normalization:unit",
        "live_evidence_verification_runtime_report_ref": "live-evidence:unit",
        "scale_recovery_report_ref": "scale-recovery:unit",
        "worker_pool_refs": [f"worker-pool:{pool.value}" for pool in WorkerPool],
        "worker_heartbeat_refs": [f"worker-heartbeat:{pool.value}" for pool in WorkerPool],
        "worker_capacity_refs": [f"worker-capacity:{pool.value}" for pool in WorkerPool],
        "queue_topology_ref": "queue-topology:unit",
        "queue_item_refs": ["queue-item:frontier"],
        "shard_lease_refs": ["shard-lease:frontier"],
        "lease_heartbeat_refs": ["lease-heartbeat:frontier"],
        "fencing_token_refs": ["fencing-token:frontier"],
        "visibility_timeout_refs": ["visibility-timeout:frontier"],
        "fairness_scope_refs": ["fairness:project", "fairness:site"],
        "retry_refs": ["retry:worker-crash"],
        "dead_letter_refs": ["dead-letter:worker-crash"],
        "failure_record_refs": ["failure:worker-crash"],
        "recovery_action_refs": ["recovery:worker-crash"],
        "duplicate_suppression_refs": ["dedupe:idempotency"],
        "backpressure_signal_refs": ["backpressure:queue-lag"],
        "autoscaling_decision_refs": ["autoscaling:fetch"],
        "pending_outbox_refs": ["pending-outbox:recovered"],
        "event_gap_refs": ["event-gap:checked"],
        "policy_decision_refs": ["policy:worker-orchestration"],
        "command_record_refs": ["command:worker-orchestration"],
        "event_cursor_refs": ["event-cursor:worker-orchestration"],
        "outbox_refs": ["outbox:worker-orchestration"],
        "replay_bundle_ref": "replay-bundle:worker-orchestration",
        "operator_status": "worker_orchestration_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return WorkerOrchestrationRuntimeReport(**data)


def test_worker_orchestration_report_requires_complete_success_refs() -> None:
    report = _complete_report()
    assert report.completion_result == CompletenessResult.PASS
    assert len(set(report.worker_pool_refs)) == len(WorkerPool)

    with pytest.raises(ValidationError):
        _complete_report(queue_broker_conformance_report_ref=None)

    with pytest.raises(ValidationError):
        _complete_report(worker_pool_refs=["worker-pool:fetch"])


def test_worker_orchestration_report_rejects_hidden_success_failures() -> None:
    with pytest.raises(ValidationError):
        _complete_report(hidden_dead_letter_refs=["dead-letter:hidden"])

    with pytest.raises(ValidationError):
        _complete_report(duplicate_pollution_refs=["duplicate:pollution"])

    with pytest.raises(ValidationError):
        _complete_report(unrecovered_stale_lease_refs=["shard-lease:stale"])


def test_worker_orchestration_failure_requires_typed_diagnostics() -> None:
    report = WorkerOrchestrationRuntimeReport(
        id="worker-orchestration-report:failure",
        fixture_id="worker-orchestration-missing-persistence",
        run_ref="run:failure",
        failure_type=WorkerOrchestrationFailureType.MISSING_PERSISTENCE,
        failure_report_refs=["failure:missing-persistence"],
        missing_ref_fields=["production_persistence_runtime_report_ref"],
        operator_status=WorkerOrchestrationFailureType.MISSING_PERSISTENCE.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert report.failure_type == WorkerOrchestrationFailureType.MISSING_PERSISTENCE

    with pytest.raises(ValidationError):
        WorkerOrchestrationRuntimeReport(
            id="worker-orchestration-report:bad",
            fixture_id="bad",
            run_ref="run:bad",
            operator_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_worker_orchestration_fixture_manifest_validates_target_profile() -> None:
    manifest = WorkerOrchestrationFixtureManifest(
        id="worker-orchestration-production-success",
        scenario="worker-orchestration-production-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="worker_orchestration_completed",
        required_ref_types=["worker_pool_refs", "queue_item_refs", "replay_bundle_ref"],
    )
    assert manifest.id == "worker-orchestration-production-success"

    with pytest.raises(ValidationError):
        WorkerOrchestrationFixtureManifest(
            id="worker-orchestration-negative-pass",
            scenario="worker-orchestration-negative-pass",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            negative_case=True,
            required_ref_types=["worker_pool_refs"],
        )

    with pytest.raises(ValidationError):
        WorkerOrchestrationFixtureManifest(
            id="worker-orchestration-missing-required-refs",
            scenario="worker-orchestration-missing-required-refs",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=WorkerOrchestrationFailureType.REPLAY_MISMATCH,
            negative_case=True,
        )
