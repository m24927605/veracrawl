"""Graph and memory production runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.graph_memory import GraphMemoryProductionFixtureManifest
from veracrawl.graph_memory.runtime import (
    GraphMemoryProductionRuntimeResult,
    run_graph_memory_production_runtime,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class GraphMemoryProductionFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    live_normalization_runtime_report_ref: Ref | None = None
    live_evidence_verification_runtime_report_ref: Ref | None = None
    multi_agent_repair_report_ref: Ref | None = None
    advanced_graph_projection_report_ref: Ref | None = None
    graph_frontier_review_runtime_report_ref: Ref | None = None
    temporal_kg_runtime_report_ref: Ref | None = None
    memory_kernel_report_ref: Ref | None = None
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    memory_retrieval_trace_refs: list[Ref] = Field(default_factory=list)
    memory_invalidation_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    repair_explanation_refs: list[Ref] = Field(default_factory=list)
    operator_explanation_refs: list[Ref] = Field(default_factory=list)
    source_evidence_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: str | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    graph_as_evidence_refs: list[Ref] = Field(default_factory=list)
    memory_as_evidence_refs: list[Ref] = Field(default_factory=list)
    stale_memory_refs: list[Ref] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_graph_memory_production_fixture(
    manifest: GraphMemoryProductionFixtureManifest,
    *,
    profile: str,
) -> GraphMemoryProductionFixtureRunReport:
    result = run_graph_memory_production_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:graph-memory"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: GraphMemoryProductionFixtureManifest,
    profile: str,
    result: GraphMemoryProductionRuntimeResult,
) -> GraphMemoryProductionFixtureRunReport:
    report = result.report
    return GraphMemoryProductionFixtureRunReport(
        id=f"graph-memory-production-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        live_normalization_runtime_report_ref=report.live_normalization_runtime_report_ref,
        live_evidence_verification_runtime_report_ref=(
            report.live_evidence_verification_runtime_report_ref
        ),
        multi_agent_repair_report_ref=report.multi_agent_repair_report_ref,
        advanced_graph_projection_report_ref=report.advanced_graph_projection_report_ref,
        graph_frontier_review_runtime_report_ref=(report.graph_frontier_review_runtime_report_ref),
        temporal_kg_runtime_report_ref=report.temporal_kg_runtime_report_ref,
        memory_kernel_report_ref=report.memory_kernel_report_ref,
        graph_signal_refs=report.graph_signal_refs,
        memory_retrieval_trace_refs=report.memory_retrieval_trace_refs,
        memory_invalidation_refs=report.memory_invalidation_refs,
        frontier_decision_refs=report.frontier_decision_refs,
        repair_explanation_refs=report.repair_explanation_refs,
        operator_explanation_refs=report.operator_explanation_refs,
        source_evidence_refs=report.source_evidence_refs,
        verification_decision_refs=report.verification_decision_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_type=report.failure_type.value if report.failure_type else None,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        graph_as_evidence_refs=report.graph_as_evidence_refs,
        memory_as_evidence_refs=report.memory_as_evidence_refs,
        stale_memory_refs=report.stale_memory_refs,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> GraphMemoryProductionFixtureRunReport:
    manifest = GraphMemoryProductionFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_graph_memory_production_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
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
    parser = argparse.ArgumentParser(prog="veracrawl-graph-memory-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-graph-memory-runtime"):
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
