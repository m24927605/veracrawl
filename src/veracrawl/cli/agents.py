"""Multi-agent repair fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.agents.orchestration import MultiAgentRepairResult, run_multi_agent_repair
from veracrawl.contracts.agent import MultiAgentFixtureManifest
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class MultiAgentFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    workflow_ref: Ref | None = None
    agent_model_adapter_runtime_report_ref: Ref | None = None
    live_evidence_verification_runtime_report_ref: Ref | None = None
    handoff_refs: list[Ref] = Field(default_factory=list)
    coordination_decision_refs: list[Ref] = Field(default_factory=list)
    repair_signal_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    controlled_tool_call_refs: list[Ref] = Field(default_factory=list)
    owner_command_refs: list[Ref] = Field(default_factory=list)
    review_escalation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: str | None = None


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_multi_agent_fixture(
    manifest: MultiAgentFixtureManifest,
    *,
    profile: str,
) -> MultiAgentFixtureRunReport:
    result = run_multi_agent_repair(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:multi-agent"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: MultiAgentFixtureManifest,
    profile: str,
    result: MultiAgentRepairResult,
) -> MultiAgentFixtureRunReport:
    report = result.report
    return MultiAgentFixtureRunReport(
        id=f"multi-agent-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        workflow_ref=report.workflow_ref,
        agent_model_adapter_runtime_report_ref=(report.agent_model_adapter_runtime_report_ref),
        live_evidence_verification_runtime_report_ref=(
            report.live_evidence_verification_runtime_report_ref
        ),
        handoff_refs=report.handoff_refs,
        coordination_decision_refs=report.coordination_decision_refs,
        repair_signal_refs=report.repair_signal_refs,
        agent_action_trace_refs=report.agent_action_trace_refs,
        controlled_tool_call_refs=report.controlled_tool_call_refs,
        owner_command_refs=report.owner_command_refs,
        review_escalation_refs=report.review_escalation_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        failure_type=report.failure_type.value if report.failure_type else None,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> MultiAgentFixtureRunReport:
    manifest = MultiAgentFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_multi_agent_fixture(manifest, profile=profile)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result.value}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type.value
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-agent-workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-agents"):
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
