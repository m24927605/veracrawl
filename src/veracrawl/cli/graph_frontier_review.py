"""Graph-driven frontier/review runtime fixture runner CLI."""

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
    GraphFrontierDecisionType,
    GraphReviewRouteType,
)
from veracrawl.contracts.graph import GraphFrontierReviewFixtureManifest
from veracrawl.graph.frontier_review import (
    GraphFrontierReviewRuntimeResult,
    run_graph_frontier_review_runtime_gate,
)


class GraphFrontierReviewFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    review_route_decision_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_types: list[GraphFrontierDecisionType] = Field(default_factory=list)
    review_route_types: list[GraphReviewRouteType] = Field(default_factory=list)
    frontier_item_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    source_graph_refs: list[Ref] = Field(default_factory=list)
    explanation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    graph_signal_as_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_source_graph_refs: list[Ref] = Field(default_factory=list)
    missing_explanation_refs: list[Ref] = Field(default_factory=list)
    unauthorized_frontier_mutation_refs: list[Ref] = Field(default_factory=list)
    missing_review_route_refs: list[Ref] = Field(default_factory=list)
    unsupported_signal_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_graph_frontier_review_fixture(
    manifest: GraphFrontierReviewFixtureManifest,
    *,
    profile: str,
) -> GraphFrontierReviewFixtureRunReport:
    result = run_graph_frontier_review_runtime_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:graph-frontier-review"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: GraphFrontierReviewFixtureManifest,
    profile: str,
    result: GraphFrontierReviewRuntimeResult,
) -> GraphFrontierReviewFixtureRunReport:
    report = result.report
    return GraphFrontierReviewFixtureRunReport(
        id=f"graph-frontier-review-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        graph_signal_refs=report.graph_signal_refs,
        frontier_decision_refs=report.frontier_decision_refs,
        review_route_decision_refs=report.review_route_decision_refs,
        frontier_decision_types=[
            decision.decision_type for decision in result.frontier_decisions
        ],
        review_route_types=[decision.route_type for decision in result.review_route_decisions],
        frontier_item_refs=report.frontier_item_refs,
        review_item_refs=report.review_item_refs,
        source_graph_refs=report.source_graph_refs,
        explanation_refs=report.explanation_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        graph_signal_as_evidence_refs=report.graph_signal_as_evidence_refs,
        missing_source_graph_refs=report.missing_source_graph_refs,
        missing_explanation_refs=report.missing_explanation_refs,
        unauthorized_frontier_mutation_refs=report.unauthorized_frontier_mutation_refs,
        missing_review_route_refs=report.missing_review_route_refs,
        unsupported_signal_refs=report.unsupported_signal_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> GraphFrontierReviewFixtureRunReport:
    manifest = GraphFrontierReviewFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_graph_frontier_review_fixture(manifest, profile=profile)
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
    parser = argparse.ArgumentParser(prog="veracrawl-graph-frontier-review")
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
