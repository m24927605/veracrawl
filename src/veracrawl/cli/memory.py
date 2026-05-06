"""Memory kernel fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.memory import MemoryFixtureManifest
from veracrawl.memory.kernel import MemoryKernelResult, run_memory_kernel
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class MemoryFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    memory_event_refs: list[Ref] = Field(default_factory=list)
    retrieval_trace_ref: Ref | None = None
    tunnel_ref: Ref | None = None
    operational_record_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_memory_fixture(
    manifest: MemoryFixtureManifest,
    *,
    profile: str,
) -> MemoryFixtureRunReport:
    result = run_memory_kernel(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        evidence_refs=[f"evidence-packet:{manifest.id}:accepted"],
        policy_decision_refs=[f"policy:{manifest.id}:memory"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: MemoryFixtureManifest,
    profile: str,
    result: MemoryKernelResult,
) -> MemoryFixtureRunReport:
    report = result.report
    return MemoryFixtureRunReport(
        id=f"memory-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        memory_event_refs=report.memory_event_refs,
        retrieval_trace_ref=report.retrieval_trace_ref,
        tunnel_ref=report.tunnel_ref,
        operational_record_refs=report.operational_record_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> MemoryFixtureRunReport:
    manifest = MemoryFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_memory_fixture(manifest, profile=profile)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result.value}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-memory")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-memory"):
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
