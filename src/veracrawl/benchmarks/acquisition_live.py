"""Live acquisition-escalation evidence aggregator for the 070 production gate."""

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
    AcquisitionAttemptRecord,
    ProductionGateReport,
    ProductionGradeClosureManifest,
)

_ACQUISITION_CAPABILITIES = (
    "http_acquisition",
    "browser_render_escalation",
    "source_limitation_accounting",
)


class LiveAcquisitionInputReport(TimestampedModel):
    id: str
    report_kind: str
    source_path: str
    completion_result: str
    operator_status: str | None = None
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class LiveAcquisitionEvidenceSummary(TimestampedModel):
    id: str
    fixture_id: str
    input_report_refs: list[Ref] = Field(default_factory=list)
    missing_report_kinds: list[str] = Field(default_factory=list)
    non_passing_report_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    artifact_ref_count: int
    source_anchor_ref_count: int
    content_hash_ref_count: int
    replay_bundle_ref_count: int


@dataclass(frozen=True)
class LiveAcquisitionGateResult:
    gate_result: ProductionGradeGateResult
    input_reports: list[LiveAcquisitionInputReport]
    evidence_summary: LiveAcquisitionEvidenceSummary


def run_live_acquisition_gate(
    *,
    manifest: ProductionGradeClosureManifest,
    profile: str,
    input_report_paths: list[Path],
) -> LiveAcquisitionGateResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    if manifest.gate_type != "acquisition_escalation":
        raise ValueError("live acquisition runner requires acquisition_escalation gate")

    input_reports = [
        _load_input_report(path, index)
        for index, path in enumerate(input_report_paths, start=1)
    ]
    report_by_kind = {report.report_kind: report for report in input_reports}
    diagnostics = _diagnostics(report_by_kind)
    refs = _collect_refs(input_reports)
    attempts = _build_attempts(manifest.id, report_by_kind)
    summary = LiveAcquisitionEvidenceSummary(
        id=f"live-acquisition-summary:{manifest.id}",
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
        diagnostics=diagnostics,
        metrics=_combined_metrics(report_by_kind),
        artifact_ref_count=len(refs["artifact_refs"]),
        source_anchor_ref_count=len(refs["source_anchor_refs"]),
        content_hash_ref_count=len(refs["content_hash_refs"]),
        replay_bundle_ref_count=len(refs["replay_bundle_refs"]),
    )
    report = _build_gate_report(
        manifest=manifest,
        input_reports=input_reports,
        attempts=attempts,
        summary=summary,
        refs=refs,
        diagnostics=diagnostics,
    )
    return LiveAcquisitionGateResult(
        gate_result=ProductionGradeGateResult(
            report=report,
            discovery_plans=[],
            candidate_targets=[],
            discovery_entry_points=[],
            discovery_approval_decisions=[],
            acquisition_attempts=attempts,
            authorized_sources=[],
            capability_matrices=[],
            release_decisions=[],
            false_ready_guards=[],
            release_blockers=[],
            release_reports=[],
        ),
        input_reports=input_reports,
        evidence_summary=summary,
    )


def _load_input_report(path: Path, index: int) -> LiveAcquisitionInputReport:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    report_kind = _report_kind(data, path)
    report_id = str(data.get("id") or f"acquisition-input-report:{index}:{path.stem}")
    return LiveAcquisitionInputReport(
        id=report_id,
        report_kind=report_kind,
        source_path=str(path),
        completion_result=str(data.get("completion_result", "")),
        operator_status=(
            str(data["operator_status"]) if data.get("operator_status") is not None else None
        ),
        metrics=_metrics(report_kind, data),
        artifact_refs=_string_list(data.get("artifact_refs"))
        + _string_list(data.get("dom_artifact_refs"))
        + _string_list(data.get("screenshot_artifact_refs")),
        source_anchor_refs=_string_list(data.get("source_anchor_refs")),
        content_hash_refs=_string_list(data.get("content_hash_refs"))
        + _string_list(data.get("rendered_content_hash_refs")),
        policy_decision_refs=_string_list(data.get("policy_decision_refs")),
        command_record_refs=_string_list(data.get("command_record_refs")),
        event_cursor_refs=_string_list(data.get("event_cursor_refs")),
        outbox_refs=_string_list(data.get("outbox_refs")),
        replay_bundle_refs=_string_list(data.get("replay_bundle_refs")),
        diagnostics=_string_list(data.get("diagnostics")),
    )


