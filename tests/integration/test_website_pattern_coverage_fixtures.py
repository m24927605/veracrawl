from __future__ import annotations

from pathlib import Path

from tests.helpers.website_pattern_fixture_assertions import (
    assert_website_pattern_coverage_needs_review,
    assert_website_pattern_coverage_negative,
    assert_website_pattern_coverage_success,
)
from veracrawl.cli.website_patterns import run_fixture
from veracrawl.contracts.enums import WebsitePatternCoverageFailureType


def test_website_pattern_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "website-pattern-coverage-success",
        profile="target",
        out=tmp_path / "website-pattern-coverage-success",
    )
    assert_website_pattern_coverage_success(report)


def test_website_pattern_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "website-pattern-runtime-unavailable",
        profile="target",
        out=tmp_path / "website-pattern-runtime-unavailable",
    )
    assert_website_pattern_coverage_needs_review(report)


def test_website_pattern_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "website-pattern-missing-pattern": (
            WebsitePatternCoverageFailureType.MISSING_PATTERN.value,
            "covered_patterns",
        ),
        "website-pattern-unsupported-pattern": (
            WebsitePatternCoverageFailureType.UNSUPPORTED_PATTERN.value,
            "unsupported_pattern",
        ),
        "website-pattern-single-site-assumption": (
            WebsitePatternCoverageFailureType.SINGLE_SITE_ASSUMPTION.value,
            "general_pattern_fixture_refs",
        ),
        "website-pattern-scaffold-only": (
            WebsitePatternCoverageFailureType.SCAFFOLD_ONLY.value,
            "executable_oracle_refs",
        ),
        "website-pattern-missing-source-adapter": (
            WebsitePatternCoverageFailureType.MISSING_SOURCE_ADAPTER.value,
            "source_adapter_refs",
        ),
        "website-pattern-missing-site-model": (
            WebsitePatternCoverageFailureType.MISSING_SITE_MODEL.value,
            "site_model_refs",
        ),
        "website-pattern-missing-output-evidence": (
            WebsitePatternCoverageFailureType.MISSING_OUTPUT_EVIDENCE.value,
            "evidence_coverage_refs",
        ),
        "website-pattern-missing-pattern-specific-refs": (
            WebsitePatternCoverageFailureType.MISSING_PATTERN_SPECIFIC_REFS.value,
            "pattern_specific_refs",
        ),
        "website-pattern-unsafe-interaction": (
            WebsitePatternCoverageFailureType.UNSAFE_INTERACTION.value,
            "safety_refs",
        ),
        "website-pattern-missing-replay": (
            WebsitePatternCoverageFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_website_pattern_coverage_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
