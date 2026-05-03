from __future__ import annotations

import json

import pytest

from veracrawl.cli.contracts import main


def test_contracts_cli_validate_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "contracts" in payload
