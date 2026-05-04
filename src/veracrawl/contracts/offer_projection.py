"""Sortable ecommerce offer projection contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, ProductAvailabilityStatus


class SortableProductOfferRecord(TimestampedModel):
    id: str
    fixture_id: str
    product_name: str
    target_spec_ref: Ref
    source_site_result_ref: Ref
    site_name: str
    offer_url: str
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    price_evidence_ref: Ref | None = None
    availability_evidence_ref: Ref | None = None
    delivery_evidence_ref: Ref | None = None
    shipping_fee_evidence_ref: Ref | None = None
    price_amount: float | None = None
    price_currency: str | None = None
    shipping_fee_amount: float | None = None
    shipping_fee_currency: str | None = None
    total_price_amount: float | None = None
    total_price_currency: str | None = None
    availability_status: ProductAvailabilityStatus | None = None
    availability_sort_rank: int
    delivery_eta_raw_text: str | None = None
    delivery_eta_min_days: int | None = None
    delivery_eta_max_days: int | None = None
    delivery_sort_rank: int
    price_sort_amount: float | None = None
    total_price_sort_amount: float | None = None
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    failure_type: str | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_offer_record(self) -> SortableProductOfferRecord:
        if self.availability_sort_rank < 0 or self.delivery_sort_rank < 0:
            raise ValueError("offer sort ranks must be non-negative")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "field_evidence_refs": self.field_evidence_refs,
                "price_evidence_ref": self.price_evidence_ref,
                "availability_evidence_ref": self.availability_evidence_ref,
                "price_amount": self.price_amount,
                "price_currency": self.price_currency,
                "availability_status": self.availability_status,
                "source_anchor_refs": self.source_anchor_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.blocked_source_refs:
                raise ValueError(f"passing offer record missing refs: {missing}")
            if self.delivery_evidence_ref is None and self.delivery_eta_min_days is not None:
                raise ValueError("delivery ETA sort data requires delivery evidence ref")
            if self.shipping_fee_amount is not None and self.shipping_fee_evidence_ref is None:
                raise ValueError("shipping fee sort data requires shipping evidence ref")
        elif not (self.blocked_source_refs and self.failure_type and self.diagnostics):
            raise ValueError("non-pass offer record requires typed diagnostics")
        return self


class ProductOfferProjectionReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    product_name: str
    target_site_count: int
    offer_record_refs: list[Ref] = Field(default_factory=list)
    sortable_offer_refs: list[Ref] = Field(default_factory=list)
    blocked_offer_refs: list[Ref] = Field(default_factory=list)
    sorted_by_price_refs: list[Ref] = Field(default_factory=list)
    sorted_by_total_price_refs: list[Ref] = Field(default_factory=list)
    sorted_by_delivery_refs: list[Ref] = Field(default_factory=list)
    sorted_by_availability_refs: list[Ref] = Field(default_factory=list)
    price_evidence_refs: list[Ref] = Field(default_factory=list)
    availability_evidence_refs: list[Ref] = Field(default_factory=list)
    delivery_evidence_refs: list[Ref] = Field(default_factory=list)
    shipping_fee_evidence_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_projection_report(self) -> ProductOfferProjectionReport:
        if self.target_site_count < 1:
            raise ValueError("offer projection target count must be positive")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "offer_record_refs": self.offer_record_refs,
                "sortable_offer_refs": self.sortable_offer_refs,
                "sorted_by_price_refs": self.sorted_by_price_refs,
                "sorted_by_total_price_refs": self.sorted_by_total_price_refs,
                "sorted_by_availability_refs": self.sorted_by_availability_refs,
                "price_evidence_refs": self.price_evidence_refs,
                "availability_evidence_refs": self.availability_evidence_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.blocked_offer_refs or self.blocked_source_refs:
                raise ValueError(f"passing offer projection missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not self.sortable_offer_refs or not self.blocked_offer_refs:
                raise ValueError("needs-review offer projection requires sorted and blocked refs")
            if not self.diagnostics:
                raise ValueError("needs-review offer projection requires diagnostics")
        elif not (self.blocked_offer_refs and self.diagnostics):
            raise ValueError("failed offer projection requires typed diagnostics")
        return self


class ProductOfferProjectionManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    product_availability_fixture_ref: Ref
    required_sort_keys: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> ProductOfferProjectionManifest:
        if "target" not in self.profile_refs:
            raise ValueError("offer projection manifest must support target profile")
        if not self.product_availability_fixture_ref:
            raise ValueError("offer projection requires product availability fixture ref")
        if not self.required_sort_keys:
            raise ValueError("offer projection requires sort keys")
        if not self.required_ref_types:
            raise ValueError("offer projection requires ref types")
        return self
