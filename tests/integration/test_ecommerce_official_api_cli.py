from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch

from veracrawl.cli.ecommerce_official_api import run_fixture
from veracrawl.contracts.enums import CompletenessResult


def test_ecommerce_official_api_cli_records_credentials_required(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    for name in [
        "AMAZON_CREATORS_API_ENDPOINT",
        "AMAZON_CREATORS_API_BEARER_TOKEN",
        "AMAZON_CREATORS_API_KEY",
        "EBAY_ACCESS_TOKEN",
        "EBAY_CLIENT_ID",
        "EBAY_CLIENT_SECRET",
    ]:
        monkeypatch.delenv(name, raising=False)

    out = tmp_path / "out"
    result = run_fixture(
        Path("tests/fixtures/us-ecommerce-official-api-product-availability"),
        profile="target",
        out=out,
        dotenv=tmp_path / "missing.env",
    )

    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["operator_status"] == "ecommerce_official_api_credentials_required"
    assert summary["blocked_site_count"] == 2
