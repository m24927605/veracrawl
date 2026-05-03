from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    MinimumProductGate,
    ProductAcceptanceFailureType,
    TargetProductWorkflow,
)
from veracrawl.contracts.product_acceptance import (
    ProductAcceptanceFixtureManifest,
    ProductAcceptanceGateReport,
    ProductWorkflowReadinessRecord,
)


def _workflow_refs(workflow: TargetProductWorkflow) -> dict[str, str]:
    refs = {
        TargetProductWorkflow.MULTI_SITE_ONBOARDING: [
            "project_ref",
            "source_scope_refs",
            "schema_refs",
            "objective_refs",
            "distinct_site_refs",
        ],
        TargetProductWorkflow.OBJECTIVE_TO_PLAN_APPROVAL: [
            "plan_proposal_ref",
            "adapter_choice_refs",
            "assumption_refs",
            "alternative_refs",
            "approval_ref",
        ],
        TargetProductWorkflow.DYNAMIC_AUTH_DOCUMENT_API_CRAWL: [
            "browser_artifact_refs",
            "credential_audit_refs",
            "document_artifact_refs",
            "api_payload_refs",
            "safety_ref",
        ],
        TargetProductWorkflow.EVIDENCE_REVIEW: [
            "source_view_refs",
            "normalized_view_refs",
            "anchor_refs",
            "verification_decision_refs",
        ],
        TargetProductWorkflow.CONFLICT_RESOLUTION: [
            "conflict_refs",
            "adjudication_refs",
            "no_silent_overwrite_ref",
        ],
        TargetProductWorkflow.DRIFT_REPAIR: [
            "drift_event_refs",
            "repair_proposal_refs",
            "reviewed_update_refs",
            "verified_recovery_refs",
        ],
        TargetProductWorkflow.MEMORY_REUSE: [
            "memory_retrieval_refs",
            "stale_exclusion_refs",
            "reanchor_evidence_refs",
        ],
        TargetProductWorkflow.EXPORT_AND_WITHDRAWAL: [
            "delivery_receipt_refs",
            "withdrawal_refs",
            "destination_mapping_refs",
            "reconciliation_refs",
        ],
        TargetProductWorkflow.REPLAY_AND_AUDIT: [
            "replay_bundle_refs",
            "tool_call_refs",
            "policy_trace_refs",
            "export_trace_refs",
        ],
        TargetProductWorkflow.OPERATOR_RECOVERY: [
            "failure_record_refs",
            "recovery_action_refs",
            "operator_status_refs",
            "replay_visible_result_refs",
        ],
    }
    return {name: f"workflow-ref:{workflow.value}:{name}" for name in refs[workflow]}


def _record(
    workflow: TargetProductWorkflow = TargetProductWorkflow.MULTI_SITE_ONBOARDING,
) -> ProductWorkflowReadinessRecord:
    return ProductWorkflowReadinessRecord(
        id=f"product-workflow-readiness:{workflow.value}",
        run_ref="run:contract",
        fixture_id="product-acceptance-contract",
        workflow=workflow,
        buyer_value_ref=f"buyer-value:{workflow.value}",
        evidence_refs=[f"evidence:{workflow.value}"],
        replay_refs=[f"replay:{workflow.value}"],
        operator_visible_result_refs=[f"operator:{workflow.value}"],
        policy_decision_refs=["policy:contract"],
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        artifact_refs=[f"artifact:{workflow.value}"],
        acceptance_oracle_refs=[f"oracle:{workflow.value}"],
        minimum_gate_refs=list(MinimumProductGate),
        workflow_specific_refs=_workflow_refs(workflow),
        capability_state_refs=[f"capability:{workflow.value}:verified-operational"],
        status_accuracy_refs=[f"status:{workflow.value}"],
        export_reconciliation_refs=(
            ["export-reconciliation:contract"]
            if workflow == TargetProductWorkflow.EXPORT_AND_WITHDRAWAL
            else []
        ),
        recovery_action_refs=(
            ["recovery-action:contract"]
            if workflow == TargetProductWorkflow.OPERATOR_RECOVERY
            else []
        ),
        failure_oracle_refs=[f"failure-oracle:{workflow.value}"],
        result=CompletenessResult.PASS,
    )


