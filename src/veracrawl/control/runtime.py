"""Runtime spine orchestration and owner-service command helpers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from veracrawl.artifact_lifecycle.runtime import InMemoryArtifactStore
from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref, TimestampedModel, stable_hash
from veracrawl.contracts.enums import (
    CommandResultStatus,
    CommandStatus,
    CompletenessResult,
    ObjectiveStatus,
    OwnerService,
    PlanStatus,
    RunStatus,
    RuntimeCompletionGateType,
    RuntimeGateStatus,
)
from veracrawl.contracts.objective import (
    CrawlObjective,
    CrawlPlan,
    CrawlRun,
    RunPlanSnapshot,
    RuntimeCompletionGate,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.policy.gates import decision_for
from veracrawl.runtime_events.event_store import InMemoryEventStore, append_runtime_event
from veracrawl.runtime_support.repositories import RuntimeRepositories

RuntimeScenario = Literal[
    "record-success",
    "blocked-source",
    "missing-evidence",
    "verification-conflict",
    "adapter-mismatch",
    "replay-gap",
    "boundary-violation",
]


class RuntimeOwnerViolation(ValueError):
    """Raised when a service tries to mutate another service's aggregate."""


class RuntimeRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: RuntimeScenario
    profile: str
    run_ref: Ref
    objective_ref: Ref
    plan_ref: Ref
    status: str
    completion_result: CompletenessResult
    published: bool = False
    published_output_ref: Ref | None = None
    output_manifest_ref: Ref | None = None
    replay_manifest_ref: Ref | None = None
    blocking_gate_ref: Ref | None = None
    blocking_gate_type: RuntimeCompletionGateType | None = None
    operator_status: str = "ok"
    command_result_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    completion_gate_refs: list[Ref] = Field(default_factory=list)
    missing_replay_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


def _has_ref(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, list | tuple | set | dict):
        return bool(value)
    return True


def require_owner(
    *,
    actual_owner: OwnerService,
    expected_owner: OwnerService,
    target_ref: Ref,
) -> None:
    if actual_owner != expected_owner:
        raise RuntimeOwnerViolation(
            f"{actual_owner.value} cannot mutate {target_ref}; owner is {expected_owner.value}"
        )


def evaluate_completion_gate(
    *,
    gate_id: str,
    run_ref: Ref,
    gate_type: RuntimeCompletionGateType,
    required_refs: dict[str, object],
    failure_status: RuntimeGateStatus = RuntimeGateStatus.FAIL,
    forced_status: RuntimeGateStatus | None = None,
    blocking_reason_refs: list[Ref] | None = None,
) -> RuntimeCompletionGate:
    present = [field for field, value in required_refs.items() if _has_ref(value)]
    missing = [field for field, value in required_refs.items() if not _has_ref(value)]
    status = forced_status or (failure_status if missing else RuntimeGateStatus.PASS)
    return RuntimeCompletionGate(
        id=gate_id,
        run_ref=run_ref,
        gate_type=gate_type,
        status=status,
        required_ref_fields=list(required_refs),
        present_ref_fields=present,
        missing_ref_fields=missing,
        blocking_reason_refs=blocking_reason_refs or [],
    )


