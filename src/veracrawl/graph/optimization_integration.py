"""Graph-owned canonical dedupe and identity optimization integration."""

from __future__ import annotations

from veracrawl.contracts.crawler_optimization import DedupeIdentityOptimizationIntegration
from veracrawl.optimization.runtime import RuntimeDedupeRankingResult


def integrate_dedupe_identity_optimization(
    result: RuntimeDedupeRankingResult,
) -> DedupeIdentityOptimizationIntegration:
    variant_refs = [
        identity.candidate_ref
        for identity in result.identity_decisions
        if identity.decision == "variant"
    ]
    return DedupeIdentityOptimizationIntegration(
        id=f"dedupe-identity-optimization-integration:{result.duplicate_suppression.fixture_id}",
        fixture_id=result.duplicate_suppression.fixture_id,
        canonicalization_refs=[decision.id for decision in result.canonicalization_decisions],
        fingerprint_refs=[fingerprint.id for fingerprint in result.fingerprints],
        identity_decision_refs=[identity.id for identity in result.identity_decisions],
        duplicate_suppression_ref=result.duplicate_suppression.id,
        retained_refs=result.duplicate_suppression.retained_refs,
        suppressed_refs=result.duplicate_suppression.suppressed_refs,
        variant_refs=variant_refs,
        policy_decision_refs=result.runtime_decision.policy_decision_refs,
        command_record_refs=[
            f"command:dedupe-identity-opt:{result.duplicate_suppression.fixture_id}"
        ],
        event_cursor_refs=[
            f"event-cursor:dedupe-identity-opt:{result.duplicate_suppression.fixture_id}"
        ],
        outbox_refs=[f"outbox:dedupe-identity-opt:{result.duplicate_suppression.fixture_id}"],
        replay_bundle_ref=f"replay-bundle:dedupe-identity-opt:{result.duplicate_suppression.fixture_id}",
    )
