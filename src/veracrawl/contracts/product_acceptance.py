"""Product acceptance contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    MinimumProductGate,
    ProductAcceptanceFailureType,
    TargetProductWorkflow,
)

TARGET_PRODUCT_WORKFLOWS: frozenset[TargetProductWorkflow] = frozenset(
    TargetProductWorkflow
)
MINIMUM_PRODUCT_GATES: frozenset[MinimumProductGate] = frozenset(MinimumProductGate)

_REQUIRED_WORKFLOW_SPECIFIC_REFS: dict[TargetProductWorkflow, frozenset[str]] = {
    TargetProductWorkflow.MULTI_SITE_ONBOARDING: frozenset(
        {
            "project_ref",
            "source_scope_refs",
            "schema_refs",
            "objective_refs",
            "distinct_site_refs",
        }
    ),
    TargetProductWorkflow.OBJECTIVE_TO_PLAN_APPROVAL: frozenset(
        {
            "plan_proposal_ref",
            "adapter_choice_refs",
            "assumption_refs",
            "alternative_refs",
            "approval_ref",
        }
    ),
    TargetProductWorkflow.DYNAMIC_AUTH_DOCUMENT_API_CRAWL: frozenset(
        {
            "browser_artifact_refs",
            "credential_audit_refs",
            "document_artifact_refs",
            "api_payload_refs",
            "safety_ref",
        }
    ),
    TargetProductWorkflow.EVIDENCE_REVIEW: frozenset(
        {
            "source_view_refs",
            "normalized_view_refs",
            "anchor_refs",
            "verification_decision_refs",
        }
    ),
    TargetProductWorkflow.CONFLICT_RESOLUTION: frozenset(
        {"conflict_refs", "adjudication_refs", "no_silent_overwrite_ref"}
    ),
    TargetProductWorkflow.DRIFT_REPAIR: frozenset(
        {
            "drift_event_refs",
            "repair_proposal_refs",
            "reviewed_update_refs",
            "verified_recovery_refs",
        }
    ),
    TargetProductWorkflow.MEMORY_REUSE: frozenset(
        {"memory_retrieval_refs", "stale_exclusion_refs", "reanchor_evidence_refs"}
    ),
    TargetProductWorkflow.EXPORT_AND_WITHDRAWAL: frozenset(
        {
            "delivery_receipt_refs",
            "withdrawal_refs",
            "destination_mapping_refs",
            "reconciliation_refs",
        }
    ),
    TargetProductWorkflow.REPLAY_AND_AUDIT: frozenset(
        {"replay_bundle_refs", "tool_call_refs", "policy_trace_refs", "export_trace_refs"}
    ),
    TargetProductWorkflow.OPERATOR_RECOVERY: frozenset(
        {
            "failure_record_refs",
            "recovery_action_refs",
            "operator_status_refs",
            "replay_visible_result_refs",
        }
    ),
}


class ProductWorkflowReadinessRecord(TimestampedModel):
    id: str
    run_ref: Ref
    fixture_id: str
    workflow: TargetProductWorkflow
    buyer_value_ref: Ref | None = None
    evidence_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    operator_visible_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    acceptance_oracle_refs: list[Ref] = Field(default_factory=list)
    minimum_gate_refs: list[MinimumProductGate] = Field(default_factory=list)
    workflow_specific_refs: dict[str, Ref] = Field(default_factory=dict)
    capability_state_refs: list[Ref] = Field(default_factory=list)
    status_accuracy_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    failure_oracle_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    false_complete_status_refs: list[Ref] = Field(default_factory=list)
    degraded_operational_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_gap_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_product_workflow(self) -> ProductWorkflowReadinessRecord:
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "buyer_value_ref": self.buyer_value_ref,
                "evidence_refs": self.evidence_refs,
                "replay_refs": self.replay_refs,
                "operator_visible_result_refs": self.operator_visible_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "acceptance_oracle_refs": self.acceptance_oracle_refs,
                "minimum_gate_refs": self.minimum_gate_refs,
                "capability_state_refs": self.capability_state_refs,
                "status_accuracy_refs": self.status_accuracy_refs,
            }
            missing = [name for name, value in required.items() if not value]
            required_specific_refs = _REQUIRED_WORKFLOW_SPECIFIC_REFS[self.workflow]
            missing.extend(
                sorted(
                    ref_name
                    for ref_name in required_specific_refs
                    if ref_name not in self.workflow_specific_refs
                )
            )
            if (
                self.workflow == TargetProductWorkflow.EXPORT_AND_WITHDRAWAL
                and not self.export_reconciliation_refs
            ):
                missing.append("export_reconciliation_refs")
            if (
                self.workflow == TargetProductWorkflow.OPERATOR_RECOVERY
                and not self.recovery_action_refs
            ):
                missing.append("recovery_action_refs")
            if (
                missing
                or self.scaffold_only_refs
                or self.contract_only_refs
                or self.false_complete_status_refs
                or self.degraded_operational_refs
                or self.export_reconciliation_gap_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing product workflow readiness missing refs: {missing}"
                )
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not self.missing_ref_fields:
                raise ValueError("needs-review product workflow requires missing refs")
        elif not (
            self.scaffold_only_refs
            or self.contract_only_refs
            or self.false_complete_status_refs
            or self.degraded_operational_refs
            or self.export_reconciliation_gap_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed product workflow requires failure details")
        return self


class ProductAcceptanceGateReport(TimestampedModel):
    id: str
    run_ref: Ref
    fixture_id: str
    workflow_record_refs: list[Ref] = Field(default_factory=list)
    covered_workflows: list[TargetProductWorkflow] = Field(default_factory=list)
    missing_workflows: list[TargetProductWorkflow] = Field(default_factory=list)
    minimum_gate_refs: list[MinimumProductGate] = Field(default_factory=list)
    missing_minimum_gates: list[MinimumProductGate] = Field(default_factory=list)
    buyer_value_workflow_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    operator_visible_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    status_accuracy_refs: list[Ref] = Field(default_factory=list)
    workflow_specific_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    missing_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_replay_refs: list[Ref] = Field(default_factory=list)
    missing_operator_visible_result_refs: list[Ref] = Field(default_factory=list)
    missing_policy_refs: list[Ref] = Field(default_factory=list)
    missing_workflow_specific_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    false_complete_status_refs: list[Ref] = Field(default_factory=list)
    degraded_operational_refs: list[Ref] = Field(default_factory=list)
    missing_export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    failure_type: ProductAcceptanceFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_product_acceptance_report(self) -> ProductAcceptanceGateReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "workflow_record_refs": self.workflow_record_refs,
                "minimum_gate_refs": self.minimum_gate_refs,
                "buyer_value_workflow_refs": self.buyer_value_workflow_refs,
                "evidence_refs": self.evidence_refs,
                "replay_refs": self.replay_refs,
                "operator_visible_result_refs": self.operator_visible_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "status_accuracy_refs": self.status_accuracy_refs,
                "workflow_specific_refs": self.workflow_specific_refs,
                "export_reconciliation_refs": self.export_reconciliation_refs,
                "recovery_action_refs": self.recovery_action_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or set(self.covered_workflows) != TARGET_PRODUCT_WORKFLOWS
                or set(self.minimum_gate_refs) != MINIMUM_PRODUCT_GATES
                or self.missing_workflows
                or self.missing_minimum_gates
                or self.missing_evidence_refs
                or self.missing_replay_refs
                or self.missing_operator_visible_result_refs
                or self.missing_policy_refs
                or self.missing_workflow_specific_refs
                or self.scaffold_only_refs
                or self.contract_only_refs
                or self.false_complete_status_refs
                or self.degraded_operational_refs
                or self.missing_export_reconciliation_refs
                or self.missing_runtime_refs
                or self.missing_ref_fields
                or self.failure_type is not None
            ):
                raise ValueError(
                    f"passing product acceptance report missing refs: {missing}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review product acceptance report requires refs")
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_workflows
                or self.missing_minimum_gates
                or self.missing_evidence_refs
                or self.missing_replay_refs
                or self.missing_operator_visible_result_refs
                or self.missing_policy_refs
                or self.missing_workflow_specific_refs
                or self.scaffold_only_refs
                or self.contract_only_refs
                or self.false_complete_status_refs
                or self.degraded_operational_refs
                or self.missing_export_reconciliation_refs
                or self.missing_ref_fields
            )
        ):
            raise ValueError("failed product acceptance report requires failure details")
        return self


class ProductAcceptanceFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ProductAcceptanceFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_product_acceptance_fixture(self) -> ProductAcceptanceFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("product acceptance fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative product acceptance fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
