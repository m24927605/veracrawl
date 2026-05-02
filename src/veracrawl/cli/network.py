"""Network and browser acquisition fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from veracrawl.browser.observation import (
    build_browser_sandbox_policy,
    execute_browser_observation_acquisition,
)
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import BrowserSideEffectClass, CompletenessResult
from veracrawl.contracts.network import NetworkFixtureManifest
from veracrawl.fetch.network_acquisition import (
    build_network_request,
    execute_http_network_acquisition,
    url_origin,
)
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort


class NetworkFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    acquisition_type: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    network_request_ref: Ref | None = None
    network_response_ref: Ref | None = None
    redirect_hop_refs: list[Ref] = Field(default_factory=list)
    browser_step_ref: Ref | None = None
    source_acquisition_report_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _to_run_report(
    *,
    fixture_id: str,
    scenario: str,
    acquisition_type: str,
    profile: str,
    report_id: str,
    report: Any,
) -> NetworkFixtureRunReport:
    return NetworkFixtureRunReport(
        id=report_id,
        fixture_id=fixture_id,
        scenario=scenario,
        acquisition_type=acquisition_type,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        network_request_ref=report.network_request_ref,
        network_response_ref=report.network_response_ref,
        redirect_hop_refs=report.redirect_hop_refs,
        browser_step_ref=report.browser_step_ref,
        source_acquisition_report_ref=report.source_acquisition_report_ref,
        artifact_refs=report.artifact_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        recovery_report_refs=report.recovery_report_refs,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def _run_http_fixture(
    manifest: NetworkFixtureManifest,
    *,
    profile: str,
    target_url: str,
    egress_allowlist: list[str],
    allow_private_network: bool,
) -> NetworkFixtureRunReport:
    size_budget = 64 if manifest.scenario == "size-budget" else 8192
    timeout_ms = 1 if manifest.scenario == "timeout" else 1000
    request = build_network_request(
        fixture_id=manifest.id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{manifest.id}:network"],
        size_budget_bytes=size_budget,
        timeout_ms=timeout_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    adapter = cast(
        NetworkSourceAdapterPort,
        adapter_module.StdlibHttpSourceAdapter(request),
    )
    outcome = execute_http_network_acquisition(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        target_url=target_url,
        adapter=adapter,
        egress_allowlist=egress_allowlist,
        allow_private_network=allow_private_network,
        size_budget_bytes=size_budget,
        timeout_ms=timeout_ms,
    )
    return _to_run_report(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        acquisition_type=manifest.acquisition_type,
        profile=profile,
        report_id=f"network-run-report:{manifest.id}",
        report=outcome.report,
    )


def _run_browser_fixture(
    manifest: NetworkFixtureManifest,
    *,
    profile: str,
    target_url: str,
    origin: str,
) -> NetworkFixtureRunReport:
    sandbox_policy = build_browser_sandbox_policy(fixture_id=manifest.id, origin=origin)
    side_effect = (
        BrowserSideEffectClass.DELETE
        if manifest.scenario == "browser-unsafe-side-effect"
        else BrowserSideEffectClass.READ_ONLY
    )
    adapter_module = importlib.import_module("veracrawl.adapters.browser.deterministic")
    adapter = cast(
        BrowserSourceAdapterPort,
        adapter_module.DeterministicBrowserObservationAdapter(
            fixture_id=manifest.id,
            target_url=target_url,
            sandbox_policy=sandbox_policy,
            side_effect_class=side_effect,
        ),
    )
    outcome = execute_browser_observation_acquisition(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        target_url=target_url,
        adapter=adapter,
        sandbox_policy=sandbox_policy,
        side_effect_class=side_effect,
    )
    return _to_run_report(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        acquisition_type=manifest.acquisition_type,
        profile=profile,
        report_id=f"network-run-report:{manifest.id}",
        report=outcome.report,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> NetworkFixtureRunReport:
    manifest = NetworkFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    server_module = importlib.import_module("veracrawl.adapters.network.local_benchmark")
    if manifest.scenario == "egress-denied":
        target_url = "http://example.invalid/blocked"
        report = _run_http_fixture(
            manifest,
            profile=profile,
            target_url=target_url,
            egress_allowlist=["http://allowed.invalid"],
            allow_private_network=False,
        )
    elif manifest.scenario == "private-denied":
        target_url = "http://127.0.0.1:1/private"
        report = _run_http_fixture(
            manifest,
            profile=profile,
            target_url=target_url,
            egress_allowlist=[url_origin(target_url)],
            allow_private_network=False,
        )
    else:
        with server_module.LocalBenchmarkServer() as server:
            origin = str(server.origin)
            target_url = f"{origin}{manifest.path}"
            if manifest.acquisition_type == "browser":
                report = _run_browser_fixture(
                    manifest,
                    profile=profile,
                    target_url=target_url,
                    origin=origin,
                )
            else:
                report = _run_http_fixture(
                    manifest,
                    profile=profile,
                    target_url=target_url,
                    egress_allowlist=[origin],
                    allow_private_network=True,
                )

    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-network")
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
