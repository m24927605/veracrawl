"""Crawler intelligence optimization contracts.

These contracts materialize specs 081-086 without binding the core crawler to a
specific website, model SDK, browser engine, or agent framework.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _check_score(name: str, value: float) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1")


def _missing_refs(values: Mapping[str, object]) -> list[str]:
    return [name for name, value in values.items() if not value]


OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF = (
    "optimization-score-v1-weighted-accuracy-time-cost"
)
OPTIMIZATION_OBJECTIVE_SCORE_TOLERANCE = 1e-9


class FrontierScoringProfile(TimestampedModel):
    id: str
    profile_refs: list[str] = Field(default_factory=list)
    objective_ref: Ref
    scoring_formula_ref: Ref
    url_pattern_weight: float = 0.12
    anchor_text_weight: float = 0.12
    page_title_weight: float = 0.10
    semantic_similarity_weight: float = 0.18
    domain_authority_weight: float = 0.10
    freshness_weight: float = 0.08
    historical_success_weight: float = 0.12
    page_type_weight: float = 0.12
    cost_penalty_weight: float = 0.04
    risk_penalty_weight: float = 0.02
    confidence_threshold: float = 0.72
    stop_confidence_threshold: float = 0.86
    max_crawl_budget: int = 1000
    max_llm_action_budget: int = 20
    required_signal_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_profile(self) -> FrontierScoringProfile:
        if "optimization" not in self.profile_refs:
            raise ValueError("frontier profile must support optimization profile")
        weights = [
            self.url_pattern_weight,
            self.anchor_text_weight,
            self.page_title_weight,
            self.semantic_similarity_weight,
            self.domain_authority_weight,
            self.freshness_weight,
            self.historical_success_weight,
            self.page_type_weight,
            self.cost_penalty_weight,
            self.risk_penalty_weight,
        ]
        if any(weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError("frontier score weights must be non-negative and non-empty")
        _check_score("confidence_threshold", self.confidence_threshold)
        _check_score("stop_confidence_threshold", self.stop_confidence_threshold)
        if self.stop_confidence_threshold < self.confidence_threshold:
            raise ValueError("stop threshold cannot be below action confidence threshold")
        if self.max_crawl_budget < 1 or self.max_llm_action_budget < 0:
            raise ValueError("frontier budgets must be positive")
        if not self.required_signal_refs:
            raise ValueError("frontier scoring profile requires signal refs")
        return self


class FrontierScoreBreakdown(TimestampedModel):
    id: str
    fixture_id: str
    profile_ref: Ref
    frontier_url: str
    normalized_url: str
    page_type: str
    url_pattern_score: float
    anchor_text_score: float
    page_title_score: float
    semantic_similarity_score: float
    domain_authority_score: float
    freshness_score: float
    historical_success_score: float
    page_type_score: float
    expected_value_score: float
    cost_penalty: float
    risk_penalty: float
    final_score: float
    source_signal_refs: list[Ref] = Field(default_factory=list)
    dom_context_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_score(self) -> FrontierScoreBreakdown:
        if not _is_http_url(self.frontier_url) or not _is_http_url(self.normalized_url):
            raise ValueError("frontier URLs must be absolute http(s)")
        for name in [
            "url_pattern_score",
            "anchor_text_score",
            "page_title_score",
            "semantic_similarity_score",
            "domain_authority_score",
            "freshness_score",
            "historical_success_score",
            "page_type_score",
            "expected_value_score",
            "cost_penalty",
            "risk_penalty",
            "final_score",
        ]:
            _check_score(name, getattr(self, name))
        missing = _missing_refs(
            {
                "source_signal_refs": self.source_signal_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"frontier score missing refs: {missing}")
        if self.llm_output_evidence_refs:
            raise ValueError("LLM output cannot be frontier scoring source evidence")
        return self


class DomNodeSummary(TimestampedModel):
    id: str
    fixture_id: str
    node_ref: Ref
    tag_name: str
    role: str
    text_excerpt: str
    css_selector: str
    xpath: str
    attributes_hash_ref: Ref
    source_anchor_ref: Ref
    artifact_ref: Ref
    parent_ref: Ref | None = None
    child_count: int = 0
    token_count_estimate: int = 0
    visibility_score: float = 0.0
    interaction_score: float = 0.0

    @model_validator(mode="after")
    def validate_node(self) -> DomNodeSummary:
        if not self.tag_name or self.child_count < 0 or self.token_count_estimate < 0:
            raise ValueError("DOM node summary requires a tag and non-negative counts")
        _check_score("visibility_score", self.visibility_score)
        _check_score("interaction_score", self.interaction_score)
        required = {
            "node_ref": self.node_ref,
            "css_selector": self.css_selector,
            "xpath": self.xpath,
            "attributes_hash_ref": self.attributes_hash_ref,
            "source_anchor_ref": self.source_anchor_ref,
            "artifact_ref": self.artifact_ref,
        }
        missing = _missing_refs(required)
        if missing:
            raise ValueError(f"DOM node summary missing refs: {missing}")
        return self


class PageZoneClassification(TimestampedModel):
    id: str
    fixture_id: str
    dom_artifact_ref: Ref
    zone_ref: Ref
    zone_type: str
    selector: str
    confidence: float
    node_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_zone(self) -> PageZoneClassification:
        _check_score("confidence", self.confidence)
        allowed = {
            "search_box",
            "filter",
            "pagination",
            "sort_button",
            "product_card",
            "price_block",
            "content",
            "navigation",
        }
        if self.zone_type not in allowed:
            raise ValueError("unsupported page zone type")
        missing = _missing_refs(
            {
                "dom_artifact_ref": self.dom_artifact_ref,
                "zone_ref": self.zone_ref,
                "selector": self.selector,
                "node_refs": self.node_refs,
                "evidence_refs": self.evidence_refs,
            }
        )
        if missing:
            raise ValueError(f"page zone classification missing refs: {missing}")
        return self


class InteractiveElementCandidate(TimestampedModel):
    id: str
    fixture_id: str
    element_ref: Ref
    element_type: str
    label: str
    selector: str
    action_kind: str
    intent_rank: int
    interaction_score: float
    action_cost: float
    source_anchor_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_interactive_element(self) -> InteractiveElementCandidate:
        if self.intent_rank < 1:
            raise ValueError("interactive element rank must be positive")
        _check_score("interaction_score", self.interaction_score)
        _check_score("action_cost", self.action_cost)
        allowed = {"input", "button", "link", "select", "checkbox", "radio", "form"}
        if self.element_type not in allowed:
            raise ValueError("unsupported interactive element type")
        missing = _missing_refs(
            {
                "element_ref": self.element_ref,
                "label": self.label,
                "selector": self.selector,
                "source_anchor_ref": self.source_anchor_ref,
                "policy_decision_refs": self.policy_decision_refs,
            }
        )
        if missing:
            raise ValueError(f"interactive element missing refs: {missing}")
        return self


class DomContextBundle(TimestampedModel):
    id: str
    fixture_id: str
    source_url: str
    html_artifact_ref: Ref
    pruned_dom_ref: Ref
    dom_hash_ref: Ref
    token_budget: int
    original_node_count: int
    retained_node_count: int
    retained_node_refs: list[Ref] = Field(default_factory=list)
    zone_classification_refs: list[Ref] = Field(default_factory=list)
    interactive_element_refs: list[Ref] = Field(default_factory=list)
    screenshot_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_dom_context(self) -> DomContextBundle:
        if not _is_http_url(self.source_url):
            raise ValueError("DOM context source_url must be absolute http(s)")
        if self.token_budget < 1 or self.original_node_count < self.retained_node_count:
            raise ValueError("invalid DOM pruning budget or node counts")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "html_artifact_ref": self.html_artifact_ref,
                    "pruned_dom_ref": self.pruned_dom_ref,
                    "dom_hash_ref": self.dom_hash_ref,
                    "retained_node_refs": self.retained_node_refs,
                    "zone_classification_refs": self.zone_classification_refs,
                    "interactive_element_refs": self.interactive_element_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing:
                raise ValueError(f"passing DOM context missing refs: {missing}")
        if self.llm_output_evidence_refs:
            raise ValueError("LLM output cannot be DOM source evidence")
        return self


class ExtractorFallbackPlan(TimestampedModel):
    id: str
    fixture_id: str
    target_schema_ref: Ref
    source_url: str
    field_names: list[str] = Field(default_factory=list)
    fallback_chain: list[str] = Field(default_factory=list)
    confidence_threshold: float = 0.85
    llm_structured_fallback_allowed: bool = True
    max_llm_chunks: int = 2
    token_budget: int = 3000
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_plan(self) -> ExtractorFallbackPlan:
        if not _is_http_url(self.source_url):
            raise ValueError("extractor plan source_url must be absolute http(s)")
        _check_score("confidence_threshold", self.confidence_threshold)
        if not self.field_names or not self.fallback_chain:
            raise ValueError("extractor plan requires fields and fallback chain")
        allowed = {
            "json_ld",
            "schema_org",
            "open_graph",
            "css_selector",
            "xpath",
            "regex",
            "llm_structured",
        }
        if any(step not in allowed for step in self.fallback_chain):
            raise ValueError("unsupported extractor fallback step")
        if "llm_structured" in self.fallback_chain and not self.llm_structured_fallback_allowed:
            raise ValueError("llm_structured fallback present but not allowed")
        if self.max_llm_chunks < 0 or self.token_budget < 1:
            raise ValueError("extractor LLM and token budgets must be non-negative")
        missing = _missing_refs(
            {
                "target_schema_ref": self.target_schema_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"extractor plan missing refs: {missing}")
        return self


class ExtractorAttemptRecord(TimestampedModel):
    id: str
    fixture_id: str
    plan_ref: Ref
    field_name: str
    fallback_step: str
    fallback_rank: int
    source_kind: str
    raw_value: str
    normalized_value: str
    confidence: float
    accepted: bool
    source_anchor_ref: Ref
    artifact_ref: Ref
    content_hash_ref: Ref
    validation_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_attempt(self) -> ExtractorAttemptRecord:
        if self.fallback_rank < 1:
            raise ValueError("extractor fallback rank must be positive")
        _check_score("confidence", self.confidence)
        if self.accepted:
            missing = _missing_refs(
                {
                    "raw_value": self.raw_value,
                    "normalized_value": self.normalized_value,
                    "source_anchor_ref": self.source_anchor_ref,
                    "artifact_ref": self.artifact_ref,
                    "content_hash_ref": self.content_hash_ref,
                    "validation_refs": self.validation_refs,
                    "evidence_packet_refs": self.evidence_packet_refs,
                }
            )
            if missing:
                raise ValueError(f"accepted extractor attempt missing refs: {missing}")
            if self.llm_output_evidence_refs:
                raise ValueError("LLM output cannot be accepted field evidence")
        return self


class FieldConfidenceScore(TimestampedModel):
    id: str
    fixture_id: str
    field_name: str
    extracted_value_ref: Ref
    confidence: float
    validator_refs: list[Ref] = Field(default_factory=list)
    normalization_ref: Ref
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_confidence(self) -> FieldConfidenceScore:
        _check_score("confidence", self.confidence)
        missing = _missing_refs(
            {
                "extracted_value_ref": self.extracted_value_ref,
                "validator_refs": self.validator_refs,
                "normalization_ref": self.normalization_ref,
                "evidence_packet_refs": self.evidence_packet_refs,
                "publication_gate_refs": self.publication_gate_refs,
            }
        )
        if missing:
            raise ValueError(f"field confidence missing refs: {missing}")
        return self


class ExtractorAbstentionDecision(TimestampedModel):
    id: str
    fixture_id: str
    plan_ref: Ref
    field_name: str
    confidence: float
    threshold: float
    abstain: bool
    reason: str
    source_attempt_refs: list[Ref] = Field(default_factory=list)
    review_queue_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_abstention(self) -> ExtractorAbstentionDecision:
        _check_score("confidence", self.confidence)
        _check_score("threshold", self.threshold)
        if self.abstain and not self.review_queue_ref:
            raise ValueError("abstention requires review queue ref")
        if not self.source_attempt_refs:
            raise ValueError("abstention decision requires source attempt refs")
        return self


class CanonicalizationDecision(TimestampedModel):
    id: str
    fixture_id: str
    input_url: str
    canonical_url: str
    canonical_url_ref: Ref
    removed_query_params: list[str] = Field(default_factory=list)
    normalized_host: str
    normalized_path: str
    rule_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_canonicalization(self) -> CanonicalizationDecision:
        if not _is_http_url(self.input_url) or not _is_http_url(self.canonical_url):
            raise ValueError("canonicalization URLs must be absolute http(s)")
        missing = _missing_refs(
            {
                "canonical_url_ref": self.canonical_url_ref,
                "normalized_host": self.normalized_host,
                "normalized_path": self.normalized_path,
                "rule_refs": self.rule_refs,
                "policy_decision_refs": self.policy_decision_refs,
            }
        )
        if missing:
            raise ValueError(f"canonicalization missing refs: {missing}")
        return self


class ContentFingerprintRecord(TimestampedModel):
    id: str
    fixture_id: str
    source_ref: Ref
    simhash: str
    minhash: str
    text_digest_ref: Ref
    structural_hash_ref: Ref
    embedding_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_fingerprint(self) -> ContentFingerprintRecord:
        missing = _missing_refs(
            {
                "source_ref": self.source_ref,
                "simhash": self.simhash,
                "minhash": self.minhash,
                "text_digest_ref": self.text_digest_ref,
                "structural_hash_ref": self.structural_hash_ref,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"content fingerprint missing refs: {missing}")
        return self


class IdentityResolutionDecision(TimestampedModel):
    id: str
    fixture_id: str
    candidate_ref: Ref
    canonical_url_ref: Ref
    fingerprint_ref: Ref
    identity_key: str
    identity_scope: str
    decision: str
    confidence: float
    duplicate_of_ref: Ref | None = None
    variant_of_ref: Ref | None = None
    similarity_scores: dict[str, float] = Field(default_factory=dict)
    evidence_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity(self) -> IdentityResolutionDecision:
        _check_score("confidence", self.confidence)
        if self.decision not in {"unique", "duplicate", "variant", "needs_review"}:
            raise ValueError("unsupported identity decision")
        if self.decision == "duplicate" and not self.duplicate_of_ref:
            raise ValueError("duplicate identity decision requires duplicate_of_ref")
        if self.decision == "variant" and not self.variant_of_ref:
            raise ValueError("variant identity decision requires variant_of_ref")
        for name, value in self.similarity_scores.items():
            _check_score(name, value)
        missing = _missing_refs(
            {
                "candidate_ref": self.candidate_ref,
                "canonical_url_ref": self.canonical_url_ref,
                "fingerprint_ref": self.fingerprint_ref,
                "identity_key": self.identity_key,
                "identity_scope": self.identity_scope,
                "evidence_refs": self.evidence_refs,
                "policy_decision_refs": self.policy_decision_refs,
            }
        )
        if missing:
            raise ValueError(f"identity decision missing refs: {missing}")
        return self


class DuplicateSuppressionRecord(TimestampedModel):
    id: str
    fixture_id: str
    output_set_ref: Ref
    candidate_refs: list[Ref] = Field(default_factory=list)
    suppressed_refs: list[Ref] = Field(default_factory=list)
    retained_refs: list[Ref] = Field(default_factory=list)
    identity_decision_refs: list[Ref] = Field(default_factory=list)
    duplicate_rate: float = 0.0
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_dedup(self) -> DuplicateSuppressionRecord:
        _check_score("duplicate_rate", self.duplicate_rate)
        missing = _missing_refs(
            {
                "output_set_ref": self.output_set_ref,
                "candidate_refs": self.candidate_refs,
                "retained_refs": self.retained_refs,
                "identity_decision_refs": self.identity_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"duplicate suppression missing refs: {missing}")
        return self


class RankingProfile(TimestampedModel):
    id: str
    profile_refs: list[str] = Field(default_factory=list)
    objective_ref: Ref
    weights: dict[str, float] = Field(default_factory=dict)
    ranking_formula_ref: Ref
    min_extraction_confidence: float = 0.85
    tie_breakers: list[str] = Field(default_factory=list)
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ranking_profile(self) -> RankingProfile:
        if "optimization" not in self.profile_refs:
            raise ValueError("ranking profile must support optimization profile")
        if not self.weights or any(value < 0 for value in self.weights.values()):
            raise ValueError("ranking profile requires non-negative weights")
        if sum(self.weights.values()) <= 0:
            raise ValueError("ranking profile weight sum must be positive")
        _check_score("min_extraction_confidence", self.min_extraction_confidence)
        if not self.tie_breakers or not self.required_ref_types:
            raise ValueError("ranking profile requires tie breakers and ref types")
        return self


class RankingScoreBreakdown(TimestampedModel):
    id: str
    fixture_id: str
    item_ref: Ref
    rank: int
    feature_values: dict[str, float] = Field(default_factory=dict)
    component_scores: dict[str, float] = Field(default_factory=dict)
    extraction_confidence: float
    final_score: float
    source_reliability_ref: Ref
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_ranking_score(self) -> RankingScoreBreakdown:
        if self.rank < 1:
            raise ValueError("rank must be positive")
        _check_score("extraction_confidence", self.extraction_confidence)
        _check_score("final_score", self.final_score)
        for name, value in self.feature_values.items():
            _check_score(name, value)
        for name, value in self.component_scores.items():
            _check_score(name, value)
        missing = _missing_refs(
            {
                "item_ref": self.item_ref,
                "feature_values": self.feature_values,
                "component_scores": self.component_scores,
                "source_reliability_ref": self.source_reliability_ref,
                "evidence_packet_refs": self.evidence_packet_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"ranking score missing refs: {missing}")
        return self


class RankedOutputSet(TimestampedModel):
    id: str
    fixture_id: str
    profile_ref: Ref
    objective_ref: Ref
    sorted_item_refs: list[Ref] = Field(default_factory=list)
    score_refs: list[Ref] = Field(default_factory=list)
    dedupe_record_ref: Ref
    ranking_score_report_ref: Ref
    top_k: int
    score_formula_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_ranked_output(self) -> RankedOutputSet:
        if self.top_k < 1:
            raise ValueError("ranked output top_k must be positive")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "sorted_item_refs": self.sorted_item_refs,
                    "score_refs": self.score_refs,
                    "dedupe_record_ref": self.dedupe_record_ref,
                    "ranking_score_report_ref": self.ranking_score_report_ref,
                    "score_formula_ref": self.score_formula_ref,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing:
                raise ValueError(f"passing ranked output missing refs: {missing}")
        return self


class RankingEvaluationReport(TimestampedModel):
    id: str
    fixture_id: str
    baseline_ref: Ref
    ranked_output_set_ref: Ref
    metric_refs: list[Ref] = Field(default_factory=list)
    intent_match_precision: float
    duplicate_rate: float
    accepted_result_count: int
    ndcg_at_k: float
    cost_per_success: float
    latency_p95_ms: int
    improvement_summary_refs: list[Ref] = Field(default_factory=list)
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ranking_eval(self) -> RankingEvaluationReport:
        for name in ["intent_match_precision", "duplicate_rate", "ndcg_at_k"]:
            _check_score(name, getattr(self, name))
        if self.accepted_result_count < 0 or self.cost_per_success < 0 or self.latency_p95_ms < 0:
            raise ValueError("ranking evaluation counts and costs must be non-negative")
        missing = _missing_refs(
            {
                "baseline_ref": self.baseline_ref,
                "ranked_output_set_ref": self.ranked_output_set_ref,
                "metric_refs": self.metric_refs,
                "improvement_summary_refs": self.improvement_summary_refs,
            }
        )
        if missing:
            raise ValueError(f"ranking evaluation missing refs: {missing}")
        if self.failure_type and not self.diagnostics:
            raise ValueError("ranking evaluation failure requires diagnostics")
        return self


class OptimizationMetricSlice(TimestampedModel):
    id: str
    fixture_id: str
    dimension: str
    slice_ref: Ref
    precision: float
    recall: float
    extraction_accuracy: float
    duplicate_rate: float
    crawl_success_rate: float
    cost_per_success: float
    latency_p95_ms: int
    ranking_ndcg: float
    llm_token_savings_rate: float
    metric_evidence_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_metric_slice(self) -> OptimizationMetricSlice:
        for name in [
            "precision",
            "recall",
            "extraction_accuracy",
            "duplicate_rate",
            "crawl_success_rate",
            "ranking_ndcg",
            "llm_token_savings_rate",
        ]:
            _check_score(name, getattr(self, name))
        if self.cost_per_success < 0 or self.latency_p95_ms < 0:
            raise ValueError("metric slice cost and latency must be non-negative")
        if not self.metric_evidence_refs:
            raise ValueError("metric slice requires evidence refs")
        return self


class CrawlerOptimizationReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    manifest_ref: Ref
    profile: str
    frontier_profile_ref: Ref | None = None
    frontier_score_refs: list[Ref] = Field(default_factory=list)
    dom_context_refs: list[Ref] = Field(default_factory=list)
    extractor_plan_refs: list[Ref] = Field(default_factory=list)
    extractor_attempt_refs: list[Ref] = Field(default_factory=list)
    field_confidence_refs: list[Ref] = Field(default_factory=list)
    canonicalization_refs: list[Ref] = Field(default_factory=list)
    fingerprint_refs: list[Ref] = Field(default_factory=list)
    identity_decision_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_refs: list[Ref] = Field(default_factory=list)
    ranking_profile_ref: Ref | None = None
    ranking_score_refs: list[Ref] = Field(default_factory=list)
    ranked_output_set_refs: list[Ref] = Field(default_factory=list)
    ranking_evaluation_refs: list[Ref] = Field(default_factory=list)
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    crawl_success_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    extraction_accuracy: float = 0.0
    duplicate_rate: float = 0.0
    cost_per_success: float = 0.0
    latency_p95_ms: int = 0
    ranking_ndcg: float = 0.0
    llm_token_savings_rate: float = 0.0
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> CrawlerOptimizationReport:
        for name in [
            "crawl_success_rate",
            "precision",
            "recall",
            "extraction_accuracy",
            "duplicate_rate",
            "ranking_ndcg",
            "llm_token_savings_rate",
        ]:
            _check_score(name, getattr(self, name))
        if self.cost_per_success < 0 or self.latency_p95_ms < 0:
            raise ValueError("optimization report cost and latency must be non-negative")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "frontier_profile_ref": self.frontier_profile_ref,
                    "frontier_score_refs": self.frontier_score_refs,
                    "dom_context_refs": self.dom_context_refs,
                    "extractor_plan_refs": self.extractor_plan_refs,
                    "extractor_attempt_refs": self.extractor_attempt_refs,
                    "field_confidence_refs": self.field_confidence_refs,
                    "canonicalization_refs": self.canonicalization_refs,
                    "fingerprint_refs": self.fingerprint_refs,
                    "identity_decision_refs": self.identity_decision_refs,
                    "duplicate_suppression_refs": self.duplicate_suppression_refs,
                    "ranking_profile_ref": self.ranking_profile_ref,
                    "ranking_score_refs": self.ranking_score_refs,
                    "ranked_output_set_refs": self.ranked_output_set_refs,
                    "ranking_evaluation_refs": self.ranking_evaluation_refs,
                    "metric_slice_refs": self.metric_slice_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_refs": self.replay_bundle_refs,
                }
            )
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing optimization report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass optimization report requires typed diagnostics")
        return self


class RuntimeOptimizationSignalSet(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    objective_ref: Ref
    candidate_url: str
    source_anchor_ref: Ref | None = None
    source_signal_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    allowed: bool = True
    blocked_reason_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_runtime_signals(self) -> RuntimeOptimizationSignalSet:
        if not _is_http_url(self.candidate_url):
            raise ValueError("runtime optimization candidate_url must be absolute http(s)")
        missing = _missing_refs(
            {
                "run_ref": self.run_ref,
                "objective_ref": self.objective_ref,
                "policy_decision_refs": self.policy_decision_refs,
            }
        )
        if missing:
            raise ValueError(f"runtime signal set missing refs: {missing}")
        if self.allowed:
            missing_allowed = _missing_refs(
                {
                    "source_anchor_ref": self.source_anchor_ref,
                    "source_signal_refs": self.source_signal_refs,
                }
            )
            if missing_allowed:
                raise ValueError(f"allowed runtime signal set missing refs: {missing_allowed}")
        elif not self.blocked_reason_refs:
            raise ValueError("blocked runtime signal set requires blocked_reason_refs")
        return self


class RuntimeFrontierOptimizationDecision(TimestampedModel):
    id: str
    fixture_id: str
    signal_set_ref: Ref
    candidate_url: str
    scheduler_action: str
    scheduler_priority: int = 0
    frontier_score_ref: Ref | None = None
    blocked_reason_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_frontier_decision(self) -> RuntimeFrontierOptimizationDecision:
        if not _is_http_url(self.candidate_url):
            raise ValueError("runtime frontier candidate_url must be absolute http(s)")
        if self.scheduler_action not in {"enqueue", "block", "retire", "review"}:
            raise ValueError("unsupported runtime frontier scheduler_action")
        if self.scheduler_priority < 0:
            raise ValueError("scheduler_priority cannot be negative")
        if self.scheduler_action == "enqueue" and (
            not self.frontier_score_ref or self.scheduler_priority < 1
        ):
            raise ValueError("enqueue frontier decision requires score ref and positive priority")
        if self.scheduler_action == "block" and not self.blocked_reason_refs:
            raise ValueError("blocked frontier decision requires blocked_reason_refs")
        missing = _missing_refs(
            {
                "signal_set_ref": self.signal_set_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"runtime frontier decision missing refs: {missing}")
        return self


class RuntimeDomExtractionContext(TimestampedModel):
    id: str
    fixture_id: str
    normalized_document_ref: Ref
    dom_context_ref: Ref
    extractor_plan_ref: Ref
    extractor_attempt_refs: list[Ref] = Field(default_factory=list)
    field_confidence_refs: list[Ref] = Field(default_factory=list)
    abstention_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_dom_extraction_context(self) -> RuntimeDomExtractionContext:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "normalized_document_ref": self.normalized_document_ref,
                    "dom_context_ref": self.dom_context_ref,
                    "extractor_plan_ref": self.extractor_plan_ref,
                    "extractor_attempt_refs": self.extractor_attempt_refs,
                    "field_confidence_refs": self.field_confidence_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing:
                raise ValueError(f"runtime DOM extraction context missing refs: {missing}")
        return self


class RuntimeDedupeRankingDecision(TimestampedModel):
    id: str
    fixture_id: str
    input_candidate_refs: list[Ref] = Field(default_factory=list)
    canonicalization_refs: list[Ref] = Field(default_factory=list)
    fingerprint_refs: list[Ref] = Field(default_factory=list)
    identity_decision_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_ref: Ref
    ranking_score_refs: list[Ref] = Field(default_factory=list)
    ranked_output_set_ref: Ref
    retained_refs: list[Ref] = Field(default_factory=list)
    suppressed_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_dedupe_ranking(self) -> RuntimeDedupeRankingDecision:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "input_candidate_refs": self.input_candidate_refs,
                    "canonicalization_refs": self.canonicalization_refs,
                    "fingerprint_refs": self.fingerprint_refs,
                    "identity_decision_refs": self.identity_decision_refs,
                    "duplicate_suppression_ref": self.duplicate_suppression_ref,
                    "ranking_score_refs": self.ranking_score_refs,
                    "ranked_output_set_ref": self.ranked_output_set_ref,
                    "retained_refs": self.retained_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing:
                raise ValueError(f"runtime dedupe ranking decision missing refs: {missing}")
            if not set(self.retained_refs).issubset(set(self.input_candidate_refs)):
                raise ValueError("retained refs must come from input candidates")
            if set(self.retained_refs) & set(self.suppressed_refs):
                raise ValueError("candidate cannot be both retained and suppressed")
        return self


class RuntimeOptimizationAggregate(TimestampedModel):
    id: str
    fixture_id: str
    lower_decision_refs: list[Ref] = Field(default_factory=list)
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    optimization_report_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_runtime_aggregate(self) -> RuntimeOptimizationAggregate:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "lower_decision_refs": self.lower_decision_refs,
                    "metric_slice_refs": self.metric_slice_refs,
                    "optimization_report_ref": self.optimization_report_ref,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_refs": self.replay_bundle_refs,
                }
            )
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing runtime aggregate missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass runtime aggregate requires typed diagnostics")
        return self


class OptimizationOwnerIntegrationRoadmap(TimestampedModel):
    id: str
    fixture_id: str
    spec_refs: list[Ref] = Field(default_factory=list)
    dependency_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_owner_integration_roadmap(self) -> OptimizationOwnerIntegrationRoadmap:
        required_specs = {f"spec:{number:03d}" for number in range(89, 97)}
        if not required_specs.issubset(set(self.spec_refs)):
            raise ValueError("owner integration roadmap must include specs 089-096")
        missing = _missing_refs(
            {
                "dependency_refs": self.dependency_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
        )
        if missing:
            raise ValueError(f"owner integration roadmap missing refs: {missing}")
        return self


class SchedulerOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    enqueue_refs: list[Ref] = Field(default_factory=list)
    blocked_refs: list[Ref] = Field(default_factory=list)
    retired_refs: list[Ref] = Field(default_factory=list)
    stop_reason_refs: list[Ref] = Field(default_factory=list)
    scheduler_priority_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scheduler_integration(self) -> SchedulerOptimizationIntegration:
        if self.completion_result == CompletenessResult.PASS:
            outcomes = (
                self.enqueue_refs
                + self.blocked_refs
                + self.retired_refs
                + self.stop_reason_refs
            )
            missing = _missing_refs(
                {
                    "run_ref": self.run_ref,
                    "frontier_decision_refs": self.frontier_decision_refs,
                    "outcomes": outcomes,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing scheduler integration missing refs: {missing}")
            if self.enqueue_refs and not self.scheduler_priority_refs:
                raise ValueError("enqueue scheduler integration requires priority refs")
            if (self.blocked_refs or self.retired_refs) and not self.stop_reason_refs:
                raise ValueError("blocked or retired scheduler integration requires stop reasons")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass scheduler integration requires typed diagnostics")
        return self


class NormalizeOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    normalized_document_ref: Ref
    dom_context_ref: Ref
    retained_node_refs: list[Ref] = Field(default_factory=list)
    page_zone_refs: list[Ref] = Field(default_factory=list)
    interactive_element_refs: list[Ref] = Field(default_factory=list)
    context_reduction_ratio: float
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_normalize_integration(self) -> NormalizeOptimizationIntegration:
        _check_score("context_reduction_ratio", self.context_reduction_ratio)
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "normalized_document_ref": self.normalized_document_ref,
                    "dom_context_ref": self.dom_context_ref,
                    "retained_node_refs": self.retained_node_refs,
                    "artifact_refs": self.artifact_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing normalize integration missing refs: {missing}")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass normalize integration requires typed diagnostics")
        return self


class ExtractVerifyOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    normalized_document_ref: Ref
    extractor_plan_ref: Ref
    accepted_attempt_refs: list[Ref] = Field(default_factory=list)
    rejected_attempt_refs: list[Ref] = Field(default_factory=list)
    field_confidence_refs: list[Ref] = Field(default_factory=list)
    abstention_refs: list[Ref] = Field(default_factory=list)
    review_refs: list[Ref] = Field(default_factory=list)
    publication_eligible_field_refs: list[Ref] = Field(default_factory=list)
    llm_only_rejected_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_extract_verify_integration(self) -> ExtractVerifyOptimizationIntegration:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "normalized_document_ref": self.normalized_document_ref,
                    "extractor_plan_ref": self.extractor_plan_ref,
                    "field_confidence_refs": self.field_confidence_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing extract/verify integration missing refs: {missing}")
            if not (
                self.accepted_attempt_refs
                or self.rejected_attempt_refs
                or self.abstention_refs
            ):
                raise ValueError("extract/verify integration requires field outcomes")
            if self.llm_only_rejected_refs and not (self.rejected_attempt_refs or self.review_refs):
                raise ValueError("LLM-only refs must be rejected or routed to review")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass extract/verify integration requires typed diagnostics")
        return self


class DedupeIdentityOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    canonicalization_refs: list[Ref] = Field(default_factory=list)
    fingerprint_refs: list[Ref] = Field(default_factory=list)
    identity_decision_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_ref: Ref
    retained_refs: list[Ref] = Field(default_factory=list)
    suppressed_refs: list[Ref] = Field(default_factory=list)
    variant_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dedupe_identity_integration(self) -> DedupeIdentityOptimizationIntegration:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "canonicalization_refs": self.canonicalization_refs,
                    "fingerprint_refs": self.fingerprint_refs,
                    "identity_decision_refs": self.identity_decision_refs,
                    "duplicate_suppression_ref": self.duplicate_suppression_ref,
                    "retained_refs": self.retained_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing dedupe integration missing refs: {missing}")
            if set(self.retained_refs) & set(self.suppressed_refs):
                raise ValueError("dedupe integration cannot retain and suppress the same ref")
            if not set(self.variant_refs).issubset(set(self.retained_refs)):
                raise ValueError("variant refs must be retained")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass dedupe integration requires typed diagnostics")
        return self


class RankingPublicationOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    ranked_output_set_ref: Ref
    ranking_score_refs: list[Ref] = Field(default_factory=list)
    retained_output_refs: list[Ref] = Field(default_factory=list)
    verification_status_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    missing_optional_feature_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS
    failure_type: CrawlerOptimizationFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ranking_publication_integration(
        self,
    ) -> RankingPublicationOptimizationIntegration:
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "ranked_output_set_ref": self.ranked_output_set_ref,
                    "ranking_score_refs": self.ranking_score_refs,
                    "retained_output_refs": self.retained_output_refs,
                    "verification_status_refs": self.verification_status_refs,
                    "publication_gate_refs": self.publication_gate_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing ranking integration missing refs: {missing}")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass ranking integration requires typed diagnostics")
        return self


class CostCacheBudgetOptimizationIntegration(TimestampedModel):
    id: str
    fixture_id: str
    fetch_cost: float
    browser_cost: float
    token_cost: float
    cache_hit_refs: list[Ref] = Field(default_factory=list)
    stale_cache_refs: list[Ref] = Field(default_factory=list)
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    budget_exhausted: bool = False
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_cost_cache_budget_integration(
        self,
    ) -> CostCacheBudgetOptimizationIntegration:
        if self.fetch_cost < 0 or self.browser_cost < 0 or self.token_cost < 0:
            raise ValueError("cost values must be non-negative")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "metric_slice_refs": self.metric_slice_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing cost/cache integration missing refs: {missing}")
            if self.stale_cache_refs or self.budget_exhausted:
                raise ValueError(
                    "passing cost/cache integration cannot have stale cache or budget exhaustion"
                )
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass cost/cache integration requires typed diagnostics")
        return self


class DriftRecoveryFeedbackIntegration(TimestampedModel):
    id: str
    fixture_id: str
    drift_type: str
    affected_ref: Ref
    retry_class: str
    repair_outcome: str
    memory_advisory_refs: list[Ref] = Field(default_factory=list)
    unsafe_recovery_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_drift_recovery_feedback(self) -> DriftRecoveryFeedbackIntegration:
        allowed_drift = {
            "selector_drift",
            "template_drift",
            "field_validation_drift",
            "stale_cache",
            "timeout_retry",
            "source_limited",
        }
        if self.drift_type not in allowed_drift:
            raise ValueError("unsupported drift type")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "affected_ref": self.affected_ref,
                    "retry_class": self.retry_class,
                    "repair_outcome": self.repair_outcome,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type:
                raise ValueError(f"passing drift/recovery integration missing refs: {missing}")
            if self.unsafe_recovery_refs:
                raise ValueError(
                    "passing drift/recovery integration cannot include unsafe recovery"
                )
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass drift/recovery integration requires typed diagnostics")
        return self


class OptimizationRegressionReleaseGate(TimestampedModel):
    id: str
    fixture_id: str
    required_lower_integration_kinds: list[str] = Field(default_factory=list)
    present_lower_integration_kinds: list[str] = Field(default_factory=list)
    lower_integration_refs: list[Ref] = Field(default_factory=list)
    missing_lower_integration_refs: list[Ref] = Field(default_factory=list)
    failed_lower_integration_refs: list[Ref] = Field(default_factory=list)
    replay_gap_refs: list[Ref] = Field(default_factory=list)
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    metric_regression_refs: list[Ref] = Field(default_factory=list)
    false_ready_guard_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_regression_release_gate(self) -> OptimizationRegressionReleaseGate:
        if self.completion_result == CompletenessResult.PASS:
            missing_kinds = sorted(
                set(self.required_lower_integration_kinds)
                - set(self.present_lower_integration_kinds)
            )
            expected_prefixes = {
                "scheduler": "scheduler-optimization-integration:",
                "normalize": "normalize-optimization-integration:",
                "extract_verify": "extract-verify-optimization-integration:",
                "dedupe_identity": "dedupe-identity-optimization-integration:",
                "ranking_publication": "ranking-publication-optimization-integration:",
                "cost_cache_budget": "cost-cache-budget-optimization-integration:",
                "drift_recovery": "drift-recovery-feedback-integration:",
            }
            missing_report_refs = [
                kind
                for kind, prefix in expected_prefixes.items()
                if kind in self.required_lower_integration_kinds
                and not any(ref.startswith(prefix) for ref in self.lower_integration_refs)
            ]
            missing = _missing_refs(
                {
                    "required_lower_integration_kinds": (
                        self.required_lower_integration_kinds
                    ),
                    "present_lower_integration_kinds": self.present_lower_integration_kinds,
                    "lower_integration_refs": self.lower_integration_refs,
                    "metric_slice_refs": self.metric_slice_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if (
                missing
                or missing_kinds
                or missing_report_refs
                or self.failure_type
                or self.missing_lower_integration_refs
                or self.failed_lower_integration_refs
                or self.replay_gap_refs
                or self.metric_regression_refs
                or self.false_ready_guard_refs
            ):
                raise ValueError(
                    "passing regression gate missing refs: "
                    f"{missing}; missing lower integration kinds: {missing_kinds}; "
                    f"missing lower report refs: {missing_report_refs}"
                )
        elif not (
            self.failure_type
            and self.diagnostics
            and (
                self.missing_lower_integration_refs
                or self.failed_lower_integration_refs
                or self.replay_gap_refs
                or self.metric_regression_refs
                or self.false_ready_guard_refs
            )
        ):
            raise ValueError("non-pass regression gate requires typed diagnostics")
        return self


class OptimizationObjectiveScore(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    profile_ref: Ref
    score_formula_ref: Ref = OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF
    score_threshold: float = 0.82
    extraction_accuracy: float
    intent_match_precision: float
    crawl_success_rate: float
    dedupe_quality: float
    freshness: float
    normalized_latency: float
    normalized_cost: float
    optimization_score: float
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    algorithm_recommendation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_objective_score(self) -> OptimizationObjectiveScore:
        for name in [
            "score_threshold",
            "extraction_accuracy",
            "intent_match_precision",
            "crawl_success_rate",
            "dedupe_quality",
            "freshness",
            "normalized_latency",
            "normalized_cost",
        ]:
            _check_score(name, getattr(self, name))
        if self.optimization_score < -0.05 or self.optimization_score > 1:
            raise ValueError("optimization_score must be between -0.05 and 1")
        if self.score_formula_ref != OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF:
            raise ValueError("unsupported optimization objective score formula")
        expected_score = (
            0.35 * self.extraction_accuracy
            + 0.25 * self.intent_match_precision
            + 0.15 * self.crawl_success_rate
            + 0.10 * self.dedupe_quality
            + 0.10 * self.freshness
            - 0.03 * self.normalized_latency
            - 0.02 * self.normalized_cost
        )
        if abs(self.optimization_score - expected_score) > (
            OPTIMIZATION_OBJECTIVE_SCORE_TOLERANCE
        ):
            raise ValueError("optimization objective score formula mismatch")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "run_ref": self.run_ref,
                    "profile_ref": self.profile_ref,
                    "score_formula_ref": self.score_formula_ref,
                    "metric_slice_refs": self.metric_slice_refs,
                    "algorithm_recommendation_refs": self.algorithm_recommendation_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "artifact_refs": self.artifact_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type or self.optimization_score < self.score_threshold:
                raise ValueError(
                    "passing optimization objective score missing refs or below "
                    f"threshold: {missing}"
                )
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass objective score requires typed diagnostics")
        return self


class AgentDecisionLoopEvidence(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    objective_score_ref: Ref
    observe_ref: Ref | None = None
    think_ref: Ref | None = None
    act_ref: Ref | None = None
    verify_ref: Ref | None = None
    confidence: float
    confidence_threshold: float = 0.82
    stop_condition_ref: Ref | None = None
    deterministic_decision_refs: list[Ref] = Field(default_factory=list)
    llm_fallback_used: bool = False
    llm_fallback_reason_refs: list[Ref] = Field(default_factory=list)
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    model_trace_refs: list[Ref] = Field(default_factory=list)
    tool_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_decision_loop(self) -> AgentDecisionLoopEvidence:
        _check_score("confidence", self.confidence)
        _check_score("confidence_threshold", self.confidence_threshold)
        if self.llm_fallback_used and not (
            self.llm_fallback_reason_refs and self.model_trace_refs
        ):
            raise ValueError("LLM fallback requires reason and model trace refs")
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "run_ref": self.run_ref,
                    "objective_score_ref": self.objective_score_ref,
                    "observe_ref": self.observe_ref,
                    "think_ref": self.think_ref,
                    "act_ref": self.act_ref,
                    "verify_ref": self.verify_ref,
                    "stop_condition_ref": self.stop_condition_ref,
                    "deterministic_decision_refs": self.deterministic_decision_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "artifact_refs": self.artifact_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if missing or self.failure_type or self.confidence < self.confidence_threshold:
                raise ValueError(
                    "passing agent decision loop evidence missing refs or below "
                    f"threshold: {missing}"
                )
            if self.llm_output_evidence_refs:
                raise ValueError("LLM output cannot be agent decision source evidence")
        elif not (self.failure_type and self.diagnostics):
            raise ValueError("non-pass agent decision loop requires typed diagnostics")
        return self


class OptimizationObjectiveReleaseGate(TimestampedModel):
    id: str
    fixture_id: str
    claim_scope_ref: Ref
    required_lower_gate_refs: list[Ref] = Field(default_factory=list)
    present_lower_gate_refs: list[Ref] = Field(default_factory=list)
    failed_lower_gate_refs: list[Ref] = Field(default_factory=list)
    objective_score_refs: list[Ref] = Field(default_factory=list)
    failed_objective_score_refs: list[Ref] = Field(default_factory=list)
    agent_decision_loop_refs: list[Ref] = Field(default_factory=list)
    failed_agent_decision_loop_refs: list[Ref] = Field(default_factory=list)
    metric_slice_refs: list[Ref] = Field(default_factory=list)
    algorithm_recommendation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult
    failure_type: CrawlerOptimizationFailureType | None = None

    @model_validator(mode="after")
    def validate_objective_release_gate(self) -> OptimizationObjectiveReleaseGate:
        missing_lower = sorted(
            set(self.required_lower_gate_refs) - set(self.present_lower_gate_refs)
        )
        non_096_lower_refs = [
            ref
            for ref in self.present_lower_gate_refs
            if not ref.startswith("optimization-regression-release-gate:")
        ]
        if self.completion_result == CompletenessResult.PASS:
            missing = _missing_refs(
                {
                    "claim_scope_ref": self.claim_scope_ref,
                    "required_lower_gate_refs": self.required_lower_gate_refs,
                    "present_lower_gate_refs": self.present_lower_gate_refs,
                    "objective_score_refs": self.objective_score_refs,
                    "agent_decision_loop_refs": self.agent_decision_loop_refs,
                    "metric_slice_refs": self.metric_slice_refs,
                    "algorithm_recommendation_refs": self.algorithm_recommendation_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "artifact_refs": self.artifact_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                }
            )
            if (
                missing
                or missing_lower
                or non_096_lower_refs
                or self.failure_type
                or self.failed_lower_gate_refs
                or self.failed_objective_score_refs
                or self.failed_agent_decision_loop_refs
            ):
                raise ValueError(
                    "passing optimization objective release gate missing refs: "
                    f"{missing}; missing lower gates: {missing_lower}; "
                    f"non-096 lower refs: {non_096_lower_refs}"
                )
        elif not (
            self.failure_type
            and self.diagnostics
            and (
                missing_lower
                or self.failed_lower_gate_refs
                or self.failed_objective_score_refs
                or self.failed_agent_decision_loop_refs
            )
        ):
            raise ValueError("non-pass objective release gate requires typed diagnostics")
        return self


class CrawlerOptimizationManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    objective_ref: Ref
    min_crawl_success_rate: float = 0.95
    min_precision: float = 0.95
    min_recall: float = 0.88
    min_extraction_accuracy: float = 0.96
    max_duplicate_rate: float = 0.05
    max_cost_per_success: float = 0.12
    max_latency_p95_ms: int = 5000
    min_ranking_ndcg: float = 0.90
    min_llm_token_savings_rate: float = 0.30
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: CrawlerOptimizationFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)
    algorithm_refs: list[Ref] = Field(default_factory=list)
    architecture_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> CrawlerOptimizationManifest:
        if "optimization" not in self.profile_refs:
            raise ValueError("crawler optimization manifest must support optimization profile")
        for name in [
            "min_crawl_success_rate",
            "min_precision",
            "min_recall",
            "min_extraction_accuracy",
            "max_duplicate_rate",
            "min_ranking_ndcg",
            "min_llm_token_savings_rate",
        ]:
            _check_score(name, getattr(self, name))
        if self.max_cost_per_success <= 0 or self.max_latency_p95_ms < 1:
            raise ValueError("crawler optimization cost and latency thresholds must be positive")
        if not self.required_ref_types or not self.algorithm_refs or not self.architecture_refs:
            raise ValueError("crawler optimization manifest requires refs")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative optimization fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative optimization fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive optimization fixture must expect pass")
        return self


class CrawlerOptimizationArchitectureSpec(TimestampedModel):
    id: str
    architecture_ref: Ref
    component_refs: list[Ref] = Field(default_factory=list)
    data_contract_refs: list[Ref] = Field(default_factory=list)
    port_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    replay_policy_ref: Ref
    safety_policy_ref: Ref
    module_boundaries: dict[str, list[str]] = Field(default_factory=dict)
    roadmap_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_architecture(self) -> CrawlerOptimizationArchitectureSpec:
        missing = _missing_refs(
            {
                "architecture_ref": self.architecture_ref,
                "component_refs": self.component_refs,
                "data_contract_refs": self.data_contract_refs,
                "port_refs": self.port_refs,
                "event_refs": self.event_refs,
                "replay_policy_ref": self.replay_policy_ref,
                "safety_policy_ref": self.safety_policy_ref,
                "module_boundaries": self.module_boundaries,
                "roadmap_refs": self.roadmap_refs,
            }
        )
        if missing:
            raise ValueError(f"crawler optimization architecture missing refs: {missing}")
        return self


class AlgorithmRecommendation(TimestampedModel):
    id: str
    algorithm_name: str
    solves_problem_refs: list[Ref] = Field(default_factory=list)
    priority: str
    expected_benefit: str
    implementation_complexity: str
    system_change_refs: list[Ref] = Field(default_factory=list)
    validation_metric_refs: list[Ref] = Field(default_factory=list)
    pseudo_code_ref: Ref
    score_formula_ref: Ref | None = None
    fallback_chain_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_algorithm(self) -> AlgorithmRecommendation:
        if self.priority not in {"P0", "P1", "P2"}:
            raise ValueError("algorithm priority must be P0, P1, or P2")
        if self.implementation_complexity not in {"low", "medium", "high"}:
            raise ValueError("implementation complexity must be low, medium, or high")
        missing = _missing_refs(
            {
                "algorithm_name": self.algorithm_name,
                "solves_problem_refs": self.solves_problem_refs,
                "expected_benefit": self.expected_benefit,
                "system_change_refs": self.system_change_refs,
                "validation_metric_refs": self.validation_metric_refs,
                "pseudo_code_ref": self.pseudo_code_ref,
            }
        )
        if missing:
            raise ValueError(f"algorithm recommendation missing refs: {missing}")
        return self


JsonObject = dict[str, Any]
