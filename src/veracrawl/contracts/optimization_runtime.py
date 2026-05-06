"""Optimization runtime types shared across modules.

These two dataclasses live in ``contracts/`` rather than
``optimization/runtime.py`` because they appear on both sides of a
producer/consumer boundary:

- ``optimization/runtime.py`` is the producer — it builds these results
  from raw signals.
- The downstream ``extract / graph / normalize / publish / scheduler /
  ops`` packages each have an ``optimization_integration.py`` that
  *consumes* a result and turns it into module-specific decisions.

Importing the producer's types from the consumer creates a cycle
(``optimization → extract → optimization``) that Python only papered
over via function-level imports. Hoisting the contract here breaks that
cycle: the consumer depends on the contract, the producer also depends
on the contract, and nobody imports the producer's runtime module just
for its type aliases.

``optimization/runtime.py`` re-exports both names for backwards
compatibility with any caller still importing them from there.
"""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.crawler_optimization import (
    CanonicalizationDecision,
    ContentFingerprintRecord,
    DomContextBundle,
    DomNodeSummary,
    DuplicateSuppressionRecord,
    ExtractorAbstentionDecision,
    ExtractorAttemptRecord,
    ExtractorFallbackPlan,
    FieldConfidenceScore,
    IdentityResolutionDecision,
    InteractiveElementCandidate,
    PageZoneClassification,
    RankedOutputSet,
    RankingProfile,
    RankingScoreBreakdown,
    RuntimeDedupeRankingDecision,
    RuntimeDomExtractionContext,
)


@dataclass(frozen=True)
class RuntimeDomExtractionResult:
    dom_nodes: list[DomNodeSummary]
    page_zones: list[PageZoneClassification]
    interactive_elements: list[InteractiveElementCandidate]
    dom_context: DomContextBundle
    extractor_plan: ExtractorFallbackPlan
    extractor_attempts: list[ExtractorAttemptRecord]
    field_confidences: list[FieldConfidenceScore]
    abstentions: list[ExtractorAbstentionDecision]
    runtime_context: RuntimeDomExtractionContext


@dataclass(frozen=True)
class RuntimeDedupeRankingResult:
    canonicalization_decisions: list[CanonicalizationDecision]
    fingerprints: list[ContentFingerprintRecord]
    identity_decisions: list[IdentityResolutionDecision]
    duplicate_suppression: DuplicateSuppressionRecord
    ranking_profile: RankingProfile
    ranking_scores: list[RankingScoreBreakdown]
    ranked_output_set: RankedOutputSet
    runtime_decision: RuntimeDedupeRankingDecision
