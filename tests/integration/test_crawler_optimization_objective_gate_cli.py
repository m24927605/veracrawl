from __future__ import annotations

import json
from pathlib import Path

from veracrawl.cli import crawler_optimization


def test_crawler_optimization_cli_runs_objective_gate_evidence(
    tmp_path: Path,
    capsys: object,
) -> None:
    out = tmp_path / "objective-gate"
    rc = crawler_optimization.main(
        [
            "run-objective-gate",
            "tests/fixtures/crawler-optimization-success",
            "--out",
            str(out),
        ]
    )

    assert rc == 0
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["ok"] is True
    assert summary["completion_result"] == "pass"
    for name in [
        "metric_slice.json",
        "lower_optimization_integrations.json",
        "optimization_regression_release_gate.json",
        "optimization_objective_score.json",
        "agent_decision_loop_evidence.json",
        "optimization_objective_release_gate.json",
        "summary.json",
    ]:
        assert (out / name).exists()

    written_summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert written_summary["objective_release_gate_ref"] == (
        summary["objective_release_gate_ref"]
    )


def test_crawler_optimization_cli_objective_gate_rejects_negative_fixture(
    tmp_path: Path,
    capsys: object,
) -> None:
    rc = crawler_optimization.main(
        [
            "run-objective-gate",
            "tests/fixtures/crawler-optimization-missing-replay",
            "--out",
            str(tmp_path / "negative"),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["ok"] is False
    assert "passing optimization fixture" in summary["error"]