def create_runtime_command(
    *,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    actor_ref: Ref = "actor:runtime-fixture",
    payload_ref: Ref | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> CommandEnvelope:
    return CommandEnvelope(
        id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        expected_version=1,
        idempotency_key=f"idem:{command_id}",
        actor_ref=actor_ref,
        policy_decision_refs=policy_decision_refs or [],
        payload_ref=payload_ref or f"payload:{command_id}",
        status=CommandStatus.ACCEPTED,
    )


def command_result(
    *,
    command: CommandEnvelope,
    result: CommandResultStatus,
    emitted_event_refs: list[Ref] | None = None,
    output_refs: list[Ref] | None = None,
    rejection_reasons: list[str] | None = None,
    error: dict[str, object] | None = None,
) -> CommandResult:
    return CommandResult(
        id=f"command-result:{command.id}",
        command_id=command.id,
        result=result,
        emitted_event_refs=emitted_event_refs or [],
        output_refs=output_refs or [],
        rejection_reasons=rejection_reasons or [],
        error=error or {},
    )


def commit_owner_mutation(
    *,
    event_store: InMemoryEventStore,
    repositories: RuntimeRepositories,
    run: CrawlRun,
    objective: CrawlObjective,
    plan: CrawlPlan,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    expected_owner: OwnerService,
    actual_owner: OwnerService,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref] | None = None,
) -> tuple[CommandEnvelope, CommandResult, Ref]:
    command = create_runtime_command(
        command_id=f"cmd:{run.id}:{command_type}:{len(repositories.command_results.list()) + 1}",
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        policy_decision_refs=policy_decision_refs,
    )
    if actual_owner != expected_owner:
        event_ref = append_runtime_event(
            event_store,
            run_id=run.id,
            objective_id=objective.id,
            plan_id=plan.id,
            event_type="runtime_owner_violation_recorded",
            payload_ref=command.payload_ref,
            causation_id=command.id,
            correlation_id=f"corr:{run.id}",
            output_refs=[],
            error={
                "actual_owner": actual_owner.value,
                "expected_owner": expected_owner.value,
                "target_ref": target_aggregate_id,
            },
        )
        result = command_result(
            command=command,
            result=CommandResultStatus.REJECTED,
            emitted_event_refs=[],
            rejection_reasons=[
                f"{actual_owner.value} cannot mutate {target_aggregate_id}; "
                f"owner is {expected_owner.value}"
            ],
        )
        repositories.command_results.save(result)
        return command, result, event_ref

    event_ref = append_runtime_event(
        event_store,
        run_id=run.id,
        objective_id=objective.id,
        plan_id=plan.id,
        event_type=f"{command_type}_committed",
        payload_ref=command.payload_ref,
        causation_id=command.id,
        correlation_id=f"corr:{run.id}",
        output_refs=output_refs,
        policy_decision_refs=policy_decision_refs or [],
        state_before={"status": "accepted"},
        state_after={"status": "committed", "target_ref": target_aggregate_id},
    )
    result = command_result(
        command=command,
        result=CommandResultStatus.COMMITTED,
        emitted_event_refs=[event_ref],
        output_refs=output_refs,
    )
    repositories.command_results.save(result)
    return command, result, event_ref


def _runtime_ids(fixture_id: str) -> tuple[str, str, str]:
    suffix = fixture_id.removeprefix("runtime-")
    return f"objective:{suffix}", f"plan:{suffix}", f"run:{suffix}"


def _bootstrap_run(
    fixture_id: str,
    repositories: RuntimeRepositories,
) -> tuple[CrawlObjective, CrawlPlan, RunPlanSnapshot, CrawlRun]:
    objective_id, plan_id, run_id = _runtime_ids(fixture_id)
    objective = CrawlObjective(
        id=objective_id,
        project_ref="project:runtime-fixture",
        site_scope_refs=["scope:any-authorized-site"],
        objective_text_ref=f"objective-text:{fixture_id}",
        target_schema_refs=["schema:record-output"],
        evidence_requirement_refs=["evidence-requirement:field-source-anchors"],
        freshness_policy_ref="freshness:fixture",
        source_policy_refs=["policy:source"],
        publication_policy_refs=["policy:publication"],
        status=ObjectiveStatus.APPROVED,
        created_by_ref="actor:runtime-fixture",
    )
    plan = CrawlPlan(
        id=plan_id,
        objective_ref=objective.id,
        plan_version="1",
        adapter_plan=[{"adapter_spec_ref": "adapter:http-fixture", "source_ref": "source:fixture"}],
        seed_refs=["seed:fixture"],
        evidence_requirement_refs=objective.evidence_requirement_refs,
        budget_ref="budget:fixture",
        approval_decision_ref="approval:fixture",
        status=PlanStatus.APPROVED,
    )
    snapshot = RunPlanSnapshot(
        id=f"snapshot:{run_id}",
        objective_ref=objective.id,
        plan_ref=plan.id,
        plan_hash=stable_hash(plan),
        policy_refs=objective.source_policy_refs + objective.publication_policy_refs,
        schema_refs=objective.target_schema_refs,
        adapter_spec_refs=["adapter:http-fixture"],
        tool_refs=["tool:runtime-fixture"],
        model_refs=["model:structural-none"],
        evidence_requirement_refs=objective.evidence_requirement_refs,
        replay_config_ref="replay-config:runtime-fixture",
    )
    run = CrawlRun(
        id=run_id,
        objective_ref=objective.id,
        plan_ref=plan.id,
        run_plan_snapshot_ref=snapshot.id,
        status=RunStatus.RUNNING,
        policy_snapshot_ref="policy-snapshot:runtime-fixture",
        budget_ref="budget:fixture",
    )
    repositories.objectives.save(objective)
    repositories.plans.save(plan)
    repositories.runs.save(run)
    return objective, plan, snapshot, run


