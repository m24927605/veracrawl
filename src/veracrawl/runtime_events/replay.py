"""Replay completeness validation."""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.contracts.enums import CompletenessResult, ReplayMissingRefBehavior
from veracrawl.contracts.replay import ReplayBundleManifest, ReplayValidationReport

REQUIRED_LIST_FIELDS = [
    "event_cursor_refs",
    "artifact_hash_refs",
    "source_adapter_result_refs",
    "command_result_refs",
    "agent_action_trace_refs",
    "model_call_trace_refs",
    "tool_call_trace_refs",
    "context_bundle_trace_refs",
    "policy_decision_refs",
]

REQUIRED_SCALAR_FIELDS = [
    "deterministic_clock_ref",
    "randomness_seed_ref",
    "redaction_map_ref",
]


def missing_replay_refs(manifest: ReplayBundleManifest) -> list[str]:
    missing: list[str] = []
    for field_name in REQUIRED_LIST_FIELDS:
        if not getattr(manifest, field_name):
            missing.append(field_name)
    for field_name in REQUIRED_SCALAR_FIELDS:
        if getattr(manifest, field_name) in (None, ""):
            missing.append(field_name)
    return missing


def validate_replay_manifest(manifest: ReplayBundleManifest) -> ReplayValidationReport:
    missing = missing_replay_refs(manifest)
    if not missing:
        result = CompletenessResult.PASS
        gap_report_ref = None
    elif manifest.missing_ref_behavior == ReplayMissingRefBehavior.FAIL_REPLAY:
        result = CompletenessResult.FAIL
        gap_report_ref = f"gap:{manifest.id}"
    else:
        result = CompletenessResult.NEEDS_REVIEW
        gap_report_ref = f"gap:{manifest.id}"
    return ReplayValidationReport(
        id=f"replay-report:{manifest.id}",
        manifest_id=manifest.id,
        completeness_result=result,
        missing_ref_fields=missing,
        gap_report_ref=gap_report_ref,
    )


def missing_runtime_replay_refs(
    manifest: ReplayBundleManifest,
    *,
    runtime_refs: Mapping[str, object],
) -> list[str]:
    missing = missing_replay_refs(manifest)
    for field_name, value in runtime_refs.items():
        if value in (None, ""):
            missing.append(field_name)
        elif isinstance(value, list | tuple | set | dict) and not value:
            missing.append(field_name)
    return missing


def validate_runtime_replay_manifest(
    manifest: ReplayBundleManifest,
    *,
    runtime_refs: Mapping[str, object],
) -> ReplayValidationReport:
    missing = missing_runtime_replay_refs(manifest, runtime_refs=runtime_refs)
    if not missing:
        result = CompletenessResult.PASS
        gap_report_ref = None
    elif manifest.missing_ref_behavior == ReplayMissingRefBehavior.FAIL_REPLAY:
        result = CompletenessResult.FAIL
        gap_report_ref = f"gap:{manifest.id}"
    else:
        result = CompletenessResult.NEEDS_REVIEW
        gap_report_ref = f"gap:{manifest.id}"
    return ReplayValidationReport(
        id=f"replay-report:{manifest.id}",
        manifest_id=manifest.id,
        completeness_result=result,
        missing_ref_fields=missing,
        gap_report_ref=gap_report_ref,
    )
