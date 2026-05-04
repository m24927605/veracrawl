from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, ProductAvailabilityStatus
from veracrawl.contracts.offer_projection import (
    ProductOfferProjectionManifest,
    ProductOfferProjectionReport,
    SortableProductOfferRecord,
)


def _offer(**overrides: object) -> SortableProductOfferRecord:
    data: dict[str, object] = {
        "id": "offer:1",
        "fixture_id": "fixture",
        "product_name": "SanDisk 256GB",
        "target_spec_ref": "target:1",
        "source_site_result_ref": "site:1",
        "site_name": "Example",
        "offer_url": "https://example.com/product",
        "field_evidence_refs": ["field:identity", "field:price", "field:availability"],
        "price_evidence_ref": "field:price",
        "availability_evidence_ref": "field:availability",
        "delivery_evidence_ref": "field:delivery",
        "shipping_fee_evidence_ref": "field:shipping",
        "price_amount": 100.0,
        "price_currency": "USD",
        "shipping_fee_amount": 0.0,
        "shipping_fee_currency": "USD",
        "total_price_amount": 100.0,
        "total_price_currency": "USD",
        "availability_status": ProductAvailabilityStatus.IN_STOCK,
        "availability_sort_rank": 0,
        "delivery_eta_raw_text": "arrives tomorrow",
        "delivery_eta_min_days": 1,
        "delivery_eta_max_days": 1,
        "delivery_sort_rank": 1,
        "price_sort_amount": 100.0,
        "total_price_sort_amount": 100.0,
        "source_anchor_refs": ["source-anchor:price"],
        "artifact_refs": ["artifact:1"],
        "content_hash_refs": ["hash:1"],
        "canonical_url_refs": ["canonical:1"],
        "verification_decision_refs": ["verification:1"],
        "policy_decision_refs": ["policy:1"],
        "command_record_refs": ["command:1"],
        "event_cursor_refs": ["event:1"],
        "outbox_refs": ["outbox:1"],
        "replay_bundle_refs": ["replay:1"],
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return SortableProductOfferRecord(**data)


def _report(**overrides: object) -> ProductOfferProjectionReport:
    data: dict[str, object] = {
        "id": "offer-projection:1",
        "fixture_id": "fixture",
        "run_ref": "run:fixture",
        "product_name": "SanDisk 256GB",
        "target_site_count": 1,
        "offer_record_refs": ["offer:1"],
        "sortable_offer_refs": ["offer:1"],
        "sorted_by_price_refs": ["offer:1"],
        "sorted_by_total_price_refs": ["offer:1"],
        "sorted_by_delivery_refs": ["offer:1"],
        "sorted_by_availability_refs": ["offer:1"],
        "price_evidence_refs": ["field:price"],
        "availability_evidence_refs": ["field:availability"],
        "delivery_evidence_refs": ["field:delivery"],
        "shipping_fee_evidence_refs": ["field:shipping"],
        "source_anchor_refs": ["source-anchor:price"],
        "artifact_refs": ["artifact:1"],
        "content_hash_refs": ["hash:1"],
        "canonical_url_refs": ["canonical:1"],
        "verification_decision_refs": ["verification:1"],
        "policy_decision_refs": ["policy:1"],
        "command_record_refs": ["command:1"],
        "event_cursor_refs": ["event:1"],
        "outbox_refs": ["outbox:1"],
        "replay_bundle_refs": ["replay:1"],
        "operator_status": "product_offer_projection_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return ProductOfferProjectionReport(**data)


def test_offer_record_requires_source_backed_sort_refs() -> None:
    assert _offer().total_price_amount == 100.0
    with pytest.raises(ValidationError):
        _offer(price_evidence_ref=None)


def test_offer_record_rejects_delivery_sort_without_evidence() -> None:
    with pytest.raises(ValidationError):
        _offer(delivery_evidence_ref=None)


def test_offer_projection_report_requires_sortable_refs() -> None:
    assert _report().completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        _report(sorted_by_price_refs=[])


def test_offer_projection_manifest_declares_sort_keys() -> None:
    manifest = ProductOfferProjectionManifest(
        id="manifest:offer",
        scenario="delivery-price-sorting",
        profile_refs=["target"],
        product_availability_fixture_ref="fixture:product-availability",
        required_sort_keys=["price", "total_price", "delivery_eta", "availability"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="product_offer_projection_completed",
        required_ref_types=["field_evidence", "replay"],
    )
    assert "delivery_eta" in manifest.required_sort_keys
