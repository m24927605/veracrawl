"""Deterministic target website pattern coverage gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetWebsitePattern,
    WebsitePatternCoverageFailureType,
)
from veracrawl.contracts.website_pattern import (
    WebsitePatternCoverageRecord,
    WebsitePatternCoverageReport,
)


@dataclass(frozen=True)
class WebsitePatternCoverageRuntimeResult:
    coverage_records: list[WebsitePatternCoverageRecord]
    report: WebsitePatternCoverageReport


_FAILURES: dict[
    str,
    tuple[WebsitePatternCoverageFailureType, str | None, str, TargetWebsitePattern | None],
] = {
    "website-pattern-missing-pattern": (
        WebsitePatternCoverageFailureType.MISSING_PATTERN,
        None,
        "covered_patterns",
        TargetWebsitePattern.HIGH_VOLUME_SITES,
    ),
    "website-pattern-unsupported-pattern": (
        WebsitePatternCoverageFailureType.UNSUPPORTED_PATTERN,
        "unsupported_pattern_refs",
        "unsupported_pattern",
        None,
    ),
    "website-pattern-single-site-assumption": (
        WebsitePatternCoverageFailureType.SINGLE_SITE_ASSUMPTION,
        "single_site_assumption_refs",
        "general_pattern_fixture_refs",
        None,
    ),
    "website-pattern-scaffold-only": (
        WebsitePatternCoverageFailureType.SCAFFOLD_ONLY,
        "scaffold_only_refs",
        "executable_oracle_refs",
        None,
    ),
    "website-pattern-missing-source-adapter": (
        WebsitePatternCoverageFailureType.MISSING_SOURCE_ADAPTER,
        None,
        "source_adapter_refs",
        None,
    ),
    "website-pattern-missing-site-model": (
        WebsitePatternCoverageFailureType.MISSING_SITE_MODEL,
        None,
        "site_model_refs",
        None,
    ),
    "website-pattern-missing-output-evidence": (
        WebsitePatternCoverageFailureType.MISSING_OUTPUT_EVIDENCE,
        None,
        "evidence_coverage_refs",
        None,
    ),
    "website-pattern-missing-pattern-specific-refs": (
        WebsitePatternCoverageFailureType.MISSING_PATTERN_SPECIFIC_REFS,
        "missing_pattern_specific_refs",
        "pattern_specific_refs",
        None,
    ),
    "website-pattern-unsafe-interaction": (
        WebsitePatternCoverageFailureType.UNSAFE_INTERACTION,
        "unsafe_interaction_refs",
        "safety_refs",
        None,
    ),
    "website-pattern-missing-replay": (
        WebsitePatternCoverageFailureType.MISSING_REPLAY_REFS,
        "missing_replay_refs",
        "replay_bundle_ref",
        None,
    ),
}


def run_website_pattern_coverage_gate(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> WebsitePatternCoverageRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:website-pattern"]
    if scenario == "website-pattern-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, report_field, missing_field, missing_pattern = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            report_field=report_field,
            missing_field=missing_field,
            policy_refs=policy_refs,
            missing_pattern=missing_pattern,
        )
    return _success_result(fixture_id=fixture_id, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> WebsitePatternCoverageRuntimeResult:
    records = [
        _coverage_record(fixture_id=fixture_id, pattern=pattern, policy_refs=policy_refs)
        for pattern in TargetWebsitePattern
    ]
    report = WebsitePatternCoverageReport(
        id=f"website-pattern-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        coverage_record_refs=[record.id for record in records],
        covered_patterns=[record.website_pattern for record in records],
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        operator_status="website_pattern_coverage_completed",
        completion_result=CompletenessResult.PASS,
    )
    return WebsitePatternCoverageRuntimeResult(records, report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> WebsitePatternCoverageRuntimeResult:
    report = WebsitePatternCoverageReport(
        id=f"website-pattern-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:website-pattern"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:benchmark-runner",
            f"missing-runtime:{fixture_id}:fixture-server",
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="website_pattern_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return WebsitePatternCoverageRuntimeResult([], report)


def _failure_result(
    *,
    fixture_id: str,
    failure: WebsitePatternCoverageFailureType,
    report_field: str | None,
    missing_field: str,
    policy_refs: list[Ref],
    missing_pattern: TargetWebsitePattern | None,
) -> WebsitePatternCoverageRuntimeResult:
    report_kwargs: dict[str, object] = {}
    if report_field is not None:
        report_kwargs[report_field] = [f"{report_field}:{fixture_id}"]
    missing_patterns = [missing_pattern] if missing_pattern is not None else []
    report = WebsitePatternCoverageReport(
        id=f"website-pattern-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        missing_patterns=missing_patterns,
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        **report_kwargs,
    )
    return WebsitePatternCoverageRuntimeResult([], report)


def _coverage_record(
    *,
    fixture_id: str,
    pattern: TargetWebsitePattern,
    policy_refs: list[Ref],
) -> WebsitePatternCoverageRecord:
    suffix = pattern.value
    return WebsitePatternCoverageRecord(
        id=f"website-pattern-coverage:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        website_pattern=pattern,
        benchmark_fixture_ref=f"benchmark-fixture:{fixture_id}:{suffix}",
        source_adapter_refs=[f"source-adapter:{fixture_id}:{suffix}"],
        source_evidence_refs=[f"source-evidence:{fixture_id}:{suffix}"],
        site_model_refs=[f"site-model:{fixture_id}:{suffix}"],
        page_type_refs=[f"page-type:{fixture_id}:{suffix}"],
        expected_output_oracle_refs=[f"expected-output-oracle:{fixture_id}:{suffix}"],
        evidence_coverage_refs=[f"evidence-coverage:{fixture_id}:{suffix}"],
        policy_decision_refs=policy_refs,
        artifact_oracle_refs=[f"artifact-oracle:{fixture_id}:{suffix}"],
        event_oracle_refs=[f"event-oracle:{fixture_id}:{suffix}"],
        graph_oracle_refs=[f"graph-oracle:{fixture_id}:{suffix}"],
        pattern_specific_refs=_pattern_specific_refs(fixture_id, pattern),
        safety_refs=[f"safety:{fixture_id}:{suffix}"],
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        result=CompletenessResult.PASS,
    )


def _pattern_specific_refs(
    fixture_id: str,
    pattern: TargetWebsitePattern,
) -> dict[str, Ref]:
    prefix = f"pattern-specific:{fixture_id}:{pattern.value}"
    match pattern:
        case TargetWebsitePattern.STATIC:
            names = ["linked_page_refs", "schema_bound_output_refs"]
        case TargetWebsitePattern.SITEMAP_RSS_FEED:
            names = ["sitemap_or_feed_ref", "feed_delta_ref", "freshness_window_ref"]
        case TargetWebsitePattern.LISTING_DETAIL:
            names = [
                "listing_page_refs",
                "detail_page_refs",
                "pagination_refs",
                "canonical_dedup_refs",
            ]
        case TargetWebsitePattern.SEARCH:
            names = ["bounded_query_refs", "search_result_page_refs", "budget_policy_ref"]
        case TargetWebsitePattern.NON_DESTRUCTIVE_FORMS:
            names = ["form_intent_ref", "non_destructive_policy_ref", "sandbox_ref"]
        case TargetWebsitePattern.JAVASCRIPT_PAGES:
            names = ["browser_artifact_refs", "dom_state_refs", "render_budget_ref"]
        case TargetWebsitePattern.AUTHENTICATED_SOURCES:
            names = ["credential_audit_refs", "origin_allowlist_ref", "redaction_ref"]
        case TargetWebsitePattern.API_LIKE_ENDPOINTS:
            names = ["api_payload_refs", "endpoint_provenance_refs", "schema_probe_refs"]
        case TargetWebsitePattern.DOCUMENTS:
            names = ["document_artifact_refs", "anchor_map_refs", "document_metadata_refs"]
        case TargetWebsitePattern.MULTI_LANGUAGE_PAGES:
            names = ["language_metadata_refs", "localized_field_refs"]
        case TargetWebsitePattern.DRIFTED_SITES:
            names = ["drift_event_refs", "repair_signal_refs", "review_decision_refs"]
        case TargetWebsitePattern.HIGH_VOLUME_SITES:
            names = ["queue_fairness_refs", "backpressure_refs", "retry_dedup_refs"]
    return {name: f"{prefix}:{name}" for name in names}


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:website-pattern"]


def _event_cursor_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:website-pattern"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:website-pattern"]


def _replay_ref(fixture_id: str) -> Ref:
    return f"replay:{fixture_id}:website-pattern"
