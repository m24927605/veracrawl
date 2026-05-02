from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.artifact_lifecycle.runtime import InMemoryArtifactStore
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    ArtifactType,
    CompletenessResult,
    ObjectiveStatus,
    OwnerService,
    RuntimeCompletionGateType,
    RuntimeGateStatus,
)
from veracrawl.contracts.objective import CrawlObjective, CrawlPlan, CrawlRun, RunPlanSnapshot
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.control.runtime import (
    RuntimeRepositories,
    commit_owner_mutation,
    evaluate_completion_gate,
    run_runtime_fixture,
)
from veracrawl.fetch.runtime import execute_source_adapter_fixture
from veracrawl.policy.gates import decision_for
from veracrawl.runtime_events.event_store import InMemoryEventStore


def _objective() -> CrawlObjective:
    return CrawlObjective(
        id="objective:contract",
        project_ref="project:test",
        site_scope_refs=["scope:any"],
        objective_text_ref="objective-text:test",
        target_schema_refs=["schema:test"],
        evidence_requirement_refs=["evidence:test"],
        freshness_policy_ref="freshness:test",
        source_policy_refs=["policy:source"],
        publication_policy_refs=["policy:publication"],
        status=ObjectiveStatus.APPROVED,
        created_by_ref="actor:test",
    )


def _plan(objective: CrawlObjective) -> CrawlPlan:
    return CrawlPlan(
        id="plan:contract",
        objective_ref=objective.id,
        plan_version="1",
        adapter_plan=[{"adapter_spec_ref": "adapter:http"}],
        evidence_requirement_refs=objective.evidence_requirement_refs,
        budget_ref="budget:test",
        approval_decision_ref="approval:test",
    )


def _run(objective: CrawlObjective, plan: CrawlPlan) -> CrawlRun:
    return CrawlRun(
        id="run:contract",
        objective_ref=objective.id,
        plan_ref=plan.id,
        run_plan_snapshot_ref="snapshot:contract",
        policy_snapshot_ref="policy-snapshot:test",
        budget_ref="budget:test",
    )


def test_runtime_entity_validation_rejects_incomplete_approved_objective() -> None:
    with pytest.raises(ValidationError):
        CrawlObjective(
            id="objective:bad",
            project_ref="project:test",
            objective_text_ref="objective-text:test",
            freshness_policy_ref="freshness:test",
            status=ObjectiveStatus.APPROVED,
            created_by_ref="actor:test",
        )


def test_runtime_entity_validation_covers_plan_snapshot_gate_and_candidate() -> None:
    objective = _objective()
    plan = _plan(objective)
    snapshot = RunPlanSnapshot(
        id="snapshot:contract",
        objective_ref=objective.id,
        plan_ref=plan.id,
        plan_hash="hash",
        policy_refs=["policy:source"],
        schema_refs=["schema:test"],
        adapter_spec_refs=["adapter:http"],
        replay_config_ref="replay:test",
    )
    gate = evaluate_completion_gate(
        gate_id="gate:contract",
        run_ref="run:contract",
        gate_type=RuntimeCompletionGateType.SOURCE,
        required_refs={"source_adapter_result_ref": "source-result:1"},
    )
    assert snapshot.plan_hash
    assert gate.status == RuntimeGateStatus.PASS
    with pytest.raises(ValidationError):
        ExtractionCandidate(
            id="candidate:bad",
            run_ref="run:contract",
            schema_ref="schema:test",
            normalized_document_refs=["normalized:1"],
            field_values={"name": "No anchor"},
            field_anchor_refs={},
            strategy_ref="strategy:test",
        )


def test_wrong_owner_mutation_is_rejected_and_evented() -> None:
    objective = _objective()
    plan = _plan(objective)
    run = _run(objective, plan)
    repositories = RuntimeRepositories()
    _, result, event_ref = commit_owner_mutation(
        event_store=InMemoryEventStore(),
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="record_normalized_document",
        target_aggregate_type="NormalizedDocument",
        target_aggregate_id="normalized:contract",
        expected_owner=OwnerService.NORMALIZE,
        actual_owner=OwnerService.FETCH,
        output_refs=[],
    )
    assert result.rejection_reasons
    assert event_ref.startswith("event:run:contract")


def test_fetch_like_and_non_fetch_adapter_semantics_are_preserved() -> None:
    objective = _objective()
    plan = _plan(objective)
    run = _run(objective, plan)
    policy = decision_for(
        decision_id="policy:source",
        run_id=run.id,
        objective_id=objective.id,
        decision_type="runtime_source",
        subject_ref="source:test",
        allow=True,
    )
    http_result, http_artifact = execute_source_adapter_fixture(
        run=run,
        policy_decision=policy,
        artifact_store=InMemoryArtifactStore(),
        scenario="record-success",
        adapter_type=AdapterType.HTTP,
    )
    document_result, _ = execute_source_adapter_fixture(
        run=run,
        policy_decision=policy,
        artifact_store=InMemoryArtifactStore(),
        scenario="record-success",
        adapter_type=AdapterType.DOCUMENT_SOURCE,
    )
    assert http_artifact is not None
    assert http_artifact.artifact_type == ArtifactType.RAW_SOURCE
    assert http_result.status == AdapterResultStatus.SUCCEEDED
    assert document_result.result_type.value == "document_artifact"
    assert not any(
        ref.startswith(("fetch:", "page_snapshot:")) for ref in document_result.output_refs
    )


def test_runtime_command_event_path_reaches_successful_report() -> None:
    report = run_runtime_fixture(
        fixture_id="runtime-record-success",
        scenario="record-success",
        profile="target",
    )
    assert report.completion_result == CompletenessResult.PASS
    assert len(report.command_result_refs) >= 6
    assert len(report.event_refs) >= 6
