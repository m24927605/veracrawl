from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionPersistenceFailureType,
    RunStatus,
)
from veracrawl.contracts.objective import (
    ProductionPersistenceFixtureManifest,
    ProductionPersistenceRuntimeReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> ProductionPersistenceRuntimeReport:
    return ProductionPersistenceRuntimeReport(
        id="production-persistence-runtime-report:test",
        fixture_id="production-persistence-wiring-success",
        run_ref="run:test",
        project_ref="project:test",
        site_scope_ref="site-scope:test",
        objective_ref="objective:test",
        plan_ref="plan:test",
        run_control_report_ref="production-run-control-report:test",
        status=RunStatus.COMPLETED,
        completion_result=CompletenessResult.PASS,
        operator_status="production_persistence_runtime_completed",
        adapter_ref="adapter:test",
        transaction_ref="transaction:test",
        canonical_state_refs=["canonical:run:test"],
        run_control_command_result_refs=["command-result:run-control"],
        persistence_command_record_refs=["durable-command:persistence"],
        idempotency_record_refs=["idempotency:persistence"],
        event_refs=["event:run-control", "event:persistence"],
        event_cursor_ref="event-cursor:test",
        outbox_refs=["outbox:persistence"],
        artifact_refs=["artifact:report", "artifact:replay"],
        queue_operation_refs=["queue-operation:enqueue", "queue-operation:ack"],
        lease_refs=["lease:test"],
        policy_decision_refs=["policy:test"],
        replay_bundle_ref="replay-bundle:test",
        reloaded=True,
    )


def test_production_persistence_report_requires_reloaded_refs() -> None:
    assert _passing_report().completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        ProductionPersistenceRuntimeReport.model_validate(
            _passing_report().model_dump(mode="json") | {"reloaded": False}
        )
    with pytest.raises(ValidationError):
        ProductionPersistenceRuntimeReport(
            id="production-persistence-runtime-report:bad",
            fixture_id="production-persistence-wiring-success",
            run_ref="run:test",
            project_ref="project:test",
            site_scope_ref="site-scope:test",
            objective_ref="objective:test",
            plan_ref="plan:test",
            status=RunStatus.COMPLETED,
            completion_result=CompletenessResult.PASS,
            operator_status="production_persistence_runtime_completed",
            reloaded=True,
        )


def test_production_persistence_failure_requires_typed_missing_refs() -> None:
    failure = ProductionPersistenceRuntimeReport(
        id="production-persistence-runtime-report:failure",
        fixture_id="production-persistence-event-gap",
        run_ref="run:test",
        project_ref="project:test",
        site_scope_ref="site-scope:test",
        objective_ref="objective:test",
        plan_ref="plan:test",
        status=RunStatus.FAILED,
        completion_result=CompletenessResult.FAIL,
        operator_status=ProductionPersistenceFailureType.EVENT_GAP.value,
        failure_record_refs=["failure:event-gap"],
        missing_ref_fields=["event_cursor_ref"],
        failure_type=ProductionPersistenceFailureType.EVENT_GAP,
    )
    assert failure.failure_type == ProductionPersistenceFailureType.EVENT_GAP
    with pytest.raises(ValidationError):
        ProductionPersistenceRuntimeReport(
            id="production-persistence-runtime-report:bad-failure",
            fixture_id="production-persistence-event-gap",
            run_ref="run:test",
            project_ref="project:test",
            site_scope_ref="site-scope:test",
            objective_ref="objective:test",
            plan_ref="plan:test",
            status=RunStatus.FAILED,
            completion_result=CompletenessResult.FAIL,
            operator_status=ProductionPersistenceFailureType.EVENT_GAP.value,
        )


def test_production_persistence_fixture_manifest_requires_target_and_failure_type() -> None:
    manifest = ProductionPersistenceFixtureManifest(
        id="production-persistence-wiring-success",
        scenario="success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="production_persistence_runtime_completed",
        required_ref_types=["canonical_state"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        ProductionPersistenceFixtureManifest(
            id="production-persistence-event-gap",
            scenario="event-gap",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=ProductionPersistenceFailureType.EVENT_GAP.value,
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_production_persistence_registry_is_materialized() -> None:
    assert "ProductionPersistenceRuntimeReport" in FOUNDATION_CONTRACTS
    assert "ProductionPersistenceFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_production_persistence_runtime_report" in COMMAND_TYPES
    assert "production_persistence_runtime_reported" in EVENT_TYPES
    assert "production-persistence-wiring-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["production_persistence_runtime_wiring"]
    assert area.coverage_status == "materialized"
    assert "ProductionPersistenceRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
