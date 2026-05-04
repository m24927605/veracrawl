from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductAvailabilityFailureType,
    ProductAvailabilityStatus,
)
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkManifest,
    ProductAvailabilityBenchmarkReport,
    ProductAvailabilityFieldEvidence,
    ProductAvailabilitySiteResult,
    ProductAvailabilityTargetSpec,
)


def _target(**overrides: object) -> ProductAvailabilityTargetSpec:
    data: dict[str, object] = {
        "id": "target",
        "site_name": "Example",
        "target_url": "https://example.com/product",
        "robots_url": "https://example.com/robots.txt",
        "allowed_origin": "https://example.com",
        "required_identity_terms": ["SanDisk", "256GB"],
    }
    data.update(overrides)
    return ProductAvailabilityTargetSpec(**data)


def _field(**overrides: object) -> ProductAvailabilityFieldEvidence:
    data: dict[str, object] = {
        "id": "field:price",
        "fixture_id": "fixture",
        "target_spec_ref": "target",
        "site_name": "Example",
        "target_url": "https://example.com/product",
        "field_name": "price",
        "raw_text": "$19.99",
        "normalized_value": "USD 19.99",
        "amount": 19.99,
        "currency": "USD",
        "source_anchor_ref": "source-anchor:price",
        "artifact_ref": "artifact:1",
        "content_hash_ref": "hash:1",
        "canonical_url_ref": "canonical:1",
        "model_call_trace_ref": "model-call:1",
        "agent_action_trace_ref": "agent-action:1",
        "tool_call_trace_refs": ["tool:1"],
        "context_bundle_trace_ref": "context:1",
        "evidence_packet_ref": "evidence-packet:1",
        "evidence_anchor_ref": "evidence-anchor:1",
        "verification_decision_ref": "verification:1",
        "policy_decision_refs": ["policy:1"],
        "command_record_refs": ["command:1"],
        "event_cursor_refs": ["event:1"],
        "outbox_refs": ["outbox:1"],
        "replay_bundle_ref": "replay:1",
    }
    data.update(overrides)
    return ProductAvailabilityFieldEvidence(**data)


def _site(**overrides: object) -> ProductAvailabilitySiteResult:
    data: dict[str, object] = {
        "id": "site:1",
        "fixture_id": "fixture",
        "target_spec_ref": "target",
        "site_name": "Example",
        "target_url": "https://example.com/product",
        "live_http_report_ref": "live-http:1",
        "network_response_ref": "network:1",
        "status_code": 200,
        "content_type": "text/html",
        "body_size_bytes": 1024,
        "content_digest": "hash:1",
        "source_observation_refs": ["source-observation:1"],
        "artifact_refs": ["artifact:1"],
        "content_hash_refs": ["hash:1"],
        "canonical_url_refs": ["canonical:1"],
        "identity_terms_matched": ["SanDisk", "256GB"],
        "field_evidence_refs": ["field:identity", "field:price", "field:availability"],
        "identity_evidence_ref": "field:identity",
        "price_evidence_ref": "field:price",
        "availability_evidence_ref": "field:availability",
        "price_raw_text": "$19.99",
        "price_amount": 19.99,
        "price_currency": "USD",
        "availability_status": ProductAvailabilityStatus.IN_STOCK,
        "availability_raw_text": "In Stock",
        "model_call_trace_refs": ["model-call:1"],
        "agent_action_trace_refs": ["agent-action:1"],
        "tool_call_trace_refs": ["tool:1"],
        "context_bundle_trace_refs": ["context:1"],
        "evidence_packet_refs": ["evidence-packet:1"],
        "evidence_anchor_refs": ["evidence-anchor:1"],
        "verification_decision_refs": ["verification:1"],
        "publication_gate_refs": ["publication-gate:1"],
        "policy_decision_refs": ["policy:1"],
        "command_record_refs": ["command:1"],
        "event_cursor_refs": ["event:1"],
        "outbox_refs": ["outbox:1"],
        "replay_bundle_refs": ["replay:1"],
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return ProductAvailabilitySiteResult(**data)


def test_manifest_requires_target_identity_and_refs() -> None:
    manifest = ProductAvailabilityBenchmarkManifest(
        id="fixture",
        scenario="success",
        profile_refs=["target"],
        product_name="SanDisk 256GB",
        brand="SanDisk",
        required_identity_terms=["SanDisk", "256GB"],
        target_specs=[_target()],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="product_availability_benchmark_completed",
        required_ref_types=["live_http", "replay"],
    )
    assert manifest.target_specs[0].allowed_origin == "https://example.com"


def test_target_rejects_cross_origin_robots() -> None:
    with pytest.raises(ValidationError):
        _target(robots_url="https://other.example.com/robots.txt")


def test_field_evidence_rejects_llm_output_as_evidence() -> None:
    assert _field().field_name == "price"
    with pytest.raises(ValidationError):
        _field(llm_output_evidence_refs=["model-response:1"])


def test_site_result_requires_price_and_availability_refs() -> None:
    assert _site().completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        _site(price_evidence_ref=None)


def test_non_pass_site_requires_typed_diagnostics() -> None:
    result = ProductAvailabilitySiteResult(
        id="site:blocked",
        fixture_id="fixture",
        target_spec_ref="target",
        site_name="Example",
        target_url="https://example.com/product",
        blocked_source_refs=["blocked:1"],
        failure_report_refs=["failure:1"],
        missing_ref_fields=["price"],
        failure_type=ProductAvailabilityFailureType.PRICE_NOT_FOUND,
        diagnostics=["missing price"],
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert result.failure_type == ProductAvailabilityFailureType.PRICE_NOT_FOUND


def test_report_allows_partial_source_blocked_needs_review() -> None:
    report = ProductAvailabilityBenchmarkReport(
        id="report:1",
        fixture_id="fixture",
        run_ref="run:fixture",
        product_name="SanDisk 256GB",
        target_site_count=2,
        site_result_refs=["site:pass", "site:blocked"],
        passing_site_result_refs=["site:pass"],
        blocked_site_result_refs=["site:blocked"],
        field_evidence_refs=["field:price", "field:availability"],
        price_evidence_refs=["field:price"],
        availability_evidence_refs=["field:availability"],
        blocked_source_refs=["blocked:1"],
        diagnostics=["one source blocked"],
        operator_status="product_availability_partial_sources_blocked",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
