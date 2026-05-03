"""Live normalization and site understanding runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult, LiveNormalizationFailureType
from veracrawl.contracts.processing import LiveNormalizationRuntimeReport
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document


@dataclass(frozen=True)
class LiveNormalizationRuntimeResult:
    report: LiveNormalizationRuntimeReport
    normalization: NormalizationResult | None = None


_DIRECT_FAILURES: dict[str, tuple[LiveNormalizationFailureType, str]] = {
    "live-normalization-missing-upstream": (
        LiveNormalizationFailureType.MISSING_UPSTREAM,
        "upstream_report_refs",
    ),
    "live-normalization-empty-content": (
        LiveNormalizationFailureType.EMPTY_CONTENT,
        "normalized_document_refs",
    ),
    "live-normalization-missing-anchor-map": (
        LiveNormalizationFailureType.MISSING_ANCHOR_MAP,
        "anchor_map_refs",
    ),
    "live-normalization-missing-site-model": (
        LiveNormalizationFailureType.MISSING_SITE_MODEL,
        "site_model_refs",
    ),
    "live-normalization-replay-mismatch": (
        LiveNormalizationFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_live_normalization_runtime(
    *,
    fixture_id: str,
    scenario: str,
    source_url: str,
    raw_artifact_ref: Ref,
    raw_html: str,
    source_adapter_result_ref: Ref,
    live_http_acquisition_report_ref: Ref | None,
    structured_source_adapters_runtime_report_ref: Ref | None,
    browser_snapshot_runtime_report_ref: Ref | None,
) -> LiveNormalizationRuntimeResult:
    policy_refs = [f"policy:{fixture_id}:live-normalization"]
    upstream_missing = not (
        live_http_acquisition_report_ref
        and structured_source_adapters_runtime_report_ref
        and browser_snapshot_runtime_report_ref
    )
    if upstream_missing:
        return _failure_result(
            fixture_id=fixture_id,
            failure=LiveNormalizationFailureType.MISSING_UPSTREAM,
            missing_field="upstream_report_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        )
    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        )
    if not raw_html.strip():
        return _failure_result(
            fixture_id=fixture_id,
            failure=LiveNormalizationFailureType.EMPTY_CONTENT,
            missing_field="normalized_document_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        )

    try:
        normalized = normalize_html_document(
            fixture_id=fixture_id,
            run_ref=f"run:{fixture_id}",
            source_adapter_result_ref=source_adapter_result_ref,
            source_url=source_url,
            raw_artifact_ref=raw_artifact_ref,
            raw_html=raw_html,
            policy_decision_refs=policy_refs,
        )
    except (ValueError, ValidationError) as exc:
        return _failure_result(
            fixture_id=fixture_id,
            failure=LiveNormalizationFailureType.NORMALIZATION_FAILED,
            missing_field="normalization_manifest_refs",
            policy_refs=policy_refs,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
            diagnostics=[str(exc)],
        )

    link_refs = [link.id for link in normalized.link_provenance]
    link_analysis_refs = [
        f"link-analysis:{fixture_id}:discovered:{len(link_refs)}"
        if link_refs
        else f"link-analysis:{fixture_id}:no-outbound-links"
    ]
    report = LiveNormalizationRuntimeReport(
        id=f"live-normalization-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        structured_source_adapters_runtime_report_ref=(
            structured_source_adapters_runtime_report_ref
        ),
        browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        normalized_document_refs=[normalized.normalized_document.id],
        normalization_manifest_refs=[normalized.manifest.id],
        anchor_map_refs=[normalized.anchor_map.id],
        source_anchor_refs=[anchor.id for anchor in normalized.anchors],
        link_provenance_refs=link_refs,
        link_analysis_refs=link_analysis_refs,
        page_type_classification_refs=[normalized.page_type.id],
        site_model_refs=[normalized.site_model.id],
        raw_artifact_refs=[raw_artifact_ref],
        normalized_artifact_refs=[normalized.normalized_document.normalized_artifact_ref],
        artifact_refs=_dedupe([raw_artifact_ref] + normalized.artifact_refs),
        policy_decision_refs=policy_refs,
        command_record_refs=[f"durable-command:{fixture_id}:live-normalization"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:live-normalization"],
        outbox_refs=[f"outbox:{fixture_id}:live-normalization"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:live-normalization",
        derived_context_refs=[normalized.page_type.id, normalized.site_model.id],
        operator_status="live_normalization_completed",
        completion_result=CompletenessResult.PASS,
    )
    return LiveNormalizationRuntimeResult(report=report, normalization=normalized)


def _failure_result(
    *,
    fixture_id: str,
    failure: LiveNormalizationFailureType,
    missing_field: str,
    policy_refs: list[Ref],
    live_http_acquisition_report_ref: Ref | None,
    structured_source_adapters_runtime_report_ref: Ref | None,
    browser_snapshot_runtime_report_ref: Ref | None,
    diagnostics: list[str] | None = None,
) -> LiveNormalizationRuntimeResult:
    report = LiveNormalizationRuntimeReport(
        id=f"live-normalization-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        structured_source_adapters_runtime_report_ref=(
            structured_source_adapters_runtime_report_ref
        ),
        browser_snapshot_runtime_report_ref=browser_snapshot_runtime_report_ref,
        policy_decision_refs=policy_refs,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=diagnostics or [f"live normalization runtime failed: {failure.value}"],
    )
    return LiveNormalizationRuntimeResult(report=report)


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
