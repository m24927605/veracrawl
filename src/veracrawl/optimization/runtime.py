"""Runtime wiring for crawler optimization decisions.

This module is intentionally framework-neutral and adapter-free. It converts
runtime-safe refs and deterministic signals into typed optimization contracts
that scheduler, extraction, projection, and ops flows can consume.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.crawler_optimization import (
    CanonicalizationDecision,
    ContentFingerprintRecord,
    CrawlerOptimizationReport,
    DomContextBundle,
    DomNodeSummary,
    DuplicateSuppressionRecord,
    ExtractorAbstentionDecision,
    ExtractorAttemptRecord,
    ExtractorFallbackPlan,
    FieldConfidenceScore,
    FrontierScoreBreakdown,
    FrontierScoringProfile,
    IdentityResolutionDecision,
    InteractiveElementCandidate,
    OptimizationMetricSlice,
    PageZoneClassification,
    RankedOutputSet,
    RankingProfile,
    RankingScoreBreakdown,
    RuntimeDedupeRankingDecision,
    RuntimeDomExtractionContext,
    RuntimeFrontierOptimizationDecision,
    RuntimeOptimizationAggregate,
    RuntimeOptimizationSignalSet,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


@dataclass(frozen=True)
class RuntimeUrlCandidate:
    candidate_url: str
    source_anchor_ref: Ref
    page_type: str
    url_pattern_score: float
    anchor_text_score: float
    page_title_score: float
    semantic_similarity_score: float
    domain_authority_score: float
    freshness_score: float
    historical_success_score: float
    page_type_score: float
    cost_penalty: float = 0.0
    risk_penalty: float = 0.0
    allowed: bool = True
    blocked_reason_refs: tuple[Ref, ...] = ()


@dataclass(frozen=True)
class RuntimeFieldSource:
    field_name: str
    raw_value: str
    normalized_value: str
    source_kind: str
    confidence: float
    accepted: bool = True
    llm_output_evidence_refs: tuple[Ref, ...] = ()


@dataclass(frozen=True)
class RuntimeRankingInput:
    item_ref: Ref
    canonical_url: str
    text: str
    variant_key: str | None = None
    features: dict[str, float] | None = None


@dataclass(frozen=True)
class RuntimeFrontierOptimizationResult:
    signal_sets: list[RuntimeOptimizationSignalSet]
    score_breakdowns: list[FrontierScoreBreakdown]
    decisions: list[RuntimeFrontierOptimizationDecision]


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


_TRACKING_QUERY_PREFIXES = ("utm_",)
_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "msclkid",
    "order",
    "phpsessid",
    "session_id",
    "sessionid",
    "sid",
    "sort",
    "yclid",
}


def runtime_frontier_optimization(
    *,
    fixture_id: str,
    run_ref: Ref,
    objective_ref: Ref,
    profile: FrontierScoringProfile,
    candidates: list[RuntimeUrlCandidate],
) -> RuntimeFrontierOptimizationResult:
    signal_sets: list[RuntimeOptimizationSignalSet] = []
    score_breakdowns: list[FrontierScoreBreakdown] = []
    decisions: list[RuntimeFrontierOptimizationDecision] = []
    for index, candidate in enumerate(candidates, start=1):
        signal = RuntimeOptimizationSignalSet(
            id=f"runtime-signal:{fixture_id}:{index}",
            fixture_id=fixture_id,
            run_ref=run_ref,
            objective_ref=objective_ref,
            candidate_url=candidate.candidate_url,
            source_anchor_ref=candidate.source_anchor_ref if candidate.allowed else None,
            source_signal_refs=_source_signal_refs(fixture_id, index) if candidate.allowed else [],
            policy_decision_refs=[f"policy:runtime-frontier:{fixture_id}:{index}"],
            allowed=candidate.allowed,
            blocked_reason_refs=list(candidate.blocked_reason_refs),
        )
        signal_sets.append(signal)
        if not candidate.allowed:
            decisions.append(
                RuntimeFrontierOptimizationDecision(
                    id=f"runtime-frontier-decision:{fixture_id}:{index}",
                    fixture_id=fixture_id,
                    signal_set_ref=signal.id,
                    candidate_url=candidate.candidate_url,
                    scheduler_action="block",
                    scheduler_priority=0,
                    blocked_reason_refs=list(candidate.blocked_reason_refs),
                    policy_decision_refs=signal.policy_decision_refs,
                    command_record_refs=[f"command:runtime-frontier:{fixture_id}:{index}"],
                    event_cursor_refs=[f"event-cursor:runtime-frontier:{fixture_id}:{index}"],
                    outbox_refs=[f"outbox:runtime-frontier:{fixture_id}:{index}"],
                    replay_bundle_ref=f"replay-bundle:runtime-frontier:{fixture_id}:{index}",
                )
            )
            continue
        final_score = _frontier_score(profile, candidate)
        score = FrontierScoreBreakdown(
            id=f"runtime-frontier-score:{fixture_id}:{index}",
            fixture_id=fixture_id,
            profile_ref=profile.id,
            frontier_url=candidate.candidate_url,
            normalized_url=canonicalize_url(candidate.candidate_url, fixture_id).canonical_url,
            page_type=candidate.page_type,
            url_pattern_score=candidate.url_pattern_score,
            anchor_text_score=candidate.anchor_text_score,
            page_title_score=candidate.page_title_score,
            semantic_similarity_score=candidate.semantic_similarity_score,
            domain_authority_score=candidate.domain_authority_score,
            freshness_score=candidate.freshness_score,
            historical_success_score=candidate.historical_success_score,
            page_type_score=candidate.page_type_score,
            expected_value_score=final_score,
            cost_penalty=candidate.cost_penalty,
            risk_penalty=candidate.risk_penalty,
            final_score=final_score,
            source_signal_refs=signal.source_signal_refs,
            policy_decision_refs=signal.policy_decision_refs,
            command_record_refs=[f"command:runtime-frontier-score:{fixture_id}:{index}"],
            event_cursor_refs=[f"event-cursor:runtime-frontier-score:{fixture_id}:{index}"],
            outbox_refs=[f"outbox:runtime-frontier-score:{fixture_id}:{index}"],
            replay_bundle_ref=f"replay-bundle:runtime-frontier-score:{fixture_id}:{index}",
        )
        score_breakdowns.append(score)
        priority = max(1, int(round(score.final_score * 1000)))
        decisions.append(
            RuntimeFrontierOptimizationDecision(
                id=f"runtime-frontier-decision:{fixture_id}:{index}",
                fixture_id=fixture_id,
                signal_set_ref=signal.id,
                candidate_url=candidate.candidate_url,
                scheduler_action="enqueue",
                scheduler_priority=priority,
                frontier_score_ref=score.id,
                policy_decision_refs=signal.policy_decision_refs,
                command_record_refs=[f"command:runtime-frontier:{fixture_id}:{index}"],
                event_cursor_refs=[f"event-cursor:runtime-frontier:{fixture_id}:{index}"],
                outbox_refs=[f"outbox:runtime-frontier:{fixture_id}:{index}"],
                replay_bundle_ref=f"replay-bundle:runtime-frontier:{fixture_id}:{index}",
            )
        )
    decisions.sort(key=lambda item: (-item.scheduler_priority, item.id))
    return RuntimeFrontierOptimizationResult(signal_sets, score_breakdowns, decisions)


def runtime_dom_extraction_context(
    *,
    fixture_id: str,
    normalized_document_ref: Ref,
    source_url: str,
    html_body: str,
    fields: list[RuntimeFieldSource],
    token_budget: int = 2000,
) -> RuntimeDomExtractionResult:
    nodes = _dom_nodes(fixture_id, html_body)
    zones = _page_zones(fixture_id, nodes)
    elements = _interactive_elements(fixture_id, nodes)
    dom_context = DomContextBundle(
        id=f"runtime-dom-context:{fixture_id}",
        fixture_id=fixture_id,
        source_url=source_url,
        html_artifact_ref=f"artifact:html:{fixture_id}",
        pruned_dom_ref=f"artifact:runtime-pruned-dom:{fixture_id}",
        dom_hash_ref=f"dom-hash:{stable_hash(html_body)[:16]}",
        token_budget=token_budget,
        original_node_count=max(len(_tokens(html_body)), len(nodes) + 1),
        retained_node_count=len(nodes),
        retained_node_refs=[node.id for node in nodes],
        zone_classification_refs=[zone.id for zone in zones],
        interactive_element_refs=[element.id for element in elements],
        policy_decision_refs=[f"policy:runtime-dom:{fixture_id}:allow"],
        command_record_refs=[f"command:runtime-dom:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-dom:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-dom:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:runtime-dom:{fixture_id}",
    )
    plan = ExtractorFallbackPlan(
        id=f"runtime-extractor-plan:{fixture_id}",
        fixture_id=fixture_id,
        target_schema_ref=f"schema:runtime:{fixture_id}",
        source_url=source_url,
        field_names=[field.field_name for field in fields],
        fallback_chain=[
            "json_ld",
            "schema_org",
            "open_graph",
            "css_selector",
            "xpath",
            "regex",
            "llm_structured",
        ],
        policy_decision_refs=[f"policy:runtime-extractor:{fixture_id}:allow"],
        replay_bundle_ref=f"replay-bundle:runtime-extractor-plan:{fixture_id}",
    )
    attempts = [_extractor_attempt(fixture_id, plan, html_body, field) for field in fields]
    confidences = [_field_confidence(fixture_id, attempt) for attempt in attempts]
    abstentions = [
        ExtractorAbstentionDecision(
            id=f"runtime-abstention:{fixture_id}:{attempt.field_name}",
            fixture_id=fixture_id,
            plan_ref=plan.id,
            field_name=attempt.field_name,
            confidence=attempt.confidence,
            threshold=plan.confidence_threshold,
            abstain=attempt.confidence < plan.confidence_threshold,
            reason=(
                "confidence_below_threshold"
                if attempt.confidence < plan.confidence_threshold
                else "confidence_above_threshold"
            ),
            source_attempt_refs=[attempt.id],
            review_queue_ref=(
                f"review-queue:runtime-extractor:{fixture_id}:{attempt.field_name}"
                if attempt.confidence < plan.confidence_threshold
                else None
            ),
        )
        for attempt in attempts
    ]
    runtime_context = RuntimeDomExtractionContext(
        id=f"runtime-dom-extraction-context:{fixture_id}",
        fixture_id=fixture_id,
        normalized_document_ref=normalized_document_ref,
        dom_context_ref=dom_context.id,
        extractor_plan_ref=plan.id,
        extractor_attempt_refs=[attempt.id for attempt in attempts],
        field_confidence_refs=[confidence.id for confidence in confidences],
        abstention_decision_refs=[abstention.id for abstention in abstentions],
        policy_decision_refs=dom_context.policy_decision_refs + plan.policy_decision_refs,
        command_record_refs=[f"command:runtime-dom-extraction:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-dom-extraction:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-dom-extraction:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:runtime-dom-extraction:{fixture_id}",
    )
    return RuntimeDomExtractionResult(
        nodes,
        zones,
        elements,
        dom_context,
        plan,
        attempts,
        confidences,
        abstentions,
        runtime_context,
    )


def runtime_dedupe_ranking_decision(
    *,
    fixture_id: str,
    objective_ref: Ref,
    inputs: list[RuntimeRankingInput],
) -> RuntimeDedupeRankingResult:
    canonicalizations = [canonicalize_url(item.canonical_url, fixture_id) for item in inputs]
    fingerprints = [
        _fingerprint(fixture_id, item.item_ref, item.text, index)
        for index, item in enumerate(inputs, start=1)
    ]
    identities = _identity_decisions(fixture_id, inputs, canonicalizations, fingerprints)
    retained = [
        identity.candidate_ref
        for identity in identities
        if identity.decision in {"unique", "variant", "needs_review"}
    ]
    suppressed = [
        identity.candidate_ref for identity in identities if identity.decision == "duplicate"
    ]
    duplicate_rate = round(len(suppressed) / max(1, len(identities)), 4)
    dedupe = DuplicateSuppressionRecord(
        id=f"runtime-duplicate-suppression:{fixture_id}",
        fixture_id=fixture_id,
        output_set_ref=f"runtime-output-set:{fixture_id}",
        candidate_refs=[item.item_ref for item in inputs],
        suppressed_refs=suppressed,
        retained_refs=retained,
        identity_decision_refs=[identity.id for identity in identities],
        duplicate_rate=duplicate_rate,
        policy_decision_refs=[f"policy:runtime-dedupe:{fixture_id}:allow"],
        command_record_refs=[f"command:runtime-dedupe:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-dedupe:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-dedupe:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:runtime-dedupe:{fixture_id}",
    )
    profile = _ranking_profile(fixture_id, objective_ref)
    scores = _ranking_scores(fixture_id, profile, inputs, retained)
    ranked_output = RankedOutputSet(
        id=f"runtime-ranked-output:{fixture_id}",
        fixture_id=fixture_id,
        profile_ref=profile.id,
        objective_ref=objective_ref,
        sorted_item_refs=[score.item_ref for score in scores],
        score_refs=[score.id for score in scores],
        dedupe_record_ref=dedupe.id,
        ranking_score_report_ref=f"runtime-ranking-score-report:{fixture_id}",
        top_k=10,
        score_formula_ref=profile.ranking_formula_ref,
        policy_decision_refs=[f"policy:runtime-ranking:{fixture_id}:allow"],
        command_record_refs=[f"command:runtime-ranking:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-ranking:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-ranking:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:runtime-ranking:{fixture_id}",
    )
    runtime_decision = RuntimeDedupeRankingDecision(
        id=f"runtime-dedupe-ranking:{fixture_id}",
        fixture_id=fixture_id,
        input_candidate_refs=[item.item_ref for item in inputs],
        canonicalization_refs=[canonical.id for canonical in canonicalizations],
        fingerprint_refs=[fingerprint.id for fingerprint in fingerprints],
        identity_decision_refs=[identity.id for identity in identities],
        duplicate_suppression_ref=dedupe.id,
        ranking_score_refs=[score.id for score in scores],
        ranked_output_set_ref=ranked_output.id,
        retained_refs=retained,
        suppressed_refs=suppressed,
        policy_decision_refs=dedupe.policy_decision_refs + ranked_output.policy_decision_refs,
        command_record_refs=[f"command:runtime-dedupe-ranking:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-dedupe-ranking:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-dedupe-ranking:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:runtime-dedupe-ranking:{fixture_id}",
    )
    return RuntimeDedupeRankingResult(
        canonicalizations,
        fingerprints,
        identities,
        dedupe,
        profile,
        scores,
        ranked_output,
        runtime_decision,
    )


def runtime_optimization_aggregate(
    *,
    fixture_id: str,
    lower_decision_refs: list[Ref],
    metric_slices: list[OptimizationMetricSlice],
    report: CrawlerOptimizationReport,
    replay_bundle_refs: list[Ref],
) -> RuntimeOptimizationAggregate:
    missing: list[str] = []
    if not lower_decision_refs:
        missing.append("lower_decision_refs")
    if not metric_slices:
        missing.append("metric_slice_refs")
    if not replay_bundle_refs:
        missing.append("replay_bundle_refs")
    if missing:
        failure = CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
        return RuntimeOptimizationAggregate(
            id=f"runtime-optimization-aggregate:{fixture_id}",
            fixture_id=fixture_id,
            lower_decision_refs=lower_decision_refs,
            metric_slice_refs=[metric.id for metric in metric_slices],
            optimization_report_ref=report.id,
            failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=missing,
            failure_type=failure,
            diagnostics=[f"runtime optimization aggregate missing refs: {missing}"],
            completion_result=CompletenessResult.FAIL,
        )
    return RuntimeOptimizationAggregate(
        id=f"runtime-optimization-aggregate:{fixture_id}",
        fixture_id=fixture_id,
        lower_decision_refs=lower_decision_refs,
        metric_slice_refs=[metric.id for metric in metric_slices],
        optimization_report_ref=report.id,
        policy_decision_refs=[f"policy:runtime-optimization-aggregate:{fixture_id}:allow"],
        command_record_refs=[f"command:runtime-optimization-aggregate:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:runtime-optimization-aggregate:{fixture_id}"],
        outbox_refs=[f"outbox:runtime-optimization-aggregate:{fixture_id}"],
        replay_bundle_refs=replay_bundle_refs,
        completion_result=CompletenessResult.PASS,
    )


def canonicalize_url(input_url: str, fixture_id: str) -> CanonicalizationDecision:
    parsed = urlparse(input_url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    path = quote(parsed.path or "/", safe="/:@")
    retained: list[tuple[str, str]] = []
    removed: list[str] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        key_lower = key.lower()
        if key_lower in _TRACKING_QUERY_KEYS or key_lower.startswith(_TRACKING_QUERY_PREFIXES):
            removed.append(key)
            continue
        retained.append((key_lower, value))
    query = urlencode(sorted(retained))
    canonical_url = urlunparse((scheme, host, path, "", query, ""))
    return CanonicalizationDecision(
        id=f"runtime-canonicalization:{fixture_id}:{stable_hash(canonical_url)[:12]}",
        fixture_id=fixture_id,
        input_url=input_url,
        canonical_url=canonical_url,
        canonical_url_ref=f"runtime-canonical-url:{stable_hash(canonical_url)[:16]}",
        removed_query_params=sorted(removed),
        normalized_host=host,
        normalized_path=path,
        rule_refs=["runtime-rule:lowercase-host", "runtime-rule:strip-tracking-query"],
        policy_decision_refs=[f"policy:runtime-canonicalization:{fixture_id}:allow"],
    )


def content_simhash(text: str, *, bits: int = 64) -> str:
    vector = [0] * bits
    for token in _tokens(text):
        digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        for index in range(bits):
            vector[index] += 1 if digest & (1 << index) else -1
    value = 0
    for index, weight in enumerate(vector):
        if weight >= 0:
            value |= 1 << index
    return f"{value:016x}"


def content_minhash(text: str, *, shingles: int = 3, count: int = 8) -> str:
    tokens = _tokens(text)
    grams = [
        " ".join(tokens[index : index + shingles])
        for index in range(max(1, len(tokens) - shingles + 1))
    ] or [text]
    hashes = sorted(hashlib.sha256(gram.encode("utf-8")).hexdigest()[:16] for gram in grams)
    return ":".join(hashes[:count])


def _frontier_score(profile: FrontierScoringProfile, candidate: RuntimeUrlCandidate) -> float:
    positive = (
        profile.url_pattern_weight * candidate.url_pattern_score
        + profile.anchor_text_weight * candidate.anchor_text_score
        + profile.page_title_weight * candidate.page_title_score
        + profile.semantic_similarity_weight * candidate.semantic_similarity_score
        + profile.domain_authority_weight * candidate.domain_authority_score
        + profile.freshness_weight * candidate.freshness_score
        + profile.historical_success_weight * candidate.historical_success_score
        + profile.page_type_weight * candidate.page_type_score
    )
    weight_sum = (
        profile.url_pattern_weight
        + profile.anchor_text_weight
        + profile.page_title_weight
        + profile.semantic_similarity_weight
        + profile.domain_authority_weight
        + profile.freshness_weight
        + profile.historical_success_weight
        + profile.page_type_weight
    )
    penalties = (
        profile.cost_penalty_weight * candidate.cost_penalty
        + profile.risk_penalty_weight * candidate.risk_penalty
    )
    return max(0.0, min(1.0, round((positive / weight_sum) - penalties, 4)))


def _source_signal_refs(fixture_id: str, index: int) -> list[Ref]:
    return [
        f"runtime-signal:{fixture_id}:{index}:url-pattern",
        f"runtime-signal:{fixture_id}:{index}:anchor-text",
        f"runtime-signal:{fixture_id}:{index}:semantic",
        f"runtime-signal:{fixture_id}:{index}:history",
    ]


def _dom_nodes(fixture_id: str, html_body: str) -> list[DomNodeSummary]:
    matches = re.findall(r"<(input|button|a|article|h1|h2|span)[^>]*>([^<]*)", html_body, re.I)
    if not matches:
        matches = [("article", _visible_text(html_body)[:80])]
    nodes: list[DomNodeSummary] = []
    for index, (tag, text) in enumerate(matches[:12], start=1):
        role = _role_for(tag.lower(), text)
        nodes.append(
            DomNodeSummary(
                id=f"runtime-dom-node:{fixture_id}:{index}",
                fixture_id=fixture_id,
                node_ref=f"runtime-node:{fixture_id}:{index}",
                tag_name=tag.lower(),
                role=role,
                text_excerpt=text.strip() or role,
                css_selector=f"{tag.lower()}:nth-of-type({index})",
                xpath=f"//{tag.lower()}[{index}]",
                attributes_hash_ref=f"attr-hash:{fixture_id}:{index}",
                source_anchor_ref=f"anchor:runtime-dom:{fixture_id}:{index}",
                artifact_ref=f"artifact:html:{fixture_id}",
                token_count_estimate=max(1, len(_tokens(text))),
                visibility_score=0.9,
                interaction_score=0.9 if tag.lower() in {"input", "button", "a"} else 0.3,
            )
        )
    return nodes


def _page_zones(fixture_id: str, nodes: list[DomNodeSummary]) -> list[PageZoneClassification]:
    zones: list[PageZoneClassification] = []
    for node in nodes:
        if node.role not in {
            "search_box",
            "pagination",
            "sort_button",
            "product_card",
            "price_block",
        }:
            continue
        zones.append(
            PageZoneClassification(
                id=f"runtime-page-zone:{fixture_id}:{len(zones) + 1}",
                fixture_id=fixture_id,
                dom_artifact_ref=f"artifact:runtime-pruned-dom:{fixture_id}",
                zone_ref=f"runtime-zone:{fixture_id}:{node.role}:{len(zones) + 1}",
                zone_type=node.role,
                selector=node.css_selector,
                confidence=0.9,
                node_refs=[node.node_ref],
                evidence_refs=[node.source_anchor_ref],
            )
        )
    return zones


def _interactive_elements(
    fixture_id: str,
    nodes: list[DomNodeSummary],
) -> list[InteractiveElementCandidate]:
    elements: list[InteractiveElementCandidate] = []
    tag_map = {"input": "input", "button": "button", "a": "link"}
    for node in nodes:
        element_type = tag_map.get(node.tag_name)
        if element_type is None:
            continue
        elements.append(
            InteractiveElementCandidate(
                id=f"runtime-interactive:{fixture_id}:{len(elements) + 1}",
                fixture_id=fixture_id,
                element_ref=node.node_ref,
                element_type=element_type,
                label=node.text_excerpt or node.role,
                selector=node.css_selector,
                action_kind="query" if node.role == "search_box" else "navigate_or_filter",
                intent_rank=len(elements) + 1,
                interaction_score=node.interaction_score,
                action_cost=0.1,
                source_anchor_ref=node.source_anchor_ref,
                policy_decision_refs=[f"policy:runtime-interaction:{fixture_id}:allow"],
            )
        )
    return elements


def _extractor_attempt(
    fixture_id: str,
    plan: ExtractorFallbackPlan,
    html_body: str,
    field: RuntimeFieldSource,
) -> ExtractorAttemptRecord:
    fallback_rank = plan.fallback_chain.index(field.source_kind) + 1
    return ExtractorAttemptRecord(
        id=f"runtime-extractor-attempt:{fixture_id}:{field.field_name}",
        fixture_id=fixture_id,
        plan_ref=plan.id,
        field_name=field.field_name,
        fallback_step=field.source_kind,
        fallback_rank=fallback_rank,
        source_kind=field.source_kind,
        raw_value=field.raw_value,
        normalized_value=field.normalized_value,
        confidence=field.confidence,
        accepted=field.accepted,
        source_anchor_ref=f"anchor:runtime-extract:{fixture_id}:{field.field_name}",
        artifact_ref=f"artifact:html:{fixture_id}",
        content_hash_ref=f"content-hash:{stable_hash(html_body + field.field_name)[:16]}",
        validation_refs=[f"validator:runtime:{field.field_name}"],
        evidence_packet_refs=[f"evidence-packet:runtime:{fixture_id}:{field.field_name}"],
        llm_output_evidence_refs=list(field.llm_output_evidence_refs),
    )


def _field_confidence(fixture_id: str, attempt: ExtractorAttemptRecord) -> FieldConfidenceScore:
    return FieldConfidenceScore(
        id=f"runtime-field-confidence:{fixture_id}:{attempt.field_name}",
        fixture_id=fixture_id,
        field_name=attempt.field_name,
        extracted_value_ref=attempt.id,
        confidence=attempt.confidence,
        validator_refs=attempt.validation_refs,
        normalization_ref=f"normalization:runtime:{fixture_id}:{attempt.field_name}",
        evidence_packet_refs=attempt.evidence_packet_refs,
        publication_gate_refs=[f"publication-gate:runtime:{fixture_id}:{attempt.field_name}"],
    )


def _fingerprint(
    fixture_id: str,
    candidate_ref: Ref,
    text: str,
    index: int,
) -> ContentFingerprintRecord:
    return ContentFingerprintRecord(
        id=f"runtime-fingerprint:{fixture_id}:{index}",
        fixture_id=fixture_id,
        source_ref=candidate_ref,
        simhash=content_simhash(text),
        minhash=content_minhash(text),
        text_digest_ref=f"text-digest:runtime:{stable_hash(text)[:16]}",
        structural_hash_ref=f"structural-hash:runtime:{stable_hash(_tokens(text))[:16]}",
        embedding_ref=f"embedding:runtime:{fixture_id}:{index}",
        artifact_refs=[f"artifact:runtime-ranking:{fixture_id}:{index}"],
        content_hash_refs=[f"content-hash:runtime:{stable_hash(text)[:16]}"],
        replay_bundle_ref=f"replay-bundle:runtime-fingerprint:{fixture_id}:{index}",
    )


def _identity_decisions(
    fixture_id: str,
    inputs: list[RuntimeRankingInput],
    canonicalizations: list[CanonicalizationDecision],
    fingerprints: list[ContentFingerprintRecord],
) -> list[IdentityResolutionDecision]:
    first_by_key: dict[str, Ref] = {}
    decisions: list[IdentityResolutionDecision] = []
    for index, item in enumerate(inputs, start=1):
        canonical = canonicalizations[index - 1]
        fingerprint = fingerprints[index - 1]
        key = item.variant_key or canonical.canonical_url
        duplicate_of = first_by_key.get(key)
        decision = "duplicate" if duplicate_of else "unique"
        if duplicate_of is None:
            first_by_key[key] = item.item_ref
        decisions.append(
            IdentityResolutionDecision(
                id=f"runtime-identity:{fixture_id}:{index}",
                fixture_id=fixture_id,
                candidate_ref=item.item_ref,
                canonical_url_ref=canonical.canonical_url_ref,
                fingerprint_ref=fingerprint.id,
                identity_key=key,
                identity_scope="runtime_output",
                decision=decision,
                duplicate_of_ref=duplicate_of,
                confidence=0.96,
                similarity_scores={"canonical_url": 1.0, "simhash": 0.96, "minhash": 0.95},
                evidence_refs=[canonical.id, fingerprint.id],
                policy_decision_refs=[f"policy:runtime-identity:{fixture_id}:allow"],
            )
        )
    return decisions


def _ranking_profile(fixture_id: str, objective_ref: Ref) -> RankingProfile:
    return RankingProfile(
        id=f"runtime-ranking-profile:{fixture_id}",
        profile_refs=["optimization"],
        objective_ref=objective_ref,
        weights={
            "intent_match": 0.30,
            "freshness": 0.10,
            "extraction_confidence": 0.20,
            "source_reliability": 0.20,
            "availability": 0.20,
        },
        ranking_formula_ref="formula:runtime-ranking-weighted-v1",
        tie_breakers=["source_reliability", "freshness"],
        required_ref_types=[
            "evidence_packet",
            "policy",
            "command",
            "event_cursor",
            "outbox",
            "replay",
        ],
    )


def _ranking_scores(
    fixture_id: str,
    profile: RankingProfile,
    inputs: list[RuntimeRankingInput],
    retained_refs: list[Ref],
) -> list[RankingScoreBreakdown]:
    retained_inputs = [item for item in inputs if item.item_ref in set(retained_refs)]
    scored: list[tuple[RuntimeRankingInput, dict[str, float], dict[str, float], float]] = []
    for item in retained_inputs:
        values = item.features or {
            "intent_match": 0.92,
            "freshness": 0.82,
            "extraction_confidence": 0.94,
            "source_reliability": 0.88,
            "availability": 0.9,
        }
        components = {
            name: round(values[name] * profile.weights[name], 4) for name in profile.weights
        }
        final = round(sum(components.values()) / sum(profile.weights.values()), 4)
        scored.append((item, values, components, final))
    scored.sort(key=lambda row: row[3], reverse=True)
    return [
        RankingScoreBreakdown(
            id=f"runtime-ranking-score:{fixture_id}:{rank}",
            fixture_id=fixture_id,
            item_ref=item.item_ref,
            rank=rank,
            feature_values=values,
            component_scores=components,
            extraction_confidence=values["extraction_confidence"],
            final_score=final,
            source_reliability_ref=f"source-reliability:runtime:{fixture_id}:{rank}",
            evidence_packet_refs=[f"evidence-packet:runtime-ranking:{fixture_id}:{rank}"],
            policy_decision_refs=[f"policy:runtime-ranking:{fixture_id}:allow"],
            command_record_refs=[f"command:runtime-ranking-score:{fixture_id}:{rank}"],
            event_cursor_refs=[f"event-cursor:runtime-ranking-score:{fixture_id}:{rank}"],
            outbox_refs=[f"outbox:runtime-ranking-score:{fixture_id}:{rank}"],
            replay_bundle_ref=f"replay-bundle:runtime-ranking-score:{fixture_id}:{rank}",
        )
        for rank, (item, values, components, final) in enumerate(scored, start=1)
    ]


def _role_for(tag_name: str, text: str) -> str:
    value = f"{tag_name} {text}".lower()
    if "search" in value:
        return "search_box"
    if "sort" in value:
        return "sort_button"
    if "next" in value or "page" in value:
        return "pagination"
    if "price" in value or "$" in value:
        return "price_block"
    if "product" in value or tag_name == "article":
        return "product_card"
    return "content"


def _visible_text(text: str) -> str:
    return " ".join(_tokens(re.sub(r"<[^>]+>", " ", text)))


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
