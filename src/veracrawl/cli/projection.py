"""Advanced graph projection fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.graph import AdvancedGraphFixtureManifest
from veracrawl.graph.build import LinkInput, build_basic_site_graph
from veracrawl.graph.projection import (
    AdvancedGraphProjectionResult,
    build_advanced_graph_projection,
)


class AdvancedGraphFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    projection_spec_ref: Ref | None = None
    rebuild_job_ref: Ref | None = None
    delta_report_ref: Ref | None = None
    quality_report_ref: Ref | None = None
    signal_refs: list[Ref] = Field(default_factory=list)
    temporal_record_refs: list[Ref] = Field(default_factory=list)
    mismatch_report_ref: Ref | None = None
    watermark_ref: Ref | None = None
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


def _base_graph_refs(fixture_id: str) -> tuple[Ref, list[Ref], list[Ref]]:
    base = build_basic_site_graph(
        fixture_id=f"{fixture_id}:base",
        scenario="url-hyperlink",
        link_inputs=[
            LinkInput(
                source_url="https://example.test/",
                target_url="https://example.test/detail",
                provenance_ref=f"link-provenance:{fixture_id}:base:1",
            )
        ],
        policy_decision_refs=[f"policy:{fixture_id}:base-graph"],
    )
    if base.manifest is None:
        raise ValueError(f"base graph failed for {fixture_id}")
    return base.manifest.id, base.manifest.node_refs, base.manifest.edge_refs


def run_advanced_graph_fixture(
    manifest: AdvancedGraphFixtureManifest,
    *,
    profile: str,
) -> AdvancedGraphFixtureRunReport:
    base_manifest_ref, graph_node_refs, graph_edge_refs = _base_graph_refs(manifest.id)
    result = build_advanced_graph_projection(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        base_manifest_ref=base_manifest_ref,
        graph_node_refs=graph_node_refs,
        graph_edge_refs=graph_edge_refs,
        source_output_refs=[f"published-output:{manifest.id}:verified"],
        evidence_packet_refs=[f"evidence-packet:{manifest.id}:accepted"],
        policy_decision_refs=[f"policy:{manifest.id}:advanced-graph"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: AdvancedGraphFixtureManifest,
    profile: str,
    result: AdvancedGraphProjectionResult,
) -> AdvancedGraphFixtureRunReport:
    report = result.report
    return AdvancedGraphFixtureRunReport(
        id=f"advanced-graph-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        projection_spec_ref=report.projection_spec_ref,
        rebuild_job_ref=report.rebuild_job_ref,
        delta_report_ref=report.delta_report_ref,
        quality_report_ref=report.quality_report_ref,
        signal_refs=report.signal_refs,
        temporal_record_refs=report.temporal_record_refs,
        mismatch_report_ref=report.mismatch_report_ref,
        watermark_ref=report.watermark_ref,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> AdvancedGraphFixtureRunReport:
    manifest = AdvancedGraphFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_advanced_graph_fixture(manifest, profile=profile)
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
    parser = argparse.ArgumentParser(prog="veracrawl-projection")
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
