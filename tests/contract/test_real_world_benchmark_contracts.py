from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldBenchmarkFailureType,
)
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkCorpusManifest,
    RealWorldBenchmarkRunReport,
    RealWorldBenchmarkSiteObservation,
    RealWorldBenchmarkSiteSpec,
)


def _site(**overrides: object) -> RealWorldBenchmarkSiteSpec:
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
    }
    data.update(overrides)
    return RealWorldBenchmarkSiteSpec(**data)


def _observation(**overrides: object) -> RealWorldBenchmarkSiteObservation:
    data: dict[str, object] = {
        "id": "real-world-site-observation:unit:example-static",
        "site_spec_ref": "example-static",
        "target_url": "https://example.com/",
        "robots_policy_ref": "policy:robots",
        "live_http_report_ref": "live-http:unit",
        "network_response_ref": "network-response:unit",
        "source_observation_refs": ["source-observation:unit"],
        "artifact_refs": ["artifact:unit"],
        "content_hash_refs": ["hash:unit"],
        "canonical_url_refs": ["canonical:unit"],
        "policy_decision_refs": ["policy:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "replay_bundle_ref": "replay:unit",
        "status_code": 200,
        "content_type": "text/html",
        "body_size_bytes": 100,
        "content_digest": "digest:unit",
        "matched_observation_refs": ["observation:unit:title"],
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return RealWorldBenchmarkSiteObservation(**data)


def _run_report(**overrides: object) -> RealWorldBenchmarkRunReport:
    data: dict[str, object] = {
        "id": "real-world-benchmark-run-report:unit",
        "fixture_id": "real-world-public-corpus",
        "run_ref": "run:unit",
        "benchmark_corpus_ref": "real-world-benchmark-corpus:unit",
        "benchmark_run_refs": ["benchmark-run:unit:example"],
        "site_observation_refs": ["real-world-site-observation:unit:example"],
        "live_http_report_refs": ["live-http:unit"],
        "network_response_refs": ["network-response:unit"],
        "source_observation_refs": ["source-observation:unit"],
        "artifact_refs": ["artifact:unit"],
        "content_hash_refs": ["hash:unit"],
        "canonical_url_refs": ["canonical:unit"],
        "policy_decision_refs": ["policy:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "replay_bundle_refs": ["replay:unit"],
        "observation_summary_refs": ["observation-summary:unit"],
        "operator_status": "real_world_benchmark_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return RealWorldBenchmarkRunReport(**data)


def test_site_spec_validates_scope_and_observations() -> None:
    site = _site()
    assert site.allowed_origin == "https://example.com"

    with pytest.raises(ValidationError):
        _site(target_url="http://127.0.0.1/private")

    with pytest.raises(ValidationError):
        _site(required_title_fragments=[], required_body_fragments=[], required_regex_counts={})


def test_manifest_requires_target_profile_and_allowlisted_origins() -> None:
    manifest = RealWorldBenchmarkCorpusManifest(
        id="real-world-public-corpus",
        scenario="success",
        profile_refs=["target"],
        site_specs=[_site()],
        allowed_origin_refs=["https://example.com"],
        rate_budget_ref="budget:real-world",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="real_world_benchmark_completed",
        required_ref_types=["artifact_refs"],
    )
    assert manifest.id == "real-world-public-corpus"

    with pytest.raises(ValidationError):
        RealWorldBenchmarkCorpusManifest(
            id="bad",
            scenario="bad",
            profile_refs=["target"],
            site_specs=[_site()],
            allowed_origin_refs=["https://not-example.test"],
            rate_budget_ref="budget:bad",
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            required_ref_types=["artifact_refs"],
        )


def test_site_observation_requires_refs_on_pass_and_diagnostics_on_fail() -> None:
    assert _observation().completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        _observation(replay_bundle_ref=None)

    failure = RealWorldBenchmarkSiteObservation(
        id="real-world-site-observation:failure",
        site_spec_ref="example-static",
        target_url="https://example.com/",
        failure_type=RealWorldBenchmarkFailureType.ROBOTS_DENIED,
        failure_report_refs=["failure:robots"],
        missing_ref_fields=["robots_policy"],
        diagnostics=["robots denied"],
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == RealWorldBenchmarkFailureType.ROBOTS_DENIED


def test_run_report_rejects_hidden_failures_on_pass() -> None:
    assert _run_report().completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        _run_report(artifact_refs=[])

    with pytest.raises(ValidationError):
        _run_report(failure_report_refs=["failure:hidden"])

    failure = RealWorldBenchmarkRunReport(
        id="real-world-benchmark-run-report:failure",
        fixture_id="real-world-public-corpus",
        run_ref="run:failure",
        failure_type=RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH,
        failure_report_refs=["failure:observation"],
        missing_ref_fields=["observation_oracle"],
        diagnostics=["title mismatch"],
        operator_status=RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failure.failure_type == RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH
