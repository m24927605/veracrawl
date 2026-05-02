from __future__ import annotations

import json

from veracrawl.cli.contracts import main


def test_contracts_cli_validate_json(capsys) -> None:
    assert main(["validate", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "contracts" in payload
