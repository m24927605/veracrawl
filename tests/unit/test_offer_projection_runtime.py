from __future__ import annotations

from veracrawl.benchmarks.offer_projection import build_product_offer_projection
from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductAvailabilityFailureType,
    ProductAvailabilityStatus,
)
from veracrawl.contracts.product_availability import (
    ProductAvailabilityFieldEvidence,
    ProductAvailabilitySiteResult,
)


def _field(
    target: str,
    field_name: str,
    *,
    raw: str,
    normalized: str,
    amount: float | None = None,
    currency: str | None = None,
) -> ProductAvailabilityFieldEvidence:
    return ProductAvailabilityFieldEvidence(
        id=f"field:{target}:{field_name}",
        fixture_id="fixture",
        target_spec_ref=target,
        site_name=f"Site {target}",
        target_url=f"https://example.com/{target}",
        field_name=field_name,
        raw_text=raw,
        normalized_value=normalized,
        amount=amount,
        currency=currency,
        source_anchor_ref=f"source-anchor:{target}:{field_name}",
        artifact_ref=f"artifact:{target}",
        content_hash_ref=f"hash:{target}",
        canonical_url_ref=f"canonical:{target}",
        model_call_trace_ref=f"model-call:{target}:{field_name}",
        agent_action_trace_ref=f"agent-action:{target}:{field_name}",
        tool_call_trace_refs=[f"tool:{target}:{field_name}"],
        context_bundle_trace_ref=f"context:{target}:{field_name}",
        evidence_packet_ref=f"evidence-packet:{target}:{field_name}",
        evidence_anchor_ref=f"evidence-anchor:{target}:{field_name}",
        verification_decision_ref=f"verification:{target}:{field_name}",
        policy_decision_refs=[f"policy:{target}"],
        command_record_refs=[f"command:{target}:{field_name}"],
        event_cursor_refs=[f"event:{target}:{field_name}"],
        outbox_refs=[f"outbox:{target}:{field_name}"],
        replay_bundle_ref=f"replay:{target}:{field_name}",
    )


def _pass_site(
    target: str,
    *,
    price: float,
    shipping: float,
    delivery_min_days: int,
    availability: ProductAvailabilityStatus = ProductAvailabilityStatus.IN_STOCK,
) -> ProductAvailabilitySiteResult:
    evidence_refs = [
        f"field:{target}:identity",
        f"field:{target}:price",
        f"field:{target}:availability",
        f"field:{target}:delivery_eta",
        f"field:{target}:shipping_fee",
    ]
    return ProductAvailabilitySiteResult(
        id=f"site:{target}",
        fixture_id="fixture",
        target_spec_ref=target,
        site_name=f"Site {target}",
        target_url=f"https://example.com/{target}",
        live_http_report_ref=f"live-http:{target}",
        network_response_ref=f"network:{target}",
        status_code=200,
        content_type="text/html",
        body_size_bytes=1024,
        content_digest=f"hash:{target}",
        source_observation_refs=[f"source-observation:{target}"],
        artifact_refs=[f"artifact:{target}"],
        content_hash_refs=[f"hash:{target}"],
        canonical_url_refs=[f"canonical:{target}"],
        identity_terms_matched=["SanDisk", "256GB"],
        field_evidence_refs=evidence_refs,
        identity_evidence_ref=evidence_refs[0],
        price_evidence_ref=evidence_refs[1],
        availability_evidence_ref=evidence_refs[2],
        price_raw_text=f"USD {price}",
        price_amount=price,
        price_currency="USD",
        availability_status=availability,
        availability_raw_text=availability.value,
        delivery_evidence_ref=evidence_refs[3],
        delivery_eta_raw_text=f"arrives in {delivery_min_days} days",
        delivery_eta_min_days=delivery_min_days,
        delivery_eta_max_days=delivery_min_days,
        shipping_fee_evidence_ref=evidence_refs[4],
        shipping_fee_raw_text=f"shipping {shipping}",
        shipping_fee_amount=shipping,
        shipping_fee_currency="USD",
        total_price_amount=price + shipping,
        total_price_currency="USD",
        model_call_trace_refs=[f"model-call:{target}"],
        agent_action_trace_refs=[f"agent-action:{target}"],
        tool_call_trace_refs=[f"tool:{target}"],
        context_bundle_trace_refs=[f"context:{target}"],
        evidence_packet_refs=[f"evidence-packet:{target}"],
        evidence_anchor_refs=[f"evidence-anchor:{target}"],
        verification_decision_refs=[f"verification:{target}"],
        publication_gate_refs=[f"publication:{target}"],
        policy_decision_refs=[f"policy:{target}"],
        command_record_refs=[f"command:{target}"],
        event_cursor_refs=[f"event:{target}"],
        outbox_refs=[f"outbox:{target}"],
        replay_bundle_refs=[f"replay:{target}"],
        completion_result=CompletenessResult.PASS,
    )


