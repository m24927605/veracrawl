from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldQualityCorpusFailureType,
)
from veracrawl.contracts.real_world_quality import (
    RealWorldQualityCorpusManifest,
    RealWorldQualityCorpusReport,
    RealWorldQualityPatternCoverageRecord,
    RealWorldQualitySiteObservation,
    RealWorldQualityTargetSpec,
)


def _target(**overrides: object) -> RealWorldQualityTargetSpec:
    data: dict[str, object] = {
        "id": "example-static",
        "target_url": "https://example.com/",
        "robots_url": "https://example.com/robots.txt",
        "allowed_origin": "https://example.com",
        "expected_status_code": 200,
        "expected_content_type": "text/html",
        "min_body_size_bytes": 10,
        "required_title_fragments": ["Example Domain"],
        "allowed_robots_status_codes": [200, 404],
        "pattern_refs": ["pattern:static"],
        "pattern_family_refs": ["pattern:static"],
    }
    data.update(overrides)
    return RealWorldQualityTargetSpec(**data)


def _quality_observation(**overrides: object) -> RealWorldQualitySiteObservation:
    data: dict[str, object] = {
        "id": "real-world-quality-site-observation:unit:example",
        "target_spec_ref": "example-static",
        "site_observation_ref": "real-world-site-observation:unit:example",
        "target_url": "https://example.com/",
        "pattern_family_refs": ["pattern:static"],
        "matched_observation_refs": ["observation:unit:title"],
        "policy_decision_refs": ["policy:unit"],
        "artifact_refs": ["artifact:unit"],
        "content_hash_refs": ["hash:unit"],
        "canonical_url_refs": ["canonical:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "replay_bundle_ref": "replay:unit",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return RealWorldQualitySiteObservation(**data)


def _pattern(**overrides: object) -> RealWorldQualityPatternCoverageRecord:
    data: dict[str, object] = {
        "id": "real-world-quality-pattern-coverage:unit:static",
        "pattern_family_ref": "pattern:static",
        "declared_target_refs": ["example-static"],
        "passing_target_refs": ["example-static"],
        "site_observation_refs": ["real-world-site-observation:unit:example"],
        "quality_observation_refs": ["real-world-quality-site-observation:unit:example"],
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return RealWorldQualityPatternCoverageRecord(**data)


def _report(**overrides: object) -> RealWorldQualityCorpusReport:
    data: dict[str, object] = {
        "id": "real-world-quality-corpus-report:unit",
        "fixture_id": "real-world-quality-corpus",
        "run_ref": "run:unit",
        "real_world_benchmark_run_report_ref": "real-world-benchmark-run-report:unit",
        "quality_observation_refs": ["real-world-quality-site-observation:unit:example"],
        "pattern_coverage_refs": ["real-world-quality-pattern-coverage:unit:static"],
        "site_observation_refs": ["real-world-site-observation:unit:example"],
        "passing_target_count": 40,
        "declared_target_count": 40,
        "origin_count": 15,
        "pattern_family_count": 10,
        "policy_decision_refs": ["policy:unit"],
        "artifact_refs": ["artifact:unit"],
        "content_hash_refs": ["hash:unit"],
        "canonical_url_refs": ["canonical:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "replay_bundle_refs": ["replay:unit"],
        "operator_status": "real_world_quality_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return RealWorldQualityCorpusReport(**data)


def test_quality_target_requires_patterns_and_public_scope() -> None:
    assert _target().pattern_family_refs == ["pattern:static"]

    with pytest.raises(ValidationError):
        _target(target_url="http://127.0.0.1/private")

    with pytest.raises(ValidationError):
        _target(pattern_family_refs=[])


def test_quality_manifest_enforces_quality_threshold_profile() -> None:
    manifest = RealWorldQualityCorpusManifest(
        id="real-world-quality-corpus",
        scenario="success",
        profile_refs=["target", "quality"],
        target_specs=[_target()],
        allowed_origin_refs=["https://example.com"],
        rate_budget_ref="budget:quality",
        minimum_target_count=40,
        minimum_origin_count=15,
        minimum_pattern_family_count=10,
        expected_completion_result=CompletenessResult.FAIL,
        expected_operator_status=(
            RealWorldQualityCorpusFailureType.INSUFFICIENT_TARGET_COVERAGE.value
        ),
        expected_failure_type=(
            RealWorldQualityCorpusFailureType.INSUFFICIENT_TARGET_COVERAGE
        ),
        negative_case=True,
        required_ref_types=["quality_observation_refs"],
    )
    assert manifest.minimum_target_count == 40

    with pytest.raises(ValidationError):
        RealWorldQualityCorpusManifest(
            id="bad",
            scenario="bad",
            profile_refs=["target"],
            target_specs=[_target()],
            allowed_origin_refs=["https://example.com"],
            rate_budget_ref="budget:bad",
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            required_ref_types=["quality_observation_refs"],
        )


def test_quality_observation_requires_refs_on_pass_and_diagnostics_on_fail() -> None:
    assert _quality_observation().completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        _quality_observation(replay_bundle_ref=None)

    failure = RealWorldQualitySiteObservation(
        id="real-world-quality-site-observation:failure",
        target_spec_ref="example-static",
        target_url="https://example.com/",
        failure_type=RealWorldQualityCorpusFailureType.TARGET_DRIFT,
        failure_report_refs=["failure:drift"],
        missing_ref_fields=["observation_oracle"],
        diagnostics=["body mismatch"],
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == RealWorldQualityCorpusFailureType.TARGET_DRIFT


def test_pattern_and_report_reject_hidden_missing_refs() -> None:
    assert _pattern().completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        _pattern(passing_target_refs=[])

    assert _report().completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        _report(replay_bundle_refs=[])

    failure = RealWorldQualityCorpusReport(
        id="real-world-quality-corpus-report:failure",
        fixture_id="real-world-quality-corpus",
        run_ref="run:failure",
        failure_type=RealWorldQualityCorpusFailureType.TARGET_DRIFT,
        failure_report_refs=["failure:drift"],
        missing_ref_fields=["observation_oracle"],
        diagnostics=["target drift"],
        operator_status=RealWorldQualityCorpusFailureType.TARGET_DRIFT.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == RealWorldQualityCorpusFailureType.TARGET_DRIFT
