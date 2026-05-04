"""Live extraction-quality evidence aggregator for the 073 production gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.benchmarks.production_grade import ProductionGradeGateResult
from veracrawl.contracts.common import Ref, TimestampedModel, stable_hash
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    ProductionGateReport,
    ProductionGradeClosureManifest,
)

_QUALITY_CAPABILITIES = (
    "field_oracles",
    "precision_recall_release_block",
    "publication_readiness",
)
_QUALITY_THRESHOLDS = {
    "precision": 0.98,
    "recall": 0.90,
    "f1": 0.94,
    "critical_field_precision": 0.99,
    "repair_success_rate": 0.80,
}


class LiveExtractionQualityInputReport(TimestampedModel):
    id: str
    report_kind: str
    source_path: str
    completion_result: str
    operator_status: str | None = None
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class LiveExtractionQualityEvidenceSummary(TimestampedModel):
    id: str
    fixture_id: str
    input_report_refs: list[Ref] = Field(default_factory=list)
    missing_report_kinds: list[str] = Field(default_factory=list)
    non_passing_report_refs: list[Ref] = Field(default_factory=list)
    threshold_diagnostics: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    artifact_ref_count: int
    source_anchor_ref_count: int
    content_hash_ref_count: int
    replay_bundle_ref_count: int


@dataclass(frozen=True)
class LiveExtractionQualityGateResult:
    gate_result: ProductionGradeGateResult
    input_reports: list[LiveExtractionQualityInputReport]
    evidence_summary: LiveExtractionQualityEvidenceSummary


def run_live_extraction_quality_gate(
    *,
    manifest: ProductionGradeClosureManifest,
    profile: str,
    input_report_paths: list[Path],
) -> LiveExtractionQualityGateResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    if manifest.gate_type != "extraction_quality":
        raise ValueError("live extraction quality runner requires extraction_quality gate")

    input_reports = [
        _load_input_report(path, index)
        for index, path in enumerate(input_report_paths, start=1)
    ]
    report_by_kind = {report.report_kind: report for report in input_reports}
    diagnostics = _quality_diagnostics(report_by_kind)
    refs = _collect_refs(input_reports)
    evidence_summary = LiveExtractionQualityEvidenceSummary(
        id=f"live-extraction-quality-summary:{manifest.id}",
        fixture_id=manifest.id,
        input_report_refs=[report.id for report in input_reports],
        missing_report_kinds=[
            kind for kind in _required_report_kinds() if kind not in report_by_kind
        ],
        non_passing_report_refs=[
            report.id
            for report in input_reports
            if report.completion_result != CompletenessResult.PASS.value
        ],
        threshold_diagnostics=diagnostics,
        metrics=_combined_metrics(report_by_kind),
        artifact_ref_count=len(refs["artifact_refs"]),
        source_anchor_ref_count=len(refs["source_anchor_refs"]),
        content_hash_ref_count=len(refs["content_hash_refs"]),
        replay_bundle_ref_count=len(refs["replay_bundle_refs"]),
    )
    report = _build_quality_gate_report(
        manifest=manifest,
        input_reports=input_reports,
        evidence_summary=evidence_summary,
        refs=refs,
        diagnostics=diagnostics,
    )
    return LiveExtractionQualityGateResult(
        gate_result=ProductionGradeGateResult(
            report=report,
            discovery_plans=[],
            candidate_targets=[],
            discovery_entry_points=[],
            discovery_approval_decisions=[],
            acquisition_attempts=[],
            authorized_sources=[],
            capability_matrices=[],
            release_decisions=[],
            false_ready_guards=[],
            release_blockers=[],
            release_reports=[],
        ),
        input_reports=input_reports,
        evidence_summary=evidence_summary,
    )


def _load_input_report(path: Path, index: int) -> LiveExtractionQualityInputReport:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    report_kind = _report_kind(data, path)
    metrics = _report_metrics(report_kind, data)
    report_id = str(data.get("id") or f"quality-input-report:{index}:{path.stem}")
    return LiveExtractionQualityInputReport(
        id=report_id,
        report_kind=report_kind,
        source_path=str(path),
        completion_result=str(data.get("completion_result", "")),
        operator_status=(
            str(data["operator_status"]) if data.get("operator_status") is not None else None
        ),
        metrics=metrics,
        artifact_refs=_string_list(data.get("artifact_refs")),
        source_anchor_refs=_string_list(data.get("source_anchor_refs")),
        content_hash_refs=_string_list(data.get("content_hash_refs")),
        evidence_packet_refs=_string_list(data.get("evidence_packet_refs")),
        verification_decision_refs=_string_list(data.get("verification_decision_refs")),
        publication_gate_refs=_string_list(data.get("publication_gate_refs")),
        policy_decision_refs=_string_list(data.get("policy_decision_refs")),
        command_record_refs=_string_list(data.get("command_record_refs")),
        event_cursor_refs=_string_list(data.get("event_cursor_refs")),
        outbox_refs=_string_list(data.get("outbox_refs")),
        replay_bundle_refs=_string_list(data.get("replay_bundle_refs")),
        diagnostics=_string_list(data.get("diagnostics")),
    )


def _report_kind(data: dict[str, Any], path: Path) -> str:
    keys = set(data)
    if {"schema_count", "expected_field_count", "accepted_field_count"} <= keys:
        return "field_oracle"
    if {"precision", "recall", "f1", "critical_field_precision"} <= keys:
        return "precision_recall"
    if {"release_decision", "observed_quality_gate_count", "stability_run_count"} <= keys:
        return "quality_release"
    if {"repair_success_rate", "unsafe_bypass_rate", "unresolved_critical_rate"} <= keys:
        return "repair_quality"
    if {"declared_target_count", "passing_target_count", "pattern_family_count"} <= keys:
        return "real_world_quality"
    raise ValueError(f"unrecognized quality evidence report: {path}")


def _report_metrics(report_kind: str, data: dict[str, Any]) -> dict[str, float | int | str]:
    metric_keys = {
        "field_oracle": (
            "schema_count",
            "expected_field_count",
            "accepted_field_count",
            "rejected_field_count",
        ),
        "precision_recall": (
            "precision",
            "recall",
            "f1",
            "critical_field_precision",
            "unsupported_rate",
        ),
        "quality_release": (
            "observed_quality_gate_count",
            "stability_run_count",
            "release_decision",
        ),
        "repair_quality": (
            "repair_success_rate",
            "unsafe_bypass_rate",
            "unresolved_critical_rate",
        ),
        "real_world_quality": (
            "declared_target_count",
            "passing_target_count",
            "origin_count",
            "pattern_family_count",
        ),
    }[report_kind]
    return {
        key: value
        for key in metric_keys
        if isinstance((value := data.get(key)), int | float | str)
    }


def _quality_diagnostics(
    report_by_kind: dict[str, LiveExtractionQualityInputReport],
) -> list[str]:
    diagnostics: list[str] = []
    for required in _required_report_kinds():
        if required not in report_by_kind:
            diagnostics.append(f"missing quality input report: {required}")
    for report in report_by_kind.values():
        if report.completion_result != CompletenessResult.PASS.value:
            diagnostics.append(f"{report.report_kind} report is not pass")
    field_oracle = report_by_kind.get("field_oracle")
    if field_oracle:
        if _metric(field_oracle, "schema_count") < 8:
            diagnostics.append("field oracle schema_count below 8")
        if _metric(field_oracle, "expected_field_count") < 200:
            diagnostics.append("field oracle expected_field_count below 200")
        if _metric(field_oracle, "accepted_field_count") < _metric(
            field_oracle,
            "expected_field_count",
        ):
            diagnostics.append("field oracle did not accept every expected field")
    precision = report_by_kind.get("precision_recall")
    if precision:
        for metric, threshold in (
            ("precision", _QUALITY_THRESHOLDS["precision"]),
            ("recall", _QUALITY_THRESHOLDS["recall"]),
            ("f1", _QUALITY_THRESHOLDS["f1"]),
            ("critical_field_precision", _QUALITY_THRESHOLDS["critical_field_precision"]),
        ):
            if _metric(precision, metric) < threshold:
                diagnostics.append(f"{metric} below threshold {threshold}")
    release = report_by_kind.get("quality_release")
    if release:
        if release.metrics.get("release_decision") != "release_ready":
            diagnostics.append("quality release decision is not release_ready")
        if _metric(release, "observed_quality_gate_count") < 6:
            diagnostics.append("quality release observed gate count below 6")
        if _metric(release, "stability_run_count") < 3:
            diagnostics.append("quality release stability run count below 3")
    repair = report_by_kind.get("repair_quality")
    if repair:
        if _metric(repair, "repair_success_rate") < _QUALITY_THRESHOLDS[
            "repair_success_rate"
        ]:
            diagnostics.append("repair success rate below threshold")
        if _metric(repair, "unsafe_bypass_rate") != 0:
            diagnostics.append("repair unsafe bypass rate is non-zero")
        if _metric(repair, "unresolved_critical_rate") != 0:
            diagnostics.append("repair unresolved critical rate is non-zero")
    real_world = report_by_kind.get("real_world_quality")
    if real_world:
        if _metric(real_world, "declared_target_count") < 40:
            diagnostics.append("real-world quality target count below 40")
        if _metric(real_world, "passing_target_count") < _metric(
            real_world,
            "declared_target_count",
        ):
            diagnostics.append("not all real-world quality targets passed")
        if _metric(real_world, "origin_count") < 15:
            diagnostics.append("real-world quality origin count below 15")
        if _metric(real_world, "pattern_family_count") < 10:
            diagnostics.append("real-world quality pattern family count below 10")
    return diagnostics


def _build_quality_gate_report(
    *,
    manifest: ProductionGradeClosureManifest,
    input_reports: list[LiveExtractionQualityInputReport],
    evidence_summary: LiveExtractionQualityEvidenceSummary,
    refs: dict[str, list[Ref]],
    diagnostics: list[str],
) -> ProductionGateReport:
    fixture_id = manifest.id
    has_required_refs = all(
        refs[name]
        for name in (
            "artifact_refs",
            "source_anchor_refs",
            "content_hash_refs",
            "replay_bundle_refs",
        )
    )
    completion = (
        CompletenessResult.PASS
        if not diagnostics
        and not evidence_summary.missing_report_kinds
        and not evidence_summary.non_passing_report_refs
        and has_required_refs
        else CompletenessResult.NEEDS_REVIEW
    )
    common = {
        "id": f"production-gate-report:{fixture_id}",
        "fixture_id": fixture_id,
        "gate_type": manifest.gate_type,
        "run_ref": f"run:{fixture_id}:live-extraction-quality",
        "capability_refs": [
            f"capability:{manifest.gate_type}:{name}" for name in _QUALITY_CAPABILITIES
        ],
        "lower_gate_report_refs": [report.id for report in input_reports],
        "source_profile_refs": [profile.id for profile in manifest.source_profiles],
        "artifact_refs": refs["artifact_refs"],
        "source_anchor_refs": refs["source_anchor_refs"],
        "content_hash_refs": refs["content_hash_refs"],
        "evidence_packet_refs": refs["evidence_packet_refs"]
        or [f"evidence-packet:{fixture_id}:live-quality"],
        "verification_decision_refs": refs["verification_decision_refs"]
        or [f"verification-decision:{fixture_id}:live-quality"],
        "publication_gate_refs": refs["publication_gate_refs"]
        or [f"publication-gate:{fixture_id}:blocked-until-release"],
        "policy_decision_refs": refs["policy_decision_refs"] or _policy_refs(fixture_id),
        "command_record_refs": refs["command_record_refs"]
        or [f"command:{fixture_id}:record-live-extraction-quality"],
        "event_cursor_refs": refs["event_cursor_refs"]
        or [f"event-cursor:{fixture_id}:live-extraction-quality-recorded"],
        "outbox_refs": refs["outbox_refs"] or [f"outbox:{fixture_id}:live-extraction-quality"],
        "replay_bundle_refs": refs["replay_bundle_refs"],
        "metrics": evidence_summary.metrics
        | {
            "input_report_count": len(input_reports),
            "artifact_ref_count": evidence_summary.artifact_ref_count,
            "source_anchor_ref_count": evidence_summary.source_anchor_ref_count,
            "content_hash_ref_count": evidence_summary.content_hash_ref_count,
            "replay_bundle_ref_count": evidence_summary.replay_bundle_ref_count,
        },
        "operator_status": (
            manifest.expected_operator_status
            if completion == CompletenessResult.PASS
            else "production_extraction_quality_needs_review"
        ),
        "completion_result": completion,
    }
    if completion == CompletenessResult.PASS:
        return ProductionGateReport(**common)
    return ProductionGateReport(
        **common,
        release_blocker_refs=[f"release-blocker:{fixture_id}:live-extraction-quality"],
        diagnostics=diagnostics or ["live extraction quality evidence is incomplete"],
    )


def _collect_refs(
    input_reports: list[LiveExtractionQualityInputReport],
) -> dict[str, list[Ref]]:
    names = (
        "artifact_refs",
        "source_anchor_refs",
        "content_hash_refs",
        "evidence_packet_refs",
        "verification_decision_refs",
        "publication_gate_refs",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "replay_bundle_refs",
    )
    return {
        name: sorted(
            {
                ref
                for report in input_reports
                for ref in getattr(report, name)
            }
        )
        for name in names
    }


def _combined_metrics(
    report_by_kind: dict[str, LiveExtractionQualityInputReport],
) -> dict[str, float | int | str]:
    combined: dict[str, float | int | str] = {}
    for kind, report in sorted(report_by_kind.items()):
        for key, value in report.metrics.items():
            combined[f"{kind}.{key}"] = value
    combined["quality_report_hash"] = stable_hash(
        {kind: report.metrics for kind, report in sorted(report_by_kind.items())}
    )
    return combined


def _metric(report: LiveExtractionQualityInputReport, key: str) -> float:
    value = report.metrics.get(key)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _required_report_kinds() -> tuple[str, ...]:
    return (
        "field_oracle",
        "precision_recall",
        "quality_release",
        "repair_quality",
        "real_world_quality",
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _policy_refs(fixture_id: str) -> list[Ref]:
    return [
        f"policy:{fixture_id}:source-scope",
        f"policy:{fixture_id}:robots",
        f"policy:{fixture_id}:no-bypass",
    ]
