"""Source coverage adapter fixture runner CLI."""

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

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AdapterType, CompletenessResult
from veracrawl.contracts.source_coverage import (
    SourceCoverageAdapterExecutionRecord,
    SourceCoverageAdapterFixtureManifest,
)
from veracrawl.fetch.source_coverage_gate import (
    SourceCoverageAdapterGateResult,
    run_source_coverage_adapter_gate,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class SourceCoverageAdapterFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    adapter_execution_refs: list[Ref] = Field(default_factory=list)
    required_adapter_types: list[AdapterType] = Field(default_factory=list)
    verified_adapter_types: list[AdapterType] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    natural_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    browser_interaction_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    document_artifact_refs: list[Ref] = Field(default_factory=list)
    api_payload_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    adapter_native_state_canonical_refs: list[Ref] = Field(default_factory=list)
    unsafe_browser_side_effect_refs: list[Ref] = Field(default_factory=list)
    unsupported_adapter_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _contract_execution_records(fixture_id: str) -> list[SourceCoverageAdapterExecutionRecord]:
    module = _load_module("veracrawl.adapters.source_coverage.contract")
    builder = cast(
        Callable[..., list[SourceCoverageAdapterExecutionRecord]],
        module.__dict__["build_contract_execution_records"],
    )
    return builder(
        fixture_id,
        policy_decision_refs=[f"policy:{fixture_id}:source-coverage"],
    )


def run_source_coverage_fixture(
    manifest: SourceCoverageAdapterFixtureManifest,
    *,
    profile: str,
) -> SourceCoverageAdapterFixtureRunReport:
    records = (
        _contract_execution_records(manifest.id)
        if manifest.scenario == "source-coverage-adapter-success"
        else None
    )
    result = run_source_coverage_adapter_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        execution_records=records,
        policy_decision_refs=[f"policy:{manifest.id}:source-coverage"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: SourceCoverageAdapterFixtureManifest,
    profile: str,
    result: SourceCoverageAdapterGateResult,
) -> SourceCoverageAdapterFixtureRunReport:
    report = result.report
    return SourceCoverageAdapterFixtureRunReport(
        id=f"source-coverage-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        adapter_execution_refs=report.adapter_execution_refs,
        required_adapter_types=report.required_adapter_types,
        verified_adapter_types=report.verified_adapter_types,
        source_adapter_result_refs=report.source_adapter_result_refs,
        natural_result_refs=report.natural_result_refs,
        fetch_attempt_refs=report.fetch_attempt_refs,
        page_snapshot_refs=report.page_snapshot_refs,
        browser_interaction_refs=report.browser_interaction_refs,
        credential_audit_refs=report.credential_audit_refs,
        document_artifact_refs=report.document_artifact_refs,
        api_payload_refs=report.api_payload_refs,
        policy_decision_refs=report.policy_decision_refs,
        observability_report_refs=report.observability_report_refs,
        security_privacy_report_refs=report.security_privacy_report_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        raw_secret_leak_refs=report.raw_secret_leak_refs,
        adapter_native_state_canonical_refs=report.adapter_native_state_canonical_refs,
        unsafe_browser_side_effect_refs=report.unsafe_browser_side_effect_refs,
        unsupported_adapter_refs=report.unsupported_adapter_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> SourceCoverageAdapterFixtureRunReport:
    manifest = SourceCoverageAdapterFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_source_coverage_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
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
    parser = argparse.ArgumentParser(prog="veracrawl-source-coverage")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-source-coverage"):
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
