"""Agent runtime adapter fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from pydantic import Field

from veracrawl.agents.adapter_gate import (
    AgentRuntimeAdapterGateResult,
    run_agent_runtime_adapter_gate,
)
from veracrawl.contracts.agent_adapter import (
    AgentAdapterExecutionRecord,
    AgentRuntimeAdapterFixtureManifest,
)
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult


class AgentRuntimeAdapterFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    framework_execution_refs: list[Ref] = Field(default_factory=list)
    required_framework_names: list[str] = Field(default_factory=list)
    verified_framework_names: list[str] = Field(default_factory=list)
    model_provider_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_leak_refs: list[Ref] = Field(default_factory=list)
    raw_response_leak_refs: list[Ref] = Field(default_factory=list)
    framework_state_canonical_refs: list[Ref] = Field(default_factory=list)
    unsupported_framework_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _contract_execution_records(fixture_id: str) -> list[AgentAdapterExecutionRecord]:
    module = _load_module("veracrawl.adapters.agent_frameworks.contract")
    builder = cast(
        Callable[..., list[AgentAdapterExecutionRecord]],
        module.__dict__["build_contract_execution_records"],
    )
    return builder(
        fixture_id,
        policy_decision_refs=[f"policy:{fixture_id}:agent-adapter"],
    )


def run_agent_adapter_fixture(
    manifest: AgentRuntimeAdapterFixtureManifest,
    *,
    profile: str,
) -> AgentRuntimeAdapterFixtureRunReport:
    records = (
        _contract_execution_records(manifest.id)
        if manifest.scenario == "agent-runtime-adapter-success"
        else None
    )
    result = run_agent_runtime_adapter_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        execution_records=records,
        policy_decision_refs=[f"policy:{manifest.id}:agent-adapter"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: AgentRuntimeAdapterFixtureManifest,
    profile: str,
    result: AgentRuntimeAdapterGateResult,
) -> AgentRuntimeAdapterFixtureRunReport:
    report = result.report
    return AgentRuntimeAdapterFixtureRunReport(
        id=f"agent-runtime-adapter-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        framework_execution_refs=report.framework_execution_refs,
        required_framework_names=report.required_framework_names,
        verified_framework_names=report.verified_framework_names,
        model_provider_refs=report.model_provider_refs,
        policy_decision_refs=report.policy_decision_refs,
        observability_report_refs=report.observability_report_refs,
        security_privacy_report_refs=report.security_privacy_report_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        raw_prompt_leak_refs=report.raw_prompt_leak_refs,
        raw_response_leak_refs=report.raw_response_leak_refs,
        framework_state_canonical_refs=report.framework_state_canonical_refs,
        unsupported_framework_refs=report.unsupported_framework_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> AgentRuntimeAdapterFixtureRunReport:
    manifest = AgentRuntimeAdapterFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_agent_adapter_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.operator_status != manifest.expected_failure_type.value
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-agent-adapters")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
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
