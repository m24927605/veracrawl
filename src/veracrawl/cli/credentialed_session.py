"""Credentialed session runtime fixture runner CLI."""

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
from veracrawl.browser.snapshot_runtime import run_browser_snapshot_runtime
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    CompletenessResult,
    CredentialedSessionFailureType,
)
from veracrawl.contracts.security_privacy import CredentialedSessionFixtureManifest
from veracrawl.contracts.source_runtime import StructuredSourceAdapterRecord
from veracrawl.fetch.credentialed_session import (
    CredentialedSessionRuntimeResult,
    run_credentialed_session_runtime,
)
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.fetch.structured_source import run_structured_source_adapters_runtime
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.ports.session import CredentialedSessionAdapterPort
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


class CredentialedSessionFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    live_http_acquisition_report_ref: Ref | None = None
    browser_snapshot_runtime_report_ref: Ref | None = None
    credential_scope_refs: list[Ref] = Field(default_factory=list)
    authorized_origin_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    credential_use_audit_refs: list[Ref] = Field(default_factory=list)
    session_adapter_result_refs: list[Ref] = Field(default_factory=list)
    session_state_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    redacted_artifact_refs: list[Ref] = Field(default_factory=list)
    redacted_replay_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    adapter_native_state_canonical_refs: list[Ref] = Field(default_factory=list)
    failure_type: CredentialedSessionFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _http_adapter(*, fixture_id: str, target_url: str) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=8192,
        timeout_ms=1000,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _browser_adapter(
    *,
    fixture_id: str,
    target_url: str,
    origin: str,
) -> BrowserSourceAdapterPort:
    sandbox_policy = build_browser_sandbox_policy(fixture_id=fixture_id, origin=origin)
    adapter_module = importlib.import_module("veracrawl.adapters.browser.deterministic")
    return cast(
        BrowserSourceAdapterPort,
        adapter_module.DeterministicBrowserObservationAdapter(
            fixture_id=fixture_id,
            target_url=target_url,
            sandbox_policy=sandbox_policy,
            side_effect_class=BrowserSideEffectClass.READ_ONLY,
        ),
    )


def _session_adapter() -> CredentialedSessionAdapterPort:
    adapter_module = importlib.import_module("veracrawl.adapters.session.deterministic")
    return cast(
        CredentialedSessionAdapterPort,
        adapter_module.DeterministicCredentialedSessionAdapter(),
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


def _prerequisite_refs(
    *,
    fixture_id: str,
    origin: str,
    state_root: Path,
    profile: str,
) -> tuple[Ref, Ref]:
    live_fixture_id = f"{fixture_id}-live-http"
    live_url = f"{origin}/static/basic"
    live_result = execute_live_http_acquisition(
        fixture_id=live_fixture_id,
        scenario="success",
        target_url=live_url,
        store=ReferencePersistenceStore(state_root / "live-http"),
        adapter=_http_adapter(fixture_id=live_fixture_id, target_url=live_url),
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

    browser_fixture_id = f"{fixture_id}-browser-snapshot"
    browser_url = f"{origin}/browser"
    sandbox_policy = build_browser_sandbox_policy(fixture_id=browser_fixture_id, origin=origin)
    browser_result = run_browser_snapshot_runtime(
        fixture_id=browser_fixture_id,
        scenario="browser-snapshot-success",
        target_url=browser_url,
        adapter=_browser_adapter(
            fixture_id=browser_fixture_id,
            target_url=browser_url,
            origin=origin,
        ),
        sandbox_policy=sandbox_policy,
        side_effect_class=BrowserSideEffectClass.READ_ONLY,
        live_http_acquisition_report_ref=live_result.report.id,
        structured_source_adapters_runtime_report_ref=structured_result.report.id,
    )
    if browser_result.report.completion_result != CompletenessResult.PASS:
        raise ValueError(f"fixture {fixture_id} browser snapshot prerequisite failed")
    return live_result.report.id, browser_result.report.id


def _to_run_report(
    *,
    manifest: CredentialedSessionFixtureManifest,
    profile: str,
    result: CredentialedSessionRuntimeResult,
) -> CredentialedSessionFixtureRunReport:
    report = result.report
    return CredentialedSessionFixtureRunReport(
        id=f"credentialed-session-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        live_http_acquisition_report_ref=report.live_http_acquisition_report_ref,
        browser_snapshot_runtime_report_ref=report.browser_snapshot_runtime_report_ref,
        credential_scope_refs=report.credential_scope_refs,
        authorized_origin_refs=report.authorized_origin_refs,
        approval_decision_refs=report.approval_decision_refs,
        credential_use_audit_refs=report.credential_use_audit_refs,
        session_adapter_result_refs=report.session_adapter_result_refs,
        session_state_refs=report.session_state_refs,
        redaction_map_refs=report.redaction_map_refs,
        redacted_artifact_refs=report.redacted_artifact_refs,
        redacted_replay_refs=report.redacted_replay_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
        raw_secret_leak_refs=report.raw_secret_leak_refs,
        adapter_native_state_canonical_refs=report.adapter_native_state_canonical_refs,
        failure_type=report.failure_type,
        diagnostics=report.diagnostics,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> CredentialedSessionFixtureRunReport:
    manifest = CredentialedSessionFixtureManifest.model_validate(
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
        live_http_ref, browser_snapshot_ref = _prerequisite_refs(
            fixture_id=manifest.id,
            origin=origin,
            state_root=state_root,
            profile=profile,
        )
        result = run_credentialed_session_runtime(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            target_origin=origin,
            adapter=_session_adapter(),
            live_http_acquisition_report_ref=live_http_ref,
            browser_snapshot_runtime_report_ref=browser_snapshot_ref,
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
    parser = argparse.ArgumentParser(prog="veracrawl-credentialed-session")
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
