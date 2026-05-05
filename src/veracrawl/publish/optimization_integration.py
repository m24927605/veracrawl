"""Publish-owned ranking optimization integration."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import RankingPublicationOptimizationIntegration
from veracrawl.optimization.runtime import RuntimeDedupeRankingResult


def integrate_ranking_publication_optimization(
    result: RuntimeDedupeRankingResult,
    *,
    verification_status_refs: list[Ref] | None = None,
    publication_gate_refs: list[Ref] | None = None,
    missing_optional_feature_refs: list[Ref] | None = None,
) -> RankingPublicationOptimizationIntegration:
    retained = result.ranked_output_set.sorted_item_refs
    return RankingPublicationOptimizationIntegration(
        id=f"ranking-publication-optimization-integration:{result.ranked_output_set.fixture_id}",
        fixture_id=result.ranked_output_set.fixture_id,
        ranked_output_set_ref=result.ranked_output_set.id,
        ranking_score_refs=result.ranked_output_set.score_refs,
        retained_output_refs=retained,
        verification_status_refs=verification_status_refs
        or [f"verification-status:{item_ref}:accepted" for item_ref in retained],
        publication_gate_refs=publication_gate_refs
        or [f"publication-gate:{item_ref}:accepted" for item_ref in retained],
        missing_optional_feature_refs=missing_optional_feature_refs or [],
        policy_decision_refs=result.ranked_output_set.policy_decision_refs,
        command_record_refs=[f"command:ranking-publication-opt:{result.ranked_output_set.fixture_id}"],
        event_cursor_refs=[
            f"event-cursor:ranking-publication-opt:{result.ranked_output_set.fixture_id}"
        ],
        outbox_refs=[f"outbox:ranking-publication-opt:{result.ranked_output_set.fixture_id}"],
        replay_bundle_ref=f"replay-bundle:ranking-publication-opt:{result.ranked_output_set.fixture_id}",
    )
