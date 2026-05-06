"""Production-grade crawler closure gate CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.acquisition_live import (
    LiveAcquisitionGateResult,
    run_live_acquisition_gate,
)
from veracrawl.benchmarks.authorized_source_live import (
    LiveAuthorizedSourceGateResult,
    run_live_authorized_source_gate,
)
from veracrawl.benchmarks.extraction_quality_live import (
    LiveExtractionQualityGateResult,
    run_live_extraction_quality_gate,
)
from veracrawl.benchmarks.production_grade import (
    ProductionGradeGateResult,
    run_production_grade_gate,
)
from veracrawl.contracts.production_grade import (
    ProductionGateReport,
    ProductionGradeClosureManifest,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging

_PROGRAM_GATE_TYPES = {
    "veracrawl-discovery-planner": "discovery_planning",
    "veracrawl-acquisition-escalation": "acquisition_escalation",
    "veracrawl-authorized-source": "authorized_source_access",
    "veracrawl-deep-crawl-production": "deep_crawl_production",
    "veracrawl-production-quality-gate": "extraction_quality",
    "veracrawl-production-ops-gate": "operations_reliability",
    "veracrawl-production-grade-release-gate": "production_grade_release",
}


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    gate_type: str | None = None,
    input_report_refs: list[str] | None = None,
    input_reports: list[Path] | None = None,
) -> ProductionGradeGateResult:
    manifest = ProductionGradeClosureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if gate_type is not None and manifest.gate_type != gate_type:
        raise ValueError(
            f"fixture {manifest.id} gate mismatch: {manifest.gate_type} != {gate_type}"
        )
    lower_gate_reports = [_load_gate_report(path) for path in input_reports or []]
    result = run_production_grade_gate(
        manifest=manifest,
        profile=profile,
        input_report_refs=input_report_refs,
        lower_gate_reports=lower_gate_reports,
    )
    _write_outputs(out, result)
    report = result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    return result


def run_live_authorized_source_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> LiveAuthorizedSourceGateResult:
    manifest = ProductionGradeClosureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    result = run_live_authorized_source_gate(manifest=manifest, profile=profile)
    _write_outputs(out, result.gate_result)
    _write_live_authorized_source_outputs(out, result)
    report = result.gate_result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    return result


def run_live_acquisition_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    input_reports: list[Path],
) -> LiveAcquisitionGateResult:
    manifest = ProductionGradeClosureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    result = run_live_acquisition_gate(
        manifest=manifest,
        profile=profile,
        input_report_paths=input_reports,
    )
    _write_outputs(out, result.gate_result)
    _write_live_acquisition_outputs(out, result)
    report = result.gate_result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    return result


def run_live_extraction_quality_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    input_reports: list[Path],
) -> LiveExtractionQualityGateResult:
    manifest = ProductionGradeClosureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    result = run_live_extraction_quality_gate(
        manifest=manifest,
        profile=profile,
        input_report_paths=input_reports,
    )
    _write_outputs(out, result.gate_result)
    _write_live_extraction_quality_outputs(out, result)
    report = result.gate_result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    return result


def _write_outputs(out: Path, result: ProductionGradeGateResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "production_gate_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "discovery_plans.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.discovery_plans],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "candidate_targets.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.candidate_targets],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "discovery_entry_points.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.discovery_entry_points],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "discovery_approval_decisions.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.discovery_approval_decisions],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "acquisition_attempts.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.acquisition_attempts],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "authorized_sources.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.authorized_sources],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "capability_matrices.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.capability_matrices],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "release_decisions.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.release_decisions],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "false_ready_guards.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.false_ready_guards],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "release_blockers.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.release_blockers],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "production_grade_release_reports.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.release_reports],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = result.report
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": report.completion_result.value == "pass",
                "fixture_id": report.fixture_id,
                "gate_type": report.gate_type,
                "completion_result": report.completion_result.value,
                "operator_status": report.operator_status,
                "capability_count": len(report.capability_refs),
                "lower_gate_report_count": len(report.lower_gate_report_refs),
                "release_blocker_count": len(report.release_blocker_refs),
                "replay_bundle_count": len(report.replay_bundle_refs),
                "candidate_target_count": len(result.candidate_targets),
                "discovery_entry_point_count": len(result.discovery_entry_points),
                "release_report_count": len(result.release_reports),
                "false_ready_guard_count": len(result.false_ready_guards),
                "metrics": report.metrics,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_live_authorized_source_outputs(
    out: Path,
    result: LiveAuthorizedSourceGateResult,
) -> None:
    (out / "source_fetches.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.source_fetches],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "redacted_artifacts.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.redacted_artifacts],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        {
            "live_official_api": True,
            "source_fetch_count": len(result.source_fetches),
            "redacted_artifact_count": len(result.redacted_artifacts),
        }
    )
    summary_path.write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_live_acquisition_outputs(
    out: Path,
    result: LiveAcquisitionGateResult,
) -> None:
    (out / "acquisition_input_reports.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.input_reports],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "acquisition_evidence_summary.json").write_text(
        json.dumps(
            result.evidence_summary.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        {
            "live_acquisition": True,
            "acquisition_input_report_count": len(result.input_reports),
            "artifact_ref_count": result.evidence_summary.artifact_ref_count,
            "source_anchor_ref_count": result.evidence_summary.source_anchor_ref_count,
            "content_hash_ref_count": result.evidence_summary.content_hash_ref_count,
            "replay_bundle_ref_count": result.evidence_summary.replay_bundle_ref_count,
        }
    )
    summary_path.write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_live_extraction_quality_outputs(
    out: Path,
    result: LiveExtractionQualityGateResult,
) -> None:
    (out / "quality_input_reports.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.input_reports],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "quality_evidence_summary.json").write_text(
        json.dumps(
            result.evidence_summary.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        {
            "live_extraction_quality": True,
            "quality_input_report_count": len(result.input_reports),
            "artifact_ref_count": result.evidence_summary.artifact_ref_count,
            "source_anchor_ref_count": result.evidence_summary.source_anchor_ref_count,
            "content_hash_ref_count": result.evidence_summary.content_hash_ref_count,
            "replay_bundle_ref_count": result.evidence_summary.replay_bundle_ref_count,
        }
    )
    summary_path.write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_gate_report(path: Path) -> ProductionGateReport:
    return ProductionGateReport.model_validate(_load_json_like(path))


def _gate_from_program(argv: list[str]) -> str | None:
    program = Path(argv[0]).name if argv else ""
    return _PROGRAM_GATE_TYPES.get(program)


def build_parser(default_gate: str | None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=Path(sys.argv[0]).name)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="production")
    run.add_argument("--out", required=True)
    if default_gate is None:
        run.add_argument(
            "--gate-type",
            choices=sorted(set(_PROGRAM_GATE_TYPES.values())),
            required=True,
        )
    run.add_argument("--input-report-ref", action="append", default=[])
    run.add_argument("--input-report", action="append", default=[])
    run_live = sub.add_parser("run-live")
    run_live.add_argument("fixture_dir")
    run_live.add_argument("--profile", default="production")
    run_live.add_argument("--out", required=True)
    run_live.add_argument("--input-report", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-production-grade"):
        args_list = sys.argv if argv is None else [sys.argv[0], *argv]
        default_gate = _gate_from_program(args_list)
        parser = build_parser(default_gate)
        args = parser.parse_args(argv)
        if args.command == "run":
            gate_type = default_gate or args.gate_type
            try:
                result = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                    gate_type=gate_type,
                    input_report_refs=args.input_report_ref,
                    input_reports=[Path(path) for path in args.input_report],
                )
            except (OSError, RuntimeError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            report = result.report
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "gate_type": report.gate_type,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                        "release_blocker_count": len(report.release_blocker_refs),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "run-live":
            gate_type = default_gate
            if gate_type not in {
                "acquisition_escalation",
                "authorized_source_access",
                "extraction_quality",
            }:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": (
                                "run-live is only supported by veracrawl-acquisition-escalation, "
                                "veracrawl-authorized-source, and "
                                "veracrawl-production-quality-gate"
                            ),
                        },
                        sort_keys=True,
                    )
                )
                return 1
            if gate_type == "acquisition_escalation":
                try:
                    acquisition_result = run_live_acquisition_fixture(
                        Path(args.fixture_dir),
                        profile=args.profile,
                        out=Path(args.out),
                        input_reports=[Path(path) for path in args.input_report],
                    )
                except (OSError, RuntimeError, ValueError) as exc:
                    print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                    return 1
                report = acquisition_result.gate_result.report
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "fixture_id": report.fixture_id,
                            "gate_type": report.gate_type,
                            "completion_result": report.completion_result.value,
                            "operator_status": report.operator_status,
                            "acquisition_input_report_count": len(acquisition_result.input_reports),
                            "release_blocker_count": len(report.release_blocker_refs),
                        },
                        sort_keys=True,
                    )
                )
                return 0
            if gate_type == "extraction_quality":
                try:
                    quality_result = run_live_extraction_quality_fixture(
                        Path(args.fixture_dir),
                        profile=args.profile,
                        out=Path(args.out),
                        input_reports=[Path(path) for path in args.input_report],
                    )
                except (OSError, RuntimeError, ValueError) as exc:
                    print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                    return 1
                report = quality_result.gate_result.report
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "fixture_id": report.fixture_id,
                            "gate_type": report.gate_type,
                            "completion_result": report.completion_result.value,
                            "operator_status": report.operator_status,
                            "quality_input_report_count": len(quality_result.input_reports),
                            "release_blocker_count": len(report.release_blocker_refs),
                        },
                        sort_keys=True,
                    )
                )
                return 0
            try:
                live_result = run_live_authorized_source_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            report = live_result.gate_result.report
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "gate_type": report.gate_type,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                        "source_fetch_count": len(live_result.source_fetches),
                        "redacted_artifact_count": len(live_result.redacted_artifacts),
                        "release_blocker_count": len(report.release_blocker_refs),
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
