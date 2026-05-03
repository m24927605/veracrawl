from __future__ import annotations

import ast
from pathlib import Path

from veracrawl.adapters.network.local_benchmark import LocalBenchmarkServer
from veracrawl.adapters.network.stdlib_http import StdlibHttpSourceAdapter
from veracrawl.contracts.enums import CompletenessResult, LiveHttpAcquisitionFailureType
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.fetch.network_acquisition import build_network_request, url_origin
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _adapter(fixture_id: str, target_url: str) -> StdlibHttpSourceAdapter:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=8192,
        timeout_ms=1000,
    )
    return StdlibHttpSourceAdapter(request)


def test_live_http_success_records_production_network_and_observation_refs(
    tmp_path: Path,
) -> None:
    with LocalBenchmarkServer() as server:
        origin = str(server.origin)
        target_url = f"{origin}/static/basic"
        result = execute_live_http_acquisition(
            fixture_id="live-http-success",
            scenario="success",
            target_url=target_url,
            store=ReferencePersistenceStore(tmp_path),
            adapter=_adapter("live-http-success", target_url),
            egress_allowlist=[origin],
            allow_private_network=True,
        )

    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert report.run_control_report_ref
    assert report.production_persistence_report_ref
    assert report.network_request_ref
    assert report.network_response_ref
    assert report.source_acquisition_report_ref
    assert report.source_adapter_result_refs
    assert report.fetch_attempt_refs
    assert report.fetch_result_refs
    assert report.page_snapshot_refs
    assert result.source_observation is not None
    assert report.source_observation_refs == [result.source_observation.id]
    assert report.artifact_refs
    assert report.content_hash_refs
    assert report.canonical_url_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def test_live_http_redirect_preserves_redirect_hop(tmp_path: Path) -> None:
    with LocalBenchmarkServer() as server:
        origin = str(server.origin)
        target_url = f"{origin}/redirect"
        result = execute_live_http_acquisition(
            fixture_id="live-http-redirect",
            scenario="redirect",
            target_url=target_url,
            store=ReferencePersistenceStore(tmp_path),
            adapter=_adapter("live-http-redirect", target_url),
            egress_allowlist=[origin],
            allow_private_network=True,
        )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.redirect_hop_refs


def test_live_http_private_network_denial_is_typed(tmp_path: Path) -> None:
    target_url = "http://127.0.0.1:1/private"
    result = execute_live_http_acquisition(
        fixture_id="live-http-private-denied",
        scenario="private-denied",
        target_url=target_url,
        store=ReferencePersistenceStore(tmp_path),
        adapter=_adapter("live-http-private-denied", target_url),
        egress_allowlist=[url_origin(target_url)],
        allow_private_network=False,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == LiveHttpAcquisitionFailureType.PRIVATE_NETWORK_DENIED
    assert result.report.failure_report_refs


def test_live_http_direct_source_bypass_is_blocked_without_adapter(tmp_path: Path) -> None:
    result = execute_live_http_acquisition(
        fixture_id="live-http-direct-source-bypass",
        scenario="direct-source-bypass",
        target_url="http://example.invalid/direct-source-bypass",
        store=ReferencePersistenceStore(tmp_path),
        adapter=None,
        egress_allowlist=[],
        allow_private_network=False,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == LiveHttpAcquisitionFailureType.DIRECT_SOURCE_BYPASS
    assert result.network_outcome is None


def test_live_http_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/fetch/live_http.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert all(not name.startswith("veracrawl.adapters") for name in imports)