def _report_kind(data: dict[str, Any], path: Path) -> str:
    keys = set(data)
    if {"browser_required_pass_count", "recovered_fragment_count", "target_count"} <= keys:
        return "browser_quality"
    if {"model_call_trace_refs", "site_observation_refs", "source_anchor_refs"} <= keys:
        return "ai_http_acquisition"
    if {"benchmark_corpus_ref", "site_observation_refs", "source_observation_refs"} <= keys:
        return "live_http_acquisition"
    raise ValueError(f"unrecognized acquisition evidence report: {path}")


def _metrics(report_kind: str, data: dict[str, Any]) -> dict[str, float | int | str]:
    metric_keys = {
        "browser_quality": (
            "target_count",
            "browser_required_pass_count",
            "recovered_fragment_count",
            "http_only_missing_count",
        ),
        "ai_http_acquisition": (
            "operator_status",
        ),
        "live_http_acquisition": (
            "operator_status",
        ),
    }[report_kind]
    metrics = {
        key: value
        for key in metric_keys
        if isinstance((value := data.get(key)), int | float | str)
    }
    if report_kind == "ai_http_acquisition":
        metrics["artifact_ref_count"] = len(_string_list(data.get("artifact_refs")))
        metrics["source_anchor_ref_count"] = len(_string_list(data.get("source_anchor_refs")))
    if report_kind == "live_http_acquisition":
        metrics["artifact_ref_count"] = len(_string_list(data.get("artifact_refs")))
        metrics["content_hash_ref_count"] = len(_string_list(data.get("content_hash_refs")))
    return metrics


def _diagnostics(report_by_kind: dict[str, LiveAcquisitionInputReport]) -> list[str]:
    diagnostics: list[str] = []
    for required in _required_report_kinds():
        if required not in report_by_kind:
            diagnostics.append(f"missing acquisition input report: {required}")
    for report in report_by_kind.values():
        if report.completion_result != CompletenessResult.PASS.value:
            diagnostics.append(f"{report.report_kind} report is not pass")
    ai_http = report_by_kind.get("ai_http_acquisition")
    if ai_http:
        if len(ai_http.artifact_refs) < 6:
            diagnostics.append("AI HTTP acquisition artifact refs below 6")
        if len(ai_http.source_anchor_refs) < 6:
            diagnostics.append("AI HTTP acquisition source anchor refs below 6")
    browser = report_by_kind.get("browser_quality")
    if browser:
        if _metric(browser, "target_count") < 8:
            diagnostics.append("browser acquisition target count below 8")
        if _metric(browser, "browser_required_pass_count") < 8:
            diagnostics.append("browser required pass count below 8")
        if _metric(browser, "recovered_fragment_count") < 8:
            diagnostics.append("browser recovered fragment count below 8")
        if not browser.artifact_refs:
            diagnostics.append("browser acquisition missing DOM/screenshot artifacts")
    live_http = report_by_kind.get("live_http_acquisition")
    if live_http and len(live_http.artifact_refs) < 6:
        diagnostics.append("live HTTP acquisition artifact refs below 6")
    return diagnostics


def _build_attempts(
    fixture_id: str,
    report_by_kind: dict[str, LiveAcquisitionInputReport],
) -> list[AcquisitionAttemptRecord]:
    attempts: list[AcquisitionAttemptRecord] = []
    for mode, kind in (
        ("http", "live_http_acquisition"),
        ("ai_http", "ai_http_acquisition"),
        ("browser", "browser_quality"),
    ):
        report = report_by_kind.get(kind)
        if report is None:
            continue
        base = f"{fixture_id}:{kind}"
        attempts.append(
            AcquisitionAttemptRecord(
                id=f"acquisition-attempt:{base}",
                fixture_id=fixture_id,
                source_profile_ref=f"source:{kind}",
                acquisition_mode=mode,
                evidence_found=report.completion_result == CompletenessResult.PASS.value,
                artifact_refs=report.artifact_refs or [f"artifact:{base}:source"],
                content_hash_refs=report.content_hash_refs
                or [stable_hash({"report": report.id, "kind": kind})],
                source_anchor_refs=report.source_anchor_refs
                or [f"source-anchor:{base}:source"],
                source_limitation_ref=(
                    None
                    if report.completion_result == CompletenessResult.PASS.value
                    else f"source-limitation:{base}:non-pass"
                ),
                policy_decision_refs=report.policy_decision_refs or _policy_refs(fixture_id),
                command_record_refs=report.command_record_refs
                or [f"command:{base}:record-acquisition"],
                event_cursor_refs=report.event_cursor_refs
                or [f"event-cursor:{base}:acquisition-recorded"],
                outbox_refs=report.outbox_refs or [f"outbox:{base}:acquisition"],
                replay_bundle_ref=(
                    report.replay_bundle_refs[0]
                    if report.replay_bundle_refs
                    else f"replay-bundle:{base}:acquisition"
                ),
                completion_result=(
                    CompletenessResult.PASS
                    if report.completion_result == CompletenessResult.PASS.value
                    else CompletenessResult.NEEDS_REVIEW
                ),
            )
        )
    return attempts


