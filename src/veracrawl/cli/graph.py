"""Basic site graph fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.graph import GraphFixtureManifest
from veracrawl.graph.build import GraphBuildResult, LinkInput, build_basic_site_graph


@dataclass(frozen=True)
class GraphFixtureInputs:
    link_inputs: list[LinkInput]
    canonical_inputs: list[LinkInput] | None = None
    redirect_inputs: list[LinkInput] | None = None
    page_type_refs: list[Ref] | None = None
    site_model_refs: list[Ref] | None = None


class GraphFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    manifest_ref: Ref | None = None
    node_refs: list[Ref] = Field(default_factory=list)
    edge_refs: list[Ref] = Field(default_factory=list)
    provenance_refs: list[Ref] = Field(default_factory=list)
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


def _inputs_for(manifest: GraphFixtureManifest) -> GraphFixtureInputs:
    if manifest.scenario == "url-hyperlink":
        return GraphFixtureInputs(
            link_inputs=[
                LinkInput(
                    source_url="https://example.test/",
                    target_url="https://example.test/detail",
                    provenance_ref=f"link-provenance:{manifest.id}:1",
                ),
                LinkInput(
                    source_url="https://example.test/",
                    target_url="https://example.test/detail",
                    provenance_ref=f"link-provenance:{manifest.id}:duplicate",
                ),
            ]
        )
    if manifest.scenario == "canonical-redirect":
        return GraphFixtureInputs(
            link_inputs=[],
            canonical_inputs=[
                LinkInput(
                    source_url="https://example.test/detail?ref=dup",
                    target_url="https://example.test/detail",
                    provenance_ref=f"canonical:{manifest.id}:detail",
                )
            ],
            redirect_inputs=[
                LinkInput(
                    source_url="http://example.test/",
                    target_url="https://example.test/",
                    provenance_ref=f"redirect-hop:{manifest.id}:1",
                )
            ],
        )
    if manifest.scenario == "page-structure":
        return GraphFixtureInputs(
            link_inputs=[],
            page_type_refs=[f"page-type:{manifest.id}:listing"],
            site_model_refs=[f"site-model:{manifest.id}:template"],
        )
    if manifest.scenario in {"rebuild-mismatch", "graph-as-evidence"}:
        return GraphFixtureInputs(
            link_inputs=[
                LinkInput(
                    source_url="https://example.test/",
                    target_url="https://example.test/detail",
                    provenance_ref=f"link-provenance:{manifest.id}:1",
                )
            ]
        )
    return GraphFixtureInputs(link_inputs=[])


def run_graph_fixture(manifest: GraphFixtureManifest, *, profile: str) -> GraphFixtureRunReport:
    inputs = _inputs_for(manifest)
    result = build_basic_site_graph(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        link_inputs=inputs.link_inputs,
        canonical_inputs=inputs.canonical_inputs,
        redirect_inputs=inputs.redirect_inputs,
        page_type_refs=inputs.page_type_refs,
        site_model_refs=inputs.site_model_refs,
        policy_decision_refs=[f"policy:{manifest.id}:graph"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: GraphFixtureManifest,
    profile: str,
    result: GraphBuildResult,
) -> GraphFixtureRunReport:
    report = result.report
    return GraphFixtureRunReport(
        id=f"graph-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        manifest_ref=report.manifest_ref,
        node_refs=report.node_refs,
        edge_refs=report.edge_refs,
        provenance_refs=report.provenance_refs,
        watermark_ref=report.watermark_ref,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> GraphFixtureRunReport:
    manifest = GraphFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_graph_fixture(manifest, profile=profile)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: "
            f"{report.completion_result.value}"
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
    parser = argparse.ArgumentParser(prog="veracrawl-graph")
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
