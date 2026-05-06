"""Target product acceptance fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    MinimumProductGate,
    ProductAcceptanceFailureType,
    TargetProductWorkflow,
)
from veracrawl.contracts.product_acceptance import ProductAcceptanceFixtureManifest
from veracrawl.product_acceptance.gate import (
    ProductAcceptanceRuntimeResult,
    run_product_acceptance_gate,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class ProductAcceptanceFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
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


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_product_acceptance_fixture(
    manifest: ProductAcceptanceFixtureManifest,
    *,
    profile: str,
) -> ProductAcceptanceFixtureRunReport:
    result = run_product_acceptance_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:product-acceptance"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: ProductAcceptanceFixtureManifest,
    profile: str,
    result: ProductAcceptanceRuntimeResult,
) -> ProductAcceptanceFixtureRunReport:
    report = result.report
    return ProductAcceptanceFixtureRunReport(
        id=f"product-acceptance-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        workflow_record_refs=report.workflow_record_refs,
        covered_workflows=report.covered_workflows,
        missing_workflows=report.missing_workflows,
        minimum_gate_refs=report.minimum_gate_refs,
        missing_minimum_gates=report.missing_minimum_gates,
        buyer_value_workflow_refs=report.buyer_value_workflow_refs,
        evidence_refs=report.evidence_refs,
        replay_refs=report.replay_refs,
        operator_visible_result_refs=report.operator_visible_result_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        artifact_refs=report.artifact_refs,
        status_accuracy_refs=report.status_accuracy_refs,
        workflow_specific_refs=report.workflow_specific_refs,
        export_reconciliation_refs=report.export_reconciliation_refs,
        recovery_action_refs=report.recovery_action_refs,
        missing_evidence_refs=report.missing_evidence_refs,
        missing_replay_refs=report.missing_replay_refs,
        missing_operator_visible_result_refs=report.missing_operator_visible_result_refs,
        missing_policy_refs=report.missing_policy_refs,
        missing_workflow_specific_refs=report.missing_workflow_specific_refs,
        scaffold_only_refs=report.scaffold_only_refs,
        contract_only_refs=report.contract_only_refs,
        false_complete_status_refs=report.false_complete_status_refs,
        degraded_operational_refs=report.degraded_operational_refs,
        missing_export_reconciliation_refs=report.missing_export_reconciliation_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        failure_type=report.failure_type,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> ProductAcceptanceFixtureRunReport:
    manifest = ProductAcceptanceFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_product_acceptance_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-product-acceptance")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-product-acceptance"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
                )
            except (OSError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    sys.exit(main())
