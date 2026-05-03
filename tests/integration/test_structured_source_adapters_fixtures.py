from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.structured_source import run_fixture
from veracrawl.contracts.enums import CompletenessResult

STRUCTURED_SOURCE_FIXTURES = [
    "structured-source-adapters-success",
    "structured-source-adapters-policy-denied",
    "structured-source-adapters-malformed-source",
    "structured-source-adapters-unsupported-adapter",
    "structured-source-adapters-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", STRUCTURED_SOURCE_FIXTURES)
def test_structured_source_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.source_adapter_record_refs
        assert report.source_adapter_result_refs
        assert report.discovered_url_refs
        assert report.api_payload_refs
        assert report.document_artifact_refs
        assert report.file_artifact_refs
        assert report.artifact_refs
        assert report.evidence_seed_refs
        assert report.replay_bundle_ref
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields


def test_structured_source_success_covers_five_adapter_types(tmp_path: Path) -> None:
    report = run_fixture(
        Path("tests/fixtures/structured-source-adapters-success"),
        profile="target",
        out=tmp_path / "success",
    )

    assert report.completion_result == CompletenessResult.PASS
    assert len(set(report.verified_adapter_types)) == 5
