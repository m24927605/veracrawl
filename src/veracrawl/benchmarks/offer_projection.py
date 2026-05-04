"""Sortable product offer projection runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult, ProductAvailabilityStatus
from veracrawl.contracts.offer_projection import (
    ProductOfferProjectionReport,
    SortableProductOfferRecord,
)
from veracrawl.contracts.product_availability import (
    ProductAvailabilityFieldEvidence,
    ProductAvailabilitySiteResult,
)


@dataclass(frozen=True)
class ProductOfferProjectionResult:
    report: ProductOfferProjectionReport
    offer_records: list[SortableProductOfferRecord]


def build_product_offer_projection(
    *,
    fixture_id: str,
    product_name: str,
    run_ref: Ref,
    site_results: list[ProductAvailabilitySiteResult],
    field_evidence: list[ProductAvailabilityFieldEvidence],
) -> ProductOfferProjectionResult:
    evidence_by_id = {item.id: item for item in field_evidence}
    offer_records = [
        _offer_record(
            fixture_id=fixture_id,
            product_name=product_name,
            site_result=site_result,
            evidence_by_id=evidence_by_id,
        )
        for site_result in site_results
    ]
    sortable = [item for item in offer_records if item.completion_result == CompletenessResult.PASS]
    blocked = [item for item in offer_records if item.completion_result != CompletenessResult.PASS]
    if sortable and not blocked:
        completion = CompletenessResult.PASS
        operator_status = "product_offer_projection_completed"
        diagnostics: list[str] = []
    elif sortable:
        completion = CompletenessResult.NEEDS_REVIEW
        operator_status = "product_offer_projection_partial_sources_blocked"
        diagnostics = [message for item in blocked for message in item.diagnostics]
    else:
        completion = CompletenessResult.FAIL
        operator_status = "product_offer_projection_no_sortable_offers"
        diagnostics = [message for item in blocked for message in item.diagnostics] or [
            "no product offers had source-backed price and availability evidence"
        ]

    report = ProductOfferProjectionReport(
        id=f"product-offer-projection-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        product_name=product_name,
        target_site_count=len(site_results),
        offer_record_refs=[item.id for item in offer_records],
        sortable_offer_refs=[item.id for item in sortable],
        blocked_offer_refs=[item.id for item in blocked],
        sorted_by_price_refs=[
            item.id
            for item in sorted(
                sortable,
                key=lambda item: (
                    item.price_sort_amount is None,
                    item.price_sort_amount or 0.0,
                    item.site_name,
                ),
            )
        ],
        sorted_by_total_price_refs=[
            item.id
            for item in sorted(
                sortable,
                key=lambda item: (
                    item.total_price_sort_amount is None,
                    item.total_price_sort_amount or 0.0,
                    item.site_name,
                ),
            )
        ],
        sorted_by_delivery_refs=[
            item.id
            for item in sorted(
                sortable,
                key=lambda item: (
                    item.delivery_sort_rank,
                    item.delivery_eta_max_days or _UNKNOWN_SORT_RANK,
                    item.site_name,
                ),
            )
        ],
        sorted_by_availability_refs=[
            item.id
            for item in sorted(
                sortable,
                key=lambda item: (item.availability_sort_rank, item.site_name),
            )
        ],
        price_evidence_refs=_collect_optional("price_evidence_ref", sortable),
        availability_evidence_refs=_collect_optional("availability_evidence_ref", sortable),
        delivery_evidence_refs=_collect_optional("delivery_evidence_ref", sortable),
        shipping_fee_evidence_refs=_collect_optional("shipping_fee_evidence_ref", sortable),
        source_anchor_refs=_collect("source_anchor_refs", sortable),
        artifact_refs=_collect("artifact_refs", sortable),
        content_hash_refs=_collect("content_hash_refs", sortable),
        canonical_url_refs=_collect("canonical_url_refs", sortable),
        verification_decision_refs=_collect("verification_decision_refs", sortable),
        policy_decision_refs=_collect("policy_decision_refs", offer_records),
        command_record_refs=sorted(
            set(
                _collect("command_record_refs", offer_records)
                + [f"command:{fixture_id}:offer-projection"]
            )
        ),
        event_cursor_refs=sorted(
            set(
                _collect("event_cursor_refs", offer_records)
                + [f"event-cursor:{fixture_id}:offer-projection"]
            )
        ),
        outbox_refs=sorted(
            set(_collect("outbox_refs", offer_records) + [f"outbox:{fixture_id}:offer-projection"])
        ),
        replay_bundle_refs=sorted(
            set(
                _collect("replay_bundle_refs", offer_records)
                + [f"replay-bundle:{fixture_id}:offer-projection"]
            )
        ),
        blocked_source_refs=_collect("blocked_source_refs", blocked),
        diagnostics=diagnostics,
        operator_status=operator_status,
        completion_result=completion,
    )
    return ProductOfferProjectionResult(report=report, offer_records=offer_records)


_UNKNOWN_SORT_RANK = 999_999


def _offer_record(
    *,
    fixture_id: str,
    product_name: str,
    site_result: ProductAvailabilitySiteResult,
    evidence_by_id: dict[Ref, ProductAvailabilityFieldEvidence],
) -> SortableProductOfferRecord:
    if site_result.completion_result != CompletenessResult.PASS:
        return SortableProductOfferRecord(
            id=f"sortable-product-offer:{fixture_id}:{site_result.target_spec_ref}",
            fixture_id=fixture_id,
            product_name=product_name,
            target_spec_ref=site_result.target_spec_ref,
            source_site_result_ref=site_result.id,
            site_name=site_result.site_name,
            offer_url=site_result.target_url,
            availability_sort_rank=_UNKNOWN_SORT_RANK,
            delivery_sort_rank=_UNKNOWN_SORT_RANK,
            policy_decision_refs=site_result.policy_decision_refs,
            command_record_refs=site_result.command_record_refs,
            event_cursor_refs=site_result.event_cursor_refs,
            outbox_refs=site_result.outbox_refs,
            replay_bundle_refs=site_result.replay_bundle_refs,
            blocked_source_refs=site_result.blocked_source_refs
            or site_result.failure_report_refs
            or [f"blocked-source:{fixture_id}:{site_result.target_spec_ref}:not-sortable"],
            failure_type=(
                site_result.failure_type.value
                if site_result.failure_type is not None
                else "product_offer_projection_source_not_sortable"
            ),
            diagnostics=site_result.diagnostics
            or ["site result did not pass source-backed product availability gates"],
            completion_result=site_result.completion_result,
        )

    field_evidence = [
        item
        for ref in site_result.field_evidence_refs
        if (item := evidence_by_id.get(ref)) is not None
    ]
    total_price, total_currency = _total_price(
        price_amount=site_result.price_amount,
        price_currency=site_result.price_currency,
        shipping_amount=site_result.shipping_fee_amount,
        shipping_currency=site_result.shipping_fee_currency,
    )
    return SortableProductOfferRecord(
        id=f"sortable-product-offer:{fixture_id}:{site_result.target_spec_ref}",
        fixture_id=fixture_id,
        product_name=product_name,
        target_spec_ref=site_result.target_spec_ref,
        source_site_result_ref=site_result.id,
        site_name=site_result.site_name,
        offer_url=site_result.target_url,
        field_evidence_refs=[item.id for item in field_evidence],
        price_evidence_ref=site_result.price_evidence_ref,
        availability_evidence_ref=site_result.availability_evidence_ref,
        delivery_evidence_ref=site_result.delivery_evidence_ref,
        shipping_fee_evidence_ref=site_result.shipping_fee_evidence_ref,
        price_amount=site_result.price_amount,
        price_currency=site_result.price_currency,
        shipping_fee_amount=site_result.shipping_fee_amount,
        shipping_fee_currency=site_result.shipping_fee_currency,
        total_price_amount=total_price,
        total_price_currency=total_currency,
        availability_status=site_result.availability_status,
        availability_sort_rank=_availability_rank(site_result.availability_status),
        delivery_eta_raw_text=site_result.delivery_eta_raw_text,
        delivery_eta_min_days=site_result.delivery_eta_min_days,
        delivery_eta_max_days=site_result.delivery_eta_max_days,
        delivery_sort_rank=_delivery_rank(site_result.delivery_eta_min_days),
        price_sort_amount=site_result.price_amount,
        total_price_sort_amount=total_price,
        source_anchor_refs=sorted({item.source_anchor_ref for item in field_evidence}),
        artifact_refs=sorted(
            set(site_result.artifact_refs + [item.artifact_ref for item in field_evidence])
        ),
        content_hash_refs=sorted(
            set(site_result.content_hash_refs + [item.content_hash_ref for item in field_evidence])
        ),
        canonical_url_refs=sorted(
            set(
                site_result.canonical_url_refs + [item.canonical_url_ref for item in field_evidence]
            )
        ),
        verification_decision_refs=sorted(
            set(
                site_result.verification_decision_refs
                + [item.verification_decision_ref for item in field_evidence]
            )
        ),
        policy_decision_refs=site_result.policy_decision_refs,
        command_record_refs=site_result.command_record_refs
        + [f"command:{fixture_id}:{site_result.target_spec_ref}:offer-record"],
        event_cursor_refs=site_result.event_cursor_refs
        + [f"event-cursor:{fixture_id}:{site_result.target_spec_ref}:offer-record"],
        outbox_refs=site_result.outbox_refs
        + [f"outbox:{fixture_id}:{site_result.target_spec_ref}:offer-record"],
        replay_bundle_refs=site_result.replay_bundle_refs
        + [f"replay-bundle:{fixture_id}:{site_result.target_spec_ref}:offer-record"],
        completion_result=CompletenessResult.PASS,
    )


def _total_price(
    *,
    price_amount: float | None,
    price_currency: str | None,
    shipping_amount: float | None,
    shipping_currency: str | None,
) -> tuple[float | None, str | None]:
    if price_amount is None or price_currency is None:
        return None, None
    if shipping_amount is None:
        return price_amount, price_currency
    if shipping_currency != price_currency:
        return None, None
    return price_amount + shipping_amount, price_currency


def _availability_rank(status: ProductAvailabilityStatus | None) -> int:
    if status is None:
        return _UNKNOWN_SORT_RANK
    ranks = {
        ProductAvailabilityStatus.IN_STOCK: 0,
        ProductAvailabilityStatus.LIMITED: 1,
        ProductAvailabilityStatus.UNKNOWN: 2,
        ProductAvailabilityStatus.OUT_OF_STOCK: 3,
        ProductAvailabilityStatus.UNAVAILABLE: 4,
    }
    return ranks[status]


def _delivery_rank(min_days: int | None) -> int:
    return min_days if min_days is not None else _UNKNOWN_SORT_RANK


def _collect(
    field_name: str,
    records: list[SortableProductOfferRecord],
) -> list[Ref]:
    refs: list[Ref] = []
    for record in records:
        refs.extend(getattr(record, field_name))
    return sorted(set(refs))


def _collect_optional(
    field_name: str,
    records: list[SortableProductOfferRecord],
) -> list[Ref]:
    refs = [getattr(record, field_name) for record in records]
    return sorted({ref for ref in refs if ref is not None})
