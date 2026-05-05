"""Normalize-owned adoption of DOM optimization context."""

from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    NormalizeOptimizationIntegration,
)
from veracrawl.optimization.runtime import RuntimeDomExtractionResult


def integrate_normalize_optimization(
    result: RuntimeDomExtractionResult,
) -> NormalizeOptimizationIntegration:
    dom = result.dom_context
    original = max(dom.original_node_count, 1)
    reduction = round(1.0 - (dom.retained_node_count / original), 4)
    return NormalizeOptimizationIntegration(
        id=f"normalize-optimization-integration:{dom.fixture_id}",
        fixture_id=dom.fixture_id,
        normalized_document_ref=result.runtime_context.normalized_document_ref,
        dom_context_ref=dom.id,
        retained_node_refs=dom.retained_node_refs,
        page_zone_refs=dom.zone_classification_refs,
        interactive_element_refs=dom.interactive_element_refs,
        context_reduction_ratio=max(0.0, min(1.0, reduction)),
        artifact_refs=[dom.html_artifact_ref, dom.pruned_dom_ref, dom.dom_hash_ref],
        policy_decision_refs=dom.policy_decision_refs,
        command_record_refs=[f"command:normalize-opt:{dom.fixture_id}"],
        event_cursor_refs=[f"event-cursor:normalize-opt:{dom.fixture_id}"],
        outbox_refs=[f"outbox:normalize-opt:{dom.fixture_id}"],
        replay_bundle_ref=f"replay-bundle:normalize-opt:{dom.fixture_id}",
    )
