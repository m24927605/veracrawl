"""Result publication and export runtime fixture runner CLI."""

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
    ResultPublicationExportFailureType,
)
from veracrawl.contracts.publication import ResultPublicationExportFixtureManifest
from veracrawl.evidence.live_verification import run_live_evidence_verification_runtime
from veracrawl.extract.schema_runtime import run_schema_extraction_runtime
from veracrawl.publish.result_runtime import (
    ResultPublicationExportRuntimeResult,
    run_result_publication_export_runtime,
)


class ResultPublicationFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    live_evidence_runtime_report_ref: Ref | None = None
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_manifest_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    publication_report_refs: list[Ref] = Field(default_factory=list)
    published_output_refs: list[Ref] = Field(default_factory=list)
    output_manifest_refs: list[Ref] = Field(default_factory=list)
    result_api_snapshot_refs: list[Ref] = Field(default_factory=list)
    export_target_spec_refs: list[Ref] = Field(default_factory=list)
    export_job_refs: list[Ref] = Field(default_factory=list)
    export_attempt_refs: list[Ref] = Field(default_factory=list)
    delivery_receipt_refs: list[Ref] = Field(default_factory=list)
    withdrawal_job_refs: list[Ref] = Field(default_factory=list)
    withdrawal_attempt_refs: list[Ref] = Field(default_factory=list)
    correction_record_refs: list[Ref] = Field(default_factory=list)
    destination_object_mapping_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    direct_export_bypass_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ResultPublicationExportFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _to_run_report(
    *,
    manifest: ResultPublicationExportFixtureManifest,
    profile: str,
    result: ResultPublicationExportRuntimeResult,
) -> ResultPublicationFixtureRunReport:
    report = result.report
    return ResultPublicationFixtureRunReport(
        id=f"result-publication-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        live_evidence_runtime_report_ref=report.live_evidence_runtime_report_ref,
        extraction_candidate_refs=report.extraction_candidate_refs,
        evidence_coverage_refs=report.evidence_coverage_refs,
        evidence_packet_refs=report.evidence_packet_refs,
        evidence_manifest_refs=report.evidence_manifest_refs,
        verification_decision_refs=report.verification_decision_refs,
        review_decision_refs=report.review_decision_refs,
        publication_report_refs=report.publication_report_refs,
        published_output_refs=report.published_output_refs,
        output_manifest_refs=report.output_manifest_refs,
        result_api_snapshot_refs=report.result_api_snapshot_refs,
        export_target_spec_refs=report.export_target_spec_refs,
        export_job_refs=report.export_job_refs,
        export_attempt_refs=report.export_attempt_refs,
        delivery_receipt_refs=report.delivery_receipt_refs,
        withdrawal_job_refs=report.withdrawal_job_refs,
        withdrawal_attempt_refs=report.withdrawal_attempt_refs,
        correction_record_refs=report.correction_record_refs,
        destination_object_mapping_refs=report.destination_object_mapping_refs,
        policy_decision_refs=report.policy_decision_refs,
        privacy_lifecycle_refs=report.privacy_lifecycle_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        direct_export_bypass_refs=report.direct_export_bypass_refs,
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
) -> ResultPublicationFixtureRunReport:
    manifest = ResultPublicationExportFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)

    if manifest.scenario == "result-publication-missing-live-evidence":
        result = run_result_publication_export_runtime(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            live_evidence_runtime_report_ref=None,
            candidate=None,
            evidence=None,
            verification=None,
            review=None,
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
            live_evidence = run_live_evidence_verification_runtime(
                fixture_id=f"{manifest.id}-live-evidence",
                scenario="live-evidence-verification-success",
                schema_extraction_runtime_report_ref=schema_result.report.id,
                candidate=schema_result.candidate,
                normalized_document_ref=normalization.normalized_document.id,
                source_artifact_ref=normalization.normalized_document.raw_artifact_ref,
                source_anchor_refs=schema_result.report.source_anchor_refs,
            )
            if live_evidence.report.completion_result != CompletenessResult.PASS:
                raise ValueError(f"fixture {manifest.id} live evidence prerequisite failed")
            result = run_result_publication_export_runtime(
                fixture_id=manifest.id,
                scenario=manifest.scenario,
                live_evidence_runtime_report_ref=live_evidence.report.id,
                candidate=schema_result.candidate,
                evidence=live_evidence.evidence,
                verification=live_evidence.verification,
                review=live_evidence.review,
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
    parser = argparse.ArgumentParser(prog="veracrawl-result-publication")
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
