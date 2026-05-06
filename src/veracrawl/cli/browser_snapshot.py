"""Browser snapshot runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from veracrawl.browser.observation import build_browser_sandbox_policy
from veracrawl.browser.snapshot_runtime import (
    BrowserSnapshotRuntimeResult,
    run_browser_snapshot_runtime,
)
from veracrawl.contracts.browser import BrowserSnapshotFixtureManifest
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    BrowserSnapshotFailureType,
    CompletenessResult,
)
from veracrawl.contracts.source_runtime import StructuredSourceAdapterRecord
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.fetch.structured_source import run_structured_source_adapters_runtime
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class BrowserSnapshotFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    live_http_acquisition_report_ref: Ref | None = None
    structured_source_adapters_runtime_report_ref: Ref | None = None
    network_acquisition_report_ref: Ref | None = None
    source_acquisition_report_ref: Ref | None = None
    sandbox_policy_ref: Ref | None = None
    browser_step_ref: Ref | None = None
    dom_artifact_refs: list[Ref] = Field(default_factory=list)
    screenshot_artifact_refs: list[Ref] = Field(default_factory=list)
    network_trace_refs: list[Ref] = Field(default_factory=list)
    console_log_refs: list[Ref] = Field(default_factory=list)
    timing_refs: list[Ref] = Field(default_factory=list)
    browser_budget_refs: list[Ref] = Field(default_factory=list)
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: BrowserSnapshotFailureType | None = None
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


def _browser_adapter(
    *,
    fixture_id: str,
    target_url: str,
    origin: str,
    side_effect_class: BrowserSideEffectClass,
) -> BrowserSourceAdapterPort:
    sandbox_policy = build_browser_sandbox_policy(fixture_id=fixture_id, origin=origin)
    adapter_module = importlib.import_module("veracrawl.adapters.browser.deterministic")
    return cast(
        BrowserSourceAdapterPort,
        adapter_module.DeterministicBrowserObservationAdapter(
            fixture_id=fixture_id,
            target_url=target_url,
            sandbox_policy=sandbox_policy,
            side_effect_class=side_effect_class,
        ),
    )


def _structured_records(fixture_id: str) -> list[StructuredSourceAdapterRecord]:
    root = Path(__file__).resolve().parents[3]
    sources_root = root / "tests" / "fixtures" / "structured-source-adapters-success" / "sources"
    module = importlib.import_module("veracrawl.adapters.sources.structured_runtime")
    builder = cast(
        Callable[..., list[StructuredSourceAdapterRecord]],
        module.__dict__["build_structured_source_adapter_records"],
    )
    return builder(
        fixture_id,
        sources_root=sources_root,
        policy_decision_refs=[f"policy:{fixture_id}:structured-source"],
    )


def _prerequisite_report_refs(
    *,
    fixture_id: str,
    origin: str,
    state_root: Path,
    profile: str,
) -> tuple[Ref, Ref]:
    live_fixture_id = f"{fixture_id}-live-http"
    live_target_url = f"{origin}/static/basic"
    live_result = execute_live_http_acquisition(
        fixture_id=live_fixture_id,
        scenario="success",
        target_url=live_target_url,
        store=ReferencePersistenceStore(state_root / "live-http"),
        adapter=_http_adapter(fixture_id=live_fixture_id, target_url=live_target_url),
        profile=profile,
        egress_allowlist=[origin],
        allow_private_network=True,
    )
    if live_result.report.completion_result != CompletenessResult.PASS:
        raise ValueError(f"fixture {fixture_id} live HTTP prerequisite failed")

    structured_fixture_id = f"{fixture_id}-structured-source"
    structured_result = run_structured_source_adapters_runtime(
        fixture_id=structured_fixture_id,
        scenario="structured-source-adapters-success",
        adapter_records=_structured_records(structured_fixture_id),
        policy_decision_refs=[f"policy:{structured_fixture_id}:structured-source"],
    )
    if structured_result.report.completion_result != CompletenessResult.PASS:
        raise ValueError(f"fixture {fixture_id} structured source prerequisite failed")
    return live_result.report.id, structured_result.report.id


def _to_run_report(
    *,
    manifest: BrowserSnapshotFixtureManifest,
    profile: str,
    result: BrowserSnapshotRuntimeResult,
) -> BrowserSnapshotFixtureRunReport:
    report = result.report
    return BrowserSnapshotFixtureRunReport(
        id=f"browser-snapshot-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        live_http_acquisition_report_ref=report.live_http_acquisition_report_ref,
        structured_source_adapters_runtime_report_ref=(
            report.structured_source_adapters_runtime_report_ref
        ),
        network_acquisition_report_ref=report.network_acquisition_report_ref,
        source_acquisition_report_ref=report.source_acquisition_report_ref,
        sandbox_policy_ref=report.sandbox_policy_ref,
        browser_step_ref=report.browser_step_ref,
        dom_artifact_refs=report.dom_artifact_refs,
        screenshot_artifact_refs=report.screenshot_artifact_refs,
        network_trace_refs=report.network_trace_refs,
        console_log_refs=report.console_log_refs,
        timing_refs=report.timing_refs,
        browser_budget_refs=report.browser_budget_refs,
        prompt_taint_boundary_refs=report.prompt_taint_boundary_refs,
        artifact_refs=report.artifact_refs,
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


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> BrowserSnapshotFixtureRunReport:
    manifest = BrowserSnapshotFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)

    server_module = importlib.import_module("veracrawl.adapters.network.local_benchmark")
    with server_module.LocalBenchmarkServer() as server:
        origin = str(server.origin)
        live_http_ref, structured_source_ref = _prerequisite_report_refs(
            fixture_id=manifest.id,
            origin=origin,
            state_root=state_root,
            profile=profile,
        )
        target_url = f"{origin}{manifest.path}"
        policy_origin = origin
        if manifest.scenario == "browser-snapshot-egress-denied":
            target_url = "http://example.invalid/browser"
        side_effect = (
            BrowserSideEffectClass.DELETE
            if manifest.scenario == "browser-snapshot-unsafe-interaction"
            else BrowserSideEffectClass.READ_ONLY
        )
        sandbox_policy = build_browser_sandbox_policy(
            fixture_id=manifest.id,
            origin=policy_origin,
        )
        adapter = _browser_adapter(
            fixture_id=manifest.id,
            target_url=target_url,
            origin=policy_origin,
            side_effect_class=side_effect,
        )
        result = run_browser_snapshot_runtime(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            target_url=target_url,
            adapter=adapter,
            sandbox_policy=sandbox_policy,
            side_effect_class=side_effect,
            live_http_acquisition_report_ref=live_http_ref,
            structured_source_adapters_runtime_report_ref=structured_source_ref,
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
    parser = argparse.ArgumentParser(prog="veracrawl-browser-snapshot")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-browser-snapshot"):
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