def _build_gate_report(
    *,
    manifest: ProductionGradeClosureManifest,
    input_reports: list[LiveAcquisitionInputReport],
    attempts: list[AcquisitionAttemptRecord],
    summary: LiveAcquisitionEvidenceSummary,
    refs: dict[str, list[Ref]],
    diagnostics: list[str],
) -> ProductionGateReport:
    fixture_id = manifest.id
    completion = (
        CompletenessResult.PASS
        if not diagnostics
        and not summary.missing_report_kinds
        and not summary.non_passing_report_refs
        else CompletenessResult.NEEDS_REVIEW
    )
    common = {
        "id": f"production-gate-report:{fixture_id}",
        "fixture_id": fixture_id,
        "gate_type": manifest.gate_type,
        "run_ref": f"run:{fixture_id}:live-acquisition",
        "capability_refs": [
            f"capability:{manifest.gate_type}:{name}" for name in _ACQUISITION_CAPABILITIES
        ],
        "acquisition_attempt_refs": [attempt.id for attempt in attempts],
        "lower_gate_report_refs": [report.id for report in input_reports],
        "source_profile_refs": [profile.id for profile in manifest.source_profiles],
        "artifact_refs": refs["artifact_refs"],
        "source_anchor_refs": refs["source_anchor_refs"],
        "content_hash_refs": refs["content_hash_refs"],
        "evidence_packet_refs": [f"evidence-packet:{fixture_id}:live-acquisition"],
        "verification_decision_refs": [
            f"verification-decision:{fixture_id}:live-acquisition"
        ],
        "publication_gate_refs": [f"publication-gate:{fixture_id}:blocked-until-release"],
        "policy_decision_refs": refs["policy_decision_refs"] or _policy_refs(fixture_id),
        "command_record_refs": refs["command_record_refs"]
        or [f"command:{fixture_id}:record-live-acquisition"],
        "event_cursor_refs": refs["event_cursor_refs"]
        or [f"event-cursor:{fixture_id}:live-acquisition-recorded"],
        "outbox_refs": refs["outbox_refs"] or [f"outbox:{fixture_id}:live-acquisition"],
        "replay_bundle_refs": refs["replay_bundle_refs"]
        or [f"replay-bundle:{fixture_id}:live-acquisition"],
        "metrics": summary.metrics
        | {
            "input_report_count": len(input_reports),
            "acquisition_attempt_count": len(attempts),
            "artifact_ref_count": summary.artifact_ref_count,
            "source_anchor_ref_count": summary.source_anchor_ref_count,
            "content_hash_ref_count": summary.content_hash_ref_count,
            "replay_bundle_ref_count": summary.replay_bundle_ref_count,
        },
        "operator_status": (
            manifest.expected_operator_status
            if completion == CompletenessResult.PASS
            else "production_acquisition_escalation_needs_review"
        ),
        "completion_result": completion,
    }
    if completion == CompletenessResult.PASS:
        return ProductionGateReport(**common)
    return ProductionGateReport(
        **common,
        release_blocker_refs=[f"release-blocker:{fixture_id}:live-acquisition"],
        diagnostics=diagnostics or ["live acquisition evidence is incomplete"],
    )


def _collect_refs(
    input_reports: list[LiveAcquisitionInputReport],
) -> dict[str, list[Ref]]:
    names = (
        "artifact_refs",
        "source_anchor_refs",
        "content_hash_refs",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "replay_bundle_refs",
    )
    return {
        name: sorted({ref for report in input_reports for ref in getattr(report, name)})
        for name in names
    }


def _combined_metrics(
    report_by_kind: dict[str, LiveAcquisitionInputReport],
) -> dict[str, float | int | str]:
    combined: dict[str, float | int | str] = {}
    for kind, report in sorted(report_by_kind.items()):
        for key, value in report.metrics.items():
            combined[f"{kind}.{key}"] = value
    combined["acquisition_report_hash"] = stable_hash(
        {kind: report.metrics for kind, report in sorted(report_by_kind.items())}
    )
    return combined


def _metric(report: LiveAcquisitionInputReport, key: str) -> float:
    value = report.metrics.get(key)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _required_report_kinds() -> tuple[str, ...]:
    return ("ai_http_acquisition", "browser_quality", "live_http_acquisition")


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
