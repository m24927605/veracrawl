from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, ProductAvailabilityStatus
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkReport,
    ProductAvailabilityFieldEvidence,
    ProductAvailabilitySiteResult,
)
from veracrawl.review_replay.product_availability import (
    product_availability_field_replay_passes,
    product_availability_report_replay_passes,
    product_availability_site_replay_passes,
)


def _field() -> ProductAvailabilityFieldEvidence:
    return ProductAvailabilityFieldEvidence(
        id="field:price",
        fixture_id="fixture",
        target_spec_ref="target",
        site_name="Example",
        target_url="https://example.com/product",
        field_name="price",
        raw_text="$19.99",
        normalized_value="USD 19.99",
        amount=19.99,
        currency="USD",
        source_anchor_ref="source-anchor:price",
        artifact_ref="artifact:1",
        content_hash_ref="hash:1",
        canonical_url_ref="canonical:1",
        model_call_trace_ref="model-call:1",
        agent_action_trace_ref="agent-action:1",
        tool_call_trace_refs=["tool:1"],
        context_bundle_trace_ref="context:1",
        evidence_packet_ref="evidence-packet:1",
        evidence_anchor_ref="evidence-anchor:1",
        verification_decision_ref="verification:1",
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:1",
    )


def _site() -> ProductAvailabilitySiteResult:
    return ProductAvailabilitySiteResult(
        id="site:1",
        fixture_id="fixture",
        target_spec_ref="target",
        site_name="Example",
        target_url="https://example.com/product",
        live_http_report_ref="live-http:1",
        network_response_ref="network:1",
        status_code=200,
        content_type="text/html",
        body_size_bytes=1024,
        content_digest="hash:1",
        source_observation_refs=["source-observation:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["hash:1"],
        canonical_url_refs=["canonical:1"],
        identity_terms_matched=["SanDisk"],
        field_evidence_refs=["field:identity", "field:price", "field:availability"],
        identity_evidence_ref="field:identity",
        price_evidence_ref="field:price",
        availability_evidence_ref="field:availability",
        price_raw_text="$19.99",
        price_amount=19.99,
        price_currency="USD",
        availability_status=ProductAvailabilityStatus.IN_STOCK,
        availability_raw_text="In Stock",
        model_call_trace_refs=["model-call:1"],
        agent_action_trace_refs=["agent-action:1"],
        tool_call_trace_refs=["tool:1"],
        context_bundle_trace_refs=["context:1"],
        evidence_packet_refs=["evidence-packet:1"],
        evidence_anchor_refs=["evidence-anchor:1"],
        verification_decision_refs=["verification:1"],
        publication_gate_refs=["publication-gate:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay:1"],
        completion_result=CompletenessResult.PASS,
    )


def _report() -> ProductAvailabilityBenchmarkReport:
    return ProductAvailabilityBenchmarkReport(
        id="report:1",
        fixture_id="fixture",
        run_ref="run:fixture",
        product_name="SanDisk",
        target_site_count=1,
        site_result_refs=["site:1"],
        passing_site_result_refs=["site:1"],
        field_evidence_refs=["field:price"],
        price_evidence_refs=["field:price"],
        availability_evidence_refs=["field:availability"],
        model_call_trace_refs=["model-call:1"],
        agent_action_trace_refs=["agent-action:1"],
        tool_call_trace_refs=["tool:1"],
        context_bundle_trace_refs=["context:1"],
        evidence_packet_refs=["evidence-packet:1"],
        evidence_anchor_refs=["evidence-anchor:1"],
        verification_decision_refs=["verification:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay:1"],
        operator_status="product_availability_benchmark_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_replay_helpers_require_product_availability_replay_refs() -> None:
    assert product_availability_field_replay_passes(_field())
    assert product_availability_site_replay_passes(_site())
    assert product_availability_report_replay_passes(_report())
    assert not product_availability_field_replay_passes(
        _field().model_copy(update={"replay_bundle_ref": ""})
    )
