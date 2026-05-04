from __future__ import annotations

import json
from pathlib import Path

from veracrawl.benchmarks.acquisition_live import run_live_acquisition_gate
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import ProductionGradeClosureManifest


def _manifest() -> ProductionGradeClosureManifest:
    path = Path("tests/fixtures/production-acquisition-escalation-live-evidence/manifest.yaml")
    return ProductionGradeClosureManifest.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _write_report(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    common: dict[str, object] = {
        "id": f"{name}-report:unit",
        "completion_result": "pass",
        "operator_status": f"{name}_completed",
        "artifact_refs": [f"artifact:{name}:{index}" for index in range(6)],
        "source_anchor_refs": [f"source-anchor:{name}:{index}" for index in range(6)],
        "content_hash_refs": [f"hash:{name}:{index}" for index in range(6)],
        "policy_decision_refs": [f"policy:{name}:1"],
        "command_record_refs": [f"command:{name}:1"],
        "event_cursor_refs": [f"event-cursor:{name}:1"],
        "outbox_refs": [f"outbox:{name}:1"],
        "replay_bundle_refs": [f"replay-bundle:{name}:1"],
    }
    path = tmp_path / f"{name}.json"
    path.write_text(
        json.dumps(common | payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _passing_reports(tmp_path: Path) -> list[Path]:
    return [
        _write_report(
            tmp_path,
            "ai-http",
            {
                "model_call_trace_refs": ["model-call:1"],
                "site_observation_refs": ["site-observation:1"],
            },
        ),
        _write_report(
            tmp_path,
            "live-http",
            {
                "benchmark_corpus_ref": "benchmark:1",
                "site_observation_refs": ["site-observation:1"],
                "source_observation_refs": ["source-observation:1"],
            },
        ),
        _write_report(
            tmp_path,
            "browser",
            {
                "target_count": 8,
                "browser_required_pass_count": 8,
                "recovered_fragment_count": 8,
                "http_only_missing_count": 8,
                "dom_artifact_refs": ["artifact:browser:dom"],
                "screenshot_artifact_refs": ["artifact:browser:screenshot"],
            },
        ),
    ]


def test_live_acquisition_passes_with_http_and_browser_evidence(tmp_path: Path) -> None:
    result = run_live_acquisition_gate(
        manifest=_manifest(),
        profile="production",
        input_report_paths=_passing_reports(tmp_path),
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.PASS
    assert len(result.gate_result.acquisition_attempts) == 3
    assert result.evidence_summary.artifact_ref_count >= 14
    assert report.acquisition_attempt_refs
    assert report.lower_gate_report_refs == [item.id for item in result.input_reports]


def test_live_acquisition_blocks_low_browser_recovery(tmp_path: Path) -> None:
    reports = _passing_reports(tmp_path)
    browser_report = json.loads(reports[2].read_text(encoding="utf-8"))
    browser_report["recovered_fragment_count"] = 1
    reports[2].write_text(json.dumps(browser_report), encoding="utf-8")

    result = run_live_acquisition_gate(
        manifest=_manifest(),
        profile="production",
        input_report_paths=reports,
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.release_blocker_refs
    assert any("browser recovered fragment count below 8" in item for item in report.diagnostics)
