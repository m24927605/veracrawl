from __future__ import annotations

from pathlib import Path

from tests.helpers.network_fixture_assertions import assert_network_negative
from veracrawl.cli.network import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_network_browser_negative_fixtures_produce_typed_outcomes(tmp_path: Path) -> None:
    expectations = {
        "network-robots-blocked": ("robots_blocked", CompletenessResult.FAIL),
        "network-private-denied": ("private_network_denied", CompletenessResult.FAIL),
        "network-egress-denied": ("egress_denied", CompletenessResult.FAIL),
        "network-rate-budget": ("rate_budget_exceeded", CompletenessResult.NEEDS_REVIEW),
        "network-size-budget": ("size_budget_exceeded", CompletenessResult.FAIL),
        "network-redirect-denied": ("redirect_denied", CompletenessResult.FAIL),
        "network-timeout": ("network_timeout", CompletenessResult.FAIL),
        "network-browser-unsafe-side-effect": (
            "unsafe_browser_side_effect",
            CompletenessResult.FAIL,
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, completion_result) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_network_negative(
            report,
            operator_status=operator_status,
            completion_result=completion_result,
        )
