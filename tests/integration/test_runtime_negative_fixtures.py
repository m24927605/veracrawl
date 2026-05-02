from __future__ import annotations

from pathlib import Path

from tests.helpers.runtime_fixture_assertions import assert_negative_runtime_report
from veracrawl.cli.runtime import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_negative_runtime_fixtures_do_not_publish(tmp_path: Path) -> None:
    expectations = {
        "runtime-blocked-source": ("source_blocked", CompletenessResult.FAIL),
        "runtime-missing-evidence": ("missing_evidence", CompletenessResult.NEEDS_REVIEW),
        "runtime-verification-conflict": ("verification_conflict", CompletenessResult.FAIL),
        "runtime-adapter-mismatch": ("adapter_mismatch", CompletenessResult.FAIL),
        "runtime-replay-gap": ("replay_gap", CompletenessResult.FAIL),
        "runtime-boundary-violation": ("owner_boundary_violation", CompletenessResult.FAIL),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_negative_runtime_report(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
