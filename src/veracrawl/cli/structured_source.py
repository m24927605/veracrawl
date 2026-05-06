"""Structured source adapter runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    StructuredSourceAdapterFailureType,
)
from veracrawl.contracts.source_runtime import (
    StructuredSourceAdapterRecord,
    StructuredSourceAdaptersFixtureManifest,
)
from veracrawl.fetch.structured_source import (
    StructuredSourceAdaptersRuntimeResult,
    run_structured_source_adapters_runtime,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class StructuredSourceAdaptersFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    required_adapter_types: list[AdapterType] = Field(default_factory=list)
    verified_adapter_types: list[AdapterType] = Field(default_factory=list)
    source_adapter_record_refs: list[Ref] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    natural_result_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    evidence_seed_refs: list[Ref] = Field(default_factory=list)
    discovered_url_refs: list[Ref] = Field(default_factory=list)
    api_payload_refs: list[Ref] = Field(default_factory=list)
    document_artifact_refs: list[Ref] = Field(default_factory=list)
    file_artifact_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: StructuredSourceAdapterFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _adapter_records(fixture_id: str, fixture_dir: Path) -> list[StructuredSourceAdapterRecord]:
    module = importlib.import_module("veracrawl.adapters.sources.structured_runtime")
    builder = cast(
        Callable[..., list[StructuredSourceAdapterRecord]],
        module.__dict__["build_structured_source_adapter_records"],
    )
    return builder(
        fixture_id,
        sources_root=fixture_dir / "sources",
        policy_decision_refs=[f"policy:{fixture_id}:structured-source"],
    )


def run_structured_source_fixture(
    manifest: StructuredSourceAdaptersFixtureManifest,
    *,
    profile: str,
    fixture_dir: Path,
) -> StructuredSourceAdaptersFixtureRunReport:
    records = (
        _adapter_records(manifest.id, fixture_dir)
        if manifest.scenario == "structured-source-adapters-success"
        else None
    )
    result = run_structured_source_adapters_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        adapter_records=records,
        policy_decision_refs=[f"policy:{manifest.id}:structured-source"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: StructuredSourceAdaptersFixtureManifest,
    profile: str,
    result: StructuredSourceAdaptersRuntimeResult,
) -> StructuredSourceAdaptersFixtureRunReport:
    report = result.report
    return StructuredSourceAdaptersFixtureRunReport(
        id=f"structured-source-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        required_adapter_types=report.required_adapter_types,
        verified_adapter_types=report.verified_adapter_types,
        source_adapter_record_refs=report.source_adapter_record_refs,
        source_adapter_result_refs=report.source_adapter_result_refs,
        natural_result_refs=report.natural_result_refs,
        artifact_refs=report.artifact_refs,
        evidence_seed_refs=report.evidence_seed_refs,
        discovered_url_refs=report.discovered_url_refs,
        api_payload_refs=report.api_payload_refs,
        document_artifact_refs=report.document_artifact_refs,
        file_artifact_refs=report.file_artifact_refs,
        fetch_attempt_refs=report.fetch_attempt_refs,
        fetch_result_refs=report.fetch_result_refs,
        page_snapshot_refs=report.page_snapshot_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        failure_type=report.failure_type,
        diagnostics=report.diagnostics,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> StructuredSourceAdaptersFixtureRunReport:
    manifest = StructuredSourceAdaptersFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_structured_source_fixture(manifest, profile=profile, fixture_dir=fixture_dir)
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
    parser = argparse.ArgumentParser(prog="veracrawl-structured-source")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-structured-source"):
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
