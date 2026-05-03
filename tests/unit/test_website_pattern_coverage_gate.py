from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetWebsitePattern,
    WebsitePatternCoverageFailureType,
)
from veracrawl.patterns.coverage import run_website_pattern_coverage_gate


def test_website_pattern_coverage_success_covers_all_target_patterns() -> None:
    result = run_website_pattern_coverage_gate(
        fixture_id="unit",
        scenario="website-pattern-coverage-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.covered_patterns) == set(TargetWebsitePattern)
    assert len(result.coverage_records) == len(TargetWebsitePattern)
    for record in result.coverage_records:
        assert record.benchmark_fixture_ref
        assert record.source_adapter_refs
        assert record.source_evidence_refs
        assert record.site_model_refs
        assert record.page_type_refs
        assert record.expected_output_oracle_refs
        assert record.evidence_coverage_refs
        assert record.pattern_specific_refs
        assert record.safety_refs
        assert record.command_record_refs
        assert record.event_cursor_refs
        assert record.outbox_refs
        assert record.replay_bundle_ref


def test_website_pattern_runtime_unavailable_needs_review() -> None:
    result = run_website_pattern_coverage_gate(
        fixture_id="unit-no-runtime",
        scenario="website-pattern-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_website_pattern_negative_scenarios_fail() -> None:
    expectations = {
        "website-pattern-missing-pattern": WebsitePatternCoverageFailureType.MISSING_PATTERN,
        "website-pattern-unsupported-pattern": (
            WebsitePatternCoverageFailureType.UNSUPPORTED_PATTERN
        ),
        "website-pattern-single-site-assumption": (
            WebsitePatternCoverageFailureType.SINGLE_SITE_ASSUMPTION
        ),
        "website-pattern-scaffold-only": WebsitePatternCoverageFailureType.SCAFFOLD_ONLY,
        "website-pattern-missing-source-adapter": (
            WebsitePatternCoverageFailureType.MISSING_SOURCE_ADAPTER
        ),
        "website-pattern-missing-site-model": (
            WebsitePatternCoverageFailureType.MISSING_SITE_MODEL
        ),
        "website-pattern-missing-output-evidence": (
            WebsitePatternCoverageFailureType.MISSING_OUTPUT_EVIDENCE
        ),
        "website-pattern-missing-pattern-specific-refs": (
            WebsitePatternCoverageFailureType.MISSING_PATTERN_SPECIFIC_REFS
        ),
        "website-pattern-unsafe-interaction": (
            WebsitePatternCoverageFailureType.UNSAFE_INTERACTION
        ),
        "website-pattern-missing-replay": WebsitePatternCoverageFailureType.MISSING_REPLAY_REFS,
    }
    for scenario, failure in expectations.items():
        result = run_website_pattern_coverage_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.failure_type == failure
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
