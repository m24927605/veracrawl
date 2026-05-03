"""Temporal KG identity projection fixture runner CLI."""

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
    TemporalKGAdjudicationDecisionType,
    TemporalKGConflictType,
    TemporalKGFailureType,
    TemporalKGStatus,
)
from veracrawl.contracts.graph import TemporalKGFixtureManifest
from veracrawl.graph.temporal_kg import (
    TemporalKGRuntimeResult,
    run_temporal_kg_runtime_gate,
)


class TemporalKGFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    identity_refs: list[Ref] = Field(default_factory=list)
    projection_record_refs: list[Ref] = Field(default_factory=list)
    adjudication_record_refs: list[Ref] = Field(default_factory=list)
    identity_statuses: list[TemporalKGStatus] = Field(default_factory=list)
    projection_statuses: list[TemporalKGStatus] = Field(default_factory=list)
    adjudication_conflict_types: list[TemporalKGConflictType] = Field(default_factory=list)
    adjudication_decision_types: list[TemporalKGAdjudicationDecisionType] = Field(
        default_factory=list
    )
    conflict_record_refs: list[Ref] = Field(default_factory=list)
    supersession_refs: list[Ref] = Field(default_factory=list)
    invalidation_refs: list[Ref] = Field(default_factory=list)
    source_verified_fact_refs: list[Ref] = Field(default_factory=list)
    source_published_output_refs: list[Ref] = Field(default_factory=list)
    source_event_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    failure_type: TemporalKGFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    temporal_kg_as_evidence_refs: list[Ref] = Field(default_factory=list)
    provisional_identity_refs: list[Ref] = Field(default_factory=list)
    missing_identity_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_canonical_source_refs: list[Ref] = Field(default_factory=list)
    missing_bitemporal_refs: list[Ref] = Field(default_factory=list)
    false_merge_without_adjudication_refs: list[Ref] = Field(default_factory=list)
    false_split_without_supersession_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_temporal_kg_fixture(
    manifest: TemporalKGFixtureManifest,
    *,
    profile: str,
) -> TemporalKGFixtureRunReport:
    result = run_temporal_kg_runtime_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:temporal-kg"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: TemporalKGFixtureManifest,
    profile: str,
    result: TemporalKGRuntimeResult,
) -> TemporalKGFixtureRunReport:
    report = result.report
    return TemporalKGFixtureRunReport(
        id=f"temporal-kg-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        identity_refs=report.identity_refs,
        projection_record_refs=report.projection_record_refs,
        adjudication_record_refs=report.adjudication_record_refs,
        identity_statuses=[identity.status for identity in result.identities],
        projection_statuses=[record.status for record in result.projection_records],
        adjudication_conflict_types=[
            adjudication.conflict_type for adjudication in result.adjudications
        ],
        adjudication_decision_types=[
            adjudication.decision_type for adjudication in result.adjudications
        ],
        conflict_record_refs=report.conflict_record_refs,
        supersession_refs=report.supersession_refs,
        invalidation_refs=report.invalidation_refs,
        source_verified_fact_refs=report.source_verified_fact_refs,
        source_published_output_refs=report.source_published_output_refs,
        source_event_refs=report.source_event_refs,
        evidence_packet_refs=report.evidence_packet_refs,
        projection_watermark_refs=report.projection_watermark_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        failure_type=report.failure_type,
        failure_report_refs=report.failure_report_refs,
        temporal_kg_as_evidence_refs=report.temporal_kg_as_evidence_refs,
        provisional_identity_refs=report.provisional_identity_refs,
        missing_identity_evidence_refs=report.missing_identity_evidence_refs,
        missing_canonical_source_refs=report.missing_canonical_source_refs,
        missing_bitemporal_refs=report.missing_bitemporal_refs,
        false_merge_without_adjudication_refs=(
            report.false_merge_without_adjudication_refs
        ),
        false_split_without_supersession_refs=(
            report.false_split_without_supersession_refs
        ),
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> TemporalKGFixtureRunReport:
    manifest = TemporalKGFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_temporal_kg_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result}"
        )
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
    parser = argparse.ArgumentParser(prog="veracrawl-temporal-kg")
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
