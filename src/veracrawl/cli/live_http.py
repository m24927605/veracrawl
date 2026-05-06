"""Live HTTP acquisition fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, LiveHttpAcquisitionFailureType
from veracrawl.contracts.network import LiveHttpAcquisitionFixtureManifest
from veracrawl.fetch.live_http import (
    LiveHttpAcquisitionRuntimeResult,
    execute_live_http_acquisition,
)
from veracrawl.fetch.network_acquisition import build_network_request, url_origin
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class LiveHttpFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    run_control_report_ref: Ref | None = None
    production_persistence_report_ref: Ref | None = None
    network_request_ref: Ref | None = None
    network_response_ref: Ref | None = None
    redirect_hop_refs: list[Ref] = Field(default_factory=list)
    source_acquisition_report_ref: Ref | None = None
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: LiveHttpAcquisitionFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _http_adapter(
    *,
    fixture_id: str,
    target_url: str,
    size_budget_bytes: int = 8192,
    timeout_ms: int = 1000,
) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=size_budget_bytes,
        timeout_ms=timeout_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _to_run_report(
    *,
    manifest: LiveHttpAcquisitionFixtureManifest,
    profile: str,
    result: LiveHttpAcquisitionRuntimeResult,
) -> LiveHttpFixtureRunReport:
    report = result.report
    return LiveHttpFixtureRunReport(
        id=f"live-http-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        run_control_report_ref=report.run_control_report_ref,
        production_persistence_report_ref=report.production_persistence_report_ref,
        network_request_ref=report.network_request_ref,
        network_response_ref=report.network_response_ref,
        redirect_hop_refs=report.redirect_hop_refs,
        source_acquisition_report_ref=report.source_acquisition_report_ref,
        source_adapter_result_refs=report.source_adapter_result_refs,
        fetch_attempt_refs=report.fetch_attempt_refs,
        fetch_result_refs=report.fetch_result_refs,
        page_snapshot_refs=report.page_snapshot_refs,
        source_observation_refs=report.source_observation_refs,
        artifact_refs=report.artifact_refs,
        content_hash_refs=report.content_hash_refs,
        canonical_url_refs=report.canonical_url_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        failure_type=report.failure_type,
        diagnostics=report.diagnostics,
    )


def _run_fixture_with_url(
    manifest: LiveHttpAcquisitionFixtureManifest,
    *,
    profile: str,
    state_root: Path,
    target_url: str,
    egress_allowlist: list[str],
    allow_private_network: bool,
    adapter: NetworkSourceAdapterPort | None,
) -> LiveHttpFixtureRunReport:
    result = execute_live_http_acquisition(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        target_url=target_url,
        store=ReferencePersistenceStore(state_root),
        adapter=adapter,
        profile=profile,
        egress_allowlist=egress_allowlist,
        allow_private_network=allow_private_network,
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> LiveHttpFixtureRunReport:
    manifest = LiveHttpAcquisitionFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)

    if manifest.scenario == "scope-denied":
        target_url = "http://example.invalid/blocked"
        report = _run_fixture_with_url(
            manifest,
            profile=profile,
            state_root=state_root,
            target_url=target_url,
            egress_allowlist=["http://allowed.invalid"],
            allow_private_network=False,
            adapter=_http_adapter(fixture_id=manifest.id, target_url=target_url),
        )
    elif manifest.scenario == "private-denied":
        target_url = "http://127.0.0.1:1/private"
        report = _run_fixture_with_url(
            manifest,
            profile=profile,
            state_root=state_root,
            target_url=target_url,
            egress_allowlist=[url_origin(target_url)],
            allow_private_network=False,
            adapter=_http_adapter(fixture_id=manifest.id, target_url=target_url),
        )
    elif manifest.negative_case:
        target_url = f"http://example.invalid/{manifest.scenario}"
        report = _run_fixture_with_url(
            manifest,
            profile=profile,
            state_root=state_root,
            target_url=target_url,
            egress_allowlist=[],
            allow_private_network=False,
            adapter=None,
        )
    else:
        server_module = importlib.import_module("veracrawl.adapters.network.local_benchmark")
        with server_module.LocalBenchmarkServer() as server:
            origin = str(server.origin)
            target_url = f"{origin}{manifest.path}"
            report = _run_fixture_with_url(
                manifest,
                profile=profile,
                state_root=state_root,
                target_url=target_url,
                egress_allowlist=[origin],
                allow_private_network=True,
                adapter=_http_adapter(fixture_id=manifest.id, target_url=target_url),
            )

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
    parser = argparse.ArgumentParser(prog="veracrawl-live-http")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-live-http"):
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
