from __future__ import annotations

import json
from pathlib import Path

from veracrawl.benchmarks.extraction_quality_live import run_live_extraction_quality_gate
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import ProductionGradeClosureManifest


def _manifest() -> ProductionGradeClosureManifest:
    path = Path("tests/fixtures/production-extraction-quality-live-evidence/manifest.yaml")
    return ProductionGradeClosureManifest.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _write_report(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    common: dict[str, object] = {
        "id": f"{name}-report:unit",
        "completion_result": "pass",
        "operator_status": f"{name}_completed",
        "artifact_refs": [f"artifact:{name}:1"],
        "source_anchor_refs": [f"source-anchor:{name}:1"],
        "content_hash_refs": [f"hash:{name}:1"],
        "evidence_packet_refs": [f"evidence-packet:{name}:1"],
        "verification_decision_refs": [f"verification-decision:{name}:1"],
        "publication_gate_refs": [f"publication-gate:{name}:1"],
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
            "field-oracle",
            {
                "schema_count": 8,
                "expected_field_count": 200,
                "accepted_field_count": 200,
                "rejected_field_count": 0,
            },
        ),
        _write_report(
            tmp_path,
            "precision-recall",
            {
                "precision": 0.99,
                "recall": 0.95,
                "f1": 0.97,
                "critical_field_precision": 1.0,
                "unsupported_rate": 0.0,
            },
        ),
        _write_report(
            tmp_path,
            "quality-release",
            {
                "release_decision": "release_ready",
                "observed_quality_gate_count": 6,
                "stability_run_count": 3,
            },
        ),
        _write_report(
            tmp_path,
            "repair-quality",
            {
                "repair_success_rate": 0.9,
                "unsafe_bypass_rate": 0.0,
                "unresolved_critical_rate": 0.0,
            },
        ),
        _write_report(
            tmp_path,
            "real-world-quality",
            {
                "declared_target_count": 40,
                "passing_target_count": 40,
                "origin_count": 20,
                "pattern_family_count": 12,
            },
        ),
    ]


def test_live_extraction_quality_passes_with_parsed_quality_reports(
    tmp_path: Path,
) -> None:
    result = run_live_extraction_quality_gate(
        manifest=_manifest(),
        profile="production",
        input_report_paths=_passing_reports(tmp_path),
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.PASS
    assert len(result.input_reports) == 5
    assert result.evidence_summary.artifact_ref_count == 5
    assert result.evidence_summary.source_anchor_ref_count == 5
    assert result.evidence_summary.replay_bundle_ref_count == 5
    assert report.lower_gate_report_refs == [item.id for item in result.input_reports]


def test_live_extraction_quality_blocks_low_precision(tmp_path: Path) -> None:
    reports = _passing_reports(tmp_path)
    precision_report = json.loads(reports[1].read_text(encoding="utf-8"))
    precision_report["precision"] = 0.5
    reports[1].write_text(json.dumps(precision_report), encoding="utf-8")

    result = run_live_extraction_quality_gate(
        manifest=_manifest(),
        profile="production",
        input_report_paths=reports,
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.release_blocker_refs
    assert any("precision below threshold" in item for item in report.diagnostics)
