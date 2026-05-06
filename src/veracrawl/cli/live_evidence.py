"""Live evidence and verification runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.cli.schema_extraction import _live_normalization_result
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveEvidenceVerificationFailureType,
)
from veracrawl.contracts.evidence import LiveEvidenceVerificationFixtureManifest
from veracrawl.evidence.live_verification import (
    LiveEvidenceVerificationRuntimeResult,
    run_live_evidence_verification_runtime,
)
from veracrawl.extract.schema_runtime import run_schema_extraction_runtime
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class LiveEvidenceFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    schema_extraction_runtime_report_ref: Ref | None = None
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    evidence_manifest_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    conflict_record_refs: list[Ref] = Field(default_factory=list)
    contradiction_record_refs: list[Ref] = Field(default_factory=list)
    freshness_refs: list[Ref] = Field(default_factory=list)
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)
    agent_reasoning_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    publication_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: LiveEvidenceVerificationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _to_run_report(
    *,
    manifest: LiveEvidenceVerificationFixtureManifest,
    profile: str,
    result: LiveEvidenceVerificationRuntimeResult,
) -> LiveEvidenceFixtureRunReport:
    report = result.report
    return LiveEvidenceFixtureRunReport(
        id=f"live-evidence-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        schema_extraction_runtime_report_ref=report.schema_extraction_runtime_report_ref,
        extraction_candidate_refs=report.extraction_candidate_refs,
        normalized_document_refs=report.normalized_document_refs,
        source_anchor_refs=report.source_anchor_refs,
        evidence_coverage_refs=report.evidence_coverage_refs,
        evidence_packet_refs=report.evidence_packet_refs,
        evidence_anchor_refs=report.evidence_anchor_refs,
        evidence_manifest_refs=report.evidence_manifest_refs,
        verification_decision_refs=report.verification_decision_refs,
        review_decision_refs=report.review_decision_refs,
        conflict_record_refs=report.conflict_record_refs,
        contradiction_record_refs=report.contradiction_record_refs,
        freshness_refs=report.freshness_refs,
        graph_signal_refs=report.graph_signal_refs,
        memory_refs=report.memory_refs,
        agent_reasoning_refs=report.agent_reasoning_refs,
        policy_decision_refs=report.policy_decision_refs,
        privacy_lifecycle_refs=report.privacy_lifecycle_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        publication_refs=report.publication_refs,
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
) -> LiveEvidenceFixtureRunReport:
    manifest = LiveEvidenceVerificationFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)

    if manifest.scenario == "live-evidence-verification-missing-schema-extraction":
        result = run_live_evidence_verification_runtime(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            schema_extraction_runtime_report_ref=None,
            candidate=None,
            normalized_document_ref=f"normalized:{manifest.id}:missing",
            source_artifact_ref=f"artifact:{manifest.id}:raw",
            source_anchor_refs=[],
        )
    else:
        server_module = importlib.import_module("veracrawl.adapters.network.local_benchmark")
        with server_module.LocalBenchmarkServer() as server:
            live_normalization = _live_normalization_result(
                fixture_id=manifest.id,
                path=manifest.path,
                origin=str(server.origin),
                state_root=state_root,
                profile=profile,
            )
            if live_normalization.normalization is None:
                raise ValueError(f"fixture {manifest.id} missing live normalization result")
            normalization = live_normalization.normalization
            schema_result = run_schema_extraction_runtime(
                fixture_id=f"{manifest.id}-schema-extraction",
                scenario="schema-extraction-record-success",
                live_normalization_runtime_report_ref=live_normalization.report.id,
                normalization=normalization,
                schema_ref=manifest.schema_ref,
            )
            if schema_result.report.completion_result != CompletenessResult.PASS:
                raise ValueError(f"fixture {manifest.id} schema extraction prerequisite failed")
            if schema_result.candidate is None:
                raise ValueError(f"fixture {manifest.id} missing schema extraction candidate")
            result = run_live_evidence_verification_runtime(
                fixture_id=manifest.id,
                scenario=manifest.scenario,
                schema_extraction_runtime_report_ref=schema_result.report.id,
                candidate=schema_result.candidate,
                normalized_document_ref=normalization.normalized_document.id,
                source_artifact_ref=normalization.normalized_document.raw_artifact_ref,
                source_anchor_refs=schema_result.report.source_anchor_refs,
            )

    report = _to_run_report(manifest=manifest, profile=profile, result=result)
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
    parser = argparse.ArgumentParser(prog="veracrawl-live-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-live-evidence"):
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
