from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetWebsitePattern,
    WebsitePatternCoverageFailureType,
)
from veracrawl.contracts.website_pattern import (
    WebsitePatternCoverageFixtureManifest,
    WebsitePatternCoverageRecord,
    WebsitePatternCoverageReport,
)


def _record(
    pattern: TargetWebsitePattern = TargetWebsitePattern.STATIC,
) -> WebsitePatternCoverageRecord:
    return WebsitePatternCoverageRecord(
        id=f"website-pattern-coverage:{pattern.value}",
        run_ref="run:contract",
        website_pattern=pattern,
        benchmark_fixture_ref=f"benchmark:{pattern.value}",
        source_adapter_refs=[f"source-adapter:{pattern.value}"],
        source_evidence_refs=[f"source-evidence:{pattern.value}"],
        site_model_refs=[f"site-model:{pattern.value}"],
        page_type_refs=[f"page-type:{pattern.value}"],
        expected_output_oracle_refs=[f"output-oracle:{pattern.value}"],
        evidence_coverage_refs=[f"evidence-coverage:{pattern.value}"],
        policy_decision_refs=["policy:contract"],
        artifact_oracle_refs=[f"artifact-oracle:{pattern.value}"],
        event_oracle_refs=[f"event-oracle:{pattern.value}"],
        graph_oracle_refs=[f"graph-oracle:{pattern.value}"],
        pattern_specific_refs=_pattern_refs(pattern),
        safety_refs=[f"safety:{pattern.value}"],
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay:contract",
        result=CompletenessResult.PASS,
    )


def _pattern_refs(pattern: TargetWebsitePattern) -> dict[str, str]:
    refs = {
        TargetWebsitePattern.STATIC: ["linked_page_refs", "schema_bound_output_refs"],
        TargetWebsitePattern.SITEMAP_RSS_FEED: [
            "sitemap_or_feed_ref",
            "feed_delta_ref",
            "freshness_window_ref",
        ],
        TargetWebsitePattern.LISTING_DETAIL: [
            "listing_page_refs",
            "detail_page_refs",
            "pagination_refs",
            "canonical_dedup_refs",
        ],
        TargetWebsitePattern.SEARCH: [
            "bounded_query_refs",
            "search_result_page_refs",
            "budget_policy_ref",
        ],
        TargetWebsitePattern.NON_DESTRUCTIVE_FORMS: [
            "form_intent_ref",
            "non_destructive_policy_ref",
            "sandbox_ref",
        ],
        TargetWebsitePattern.JAVASCRIPT_PAGES: [
            "browser_artifact_refs",
            "dom_state_refs",
            "render_budget_ref",
        ],
        TargetWebsitePattern.AUTHENTICATED_SOURCES: [
            "credential_audit_refs",
            "origin_allowlist_ref",
            "redaction_ref",
        ],
        TargetWebsitePattern.API_LIKE_ENDPOINTS: [
            "api_payload_refs",
            "endpoint_provenance_refs",
            "schema_probe_refs",
        ],
        TargetWebsitePattern.DOCUMENTS: [
            "document_artifact_refs",
            "anchor_map_refs",
            "document_metadata_refs",
        ],
        TargetWebsitePattern.MULTI_LANGUAGE_PAGES: [
            "language_metadata_refs",
            "localized_field_refs",
        ],
        TargetWebsitePattern.DRIFTED_SITES: [
            "drift_event_refs",
            "repair_signal_refs",
            "review_decision_refs",
        ],
        TargetWebsitePattern.HIGH_VOLUME_SITES: [
            "queue_fairness_refs",
            "backpressure_refs",
            "retry_dedup_refs",
        ],
    }
    return {name: f"pattern-ref:{pattern.value}:{name}" for name in refs[pattern]}


def test_website_pattern_record_rejects_missing_source_adapter() -> None:
    with pytest.raises(ValidationError):
        WebsitePatternCoverageRecord(
            **(_record().model_dump() | {"source_adapter_refs": []})
        )


def test_website_pattern_record_rejects_missing_pattern_specific_refs() -> None:
    with pytest.raises(ValidationError):
        WebsitePatternCoverageRecord(
            **(
                _record(TargetWebsitePattern.JAVASCRIPT_PAGES).model_dump()
                | {"pattern_specific_refs": {}}
            )
        )


def test_website_pattern_record_rejects_single_site_assumption() -> None:
    with pytest.raises(ValidationError):
        WebsitePatternCoverageRecord(
            **(_record().model_dump() | {"diagnostic_single_site_refs": ["site:one"]})
        )


def test_website_pattern_report_requires_all_target_patterns() -> None:
    with pytest.raises(ValidationError):
        WebsitePatternCoverageReport(
            id="website-pattern-report:bad",
            run_ref="run:bad",
            coverage_record_refs=["website-pattern-coverage:static"],
            covered_patterns=[TargetWebsitePattern.STATIC],
            policy_decision_refs=["policy:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay:bad",
            operator_status="website_pattern_coverage_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_website_pattern_report_accepts_pass_and_typed_fail() -> None:
    report = WebsitePatternCoverageReport(
        id="website-pattern-report:ok",
        run_ref="run:ok",
        coverage_record_refs=[f"coverage:{pattern.value}" for pattern in TargetWebsitePattern],
        covered_patterns=list(TargetWebsitePattern),
        policy_decision_refs=["policy:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay:ok",
        operator_status="website_pattern_coverage_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS

    failed = WebsitePatternCoverageReport(
        id="website-pattern-report:fail",
        run_ref="run:fail",
        failure_type=WebsitePatternCoverageFailureType.SCAFFOLD_ONLY,
        failure_report_refs=["failure:fail"],
        scaffold_only_refs=["scaffold:fail"],
        missing_ref_fields=["executable_oracle_refs"],
        operator_status=WebsitePatternCoverageFailureType.SCAFFOLD_ONLY.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failed.failure_type == WebsitePatternCoverageFailureType.SCAFFOLD_ONLY


def test_website_pattern_fixture_manifest_rejects_invalid_failure_expectations() -> None:
    with pytest.raises(ValidationError):
        WebsitePatternCoverageFixtureManifest(
            id="website-pattern-bad",
            scenario="website-pattern-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=WebsitePatternCoverageFailureType.MISSING_PATTERN,
            negative_case=True,
        )
    with pytest.raises(ValidationError):
        WebsitePatternCoverageFixtureManifest(
            id="website-pattern-bad",
            scenario="website-pattern-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=WebsitePatternCoverageFailureType.MISSING_PATTERN,
            negative_case=False,
        )
