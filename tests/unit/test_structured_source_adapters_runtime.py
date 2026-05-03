from __future__ import annotations

import ast
from pathlib import Path

from veracrawl.adapters.sources.structured_runtime import build_structured_source_adapter_records
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    StructuredSourceAdapterFailureType,
)
from veracrawl.contracts.source_runtime import REQUIRED_STRUCTURED_SOURCE_ADAPTERS
from veracrawl.fetch.structured_source import run_structured_source_adapters_runtime


def test_structured_source_success_aggregates_all_family_refs() -> None:
    fixture_id = "structured-source-adapters-success"
    records = build_structured_source_adapter_records(
        fixture_id,
        sources_root=Path("tests/fixtures/structured-source-adapters-success/sources"),
    )
    result = run_structured_source_adapters_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        adapter_records=records,
        policy_decision_refs=[f"policy:{fixture_id}:structured-source"],
    )

    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.verified_adapter_types) == set(REQUIRED_STRUCTURED_SOURCE_ADAPTERS)
    assert report.discovered_url_refs
    assert report.api_payload_refs
    assert report.document_artifact_refs
    assert report.file_artifact_refs
    assert report.artifact_refs
    assert report.evidence_seed_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def test_structured_adapter_records_preserve_family_semantics() -> None:
    records = build_structured_source_adapter_records(
        "structured-source-adapters-success",
        sources_root=Path("tests/fixtures/structured-source-adapters-success/sources"),
    )
    by_type = {record.adapter_type: record for record in records}

    assert by_type[AdapterType.SITEMAP].discovered_url_refs
    assert by_type[AdapterType.RSS].discovered_url_refs
    assert by_type[AdapterType.API_SOURCE].api_payload_refs
    assert by_type[AdapterType.DOCUMENT_SOURCE].document_artifact_refs
    assert by_type[AdapterType.FILE_IMPORT].file_artifact_refs


def test_structured_source_negative_scenario_returns_typed_failure() -> None:
    result = run_structured_source_adapters_runtime(
        fixture_id="structured-source-adapters-replay-mismatch",
        scenario="structured-source-adapters-replay-mismatch",
        adapter_records=None,
        policy_decision_refs=["policy:structured-source"],
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == StructuredSourceAdapterFailureType.REPLAY_MISMATCH
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields == ["replay_bundle_ref"]


def test_structured_source_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/fetch/structured_source.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    assert all(not name.startswith("veracrawl.adapters") for name in imports)
