from __future__ import annotations

from pathlib import Path

from tests.helpers.source_fixture_assertions import assert_source_success
from veracrawl.cli.source import run_fixture


def test_source_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "source-http-success",
        "source-sitemap-success",
        "source-rss-success",
        "source-api-success",
        "source-document-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_source_success(report)
    document = run_fixture(
        fixtures_root / "source-document-success",
        profile="target",
        out=tmp_path / "source-document-success-2",
    )
    assert document.document_artifact_ref
