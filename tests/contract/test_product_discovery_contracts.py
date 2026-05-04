from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, ProductDiscoveryFailureType
from veracrawl.contracts.product_discovery import (
    ProductDiscoveryBenchmarkManifest,
    ProductDiscoveryCandidate,
    ProductDiscoveryRunReport,
    ProductDiscoverySourceSpec,
)


def _source() -> ProductDiscoverySourceSpec:
    return ProductDiscoverySourceSpec(
        id="example-search",
        site_name="Example Shop",
        search_url="https://example.com/search?q=iphone%2017%20256G",
        robots_url="https://example.com/robots.txt",
        allowed_origin="https://example.com",
        query="iphone 17 256G",
        required_identity_terms=["iPhone", "17", "256G"],
        candidate_url_patterns=[r"/prod/[A-Za-z0-9-]+"],
    )


def test_product_discovery_manifest_rejects_product_target_specs() -> None:
    payload = {
        "id": "bad",
        "scenario": "bad",
        "profile_refs": ["target"],
        "product_name": "Apple iPhone 17 256G",
        "brand": "Apple",
        "query": "iphone 17 256G",
        "required_identity_terms": ["iPhone", "17", "256G"],
        "source_specs": [_source().model_dump(mode="json")],
        "target_specs": [{"target_url": "https://example.com/prod/iphone-17-256g"}],
        "provider_names": ["Local model runtime"],
        "framework_names": ["VeraCrawl Native Runtime"],
        "expected_completion_result": "pass",
        "expected_operator_status": "product_discovery_ranked_offers_completed",
        "required_ref_types": ["query_discovery", "replay"],
    }
    with pytest.raises(ValidationError):
        ProductDiscoveryBenchmarkManifest.model_validate(payload)


def test_product_discovery_candidate_requires_source_and_trace_refs() -> None:
    candidate = ProductDiscoveryCandidate(
        id="candidate:1",
        fixture_id="fixture",
        source_spec_ref="source:1",
        site_name="Example",
        query="iphone 17 256G",
        search_url="https://example.com/search?q=iphone%2017%20256G",
        candidate_url="https://example.com/prod/iphone-17-256g",
        candidate_rank=1,
        raw_anchor_text="Apple iPhone 17 256G",
        matched_identity_terms=["iPhone", "17", "256G"],
        source_anchor_ref="source-anchor:1",
        artifact_ref="artifact:1",
        content_hash_ref="hash:1",
        canonical_url_ref="canonical:1",
        model_call_trace_ref="model-call:1",
        agent_action_trace_ref="agent-action:1",
        tool_call_trace_refs=["tool:1"],
        context_bundle_trace_ref="context:1",
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:1",
    )

    assert candidate.completion_result == CompletenessResult.PASS


def test_product_discovery_report_requires_ranked_offer_refs_for_pass() -> None:
    with pytest.raises(ValidationError):
        ProductDiscoveryRunReport(
            id="report:bad",
            fixture_id="fixture",
            run_ref="run:1",
            query="iphone 17 256G",
            product_name="Apple iPhone 17 256G",
            source_count=1,
            source_result_refs=["source:1"],
            discovered_candidate_refs=["candidate:1"],
            accepted_candidate_refs=["candidate:1"],
            derived_product_availability_manifest_ref="manifest:derived",
            product_availability_report_ref="product-report:1",
            offer_projection_report_ref="projection:1",
            model_call_trace_refs=["model:1"],
            agent_action_trace_refs=["agent:1"],
            tool_call_trace_refs=["tool:1"],
            context_bundle_trace_refs=["context:1"],
            policy_decision_refs=["policy:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_refs=["replay:1"],
            operator_status="product_discovery_ranked_offers_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_product_discovery_failure_report_requires_typed_diagnostics() -> None:
    report = ProductDiscoveryRunReport(
        id="report:fail",
        fixture_id="fixture",
        run_ref="run:1",
        query="iphone 17 256G",
        product_name="Apple iPhone 17 256G",
        source_count=1,
        source_result_refs=["blocked:1"],
        blocked_source_refs=["blocked:1"],
        failure_report_refs=["failure:1"],
        missing_ref_fields=["discovered_candidate_refs"],
        failure_type=ProductDiscoveryFailureType.NO_CANDIDATES,
        operator_status="product_discovery_no_candidates",
        completion_result=CompletenessResult.FAIL,
        diagnostics=["no source-backed candidates"],
    )

    assert report.failure_type == ProductDiscoveryFailureType.NO_CANDIDATES
