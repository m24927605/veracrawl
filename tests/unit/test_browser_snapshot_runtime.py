from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.adapters.browser.deterministic import DeterministicBrowserObservationAdapter
from veracrawl.browser.observation import build_browser_sandbox_policy
from veracrawl.browser.snapshot_runtime import (
    BrowserSnapshotRuntimeResult,
    run_browser_snapshot_runtime,
)
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    BrowserSnapshotFailureType,
    CompletenessResult,
)


def _run_success(
    fixture_id: str = "browser-snapshot-success",
) -> BrowserSnapshotRuntimeResult:
    origin = "http://example.test"
    target_url = f"{origin}/browser"
    policy = build_browser_sandbox_policy(fixture_id=fixture_id, origin=origin)
    adapter = DeterministicBrowserObservationAdapter(
        fixture_id=fixture_id,
        target_url=target_url,
        sandbox_policy=policy,
    )
    return run_browser_snapshot_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        target_url=target_url,
        adapter=adapter,
        sandbox_policy=policy,
        side_effect_class=BrowserSideEffectClass.READ_ONLY,
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{fixture_id}"
        ),
    )


def test_browser_snapshot_success_preserves_browser_upstream_and_replay_refs() -> None:
    result = _run_success()
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert report.live_http_acquisition_report_ref
    assert report.structured_source_adapters_runtime_report_ref
    assert report.network_acquisition_report_ref
    assert report.source_acquisition_report_ref
    assert report.sandbox_policy_ref
    assert report.browser_step_ref
    assert report.dom_artifact_refs
    assert report.screenshot_artifact_refs
    assert report.network_trace_refs
    assert report.console_log_refs
    assert report.timing_refs
    assert report.browser_budget_refs
    assert report.prompt_taint_boundary_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("browser-snapshot-budget-exceeded", BrowserSnapshotFailureType.BUDGET_EXCEEDED),
        (
            "browser-snapshot-prompt-tainted-content",
            BrowserSnapshotFailureType.PROMPT_TAINTED_CONTENT,
        ),
        ("browser-snapshot-missing-artifact", BrowserSnapshotFailureType.MISSING_ARTIFACT),
        ("browser-snapshot-replay-mismatch", BrowserSnapshotFailureType.REPLAY_MISMATCH),
    ],
)
def test_browser_snapshot_direct_negative_scenarios_are_typed(
    scenario: str,
    failure: BrowserSnapshotFailureType,
) -> None:
    origin = "http://example.test"
    policy = build_browser_sandbox_policy(fixture_id=scenario, origin=origin)
    result = run_browser_snapshot_runtime(
        fixture_id=scenario,
        scenario=scenario,
        target_url=f"{origin}/browser",
        adapter=None,
        sandbox_policy=policy,
        side_effect_class=BrowserSideEffectClass.READ_ONLY,
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{scenario}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{scenario}"
        ),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields


def test_browser_snapshot_blocks_egress_outside_sandbox_allowlist() -> None:
    origin = "http://allowed.test"
    fixture_id = "browser-snapshot-egress-runtime"
    policy = build_browser_sandbox_policy(fixture_id=fixture_id, origin=origin)
    result = run_browser_snapshot_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        target_url="http://blocked.test/browser",
        adapter=None,
        sandbox_policy=policy,
        side_effect_class=BrowserSideEffectClass.READ_ONLY,
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{fixture_id}"
        ),
    )

    assert result.report.failure_type == BrowserSnapshotFailureType.EGRESS_DENIED


def test_browser_snapshot_blocks_unsafe_side_effect_before_adapter_execution() -> None:
    origin = "http://example.test"
    fixture_id = "browser-snapshot-unsafe-runtime"
    target_url = f"{origin}/browser"
    policy = build_browser_sandbox_policy(fixture_id=fixture_id, origin=origin)
    adapter = DeterministicBrowserObservationAdapter(
        fixture_id=fixture_id,
        target_url=target_url,
        sandbox_policy=policy,
        side_effect_class=BrowserSideEffectClass.DELETE,
    )
    result = run_browser_snapshot_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        target_url=target_url,
        adapter=adapter,
        sandbox_policy=policy,
        side_effect_class=BrowserSideEffectClass.DELETE,
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{fixture_id}"
        ),
    )

    assert result.report.failure_type == BrowserSnapshotFailureType.UNSAFE_INTERACTION
    assert adapter.last_result is None


def test_browser_snapshot_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/browser/snapshot_runtime.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert all(not name.startswith("veracrawl.adapters") for name in imports)
