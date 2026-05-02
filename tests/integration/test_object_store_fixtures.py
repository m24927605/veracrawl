from __future__ import annotations

from pathlib import Path

from tests.helpers.object_store_fixture_assertions import (
    assert_object_store_negative,
    assert_object_store_runtime_unavailable,
)
from veracrawl.cli.object_store import run_fixture


def test_object_store_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "s3-object-store-runtime-unavailable",
        profile="target",
        out=tmp_path / "s3-object-store-runtime-unavailable",
    )
    assert_object_store_runtime_unavailable(report)


def test_object_store_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "object-store-missing-digest": "object_store_missing_digest",
        "object-store-missing-read-after-write": "object_store_missing_read_after_write",
        "object-store-missing-delete-marker": "object_store_missing_delete_marker",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_object_store_negative(report, operator_status=operator_status)
