"""Source adapter fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_runtime import SourceFixtureManifest
from veracrawl.fetch.acquisition import execute_source_acquisition
from veracrawl.ports.source_adapter import SourceAdapterPort

ADAPTER_BY_NAME = {
    "http": AdapterType.HTTP,
    "sitemap": AdapterType.SITEMAP,
    "rss": AdapterType.RSS,
    "api": AdapterType.API_SOURCE,
    "document": AdapterType.DOCUMENT_SOURCE,
}


class SourceFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    source_adapter_result_ref: Ref | None = None
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_ref: Ref | None = None
    document_artifact_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    frontier_item_ref: Ref
    lease_ref: Ref
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_source_fixture(
    fixture_id: str,
    *,
    scenario: str,
    adapter_type: AdapterType,
    profile: str,
) -> SourceFixtureRunReport:
    adapter_module = importlib.import_module("veracrawl.adapters.sources.deterministic")
    adapter = cast(
        SourceAdapterPort,
        adapter_module.DeterministicSourceAdapter(
            adapter_type=adapter_type,
            result_type=(
                SourceAdapterResultType.DOCUMENT_ARTIFACT
                if scenario == "adapter-mismatch"
                else None
            ),
        ),
    )
    outcome = execute_source_acquisition(
        fixture_id=fixture_id,
        adapter_type=adapter_type,
        scenario=scenario,
        adapter=adapter,
    )
    report = outcome.report
    return SourceFixtureRunReport(
        id=f"source-run-report:{fixture_id}",
        fixture_id=fixture_id,
        scenario=scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        source_adapter_result_ref=report.source_adapter_result_ref,
        fetch_attempt_refs=report.fetch_attempt_refs,
        fetch_result_refs=report.fetch_result_refs,
        page_snapshot_ref=outcome.page_snapshot.id if outcome.page_snapshot else None,
        document_artifact_ref=outcome.document_artifact.id if outcome.document_artifact else None,
        artifact_refs=report.artifact_refs,
        policy_decision_refs=report.policy_decision_refs,
        frontier_item_ref=report.frontier_item_ref,
        lease_ref=report.lease_ref,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        recovery_report_refs=report.recovery_report_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> SourceFixtureRunReport:
    manifest = SourceFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    adapter_type = ADAPTER_BY_NAME[manifest.adapter_type]
    report = run_source_fixture(
        manifest.id,
        scenario=manifest.scenario,
        adapter_type=adapter_type,
        profile=profile,
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-source")
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
