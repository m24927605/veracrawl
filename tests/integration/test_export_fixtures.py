from __future__ import annotations

from pathlib import Path

from tests.helpers.export_fixture_assertions import assert_export_negative, assert_export_success
from veracrawl.cli.export import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_export_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "export-file-success",
        "export-api-success",
        "export-correction-withdrawal-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_export_success(report)


def test_export_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "export-missing-receipt": ("missing_delivery_receipt", CompletenessResult.FAIL),
        "duplicate-export-idempotency": ("duplicate_idempotency", CompletenessResult.FAIL),
        "withdrawal-missing-mapping": ("withdrawal_mapping_missing", CompletenessResult.FAIL),
        "destination-unsupported-withdrawal": (
            "destination_unsupported",
            CompletenessResult.NEEDS_REVIEW,
        ),
        "correction-without-withdrawal": ("correction_without_withdrawal", CompletenessResult.FAIL),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_export_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