def _blocked_site(target: str) -> ProductAvailabilitySiteResult:
    return ProductAvailabilitySiteResult(
        id=f"site:{target}",
        fixture_id="fixture",
        target_spec_ref=target,
        site_name=f"Site {target}",
        target_url=f"https://example.com/{target}",
        blocked_source_refs=[f"blocked:{target}"],
        failure_report_refs=[f"failure:{target}"],
        missing_ref_fields=["source_backed_product_identity"],
        failure_type=ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED,
        diagnostics=["source access denied"],
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )


def _fields_for(
    target: str, price: float, shipping: float, delivery_days: int
) -> list[ProductAvailabilityFieldEvidence]:
    return [
        _field(target, "identity", raw="SanDisk 256GB", normalized="SanDisk,256GB"),
        _field(
            target,
            "price",
            raw=f"USD {price}",
            normalized=f"USD {price}",
            amount=price,
            currency="USD",
        ),
        _field(target, "availability", raw="In Stock", normalized="in_stock"),
        _field(
            target,
            "delivery_eta",
            raw=f"arrives in {delivery_days} days",
            normalized=f"{delivery_days}-{delivery_days} days",
        ),
        _field(
            target,
            "shipping_fee",
            raw=f"shipping {shipping}",
            normalized=f"USD {shipping}",
            amount=shipping,
            currency="USD",
        ),
    ]


def test_offer_projection_sorts_by_price_total_delivery_and_availability() -> None:
    cheap = _pass_site("cheap", price=90.0, shipping=15.0, delivery_min_days=4)
    fast = _pass_site("fast", price=110.0, shipping=0.0, delivery_min_days=1)
    result = build_product_offer_projection(
        fixture_id="fixture",
        product_name="SanDisk 256GB",
        run_ref="run:fixture",
        site_results=[fast, cheap],
        field_evidence=[
            *_fields_for("cheap", price=90.0, shipping=15.0, delivery_days=4),
            *_fields_for("fast", price=110.0, shipping=0.0, delivery_days=1),
        ],
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.sorted_by_price_refs[0].endswith(":cheap")
    assert result.report.sorted_by_total_price_refs[0].endswith(":cheap")
    assert result.report.sorted_by_delivery_refs[0].endswith(":fast")
    assert result.report.sorted_by_availability_refs == [
        "sortable-product-offer:fixture:cheap",
        "sortable-product-offer:fixture:fast",
    ]


def test_offer_projection_records_blocked_sources_without_fabricated_sort() -> None:
    fast = _pass_site("fast", price=110.0, shipping=0.0, delivery_min_days=1)
    blocked = _blocked_site("blocked")
    result = build_product_offer_projection(
        fixture_id="fixture",
        product_name="SanDisk 256GB",
        run_ref="run:fixture",
        site_results=[fast, blocked],
        field_evidence=_fields_for("fast", price=110.0, shipping=0.0, delivery_days=1),
    )

    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.sortable_offer_refs == ["sortable-product-offer:fixture:fast"]
    assert result.report.blocked_offer_refs == ["sortable-product-offer:fixture:blocked"]
    assert result.offer_records[1].failure_type == "product_availability_source_access_denied"
