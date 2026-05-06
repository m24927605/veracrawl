"""Normalize/extract fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import Field, ValidationError

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, ProcessFailureType
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.processing import NormalizeExtractReport, ProcessFixtureManifest
from veracrawl.extract.candidates import build_extraction_strategy, create_anchored_candidate
from veracrawl.fetch.network_acquisition import (
    build_network_request,
    execute_http_network_acquisition,
    url_origin,
)
from veracrawl.normalize.pipeline import normalize_html_document
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class ProcessFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    network_acquisition_report_ref: Ref | None = None
    normalized_document_ref: Ref | None = None
    normalization_manifest_ref: Ref | None = None
    anchor_map_ref: Ref | None = None
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    page_type_classification_ref: Ref | None = None
    site_model_ref: Ref | None = None
    extraction_strategy_ref: Ref | None = None
    extraction_candidate_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    publication_refs: list[Ref] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _failure_report(
    *,
    fixture_id: str,
    failure_type: ProcessFailureType,
    network_report_ref: Ref | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> NormalizeExtractReport:
    completion = (
        CompletenessResult.NEEDS_REVIEW
        if failure_type == ProcessFailureType.EMPTY_NORMALIZED_CONTENT
        else CompletenessResult.FAIL
    )
    return NormalizeExtractReport(
        id=f"process-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        network_acquisition_report_ref=network_report_ref,
        policy_decision_refs=policy_decision_refs or [f"policy:{fixture_id}:process"],
        failure_report_refs=[f"process-failure:{fixture_id}:{failure_type.value}"],
        missing_ref_fields=[failure_type.value],
        operator_status=failure_type.value,
        completion_result=completion,
    )


def _to_run_report(
    *,
    fixture_id: str,
    scenario: str,
    profile: str,
    report: NormalizeExtractReport,
) -> ProcessFixtureRunReport:
    return ProcessFixtureRunReport(
        id=f"process-run-report:{fixture_id}",
        fixture_id=fixture_id,
        scenario=scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        network_acquisition_report_ref=report.network_acquisition_report_ref,
        normalized_document_ref=report.normalized_document_ref,
        normalization_manifest_ref=report.normalization_manifest_ref,
        anchor_map_ref=report.anchor_map_ref,
        link_provenance_refs=report.link_provenance_refs,
        page_type_classification_ref=report.page_type_classification_ref,
        site_model_ref=report.site_model_ref,
        extraction_strategy_ref=report.extraction_strategy_ref,
        extraction_candidate_ref=report.extraction_candidate_ref,
        artifact_refs=report.artifact_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def _http_adapter_for(request: NetworkRequest) -> NetworkSourceAdapterPort:
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _acquire_raw_html(
    *,
    fixture_id: str,
    target_url: str,
) -> tuple[str, Ref, NormalizeExtractReport | None, list[Ref]]:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=8192,
        timeout_ms=1000,
    )
    outcome = execute_http_network_acquisition(
        fixture_id=fixture_id,
        scenario="http-success",
        target_url=target_url,
        adapter=_http_adapter_for(request),
        egress_allowlist=[url_origin(target_url)],
        allow_private_network=True,
    )
    if outcome.network_result is None or outcome.network_result.response.raw_artifact_ref is None:
        failure = _failure_report(
            fixture_id=fixture_id,
            failure_type=ProcessFailureType.MISSING_RAW_ARTIFACT,
            network_report_ref=outcome.report.id,
        )
        return "", "", failure, outcome.report.policy_decision_refs
    return (
        outcome.network_result.body_text,
        outcome.network_result.response.raw_artifact_ref,
        None,
        outcome.report.policy_decision_refs,
    )


def run_process_fixture(
    manifest: ProcessFixtureManifest,
    *,
    profile: str,
    target_url: str,
) -> ProcessFixtureRunReport:
    if manifest.scenario == "missing-raw":
        return _to_run_report(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            profile=profile,
            report=_failure_report(
                fixture_id=manifest.id,
                failure_type=ProcessFailureType.MISSING_RAW_ARTIFACT,
            ),
        )

    raw_html, raw_artifact_ref, acquisition_failure, policy_refs = _acquire_raw_html(
        fixture_id=manifest.id,
        target_url=target_url,
    )
    if acquisition_failure:
        return _to_run_report(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            profile=profile,
            report=acquisition_failure,
        )
    if manifest.scenario == "empty-content":
        raw_html = ""
    if not raw_html.strip():
        return _to_run_report(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            profile=profile,
            report=_failure_report(
                fixture_id=manifest.id,
                failure_type=ProcessFailureType.EMPTY_NORMALIZED_CONTENT,
                network_report_ref=f"network-acquisition:{manifest.id}",
                policy_decision_refs=policy_refs,
            ),
        )

    normalized = normalize_html_document(
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        source_adapter_result_ref=f"source-result:cmd:{manifest.id}:source",
        source_url=target_url,
        raw_artifact_ref=raw_artifact_ref,
        raw_html=raw_html,
        policy_decision_refs=policy_refs,
    )
    strategy = build_extraction_strategy(
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        normalized_document=normalized.normalized_document,
        policy_decision_refs=policy_refs,
    )
    try:
        candidate = create_anchored_candidate(
            fixture_id=manifest.id,
            run_ref=f"run:{manifest.id}",
            normalized_document=normalized.normalized_document,
            anchors=normalized.anchors,
            strategy=strategy,
            link_count=len(normalized.link_provenance),
            omit_anchor_for="summary" if manifest.scenario == "anchor-gap" else None,
        )
    except (ValueError, ValidationError):
        report = _failure_report(
            fixture_id=manifest.id,
            failure_type=ProcessFailureType.CANDIDATE_ANCHOR_GAP,
            network_report_ref=f"network-acquisition:{manifest.id}",
            policy_decision_refs=policy_refs,
        )
        return _to_run_report(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            profile=profile,
            report=report,
        )

    report = NormalizeExtractReport(
        id=f"process-report:{manifest.id}",
        run_ref=f"run:{manifest.id}",
        network_acquisition_report_ref=f"network-acquisition:{manifest.id}",
        normalized_document_ref=normalized.normalized_document.id,
        normalization_manifest_ref=normalized.manifest.id,
        anchor_map_ref=normalized.anchor_map.id,
        link_provenance_refs=[link.id for link in normalized.link_provenance],
        page_type_classification_ref=normalized.page_type.id,
        site_model_ref=normalized.site_model.id,
        extraction_strategy_ref=strategy.id,
        extraction_candidate_ref=candidate.id,
        artifact_refs=normalized.artifact_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{manifest.id}:process"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:process"],
        outbox_refs=[f"outbox:{manifest.id}:process"],
        operator_status="process_completed",
        completion_result=CompletenessResult.PASS,
    )
    return _to_run_report(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        report=report,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> ProcessFixtureRunReport:
    manifest = ProcessFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    server_module = importlib.import_module("veracrawl.adapters.network.local_benchmark")
    if manifest.scenario == "missing-raw":
        report = run_process_fixture(manifest, profile=profile, target_url="http://missing.local")
    else:
        with server_module.LocalBenchmarkServer() as server:
            target_url = f"{server.origin}{manifest.path}"
            report = run_process_fixture(manifest, profile=profile, target_url=target_url)
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-process")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-process"):
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