def test_product_workflow_record_rejects_missing_evidence() -> None:
    with pytest.raises(ValidationError):
        ProductWorkflowReadinessRecord(**(_record().model_dump() | {"evidence_refs": []}))


def test_product_workflow_record_rejects_missing_workflow_specific_refs() -> None:
    with pytest.raises(ValidationError):
        ProductWorkflowReadinessRecord(
            **(
                _record(TargetProductWorkflow.DYNAMIC_AUTH_DOCUMENT_API_CRAWL).model_dump()
                | {"workflow_specific_refs": {}}
            )
        )


def test_product_workflow_record_rejects_false_complete_status() -> None:
    with pytest.raises(ValidationError):
        ProductWorkflowReadinessRecord(
            **(_record().model_dump() | {"false_complete_status_refs": ["status:bad"]})
        )


def test_product_report_requires_all_workflows_and_minimum_gates() -> None:
    with pytest.raises(ValidationError):
        ProductAcceptanceGateReport(
            id="product-acceptance-report:bad",
            run_ref="run:bad",
            fixture_id="product-acceptance-bad",
            workflow_record_refs=["record:one"],
            covered_workflows=[TargetProductWorkflow.MULTI_SITE_ONBOARDING],
            minimum_gate_refs=list(MinimumProductGate),
            buyer_value_workflow_refs=["buyer:bad"],
            evidence_refs=["evidence:bad"],
            replay_refs=["replay:bad"],
            operator_visible_result_refs=["operator:bad"],
            policy_decision_refs=["policy:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            artifact_refs=["artifact:bad"],
            status_accuracy_refs=["status:bad"],
            workflow_specific_refs=["workflow-specific:bad"],
            export_reconciliation_refs=["export:bad"],
            recovery_action_refs=["recovery:bad"],
            operator_status="product_acceptance_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_product_report_accepts_pass_and_typed_fail() -> None:
    report = ProductAcceptanceGateReport(
        id="product-acceptance-report:ok",
        run_ref="run:ok",
        fixture_id="product-acceptance-ok",
        workflow_record_refs=[f"record:{workflow.value}" for workflow in TargetProductWorkflow],
        covered_workflows=list(TargetProductWorkflow),
        minimum_gate_refs=list(MinimumProductGate),
        buyer_value_workflow_refs=["buyer:ok"],
        evidence_refs=["evidence:ok"],
        replay_refs=["replay:ok"],
        operator_visible_result_refs=["operator:ok"],
        policy_decision_refs=["policy:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        artifact_refs=["artifact:ok"],
        status_accuracy_refs=["status:ok"],
        workflow_specific_refs=["workflow-specific:ok"],
        export_reconciliation_refs=["export:ok"],
        recovery_action_refs=["recovery:ok"],
        operator_status="product_acceptance_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS

    failed = ProductAcceptanceGateReport(
        id="product-acceptance-report:fail",
        run_ref="run:fail",
        fixture_id="product-acceptance-fail",
        failure_type=ProductAcceptanceFailureType.SCAFFOLD_ONLY,
        failure_report_refs=["failure:fail"],
        scaffold_only_refs=["scaffold:fail"],
        missing_ref_fields=["executable_product_oracle_refs"],
        operator_status=ProductAcceptanceFailureType.SCAFFOLD_ONLY.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failed.failure_type == ProductAcceptanceFailureType.SCAFFOLD_ONLY


def test_product_fixture_manifest_rejects_invalid_failure_expectations() -> None:
    with pytest.raises(ValidationError):
        ProductAcceptanceFixtureManifest(
            id="product-acceptance-bad",
            scenario="product-acceptance-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=ProductAcceptanceFailureType.MISSING_WORKFLOW,
            negative_case=True,
        )
    with pytest.raises(ValidationError):
        ProductAcceptanceFixtureManifest(
            id="product-acceptance-bad",
            scenario="product-acceptance-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=ProductAcceptanceFailureType.MISSING_WORKFLOW,
            negative_case=False,
        )
