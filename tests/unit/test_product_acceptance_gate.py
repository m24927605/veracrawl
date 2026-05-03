from __future__ import annotations

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    MinimumProductGate,
    ProductAcceptanceFailureType,
    TargetProductWorkflow,
)
from veracrawl.product_acceptance.gate import run_product_acceptance_gate


@pytest.mark.parametrize("workflow", list(TargetProductWorkflow))
def test_product_acceptance_success_has_workflow_records(
    workflow: TargetProductWorkflow,
) -> None:
    result = run_product_acceptance_gate(
        fixture_id="product-acceptance-success",
        scenario="product-acceptance-success",
    )
    record = next(item for item in result.workflow_records if item.workflow == workflow)
    assert record.result == CompletenessResult.PASS
    assert record.evidence_refs
    assert record.replay_refs
    assert record.operator_visible_result_refs
    assert record.workflow_specific_refs
    assert set(record.minimum_gate_refs) == set(MinimumProductGate)


def test_product_acceptance_success_report_covers_all_workflows_and_gates() -> None:
    result = run_product_acceptance_gate(
        fixture_id="product-acceptance-success",
        scenario="product-acceptance-success",
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert set(result.report.covered_workflows) == set(TargetProductWorkflow)
    assert set(result.report.minimum_gate_refs) == set(MinimumProductGate)
    assert result.report.status_accuracy_refs


def test_product_acceptance_runtime_unavailable_needs_review() -> None:
    result = run_product_acceptance_gate(
        fixture_id="product-acceptance-runtime-unavailable",
        scenario="product-acceptance-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.missing_runtime_refs


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "product-acceptance-missing-workflow",
            ProductAcceptanceFailureType.MISSING_WORKFLOW,
        ),
        (
            "product-acceptance-missing-minimum-gate",
            ProductAcceptanceFailureType.MISSING_MINIMUM_GATE,
        ),
        (
            "product-acceptance-missing-evidence",
            ProductAcceptanceFailureType.MISSING_EVIDENCE,
        ),
        (
            "product-acceptance-missing-replay",
            ProductAcceptanceFailureType.MISSING_REPLAY,
        ),
        (
            "product-acceptance-missing-operator-visibility",
            ProductAcceptanceFailureType.MISSING_OPERATOR_VISIBILITY,
        ),
        (
            "product-acceptance-missing-policy",
            ProductAcceptanceFailureType.MISSING_POLICY,
        ),
        (
            "product-acceptance-missing-workflow-specific-refs",
            ProductAcceptanceFailureType.MISSING_WORKFLOW_SPECIFIC_REFS,
        ),
        (
            "product-acceptance-scaffold-only",
            ProductAcceptanceFailureType.SCAFFOLD_ONLY,
        ),
        (
            "product-acceptance-contract-only",
            ProductAcceptanceFailureType.CONTRACT_ONLY,
        ),
        (
            "product-acceptance-false-complete-status",
            ProductAcceptanceFailureType.FALSE_COMPLETE_STATUS,
        ),
        (
            "product-acceptance-degraded-operational",
            ProductAcceptanceFailureType.DEGRADED_OPERATIONAL,
        ),
        (
            "product-acceptance-missing-export-reconciliation",
            ProductAcceptanceFailureType.MISSING_EXPORT_RECONCILIATION,
        ),
    ],
)
def test_product_acceptance_negative_scenarios_fail(
    scenario: str,
    failure: ProductAcceptanceFailureType,
) -> None:
    result = run_product_acceptance_gate(fixture_id=scenario, scenario=scenario)
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
