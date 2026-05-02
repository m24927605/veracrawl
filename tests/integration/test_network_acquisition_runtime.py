from __future__ import annotations

from pathlib import Path

from tests.helpers.network_fixture_assertions import assert_network_success
from veracrawl.cli.network import run_fixture


def test_network_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "network-http-success",
        "network-http-redirect",
        "network-browser-readonly",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_network_success(report)
    redirect = run_fixture(
        fixtures_root / "network-http-redirect",
        profile="target",
        out=tmp_path / "network-http-redirect-2",
    )
    assert redirect.redirect_hop_refs
    browser = run_fixture(
        fixtures_root / "network-browser-readonly",
        profile="target",
        out=tmp_path / "network-browser-readonly-2",
    )
    assert browser.browser_step_ref
