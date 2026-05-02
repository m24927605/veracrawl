from __future__ import annotations

from pathlib import Path

from tests.helpers.source_fixture_assertions import assert_source_negative
from veracrawl.cli.source import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_source_negative_fixtures_produce_typed_outcomes(tmp_path: Path) -> None:
    expectations = {
        "source-blocked": ("source_blocked", CompletenessResult.FAIL),
        "source-rate-limited": ("source_rate_limited", CompletenessResult.NEEDS_REVIEW),
        "source-adapter-mismatch": ("adapter_mismatch", CompletenessResult.FAIL),
        "source-malformed-response": ("malformed_response", CompletenessResult.FAIL),
        "source-retry-exhausted": ("retry_exhausted", CompletenessResult.FAIL),
        "source-missing-artifact": ("missing_raw_artifact", CompletenessResult.FAIL),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_source_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