def _save_gate(repositories: RuntimeRepositories, gate: RuntimeCompletionGate) -> Ref:
    repositories.gates.save(gate)
    return gate.id


def _policy(
    *,
    decision_id: str,
    run: CrawlRun,
    objective: CrawlObjective,
    decision_type: str,
    subject_ref: Ref,
    allow: bool,
    reasons: list[str] | None = None,
) -> PolicyDecision:
    return decision_for(
        decision_id=decision_id,
        run_id=run.id,
        objective_id=objective.id,
        decision_type=decision_type,
        subject_ref=subject_ref,
        allow=allow,
        reasons=reasons,
    )


def _scenario_from_fixture(fixture_id: str, scenario: str | None) -> RuntimeScenario:
    if scenario:
        return scenario  # type: ignore[return-value]
    return fixture_id.removeprefix("runtime-").replace("_", "-")  # type: ignore[return-value]


def run_runtime_fixture(
    *,
    fixture_id: str,
    scenario: str | None,
    profile: str,
) -> RuntimeRunReport:
    from veracrawl.evidence.runtime import build_evidence_packet
    from veracrawl.extract.runtime import extract_candidate
    from veracrawl.fetch.runtime import execute_source_adapter_fixture
    from veracrawl.normalize.runtime import normalize_source_result
    from veracrawl.publish.runtime import publish_verified_output
    from veracrawl.review_replay.runtime import build_runtime_replay_bundle
    from veracrawl.verify.runtime import verify_candidate

    runtime_scenario = _scenario_from_fixture(fixture_id, scenario)
    repositories = RuntimeRepositories()
    artifact_store = InMemoryArtifactStore()
    event_store = InMemoryEventStore()
    objective, plan, snapshot, run = _bootstrap_run(fixture_id, repositories)

    report_kwargs: dict[str, Any] = {
        "id": f"runtime-report:{fixture_id}",
        "fixture_id": fixture_id,
        "scenario": runtime_scenario,
        "profile": profile,
        "run_ref": run.id,
        "objective_ref": objective.id,
        "plan_ref": plan.id,
    }
    command_result_refs: list[Ref] = []
    event_refs: list[Ref] = []
    policy_refs: list[Ref] = []
    gate_refs: list[Ref] = []
    diagnostics: list[str] = []

    objective_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:objective",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.OBJECTIVE,
        required_refs={
            "site_scope_refs": objective.site_scope_refs,
            "source_policy_refs": objective.source_policy_refs,
            "target_schema_refs": objective.target_schema_refs,
            "evidence_requirement_refs": objective.evidence_requirement_refs,
        },
    )
    plan_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:plan",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.PLAN,
        required_refs={
            "approval_decision_ref": plan.approval_decision_ref,
            "adapter_plan": plan.adapter_plan,
            "run_plan_snapshot_ref": snapshot.id,
        },
    )
    gate_refs.extend(
        [_save_gate(repositories, objective_gate), _save_gate(repositories, plan_gate)]
    )

    if runtime_scenario == "boundary-violation":
        _, rejected, event_ref = commit_owner_mutation(
            event_store=event_store,
            repositories=repositories,
            run=run,
            objective=objective,
            plan=plan,
            command_type="record_normalized_document",
            target_aggregate_type="NormalizedDocument",
            target_aggregate_id=f"normalized:{run.id}",
            expected_owner=OwnerService.NORMALIZE,
            actual_owner=OwnerService.FETCH,
            output_refs=[],
        )
        command_result_refs.append(rejected.id)
        event_refs.append(event_ref)
        gate = evaluate_completion_gate(
            gate_id=f"gate:{run.id}:owner-boundary",
            run_ref=run.id,
            gate_type=RuntimeCompletionGateType.NORMALIZATION,
            required_refs={"owner_command_result_ref": None},
            failure_status=RuntimeGateStatus.FAIL,
            blocking_reason_refs=rejected.rejection_reasons,
        )
        gate_refs.append(_save_gate(repositories, gate))
        return RuntimeRunReport(
            **report_kwargs,
            status="boundary_violation",
            completion_result=CompletenessResult.FAIL,
            blocking_gate_ref=gate.id,
            blocking_gate_type=gate.gate_type,
            operator_status="owner_boundary_violation",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            completion_gate_refs=gate_refs,
            diagnostics=rejected.rejection_reasons,
        )

    source_policy = _policy(
        decision_id=f"policy:{run.id}:source",
        run=run,
        objective=objective,
        decision_type="runtime_source",
        subject_ref="source:fixture",
        allow=runtime_scenario != "blocked-source",
        reasons=(
            ["source blocked by fixture policy"]
            if runtime_scenario == "blocked-source"
            else None
        ),
    )
    repositories.policy_decisions.save(source_policy)
    policy_refs.append(source_policy.id)

    try:
        source_result, raw_artifact = execute_source_adapter_fixture(
            run=run,
            policy_decision=source_policy,
            artifact_store=artifact_store,
            scenario=runtime_scenario,
        )
    except ValueError as exc:
        diagnostics.append(str(exc))
        _, failed, event_ref = commit_owner_mutation(
            event_store=event_store,
            repositories=repositories,
            run=run,
            objective=objective,
            plan=plan,
            command_type="record_source_adapter_result",
            target_aggregate_type="SourceAdapterResult",
            target_aggregate_id=f"source-result:{run.id}",
            expected_owner=OwnerService.FETCH,
            actual_owner=OwnerService.FETCH,
            output_refs=[],
            policy_decision_refs=[source_policy.id],
        )
        command_result_refs.append(failed.id)
        event_refs.append(event_ref)
        gate = evaluate_completion_gate(
            gate_id=f"gate:{run.id}:source",
            run_ref=run.id,
            gate_type=RuntimeCompletionGateType.SOURCE,
            required_refs={"source_adapter_result_ref": None},
            failure_status=RuntimeGateStatus.FAIL,
            blocking_reason_refs=[f"diagnostic:{run.id}:adapter-mismatch"],
        )
        gate_refs.append(_save_gate(repositories, gate))
        return RuntimeRunReport(
            **report_kwargs,
            status="adapter_mismatch",
            completion_result=CompletenessResult.FAIL,
            blocking_gate_ref=gate.id,
            blocking_gate_type=gate.gate_type,
            operator_status="adapter_mismatch",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            policy_decision_refs=policy_refs,
            completion_gate_refs=gate_refs,
            diagnostics=diagnostics,
        )

    repositories.source_results.save(source_result)
    if raw_artifact is not None:
        repositories.artifacts.save(raw_artifact)
    _, source_command_result, source_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="record_source_adapter_result",
        target_aggregate_type="SourceAdapterResult",
        target_aggregate_id=source_result.id,
        expected_owner=OwnerService.FETCH,
        actual_owner=OwnerService.FETCH,
        output_refs=[source_result.id],
        policy_decision_refs=[source_policy.id],
    )
    command_result_refs.append(source_command_result.id)
    event_refs.append(source_event_ref)

    source_gate_status = RuntimeGateStatus.BLOCKED if runtime_scenario == "blocked-source" else None
    source_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:source",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.SOURCE,
        required_refs={
            "source_adapter_result_ref": source_result.id,
            "raw_artifact_ref": raw_artifact.id if raw_artifact else None,
        },
        forced_status=source_gate_status,
        blocking_reason_refs=[source_policy.id] if source_gate_status else None,
    )
    gate_refs.append(_save_gate(repositories, source_gate))
    if runtime_scenario == "blocked-source":
        return RuntimeRunReport(
            **report_kwargs,
            status="blocked",
            completion_result=CompletenessResult.FAIL,
            blocking_gate_ref=source_gate.id,
            blocking_gate_type=source_gate.gate_type,
            operator_status="source_blocked",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            policy_decision_refs=policy_refs,
            source_adapter_result_refs=[source_result.id],
            artifact_refs=[],
            completion_gate_refs=gate_refs,
            diagnostics=["source blocked by runtime source policy"],
        )

    assert raw_artifact is not None
    normalized_doc, normalized_artifacts = normalize_source_result(
        run=run,
        source_result=source_result,
        raw_artifact_ref=raw_artifact,
        artifact_store=artifact_store,
    )
    repositories.normalized_documents.save(normalized_doc)
    for artifact in normalized_artifacts:
        repositories.artifacts.save(artifact)
    _, normalize_command_result, normalize_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="record_normalized_document",
        target_aggregate_type="NormalizedDocument",
        target_aggregate_id=normalized_doc.id,
        expected_owner=OwnerService.NORMALIZE,
        actual_owner=OwnerService.NORMALIZE,
        output_refs=[normalized_doc.id],
    )
    command_result_refs.append(normalize_command_result.id)
    event_refs.append(normalize_event_ref)
    normalize_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:normalization",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.NORMALIZATION,
        required_refs={
            "normalized_document_ref": normalized_doc.id,
            "anchor_map_ref": normalized_doc.anchor_map_ref,
        },
    )
    gate_refs.append(_save_gate(repositories, normalize_gate))

    candidate = extract_candidate(run=run, normalized_document=normalized_doc)
    repositories.candidates.save(candidate)
    _, extract_command_result, extract_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="record_extraction_candidate",
        target_aggregate_type="ExtractionCandidate",
        target_aggregate_id=candidate.id,
        expected_owner=OwnerService.EXTRACT,
        actual_owner=OwnerService.EXTRACT,
        output_refs=[candidate.id],
    )
    command_result_refs.append(extract_command_result.id)
    event_refs.append(extract_event_ref)
    extraction_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:extraction",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.EXTRACTION,
        required_refs={
            "candidate_ref": candidate.id,
            "field_anchor_refs": candidate.field_anchor_refs,
            "strategy_ref": candidate.strategy_ref,
        },
    )
    gate_refs.append(_save_gate(repositories, extraction_gate))

    coverage, evidence = build_evidence_packet(
        run=run,
        candidate=candidate,
        missing_fields=["price"] if runtime_scenario == "missing-evidence" else [],
    )
    repositories.evidence_coverage.save(coverage)
    repositories.evidence_packets.save(evidence)
    _, evidence_command_result, evidence_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="build_evidence_packet",
        target_aggregate_type="EvidencePacket",
        target_aggregate_id=evidence.id,
        expected_owner=OwnerService.EVIDENCE,
        actual_owner=OwnerService.EVIDENCE,
        output_refs=[evidence.id],
    )
    command_result_refs.append(evidence_command_result.id)
    event_refs.append(evidence_event_ref)
    evidence_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:evidence",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.EVIDENCE,
        required_refs={
            "evidence_packet_ref": evidence.id,
            "coverage_result_ref": coverage.id,
            "missing_field_refs": None if coverage.missing_field_refs else "none",
        },
        forced_status=(
            RuntimeGateStatus.NEEDS_REVIEW if runtime_scenario == "missing-evidence" else None
        ),
        blocking_reason_refs=coverage.missing_field_refs,
    )
    gate_refs.append(_save_gate(repositories, evidence_gate))
    if runtime_scenario == "missing-evidence":
        return RuntimeRunReport(
            **report_kwargs,
            status="needs_review",
            completion_result=CompletenessResult.NEEDS_REVIEW,
            blocking_gate_ref=evidence_gate.id,
            blocking_gate_type=evidence_gate.gate_type,
            operator_status="missing_evidence",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            policy_decision_refs=policy_refs,
            source_adapter_result_refs=[source_result.id],
            artifact_refs=[artifact.id for artifact in artifact_store.list_refs()],
            normalized_document_refs=[normalized_doc.id],
            extraction_candidate_refs=[candidate.id],
            evidence_packet_refs=[evidence.id],
            evidence_coverage_refs=[coverage.id],
            completion_gate_refs=gate_refs,
            diagnostics=["candidate is missing required field evidence: price"],
        )

    verification_policy = _policy(
        decision_id=f"policy:{run.id}:verification",
        run=run,
        objective=objective,
        decision_type="runtime_verification",
        subject_ref=candidate.id,
        allow=True,
    )
    publication_policy = _policy(
        decision_id=f"policy:{run.id}:publication",
        run=run,
        objective=objective,
        decision_type="runtime_publication",
        subject_ref=candidate.id,
        allow=True,
    )
    repositories.policy_decisions.save(verification_policy)
    repositories.policy_decisions.save(publication_policy)
    policy_refs.extend([verification_policy.id, publication_policy.id])

    verification = verify_candidate(
        run=run,
        candidate=candidate,
        evidence=evidence,
        policy_decision=verification_policy,
        conflict=runtime_scenario == "verification-conflict",
    )
    repositories.verification_decisions.save(verification)
    _, verify_command_result, verify_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="record_verification_decision",
        target_aggregate_type="VerificationDecision",
        target_aggregate_id=verification.id,
        expected_owner=OwnerService.VERIFY,
        actual_owner=OwnerService.VERIFY,
        output_refs=[verification.id],
        policy_decision_refs=[verification_policy.id],
    )
    command_result_refs.append(verify_command_result.id)
    event_refs.append(verify_event_ref)
    verification_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:verification",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.VERIFICATION,
        required_refs={
            "verification_decision_ref": verification.id,
            "policy_decision_refs": verification.policy_decision_refs,
            "conflict_record_refs": None if verification.conflict_record_refs else "none",
        },
        forced_status=(
            RuntimeGateStatus.CONFLICT if runtime_scenario == "verification-conflict" else None
        ),
        blocking_reason_refs=verification.conflict_record_refs,
    )
    gate_refs.append(_save_gate(repositories, verification_gate))
    if runtime_scenario == "verification-conflict":
        return RuntimeRunReport(
            **report_kwargs,
            status="conflict",
            completion_result=CompletenessResult.FAIL,
            blocking_gate_ref=verification_gate.id,
            blocking_gate_type=verification_gate.gate_type,
            operator_status="verification_conflict",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            policy_decision_refs=policy_refs,
            source_adapter_result_refs=[source_result.id],
            artifact_refs=[artifact.id for artifact in artifact_store.list_refs()],
            normalized_document_refs=[normalized_doc.id],
            extraction_candidate_refs=[candidate.id],
            evidence_packet_refs=[evidence.id],
            evidence_coverage_refs=[coverage.id],
            verification_decision_refs=[verification.id],
            completion_gate_refs=gate_refs,
            diagnostics=verification.conflict_record_refs,
        )

    manifest_id = f"output-manifest:{run.id}"
    replay_manifest, replay_report, runtime_missing = build_runtime_replay_bundle(
        run=run,
        objective=objective,
        plan=plan,
        event_store=event_store,
        command_result_refs=command_result_refs,
        policy_decision_refs=policy_refs,
        source_adapter_result_refs=[source_result.id],
        artifact_refs=[artifact.id for artifact in artifact_store.list_refs()],
        normalized_document_refs=[normalized_doc.id],
        extraction_candidate_refs=[candidate.id],
        evidence_packet_refs=[evidence.id],
        verification_decision_refs=[verification.id],
        output_manifest_refs=[manifest_id],
        force_gap=runtime_scenario == "replay-gap",
    )
    repositories.replay_bundles.save(replay_manifest)
    replay_gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:replay",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.REPLAY,
        required_refs={
            "replay_manifest_ref": replay_manifest.id,
            "missing_ref_fields": None if runtime_missing else "none",
        },
        forced_status=RuntimeGateStatus.FAIL if runtime_missing else None,
        blocking_reason_refs=runtime_missing,
    )
    gate_refs.append(_save_gate(repositories, replay_gate))
    if runtime_scenario == "replay-gap":
        return RuntimeRunReport(
            **report_kwargs,
            status="replay_incomplete",
            completion_result=replay_report.completeness_result,
            replay_manifest_ref=replay_manifest.id,
            blocking_gate_ref=replay_gate.id,
            blocking_gate_type=replay_gate.gate_type,
            operator_status="replay_gap",
            command_result_refs=command_result_refs,
            event_refs=event_refs,
            policy_decision_refs=policy_refs,
            source_adapter_result_refs=[source_result.id],
            artifact_refs=[artifact.id for artifact in artifact_store.list_refs()],
            normalized_document_refs=[normalized_doc.id],
            extraction_candidate_refs=[candidate.id],
            evidence_packet_refs=[evidence.id],
            evidence_coverage_refs=[coverage.id],
            verification_decision_refs=[verification.id],
            completion_gate_refs=gate_refs,
            missing_replay_ref_fields=runtime_missing,
            diagnostics=runtime_missing,
        )

    published, output_manifest, publication_gate = publish_verified_output(
        run=run,
        candidate=candidate,
        coverage=coverage,
        verification=verification,
        publication_policy_decision=publication_policy,
        replay_report=replay_report,
        replay_manifest_ref=replay_manifest.id,
        output_manifest_id=manifest_id,
    )
    repositories.output_manifests.save(output_manifest)
    repositories.published_outputs.save(published)
    _, publish_command_result, publish_event_ref = commit_owner_mutation(
        event_store=event_store,
        repositories=repositories,
        run=run,
        objective=objective,
        plan=plan,
        command_type="publish_output_manifest",
        target_aggregate_type="PublishedOutput",
        target_aggregate_id=published.id,
        expected_owner=OwnerService.PUBLISH,
        actual_owner=OwnerService.PUBLISH,
        output_refs=[published.id, output_manifest.id],
        policy_decision_refs=[publication_policy.id],
    )
    command_result_refs.append(publish_command_result.id)
    event_refs.append(publish_event_ref)
    gate_refs.append(_save_gate(repositories, publication_gate))

    return RuntimeRunReport(
        **report_kwargs,
        status="published",
        completion_result=CompletenessResult.PASS,
        published=True,
        published_output_ref=published.id,
        output_manifest_ref=output_manifest.id,
        replay_manifest_ref=replay_manifest.id,
        operator_status="published",
        command_result_refs=command_result_refs,
        event_refs=event_refs,
        policy_decision_refs=policy_refs,
        source_adapter_result_refs=[source_result.id],
        artifact_refs=[artifact.id for artifact in artifact_store.list_refs()],
        normalized_document_refs=[normalized_doc.id],
        extraction_candidate_refs=[candidate.id],
        evidence_packet_refs=[evidence.id],
        evidence_coverage_refs=[coverage.id],
        verification_decision_refs=[verification.id],
        completion_gate_refs=gate_refs,
    )
