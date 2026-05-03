from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.contracts.enums import CompletenessResult, LiveNormalizationFailureType
from veracrawl.normalize.live_runtime import (
    LiveNormalizationRuntimeResult,
    run_live_normalization_runtime,
)


def _run_success(
    *,
    fixture_id: str = "live-normalization-listing-success",
    raw_html: str = (
        "<!doctype html><html><body><main><h1>Static fixture</h1>"
        "<a href='/static/detail'>Detail</a></main></body></html>"
    ),
) -> LiveNormalizationRuntimeResult:
    return run_live_normalization_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        source_url="http://example.test/static/basic",
        raw_artifact_ref=f"artifact:{fixture_id}:raw",
        raw_html=raw_html,
        source_adapter_result_ref=f"source-result:{fixture_id}:source",
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{fixture_id}"
        ),
        browser_snapshot_runtime_report_ref=f"browser-snapshot-runtime-report:{fixture_id}",
    )


def test_live_normalization_success_records_derived_context_without_publication() -> None:
    result = _run_success()
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert result.normalization is not None
    assert report.live_http_acquisition_report_ref
    assert report.structured_source_adapters_runtime_report_ref
    assert report.browser_snapshot_runtime_report_ref
    assert report.normalized_document_refs
    assert report.normalization_manifest_refs
    assert report.anchor_map_refs
    assert report.source_anchor_refs
    assert report.link_provenance_refs
    assert report.link_analysis_refs
    assert report.page_type_classification_refs
    assert report.site_model_refs
    assert report.derived_context_refs == [
        result.normalization.page_type.id,
        result.normalization.site_model.id,
    ]
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def test_live_normalization_linkless_page_records_no_link_analysis() -> None:
    result = _run_success(
        fixture_id="live-normalization-detail-success",
        raw_html="<html><body><article>Detail page</article></body></html>",
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.link_provenance_refs == []
    assert result.report.link_analysis_refs == [
        "link-analysis:live-normalization-detail-success:no-outbound-links"
    ]


def test_live_normalization_missing_upstream_is_typed() -> None:
    result = run_live_normalization_runtime(
        fixture_id="live-normalization-missing-upstream",
        scenario="live-normalization-missing-upstream",
        source_url="http://example.test/static/basic",
        raw_artifact_ref="artifact:missing-upstream:raw",
        raw_html="<html><body>content</body></html>",
        source_adapter_result_ref="source-result:missing-upstream",
        live_http_acquisition_report_ref=None,
        structured_source_adapters_runtime_report_ref=None,
        browser_snapshot_runtime_report_ref=None,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == LiveNormalizationFailureType.MISSING_UPSTREAM
    assert result.report.missing_ref_fields == ["upstream_report_refs"]


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("live-normalization-empty-content", LiveNormalizationFailureType.EMPTY_CONTENT),
        ("live-normalization-missing-anchor-map", LiveNormalizationFailureType.MISSING_ANCHOR_MAP),
        ("live-normalization-missing-site-model", LiveNormalizationFailureType.MISSING_SITE_MODEL),
        ("live-normalization-replay-mismatch", LiveNormalizationFailureType.REPLAY_MISMATCH),
    ],
)
def test_live_normalization_negative_scenarios_are_typed(
    scenario: str,
    failure: LiveNormalizationFailureType,
) -> None:
    result = run_live_normalization_runtime(
        fixture_id=scenario,
        scenario=scenario,
        source_url="http://example.test/static/basic",
        raw_artifact_ref=f"artifact:{scenario}:raw",
        raw_html="<html><body><h1>Content</h1></body></html>",
        source_adapter_result_ref=f"source-result:{scenario}:source",
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{scenario}",
        structured_source_adapters_runtime_report_ref=(
            f"structured-source-adapters-runtime-report:{scenario}"
        ),
        browser_snapshot_runtime_report_ref=f"browser-snapshot-runtime-report:{scenario}",
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields


def test_live_normalization_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/normalize/live_runtime.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert all(not name.startswith("veracrawl.adapters") for name in imports)
