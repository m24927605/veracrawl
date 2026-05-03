"""Deterministic target product acceptance gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    MinimumProductGate,
    ProductAcceptanceFailureType,
    TargetProductWorkflow,
)
from veracrawl.contracts.product_acceptance import (
    ProductAcceptanceGateReport,
    ProductWorkflowReadinessRecord,
)


@dataclass(frozen=True)
class ProductAcceptanceRuntimeResult:
    workflow_records: list[ProductWorkflowReadinessRecord]
    report: ProductAcceptanceGateReport


_FAILURES: dict[
    str,
    tuple[
        ProductAcceptanceFailureType,
        str | None,
        str,
        TargetProductWorkflow | None,
        MinimumProductGate | None,
    ],
] = {
    "product-acceptance-missing-workflow": (
        ProductAcceptanceFailureType.MISSING_WORKFLOW,
        None,
        "covered_workflows",
        TargetProductWorkflow.OPERATOR_RECOVERY,
        None,
    ),
    "product-acceptance-missing-minimum-gate": (
        ProductAcceptanceFailureType.MISSING_MINIMUM_GATE,
        None,
        "minimum_gate_refs",
        None,
        MinimumProductGate.BUYER_VALUE_WORKFLOW_PASS,
    ),
    "product-acceptance-missing-evidence": (
        ProductAcceptanceFailureType.MISSING_EVIDENCE,
        "missing_evidence_refs",
        "evidence_refs",
        None,
        None,
    ),
    "product-acceptance-missing-replay": (
        ProductAcceptanceFailureType.MISSING_REPLAY,
        "missing_replay_refs",
        "replay_refs",
        None,
        None,
    ),
    "product-acceptance-missing-operator-visibility": (
        ProductAcceptanceFailureType.MISSING_OPERATOR_VISIBILITY,
        "missing_operator_visible_result_refs",
        "operator_visible_result_refs",
        None,
        None,
    ),
    "product-acceptance-missing-policy": (
        ProductAcceptanceFailureType.MISSING_POLICY,
        "missing_policy_refs",
        "policy_decision_refs",
        None,
        None,
    ),
    "product-acceptance-missing-workflow-specific-refs": (
        ProductAcceptanceFailureType.MISSING_WORKFLOW_SPECIFIC_REFS,
        "missing_workflow_specific_refs",
        "workflow_specific_refs",
        None,
        None,
    ),
    "product-acceptance-scaffold-only": (
        ProductAcceptanceFailureType.SCAFFOLD_ONLY,
        "scaffold_only_refs",
        "executable_product_oracle_refs",
        None,
        None,
    ),
    "product-acceptance-contract-only": (
        ProductAcceptanceFailureType.CONTRACT_ONLY,
        "contract_only_refs",
        "buyer_value_workflow_refs",
        None,
        None,
    ),
    "product-acceptance-false-complete-status": (
        ProductAcceptanceFailureType.FALSE_COMPLETE_STATUS,
        "false_complete_status_refs",
        "status_accuracy_refs",
        None,
        None,
    ),
    "product-acceptance-degraded-operational": (
        ProductAcceptanceFailureType.DEGRADED_OPERATIONAL,
        "degraded_operational_refs",
        "status_accuracy_refs",
        None,
        None,
    ),
    "product-acceptance-missing-export-reconciliation": (
        ProductAcceptanceFailureType.MISSING_EXPORT_RECONCILIATION,
        "missing_export_reconciliation_refs",
        "export_reconciliation_refs",
        None,
        None,
    ),
}


def run_product_acceptance_gate(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> ProductAcceptanceRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:product-acceptance"]
    if scenario == "product-acceptance-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, report_field, missing_field, missing_workflow, missing_gate = _FAILURES[
            scenario
        ]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            report_field=report_field,
            missing_field=missing_field,
            policy_refs=policy_refs,
            missing_workflow=missing_workflow,
            missing_gate=missing_gate,
        )
    return _success_result(fixture_id=fixture_id, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> ProductAcceptanceRuntimeResult:
    records = [
        _workflow_record(fixture_id=fixture_id, workflow=workflow, policy_refs=policy_refs)
        for workflow in TargetProductWorkflow
    ]
    report = ProductAcceptanceGateReport(
        id=f"product-acceptance-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        fixture_id=fixture_id,
        workflow_record_refs=[record.id for record in records],
        covered_workflows=[record.workflow for record in records],
        minimum_gate_refs=list(MinimumProductGate),
        buyer_value_workflow_refs=[
            f"buyer-value:{fixture_id}:{workflow.value}"
            for workflow in TargetProductWorkflow
        ],
        evidence_refs=[f"evidence:{fixture_id}:product"],
        replay_refs=[f"replay:{fixture_id}:product"],
        operator_visible_result_refs=[f"operator-result:{fixture_id}:product"],
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        artifact_refs=[f"artifact:{fixture_id}:product"],
        status_accuracy_refs=[f"status-accuracy:{fixture_id}:zero-false-complete"],
        workflow_specific_refs=[
            f"workflow-specific:{fixture_id}:{workflow.value}"
            for workflow in TargetProductWorkflow
        ],
        export_reconciliation_refs=[f"export-reconciliation:{fixture_id}:product"],
        recovery_action_refs=[f"recovery-action:{fixture_id}:product"],
        operator_status="product_acceptance_completed",
        completion_result=CompletenessResult.PASS,
    )
    return ProductAcceptanceRuntimeResult(records, report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> ProductAcceptanceRuntimeResult:
    report = ProductAcceptanceGateReport(
        id=f"product-acceptance-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        fixture_id=fixture_id,
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:product-acceptance"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:product-harness",
            f"missing-runtime:{fixture_id}:operator-console",
        ],
        missing_ref_fields=["live_product_runtime_refs"],
        operator_status="product_acceptance_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return ProductAcceptanceRuntimeResult([], report)


def _failure_result(
    *,
    fixture_id: str,
    failure: ProductAcceptanceFailureType,
    report_field: str | None,
    missing_field: str,
    policy_refs: list[Ref],
    missing_workflow: TargetProductWorkflow | None,
    missing_gate: MinimumProductGate | None,
) -> ProductAcceptanceRuntimeResult:
    report_kwargs: dict[str, object] = {}
    if report_field is not None:
        report_kwargs[report_field] = [f"{report_field}:{fixture_id}"]
    missing_workflows = [missing_workflow] if missing_workflow is not None else []
    missing_gates = [missing_gate] if missing_gate is not None else []
    report = ProductAcceptanceGateReport(
        id=f"product-acceptance-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        fixture_id=fixture_id,
        policy_decision_refs=policy_refs,
        missing_workflows=missing_workflows,
        missing_minimum_gates=missing_gates,
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        **report_kwargs,
    )
    return ProductAcceptanceRuntimeResult([], report)


def _workflow_record(
    *,
    fixture_id: str,
    workflow: TargetProductWorkflow,
    policy_refs: list[Ref],
) -> ProductWorkflowReadinessRecord:
    suffix = workflow.value
    return ProductWorkflowReadinessRecord(
        id=f"product-workflow-readiness:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        fixture_id=fixture_id,
        workflow=workflow,
        buyer_value_ref=f"buyer-value:{fixture_id}:{suffix}",
        evidence_refs=[f"evidence:{fixture_id}:{suffix}"],
        replay_refs=[f"replay:{fixture_id}:{suffix}"],
        operator_visible_result_refs=[f"operator-result:{fixture_id}:{suffix}"],
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        artifact_refs=[f"artifact:{fixture_id}:{suffix}"],
        acceptance_oracle_refs=[f"acceptance-oracle:{fixture_id}:{suffix}"],
        minimum_gate_refs=list(MinimumProductGate),
        workflow_specific_refs=_workflow_specific_refs(fixture_id, workflow),
        capability_state_refs=[f"capability-state:{fixture_id}:{suffix}:verified-operational"],
        status_accuracy_refs=[f"status-accuracy:{fixture_id}:{suffix}"],
        export_reconciliation_refs=(
            [f"export-reconciliation:{fixture_id}:{suffix}"]
            if workflow == TargetProductWorkflow.EXPORT_AND_WITHDRAWAL
            else []
        ),
        recovery_action_refs=(
            [f"recovery-action:{fixture_id}:{suffix}"]
            if workflow == TargetProductWorkflow.OPERATOR_RECOVERY
            else []
        ),
        failure_oracle_refs=[f"failure-oracle:{fixture_id}:{suffix}"],
        result=CompletenessResult.PASS,
    )


def _workflow_specific_refs(
    fixture_id: str,
    workflow: TargetProductWorkflow,
) -> dict[str, Ref]:
    prefix = f"workflow-specific:{fixture_id}:{workflow.value}"
    match workflow:
        case TargetProductWorkflow.MULTI_SITE_ONBOARDING:
            names = [
                "project_ref",
                "source_scope_refs",
                "schema_refs",
                "objective_refs",
                "distinct_site_refs",
            ]
        case TargetProductWorkflow.OBJECTIVE_TO_PLAN_APPROVAL:
            names = [
                "plan_proposal_ref",
                "adapter_choice_refs",
                "assumption_refs",
                "alternative_refs",
                "approval_ref",
            ]
        case TargetProductWorkflow.DYNAMIC_AUTH_DOCUMENT_API_CRAWL:
            names = [
                "browser_artifact_refs",
                "credential_audit_refs",
                "document_artifact_refs",
                "api_payload_refs",
                "safety_ref",
            ]
        case TargetProductWorkflow.EVIDENCE_REVIEW:
            names = [
                "source_view_refs",
                "normalized_view_refs",
                "anchor_refs",
                "verification_decision_refs",
            ]
        case TargetProductWorkflow.CONFLICT_RESOLUTION:
            names = ["conflict_refs", "adjudication_refs", "no_silent_overwrite_ref"]
        case TargetProductWorkflow.DRIFT_REPAIR:
            names = [
                "drift_event_refs",
                "repair_proposal_refs",
                "reviewed_update_refs",
                "verified_recovery_refs",
            ]
        case TargetProductWorkflow.MEMORY_REUSE:
            names = [
                "memory_retrieval_refs",
                "stale_exclusion_refs",
                "reanchor_evidence_refs",
            ]
        case TargetProductWorkflow.EXPORT_AND_WITHDRAWAL:
            names = [
                "delivery_receipt_refs",
                "withdrawal_refs",
                "destination_mapping_refs",
                "reconciliation_refs",
            ]
        case TargetProductWorkflow.REPLAY_AND_AUDIT:
            names = [
                "replay_bundle_refs",
                "tool_call_refs",
                "policy_trace_refs",
                "export_trace_refs",
            ]
        case TargetProductWorkflow.OPERATOR_RECOVERY:
            names = [
                "failure_record_refs",
                "recovery_action_refs",
                "operator_status_refs",
                "replay_visible_result_refs",
            ]
    return {name: f"{prefix}:{name}" for name in names}


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:product-acceptance"]


def _event_cursor_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:product-acceptance"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:product-acceptance"]
