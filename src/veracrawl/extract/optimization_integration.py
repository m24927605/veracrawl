"""Extract/verify-owned adoption of optimization fallback context."""

from __future__ import annotations

from veracrawl.contracts.crawler_optimization import ExtractVerifyOptimizationIntegration
from veracrawl.optimization.runtime import RuntimeDomExtractionResult


def integrate_extract_verify_optimization(
    result: RuntimeDomExtractionResult,
) -> ExtractVerifyOptimizationIntegration:
    threshold = result.extractor_plan.confidence_threshold
    accepted = [
        attempt.id
        for attempt in result.extractor_attempts
        if attempt.accepted
        and attempt.confidence >= threshold
        and not attempt.llm_output_evidence_refs
    ]
    llm_only_rejected = [
        ref
        for attempt in result.extractor_attempts
        for ref in attempt.llm_output_evidence_refs
    ]
    rejected = [
        attempt.id
        for attempt in result.extractor_attempts
        if not attempt.accepted
        or attempt.confidence < threshold
        or bool(attempt.llm_output_evidence_refs)
    ]
    abstentions = [abstention.id for abstention in result.abstentions if abstention.abstain]
    reviews = [
        ref
        for abstention in result.abstentions
        for ref in ([abstention.review_queue_ref] if abstention.review_queue_ref else [])
    ]
    reviews.extend(f"review:llm-only:{ref}" for ref in llm_only_rejected)
    eligible_fields = [
        confidence.id
        for confidence in result.field_confidences
        if confidence.extracted_value_ref in set(accepted)
    ]
    return ExtractVerifyOptimizationIntegration(
        id=f"extract-verify-optimization-integration:{result.extractor_plan.fixture_id}",
        fixture_id=result.extractor_plan.fixture_id,
        normalized_document_ref=result.runtime_context.normalized_document_ref,
        extractor_plan_ref=result.extractor_plan.id,
        accepted_attempt_refs=accepted,
        rejected_attempt_refs=rejected,
        field_confidence_refs=[confidence.id for confidence in result.field_confidences],
        abstention_refs=abstentions,
        review_refs=reviews,
        publication_eligible_field_refs=eligible_fields,
        llm_only_rejected_refs=llm_only_rejected,
        policy_decision_refs=result.runtime_context.policy_decision_refs,
        command_record_refs=[f"command:extract-verify-opt:{result.extractor_plan.fixture_id}"],
        event_cursor_refs=[f"event-cursor:extract-verify-opt:{result.extractor_plan.fixture_id}"],
        outbox_refs=[f"outbox:extract-verify-opt:{result.extractor_plan.fixture_id}"],
        replay_bundle_ref=f"replay-bundle:extract-verify-opt:{result.extractor_plan.fixture_id}",
    )
