from __future__ import annotations

from pathlib import Path

from tests.helpers.durable_fixture_assertions import assert_durable_negative
from veracrawl.cli.durable import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_durable_negative_fixtures_produce_typed_non_success_reports(tmp_path: Path) -> None:
    expectations = {
        "durable-event-gap": ("event_gap", CompletenessResult.FAIL),
        "durable-pending-outbox": ("pending_outbox", CompletenessResult.NEEDS_REVIEW),
        "durable-stale-lease": ("stale_lease", CompletenessResult.NEEDS_REVIEW),
        "durable-invalid-lease": ("invalid_lease", CompletenessResult.FAIL),
        "durable-missing-artifact": ("missing_artifact", CompletenessResult.FAIL),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_durable_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
