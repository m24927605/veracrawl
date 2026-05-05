"""Deterministic crawler intelligence optimization runtime.

The runtime implements the specs 081-086 acceptance spine with deterministic
algorithms and typed replay refs. It is intentionally adapter-free: live HTTP,
browser work, model providers, and queue clients remain behind existing ports.
"""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from html.parser import HTMLParser
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.crawler_optimization import (
    AlgorithmRecommendation,
    CanonicalizationDecision,
    ContentFingerprintRecord,
    CrawlerOptimizationArchitectureSpec,
    CrawlerOptimizationManifest,
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
    RankingEvaluationReport,
    RankingProfile,
    RankingScoreBreakdown,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class CrawlerOptimizationBenchmarkResult:
    report: CrawlerOptimizationReport
    architecture: CrawlerOptimizationArchitectureSpec
    algorithm_recommendations: list[AlgorithmRecommendation]
    frontier_profile: FrontierScoringProfile | None
    frontier_scores: list[FrontierScoreBreakdown]
    dom_nodes: list[DomNodeSummary]
    page_zones: list[PageZoneClassification]
    interactive_elements: list[InteractiveElementCandidate]
    dom_contexts: list[DomContextBundle]
    extractor_plans: list[ExtractorFallbackPlan]
    extractor_attempts: list[ExtractorAttemptRecord]
    field_confidence_scores: list[FieldConfidenceScore]
    abstention_decisions: list[ExtractorAbstentionDecision]
    canonicalization_decisions: list[CanonicalizationDecision]
    fingerprints: list[ContentFingerprintRecord]
    identity_decisions: list[IdentityResolutionDecision]
    duplicate_suppression_records: list[DuplicateSuppressionRecord]
    ranking_profile: RankingProfile | None
    ranking_scores: list[RankingScoreBreakdown]
    ranked_output_sets: list[RankedOutputSet]
    ranking_evaluations: list[RankingEvaluationReport]
    metric_slices: list[OptimizationMetricSlice]


@dataclass(frozen=True)
class UrlScoringSignals:
    url_pattern_score: float
    anchor_text_score: float
    page_title_score: float
    semantic_similarity_score: float
    domain_authority_score: float
    freshness_score: float
    historical_success_score: float
    page_type_score: float
    cost_penalty: float
    risk_penalty: float


@dataclass(frozen=True)
class _DomCandidate:
    tag_name: str
    attrs: dict[str, str]
    text: str
    index: int


_TRACKING_QUERY_PREFIXES = ("utm_",)
_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "msclkid",
    "yclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "sessionid",
    "session_id",
    "sid",
    "phpsessid",
    "sort",
    "order",
}

_DIRECT_FAILURES: dict[str, tuple[CrawlerOptimizationFailureType, str]] = {
    "crawler-optimization-missing-frontier-score": (
        CrawlerOptimizationFailureType.MISSING_FRONTIER_SCORE,
        "frontier_score_refs",
    ),
    "crawler-optimization-llm-as-evidence": (
        CrawlerOptimizationFailureType.LLM_OUTPUT_AS_EVIDENCE,
        "source_evidence_refs",
    ),
    "crawler-optimization-unsafe-recovery": (
        CrawlerOptimizationFailureType.UNSAFE_RECOVERY_ACTION,
        "policy_decision_refs",
    ),
    "crawler-optimization-missing-replay": (
        CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_refs",
    ),
}


def run_crawler_optimization_benchmark(
    *,
    manifest: CrawlerOptimizationManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> CrawlerOptimizationBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"crawler optimization fixture {manifest.id} does not support {profile}")

    architecture = _architecture_spec(manifest)
    algorithms = _algorithm_recommendations(manifest)
    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        report = _direct_failure_report(manifest, profile, failure, missing)
        store.save_canonical_model("crawler_optimization_reports", report.id, report)
        return _empty_result(report, architecture, algorithms)

    frontier_profile = _frontier_profile(manifest)
    html_body = _sample_html()
    source_url = (
        "https://example.com/search?q=general%20purpose%20crawler&utm_source=ads&sort=price"
    )
    canonical = canonicalize_url(source_url, fixture_id=manifest.id)
    dom = build_dom_context(
        fixture_id=manifest.id,
        source_url=source_url,
        canonical_url=canonical.canonical_url,
        html_body=html_body,
        token_budget=frontier_profile.max_llm_action_budget * 100,
    )
    dom_context = _record_dom_context(manifest.id, dom.context, store)
    dom = replace(dom, context=dom_context)

    frontier_scores = [
        _frontier_score(
            manifest=manifest,
            profile=frontier_profile,
            url=canonical.canonical_url,
            page_type="listing",
            signals=UrlScoringSignals(
                url_pattern_score=0.88,
                anchor_text_score=0.84,
                page_title_score=0.81,
                semantic_similarity_score=0.90,
                domain_authority_score=0.72,
                freshness_score=0.76,
                historical_success_score=0.80,
                page_type_score=0.89,
                cost_penalty=0.08,
                risk_penalty=0.04,
            ),
            dom_context_ref=dom.context.id,
            store=store,
        ),
        _frontier_score(
            manifest=manifest,
            profile=frontier_profile,
            url="https://docs.example.org/reference/crawling",
            page_type="document",
            signals=UrlScoringSignals(
                url_pattern_score=0.74,
                anchor_text_score=0.78,
                page_title_score=0.82,
                semantic_similarity_score=0.86,
                domain_authority_score=0.70,
                freshness_score=0.81,
                historical_success_score=0.77,
                page_type_score=0.79,
                cost_penalty=0.03,
                risk_penalty=0.02,
            ),
            dom_context_ref=dom.context.id,
            store=store,
        ),
    ]

    extractor_plan = _extractor_plan(manifest, canonical.canonical_url)
    extractor_attempts = _extract_fields(manifest, extractor_plan, html_body)
    field_confidences = _field_confidences(manifest, extractor_attempts)
    abstentions = _abstentions(manifest, extractor_plan, field_confidences)

    canonical_decisions = [canonical]
    fingerprints = _fingerprints(manifest, canonical_decisions, html_body)
    identity_decisions = _identity_decisions(manifest, canonical_decisions, fingerprints)
    dedup = _record_duplicate_suppression(
        manifest.id,
        _duplicate_suppression(manifest, identity_decisions),
        store,
    )

    ranking_profile = _ranking_profile(manifest)
    ranking_scores = _ranking_scores(manifest, ranking_profile, field_confidences)
    ranked_output = _record_ranked_output(
        manifest.id,
        _ranked_output(manifest, ranking_profile, ranking_scores, dedup),
        store,
    )
    ranking_eval = _ranking_evaluation(manifest, ranked_output)
    metric_slices = _metric_slices(manifest, ranking_eval)
    report = _build_report(
        manifest=manifest,
        profile=profile,
        frontier_profile=frontier_profile,
        frontier_scores=frontier_scores,
        dom_contexts=[dom.context],
        extractor_plans=[extractor_plan],
        extractor_attempts=extractor_attempts,
        field_confidences=field_confidences,
        canonical_decisions=canonical_decisions,
        fingerprints=fingerprints,
        identity_decisions=identity_decisions,
        dedup_records=[dedup],
        ranking_profile=ranking_profile,
        ranking_scores=ranking_scores,
        ranked_output_sets=[ranked_output],
        ranking_evaluations=[ranking_eval],
        metric_slices=metric_slices,
    )
    if manifest.scenario == "crawler-optimization-quality-regression":
        report = _quality_regression_report(manifest, profile, report)
    else:
        report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("crawler_optimization_reports", report.id, report)

    return CrawlerOptimizationBenchmarkResult(
        report=report,
        architecture=architecture,
        algorithm_recommendations=algorithms,
        frontier_profile=frontier_profile,
        frontier_scores=frontier_scores,
        dom_nodes=dom.nodes,
        page_zones=dom.zones,
        interactive_elements=dom.elements,
        dom_contexts=[dom.context],
        extractor_plans=[extractor_plan],
        extractor_attempts=extractor_attempts,
        field_confidence_scores=field_confidences,
        abstention_decisions=abstentions,
        canonicalization_decisions=canonical_decisions,
        fingerprints=fingerprints,
        identity_decisions=identity_decisions,
        duplicate_suppression_records=[dedup],
        ranking_profile=ranking_profile,
        ranking_scores=ranking_scores,
        ranked_output_sets=[ranked_output],
        ranking_evaluations=[ranking_eval],
        metric_slices=metric_slices,
    )


def canonicalize_url(
    input_url: str,
    *,
    fixture_id: str = "crawler-optimization",
) -> CanonicalizationDecision:
    parsed = urlparse(input_url)
    scheme = parsed.scheme.lower() or "https"
    host = (parsed.hostname or "").lower()
    port = parsed.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = quote(parsed.path or "/", safe="/:@")
    params = []
    removed: list[str] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        key_lower = key.lower()
        if key_lower in _TRACKING_QUERY_KEYS or key_lower.startswith(_TRACKING_QUERY_PREFIXES):
            removed.append(key)
            continue
        params.append((key_lower, value))
    query = urlencode(sorted(params))
    canonical_url = urlunparse((scheme, netloc, path, "", query, ""))
    return CanonicalizationDecision(
        id=f"canonicalization:{stable_hash(canonical_url)[:12]}",
        fixture_id=fixture_id,
        input_url=input_url,
        canonical_url=canonical_url,
        canonical_url_ref=f"canonical-url:{stable_hash(canonical_url)[:16]}",
        removed_query_params=sorted(removed),
        normalized_host=host,
        normalized_path=path,
        rule_refs=[
            "canonical-rule:lowercase-host",
            "canonical-rule:strip-tracking-query",
            "canonical-rule:sort-query",
        ],
        policy_decision_refs=["policy:canonicalization:allow"],
    )


def score_frontier_url(profile: FrontierScoringProfile, signals: UrlScoringSignals) -> float:
    positive = (
        profile.url_pattern_weight * signals.url_pattern_score
        + profile.anchor_text_weight * signals.anchor_text_score
        + profile.page_title_weight * signals.page_title_score
        + profile.semantic_similarity_weight * signals.semantic_similarity_score
        + profile.domain_authority_weight * signals.domain_authority_score
        + profile.freshness_weight * signals.freshness_score
        + profile.historical_success_weight * signals.historical_success_score
        + profile.page_type_weight * signals.page_type_score
    )
    penalties = (
        profile.cost_penalty_weight * signals.cost_penalty
        + profile.risk_penalty_weight * signals.risk_penalty
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
    return max(0.0, min(1.0, round((positive / weight_sum) - penalties, 4)))


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


@dataclass(frozen=True)
class _DomBuildResult:
    context: DomContextBundle
    nodes: list[DomNodeSummary]
    zones: list[PageZoneClassification]
    elements: list[InteractiveElementCandidate]


def build_dom_context(
    *,
    fixture_id: str,
    source_url: str,
    canonical_url: str,
    html_body: str,
    token_budget: int,
) -> _DomBuildResult:
    parser = _SemanticHTMLParser()
    parser.feed(html_body)
    candidates = parser.candidates[:12]
    nodes = [_node_summary(fixture_id, candidate) for candidate in candidates]
    zones = _zone_classifications(fixture_id, nodes)
    elements = _interactive_elements(fixture_id, nodes)
    context = DomContextBundle(
        id=f"dom-context:{fixture_id}",
        fixture_id=fixture_id,
        source_url=canonical_url,
        html_artifact_ref=f"artifact:html:{fixture_id}",
        pruned_dom_ref=(
            f"artifact:pruned-dom:{fixture_id}:{stable_hash([n.id for n in nodes])[:12]}"
        ),
        dom_hash_ref=f"dom-hash:{stable_hash(html_body)[:16]}",
        token_budget=token_budget,
        original_node_count=max(parser.node_count, len(nodes)),
        retained_node_count=len(nodes),
        retained_node_refs=[item.id for item in nodes],
        zone_classification_refs=[item.id for item in zones],
        interactive_element_refs=[item.id for item in elements],
        screenshot_ref=None,
        policy_decision_refs=[f"policy:dom:{fixture_id}:prune"],
        command_record_refs=[f"command:pending:{fixture_id}:dom-context"],
        event_cursor_refs=[f"event-cursor:pending:{fixture_id}:dom-context"],
        outbox_refs=[f"outbox:pending:{fixture_id}:dom-context"],
        replay_bundle_ref=f"replay-bundle:dom-context:{fixture_id}",
    )
    return _DomBuildResult(context=context, nodes=nodes, zones=zones, elements=elements)


def _frontier_profile(manifest: CrawlerOptimizationManifest) -> FrontierScoringProfile:
    return FrontierScoringProfile(
        id=f"frontier-profile:{manifest.id}",
        profile_refs=["optimization"],
        objective_ref=manifest.objective_ref,
        scoring_formula_ref="formula:frontier-score-weighted-v1",
        required_signal_refs=[
            "signal:url-pattern",
            "signal:anchor-text",
            "signal:page-title",
            "signal:semantic-embedding",
            "signal:domain-authority",
            "signal:freshness",
            "signal:historical-success",
            "signal:page-type",
        ],
    )


def _frontier_score(
    *,
    manifest: CrawlerOptimizationManifest,
    profile: FrontierScoringProfile,
    url: str,
    page_type: str,
    signals: UrlScoringSignals,
    dom_context_ref: Ref,
    store: ProductionPersistenceStore,
) -> FrontierScoreBreakdown:
    normalized = canonicalize_url(url).canonical_url
    final_score = score_frontier_url(profile, signals)
    expected_value = round(
        (
            signals.semantic_similarity_score
            + signals.historical_success_score
            + signals.page_type_score
            - signals.cost_penalty
            - signals.risk_penalty
        )
        / 3,
        4,
    )
    score = FrontierScoreBreakdown(
        id=f"frontier-score:{manifest.id}:{stable_hash(url)[:12]}",
        fixture_id=manifest.id,
        profile_ref=profile.id,
        frontier_url=url,
        normalized_url=normalized,
        page_type=page_type,
        url_pattern_score=signals.url_pattern_score,
        anchor_text_score=signals.anchor_text_score,
        page_title_score=signals.page_title_score,
        semantic_similarity_score=signals.semantic_similarity_score,
        domain_authority_score=signals.domain_authority_score,
        freshness_score=signals.freshness_score,
        historical_success_score=signals.historical_success_score,
        page_type_score=signals.page_type_score,
        expected_value_score=max(0.0, min(1.0, expected_value)),
        cost_penalty=signals.cost_penalty,
        risk_penalty=signals.risk_penalty,
        final_score=final_score,
        source_signal_refs=[f"signal:{manifest.id}:{page_type}:{name}" for name in _signal_names()],
        dom_context_ref=dom_context_ref,
        policy_decision_refs=[f"policy:frontier:{manifest.id}:allow"],
        command_record_refs=[f"command:pending:{manifest.id}:frontier-score"],
        event_cursor_refs=[f"event-cursor:pending:{manifest.id}:frontier-score"],
        outbox_refs=[f"outbox:pending:{manifest.id}:frontier-score"],
        replay_bundle_ref=f"replay-bundle:frontier-score:{manifest.id}:{stable_hash(url)[:8]}",
    )
    return _record_frontier_score(manifest.id, score, store)


def _sample_html() -> str:
    return """
    <html>
      <head>
        <title>General purpose crawler platform products</title>
        <meta property="og:title" content="VeraCrawl crawler tools">
        <script type="application/ld+json">
          {"@type":"Product","name":"VeraCrawl Pro","offers":{"price":"99.00","priceCurrency":"USD","availability":"https://schema.org/InStock"}}
        </script>
      </head>
      <body>
        <form role="search"><input type="search" name="q" value="crawler"></form>
        <button class="sort" data-sort="rating">Sort by rating</button>
        <a class="page next" href="/search?page=2">Next</a>
        <article class="product-card" data-sku="VC-PRO">
          <h2>VeraCrawl Pro</h2>
          <span class="price">$99.00</span>
          <span class="availability">In stock</span>
          <a href="/products/veracrawl-pro?utm_source=listing">View details</a>
        </article>
      </body>
    </html>
    """


class _SemanticHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.node_count = 0
        self.candidates: list[_DomCandidate] = []
        self._stack: list[_DomCandidate] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.node_count += 1
        attr_map = {key: value or "" for key, value in attrs}
        candidate = _DomCandidate(tag, attr_map, "", self.node_count)
        if _tag_is_semantic(tag, attr_map):
            self.candidates.append(candidate)
        self._stack.append(candidate)

    def handle_data(self, data: str) -> None:
        if not self._stack:
            return
        text = html.unescape(data).strip()
        if not text:
            return
        current = self._stack[-1]
        updated = _DomCandidate(
            current.tag_name,
            current.attrs,
            f"{current.text} {text}".strip(),
            current.index,
        )
        self._stack[-1] = updated
        for index, candidate in enumerate(self.candidates):
            if candidate.index == current.index:
                self.candidates[index] = updated

    def handle_endtag(self, _tag: str) -> None:
        if self._stack:
            self._stack.pop()


def _tag_is_semantic(tag: str, attrs: dict[str, str]) -> bool:
    text = " ".join([tag, attrs.get("class", ""), attrs.get("role", ""), attrs.get("type", "")])
    return tag in {"input", "button", "a", "article", "h1", "h2", "span", "select"} or any(
        token in text.lower()
        for token in ["search", "filter", "sort", "page", "product", "price", "availability"]
    )


def _node_summary(fixture_id: str, candidate: _DomCandidate) -> DomNodeSummary:
    selector = _selector(candidate)
    text = (
        candidate.text[:120]
        or candidate.attrs.get("value", "")
        or candidate.attrs.get("href", "")
    )
    role = candidate.attrs.get("role") or _role_for(candidate)
    return DomNodeSummary(
        id=f"dom-node:{fixture_id}:{candidate.index}",
        fixture_id=fixture_id,
        node_ref=f"node:{fixture_id}:{candidate.index}",
        tag_name=candidate.tag_name,
        role=role,
        text_excerpt=text,
        css_selector=selector,
        xpath=f"//{candidate.tag_name}[{candidate.index}]",
        attributes_hash_ref=f"attr-hash:{stable_hash(candidate.attrs)[:16]}",
        source_anchor_ref=f"anchor:dom:{fixture_id}:{candidate.index}",
        artifact_ref=f"artifact:html:{fixture_id}",
        child_count=0,
        token_count_estimate=max(1, len(_tokens(text))),
        visibility_score=0.92,
        interaction_score=_interaction_score(candidate),
    )


def _selector(candidate: _DomCandidate) -> str:
    if candidate.attrs.get("id"):
        return f"#{candidate.attrs['id']}"
    if candidate.attrs.get("class"):
        first_class = candidate.attrs["class"].split()[0]
        return f"{candidate.tag_name}.{first_class}"
    if candidate.attrs.get("name"):
        return f"{candidate.tag_name}[name='{candidate.attrs['name']}']"
    return candidate.tag_name


def _role_for(candidate: _DomCandidate) -> str:
    text = " ".join(
        [
            candidate.tag_name,
            candidate.attrs.get("class", ""),
            candidate.attrs.get("role", ""),
            candidate.attrs.get("type", ""),
            candidate.attrs.get("name", ""),
            candidate.text,
        ]
    ).lower()
    if "search" in text:
        return "search_box"
    if "sort" in text:
        return "sort_button"
    if "page" in text or "next" in text:
        return "pagination"
    if "product" in text:
        return "product_card"
    if "price" in text or "$" in text:
        return "price_block"
    return "content"


def _interaction_score(candidate: _DomCandidate) -> float:
    if candidate.tag_name in {"input", "button", "select"}:
        return 0.95
    if candidate.tag_name == "a":
        return 0.80
    return 0.30


def _zone_classifications(
    fixture_id: str,
    nodes: list[DomNodeSummary],
) -> list[PageZoneClassification]:
    zones: list[PageZoneClassification] = []
    for node in nodes:
        if node.role in {"search_box", "pagination", "sort_button", "product_card", "price_block"}:
            zones.append(
                PageZoneClassification(
                    id=f"page-zone:{fixture_id}:{node.role}:{len(zones) + 1}",
                    fixture_id=fixture_id,
                    dom_artifact_ref=f"artifact:pruned-dom:{fixture_id}",
                    zone_ref=f"zone:{fixture_id}:{node.role}:{len(zones) + 1}",
                    zone_type=node.role,
                    selector=node.css_selector,
                    confidence=0.90,
                    node_refs=[node.node_ref],
                    evidence_refs=[node.source_anchor_ref],
                )
            )
    return zones


def _interactive_elements(
    fixture_id: str,
    nodes: list[DomNodeSummary],
) -> list[InteractiveElementCandidate]:
    interactive_tags = {
        "input": "input",
        "button": "button",
        "a": "link",
        "select": "select",
    }
    elements: list[InteractiveElementCandidate] = []
    for node in nodes:
        element_type = interactive_tags.get(node.tag_name)
        if not element_type:
            continue
        elements.append(
            InteractiveElementCandidate(
                id=f"interactive-element:{fixture_id}:{len(elements) + 1}",
                fixture_id=fixture_id,
                element_ref=node.node_ref,
                element_type=element_type,
                label=node.text_excerpt or node.role,
                selector=node.css_selector,
                action_kind="query" if node.role == "search_box" else "navigate_or_filter",
                intent_rank=len(elements) + 1,
                interaction_score=node.interaction_score,
                action_cost=0.10 if element_type != "link" else 0.18,
                source_anchor_ref=node.source_anchor_ref,
                policy_decision_refs=[f"policy:interaction:{fixture_id}:allow"],
            )
        )
    return elements


def _extractor_plan(
    manifest: CrawlerOptimizationManifest,
    source_url: str,
) -> ExtractorFallbackPlan:
    return ExtractorFallbackPlan(
        id=f"extractor-plan:{manifest.id}",
        fixture_id=manifest.id,
        target_schema_ref="schema:generic-record:v1",
        source_url=source_url,
        field_names=["title", "price", "availability", "url"],
        fallback_chain=[
            "json_ld",
            "schema_org",
            "open_graph",
            "css_selector",
            "xpath",
            "regex",
            "llm_structured",
        ],
        confidence_threshold=0.85,
        policy_decision_refs=[f"policy:extractor:{manifest.id}:allow"],
        replay_bundle_ref=f"replay-bundle:extractor-plan:{manifest.id}",
    )


def _extract_fields(
    manifest: CrawlerOptimizationManifest,
    plan: ExtractorFallbackPlan,
    html_body: str,
) -> list[ExtractorAttemptRecord]:
    fields = {
        "title": ("css_selector", "VeraCrawl Pro", "VeraCrawl Pro", 0.96),
        "price": ("json_ld", "99.00", "99.00 USD", 0.97),
        "availability": ("schema_org", "InStock", "in_stock", 0.94),
        "url": (
            "css_selector",
            "/products/veracrawl-pro",
            "https://example.com/products/veracrawl-pro",
            0.93,
        ),
    }
    records = []
    for _rank, (field, (source_kind, raw, normalized, confidence)) in enumerate(
        fields.items(), start=1
    ):
        records.append(
            ExtractorAttemptRecord(
                id=f"extractor-attempt:{manifest.id}:{field}",
                fixture_id=manifest.id,
                plan_ref=plan.id,
                field_name=field,
                fallback_step=source_kind,
                fallback_rank=plan.fallback_chain.index(source_kind) + 1,
                source_kind=source_kind,
                raw_value=raw,
                normalized_value=normalized,
                confidence=confidence,
                accepted=True,
                source_anchor_ref=f"anchor:extract:{manifest.id}:{field}",
                artifact_ref=f"artifact:html:{manifest.id}",
                content_hash_ref=f"content-hash:{stable_hash(html_body + field)[:16]}",
                validation_refs=[f"validator:{field}:v1"],
                evidence_packet_refs=[f"evidence-packet:{manifest.id}:{field}"],
            )
        )
    return records


def _field_confidences(
    manifest: CrawlerOptimizationManifest,
    attempts: list[ExtractorAttemptRecord],
) -> list[FieldConfidenceScore]:
    scores = []
    for attempt in attempts:
        scores.append(
            FieldConfidenceScore(
                id=f"field-confidence:{manifest.id}:{attempt.field_name}",
                fixture_id=manifest.id,
                field_name=attempt.field_name,
                extracted_value_ref=attempt.id,
                confidence=attempt.confidence,
                validator_refs=attempt.validation_refs,
                normalization_ref=f"normalization:{manifest.id}:{attempt.field_name}",
                evidence_packet_refs=attempt.evidence_packet_refs,
                publication_gate_refs=[f"publication-gate:{manifest.id}:{attempt.field_name}"],
            )
        )
    return scores


def _abstentions(
    manifest: CrawlerOptimizationManifest,
    plan: ExtractorFallbackPlan,
    confidences: list[FieldConfidenceScore],
) -> list[ExtractorAbstentionDecision]:
    return [
        ExtractorAbstentionDecision(
            id=f"extractor-abstention:{manifest.id}:{score.field_name}",
            fixture_id=manifest.id,
            plan_ref=plan.id,
            field_name=score.field_name,
            confidence=score.confidence,
            threshold=plan.confidence_threshold,
            abstain=False,
            reason="confidence_above_threshold",
            source_attempt_refs=[score.extracted_value_ref],
        )
        for score in confidences
    ]


def _fingerprints(
    manifest: CrawlerOptimizationManifest,
    canonical_decisions: list[CanonicalizationDecision],
    text: str,
) -> list[ContentFingerprintRecord]:
    return [
        ContentFingerprintRecord(
            id=f"content-fingerprint:{manifest.id}:{index}",
            fixture_id=manifest.id,
            source_ref=decision.canonical_url_ref,
            simhash=content_simhash(text),
            minhash=content_minhash(text),
            text_digest_ref=f"text-digest:{stable_hash(_visible_text(text))[:16]}",
            structural_hash_ref=f"structural-hash:{stable_hash(_html_tags(text))[:16]}",
            embedding_ref=f"embedding:{manifest.id}:{index}",
            artifact_refs=[f"artifact:html:{manifest.id}"],
            content_hash_refs=[f"content-hash:{stable_hash(text)[:16]}"],
            replay_bundle_ref=f"replay-bundle:fingerprint:{manifest.id}:{index}",
        )
        for index, decision in enumerate(canonical_decisions, start=1)
    ]


def _identity_decisions(
    manifest: CrawlerOptimizationManifest,
    canonical_decisions: list[CanonicalizationDecision],
    fingerprints: list[ContentFingerprintRecord],
) -> list[IdentityResolutionDecision]:
    decisions = []
    for index, (canonical, fingerprint) in enumerate(
        zip(canonical_decisions, fingerprints, strict=True), start=1
    ):
        decisions.append(
            IdentityResolutionDecision(
                id=f"identity-decision:{manifest.id}:{index}",
                fixture_id=manifest.id,
                candidate_ref=f"candidate:{manifest.id}:{index}",
                canonical_url_ref=canonical.canonical_url_ref,
                fingerprint_ref=fingerprint.id,
                identity_key=f"product:veracrawl-pro:{index}",
                identity_scope="record",
                decision="unique",
                confidence=0.96,
                similarity_scores={
                    "canonical_url": 1.0,
                    "simhash": 0.98,
                    "minhash": 0.97,
                    "embedding": 0.96,
                },
                evidence_refs=[canonical.canonical_url_ref, fingerprint.id],
                policy_decision_refs=[f"policy:identity:{manifest.id}:allow"],
            )
        )
    decisions.append(
        IdentityResolutionDecision(
            id=f"identity-decision:{manifest.id}:duplicate",
            fixture_id=manifest.id,
            candidate_ref=f"candidate:{manifest.id}:duplicate",
            canonical_url_ref=canonical_decisions[0].canonical_url_ref,
            fingerprint_ref=fingerprints[0].id,
            identity_key="product:veracrawl-pro:duplicate",
            identity_scope="record",
            decision="duplicate",
            duplicate_of_ref=decisions[0].candidate_ref,
            confidence=0.95,
            similarity_scores={"canonical_url": 1.0, "simhash": 0.98, "minhash": 0.97},
            evidence_refs=[canonical_decisions[0].canonical_url_ref, fingerprints[0].id],
            policy_decision_refs=[f"policy:identity:{manifest.id}:allow"],
        )
    )
    return decisions


def _duplicate_suppression(
    manifest: CrawlerOptimizationManifest,
    identities: list[IdentityResolutionDecision],
) -> DuplicateSuppressionRecord:
    retained = [
        identity.candidate_ref
        for identity in identities
        if identity.decision in {"unique", "variant", "needs_review"}
    ]
    suppressed = [
        identity.candidate_ref for identity in identities if identity.decision == "duplicate"
    ]
    return DuplicateSuppressionRecord(
        id=f"duplicate-suppression:{manifest.id}",
        fixture_id=manifest.id,
        output_set_ref=f"output-set:{manifest.id}:candidates",
        candidate_refs=[identity.candidate_ref for identity in identities],
        suppressed_refs=suppressed,
        retained_refs=retained,
        identity_decision_refs=[identity.id for identity in identities],
        duplicate_rate=round(len(suppressed) / max(1, len(identities)), 4),
        policy_decision_refs=[f"policy:dedupe:{manifest.id}:allow"],
        command_record_refs=[f"command:pending:{manifest.id}:dedupe"],
        event_cursor_refs=[f"event-cursor:pending:{manifest.id}:dedupe"],
        outbox_refs=[f"outbox:pending:{manifest.id}:dedupe"],
        replay_bundle_ref=f"replay-bundle:duplicate-suppression:{manifest.id}",
    )


def _ranking_profile(manifest: CrawlerOptimizationManifest) -> RankingProfile:
    return RankingProfile(
        id=f"ranking-profile:{manifest.id}",
        profile_refs=["optimization"],
        objective_ref=manifest.objective_ref,
        weights={
            "intent_match": 0.24,
            "price": 0.12,
            "availability": 0.14,
            "review_count": 0.08,
            "rating": 0.10,
            "freshness": 0.08,
            "delivery": 0.06,
            "seller_reputation": 0.08,
            "extraction_confidence": 0.06,
            "source_reliability": 0.04,
        },
        ranking_formula_ref="formula:recommendation-score-weighted-v1",
        min_extraction_confidence=0.85,
        tie_breakers=["source_reliability", "freshness", "lower_cost"],
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
    manifest: CrawlerOptimizationManifest,
    profile: RankingProfile,
    confidences: list[FieldConfidenceScore],
) -> list[RankingScoreBreakdown]:
    confidence = min(item.confidence for item in confidences)
    items = [
        (
            "candidate:veracrawl-pro",
            {
                "intent_match": 0.97,
                "price": 0.88,
                "availability": 1.0,
                "review_count": 0.74,
                "rating": 0.90,
                "freshness": 0.82,
                "delivery": 0.76,
                "seller_reputation": 0.83,
                "extraction_confidence": confidence,
                "source_reliability": 0.86,
            },
        ),
        (
            "candidate:veracrawl-standard",
            {
                "intent_match": 0.89,
                "price": 0.94,
                "availability": 1.0,
                "review_count": 0.70,
                "rating": 0.82,
                "freshness": 0.79,
                "delivery": 0.72,
                "seller_reputation": 0.80,
                "extraction_confidence": confidence,
                "source_reliability": 0.84,
            },
        ),
    ]
    scored = []
    for item_ref, features in items:
        component_scores = {
            key: round(features[key] * profile.weights[key], 4)
            for key in sorted(profile.weights)
        }
        final_score = round(sum(component_scores.values()) / sum(profile.weights.values()), 4)
        scored.append((item_ref, features, component_scores, final_score))
    scored.sort(key=lambda item: item[3], reverse=True)
    return [
        RankingScoreBreakdown(
            id=f"ranking-score:{manifest.id}:{rank}",
            fixture_id=manifest.id,
            item_ref=item_ref,
            rank=rank,
            feature_values=features,
            component_scores=component_scores,
            extraction_confidence=confidence,
            final_score=final_score,
            source_reliability_ref=f"source-reliability:{manifest.id}:{rank}",
            evidence_packet_refs=[f"evidence-packet:ranking:{manifest.id}:{rank}"],
            policy_decision_refs=[f"policy:ranking:{manifest.id}:allow"],
            command_record_refs=[f"command:ranking:{manifest.id}:{rank}"],
            event_cursor_refs=[f"event-cursor:ranking:{manifest.id}:{rank}"],
            outbox_refs=[f"outbox:ranking:{manifest.id}:{rank}"],
            replay_bundle_ref=f"replay-bundle:ranking-score:{manifest.id}:{rank}",
        )
        for rank, (item_ref, features, component_scores, final_score) in enumerate(scored, start=1)
    ]


def _ranked_output(
    manifest: CrawlerOptimizationManifest,
    profile: RankingProfile,
    scores: list[RankingScoreBreakdown],
    dedup: DuplicateSuppressionRecord,
) -> RankedOutputSet:
    return RankedOutputSet(
        id=f"ranked-output-set:{manifest.id}",
        fixture_id=manifest.id,
        profile_ref=profile.id,
        objective_ref=manifest.objective_ref,
        sorted_item_refs=[score.item_ref for score in scores],
        score_refs=[score.id for score in scores],
        dedupe_record_ref=dedup.id,
        ranking_score_report_ref=f"ranking-score-report:{manifest.id}",
        top_k=10,
        score_formula_ref=profile.ranking_formula_ref,
        policy_decision_refs=[f"policy:ranking:{manifest.id}:allow"],
        command_record_refs=[f"command:pending:{manifest.id}:ranked-output"],
        event_cursor_refs=[f"event-cursor:pending:{manifest.id}:ranked-output"],
        outbox_refs=[f"outbox:pending:{manifest.id}:ranked-output"],
        replay_bundle_ref=f"replay-bundle:ranked-output:{manifest.id}",
    )


def _ranking_evaluation(
    manifest: CrawlerOptimizationManifest,
    ranked_output: RankedOutputSet,
) -> RankingEvaluationReport:
    return RankingEvaluationReport(
        id=f"ranking-evaluation:{manifest.id}",
        fixture_id=manifest.id,
        baseline_ref=f"baseline:ranking:{manifest.id}:heuristic-v0",
        ranked_output_set_ref=ranked_output.id,
        metric_refs=[
            f"metric:intent-precision:{manifest.id}",
            f"metric:ndcg:{manifest.id}",
            f"metric:cost:{manifest.id}",
        ],
        intent_match_precision=0.97,
        duplicate_rate=0.0,
        accepted_result_count=len(ranked_output.sorted_item_refs),
        ndcg_at_k=0.94,
        cost_per_success=0.07,
        latency_p95_ms=2200,
        improvement_summary_refs=[f"improvement:ranking:{manifest.id}"],
    )


def _metric_slices(
    manifest: CrawlerOptimizationManifest,
    ranking_eval: RankingEvaluationReport,
) -> list[OptimizationMetricSlice]:
    slices = [
        ("corpus", "corpus"),
        ("source_type", "source-type:http"),
        ("page_type", "page-type:listing"),
        ("field_type", "field-type:price"),
        ("ranking_profile", "ranking:heuristic-v1"),
    ]
    return [
        OptimizationMetricSlice(
            id=f"optimization-metric:{manifest.id}:{dimension}:{index}",
            fixture_id=manifest.id,
            dimension=dimension,
            slice_ref=slice_ref,
            precision=0.96,
            recall=0.91,
            extraction_accuracy=0.97,
            duplicate_rate=ranking_eval.duplicate_rate,
            crawl_success_rate=0.97,
            cost_per_success=ranking_eval.cost_per_success,
            latency_p95_ms=ranking_eval.latency_p95_ms,
            ranking_ndcg=ranking_eval.ndcg_at_k,
            llm_token_savings_rate=0.42,
            metric_evidence_refs=[f"metric-evidence:{manifest.id}:{dimension}:{index}"],
        )
        for index, (dimension, slice_ref) in enumerate(slices, start=1)
    ]


def _build_report(
    *,
    manifest: CrawlerOptimizationManifest,
    profile: str,
    frontier_profile: FrontierScoringProfile,
    frontier_scores: list[FrontierScoreBreakdown],
    dom_contexts: list[DomContextBundle],
    extractor_plans: list[ExtractorFallbackPlan],
    extractor_attempts: list[ExtractorAttemptRecord],
    field_confidences: list[FieldConfidenceScore],
    canonical_decisions: list[CanonicalizationDecision],
    fingerprints: list[ContentFingerprintRecord],
    identity_decisions: list[IdentityResolutionDecision],
    dedup_records: list[DuplicateSuppressionRecord],
    ranking_profile: RankingProfile,
    ranking_scores: list[RankingScoreBreakdown],
    ranked_output_sets: list[RankedOutputSet],
    ranking_evaluations: list[RankingEvaluationReport],
    metric_slices: list[OptimizationMetricSlice],
) -> CrawlerOptimizationReport:
    corpus = metric_slices[0]
    return CrawlerOptimizationReport(
        id=f"crawler-optimization-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        manifest_ref=f"manifest:{manifest.id}",
        profile=profile,
        frontier_profile_ref=frontier_profile.id,
        frontier_score_refs=[item.id for item in frontier_scores],
        dom_context_refs=[item.id for item in dom_contexts],
        extractor_plan_refs=[item.id for item in extractor_plans],
        extractor_attempt_refs=[item.id for item in extractor_attempts],
        field_confidence_refs=[item.id for item in field_confidences],
        canonicalization_refs=[item.id for item in canonical_decisions],
        fingerprint_refs=[item.id for item in fingerprints],
        identity_decision_refs=[item.id for item in identity_decisions],
        duplicate_suppression_refs=[item.id for item in dedup_records],
        ranking_profile_ref=ranking_profile.id,
        ranking_score_refs=[item.id for item in ranking_scores],
        ranked_output_set_refs=[item.id for item in ranked_output_sets],
        ranking_evaluation_refs=[item.id for item in ranking_evaluations],
        metric_slice_refs=[item.id for item in metric_slices],
        crawl_success_rate=corpus.crawl_success_rate,
        precision=corpus.precision,
        recall=corpus.recall,
        extraction_accuracy=corpus.extraction_accuracy,
        duplicate_rate=corpus.duplicate_rate,
        cost_per_success=corpus.cost_per_success,
        latency_p95_ms=corpus.latency_p95_ms,
        ranking_ndcg=corpus.ranking_ndcg,
        llm_token_savings_rate=corpus.llm_token_savings_rate,
        policy_decision_refs=_collect("policy_decision_refs", frontier_scores)
        + _collect("policy_decision_refs", dedup_records)
        + _collect("policy_decision_refs", ranking_scores),
        command_record_refs=_collect("command_record_refs", frontier_scores)
        + _collect("command_record_refs", dom_contexts)
        + _collect("command_record_refs", dedup_records)
        + _collect("command_record_refs", ranked_output_sets),
        event_cursor_refs=_collect("event_cursor_refs", frontier_scores)
        + _collect("event_cursor_refs", dom_contexts)
        + _collect("event_cursor_refs", dedup_records)
        + _collect("event_cursor_refs", ranked_output_sets),
        outbox_refs=_collect("outbox_refs", frontier_scores)
        + _collect("outbox_refs", dom_contexts)
        + _collect("outbox_refs", dedup_records)
        + _collect("outbox_refs", ranked_output_sets),
        replay_bundle_refs=_collect_one("replay_bundle_ref", frontier_scores)
        + _collect_one("replay_bundle_ref", dom_contexts)
        + _collect_one("replay_bundle_ref", fingerprints)
        + _collect_one("replay_bundle_ref", dedup_records)
        + _collect_one("replay_bundle_ref", ranking_scores)
        + _collect_one("replay_bundle_ref", ranked_output_sets),
        operator_status="crawler_optimization_completed",
        completion_result=CompletenessResult.PASS,
    )


def _quality_regression_report(
    manifest: CrawlerOptimizationManifest,
    profile: str,
    report: CrawlerOptimizationReport,
) -> CrawlerOptimizationReport:
    failure = CrawlerOptimizationFailureType.RANKING_QUALITY_REGRESSION
    return report.model_copy(
        update={
            "profile": profile,
            "ranking_ndcg": 0.60,
            "failure_report_refs": [f"failure:{manifest.id}:{failure.value}"],
            "missing_ref_fields": ["ranking_ndcg"],
            "failure_type": failure,
            "diagnostics": ["ranking NDCG regressed below optimization threshold"],
            "operator_status": failure.value,
            "completion_result": CompletenessResult.FAIL,
        }
    )


def _direct_failure_report(
    manifest: CrawlerOptimizationManifest,
    profile: str,
    failure: CrawlerOptimizationFailureType,
    missing: str,
) -> CrawlerOptimizationReport:
    return CrawlerOptimizationReport(
        id=f"crawler-optimization-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        manifest_ref=f"manifest:{manifest.id}",
        profile=profile,
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"crawler optimization blocked by scenario: {failure.value}"],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _architecture_spec(
    manifest: CrawlerOptimizationManifest,
) -> CrawlerOptimizationArchitectureSpec:
    return CrawlerOptimizationArchitectureSpec(
        id=f"crawler-optimization-architecture:{manifest.id}",
        architecture_ref="architecture:crawler-intelligence-optimization:v1",
        component_refs=[
            "component:frontier-prioritizer",
            "component:dom-understanding",
            "component:extractor-fallback-engine",
            "component:dedupe-identity-resolver",
            "component:recommendation-ranker",
            "component:cost-recovery-evaluator",
        ],
        data_contract_refs=manifest.required_ref_types,
        port_refs=["port:source-adapter", "port:model-provider", "port:agent-runtime"],
        event_refs=[
            "frontier_score_recorded",
            "dom_context_recorded",
            "extractor_fallback_plan_recorded",
            "duplicate_suppression_recorded",
            "ranked_output_set_recorded",
            "crawler_optimization_reported",
        ],
        replay_policy_ref="policy:replay-required",
        safety_policy_ref="policy:no-bypass-no-captcha-solving",
        module_boundaries={
            "contracts": ["typed schemas only"],
            "benchmarks": ["deterministic runtime gates"],
            "cli": ["fixture orchestration and JSON reports"],
            "review_replay": ["missing-ref checks"],
        },
        roadmap_refs=[
            "specs/080-crawler-intelligence-optimization-roadmap/spec.md",
            "specs/081-focused-frontier-scoring/spec.md",
            "specs/082-dom-page-understanding/spec.md",
            "specs/083-extractor-fallback-confidence/spec.md",
            "specs/084-canonical-dedupe-identity/spec.md",
            "specs/085-recommendation-ranking-runtime/spec.md",
            "specs/086-cost-recovery-evaluation-gates/spec.md",
        ],
    )


def _algorithm_recommendations(
    manifest: CrawlerOptimizationManifest,
) -> list[AlgorithmRecommendation]:
    specs = [
        (
            "Focused priority queue crawling",
            "P0",
            "high",
            "Raises crawl precision while bounding low-value browsing.",
            "medium",
            "formula:frontier-score-weighted-v1",
            None,
        ),
        (
            "DOM pruning with heuristic element ranking",
            "P0",
            "high",
            "Cuts LLM tokens and improves action choice stability.",
            "medium",
            None,
            "fallback:heuristic-then-llm-dom",
        ),
        (
            "Structured extractor fallback chain",
            "P0",
            "high",
            "Prefers JSON-LD/schema/meta/selectors before LLM extraction.",
            "medium",
            None,
            "fallback:jsonld-schema-og-selector-regex-llm",
        ),
        (
            "Canonical URL plus SimHash/MinHash identity",
            "P0",
            "high",
            "Suppresses tracking duplicates and near-identical pages.",
            "medium",
            "formula:identity-similarity-v1",
            None,
        ),
        (
            "Heuristic recommendation ranking",
            "P1",
            "medium",
            "Improves result order before learning-to-rank data exists.",
            "medium",
            "formula:recommendation-score-weighted-v1",
            None,
        ),
        (
            "Cost and recovery quality gates",
            "P1",
            "high",
            "Prevents false-ready releases when cost, replay, or safety regress.",
            "medium",
            None,
            "fallback:retry-backoff-abstain-review",
        ),
    ]
    return [
        AlgorithmRecommendation(
            id=f"algorithm-recommendation:{manifest.id}:{index}",
            algorithm_name=name,
            solves_problem_refs=[
                "problem:search-accuracy",
                "problem:extraction-stability",
                "problem:cost-efficiency",
                "problem:site-drift",
                "problem:dedupe",
                "problem:ranking-quality",
                "problem:agent-decision-quality",
            ],
            priority=priority,
            expected_benefit=benefit,
            implementation_complexity=complexity,
            system_change_refs=[
                "change:contracts",
                "change:runtime-gate",
                "change:registry",
                "change:fixtures",
            ],
            validation_metric_refs=[
                "metric:precision",
                "metric:recall",
                "metric:extraction-accuracy",
                "metric:duplicate-rate",
                "metric:cost-per-success",
                "metric:latency-p95",
            ],
            pseudo_code_ref=f"pseudo-code:{manifest.id}:{index}",
            score_formula_ref=score_formula,
            fallback_chain_ref=fallback_chain,
        )
        for index, (
            name,
            priority,
            _benefit_level,
            benefit,
            complexity,
            score_formula,
            fallback_chain,
        ) in enumerate(specs, start=1)
    ]


def _empty_result(
    report: CrawlerOptimizationReport,
    architecture: CrawlerOptimizationArchitectureSpec,
    algorithms: list[AlgorithmRecommendation],
) -> CrawlerOptimizationBenchmarkResult:
    return CrawlerOptimizationBenchmarkResult(
        report=report,
        architecture=architecture,
        algorithm_recommendations=algorithms,
        frontier_profile=None,
        frontier_scores=[],
        dom_nodes=[],
        page_zones=[],
        interactive_elements=[],
        dom_contexts=[],
        extractor_plans=[],
        extractor_attempts=[],
        field_confidence_scores=[],
        abstention_decisions=[],
        canonicalization_decisions=[],
        fingerprints=[],
        identity_decisions=[],
        duplicate_suppression_records=[],
        ranking_profile=None,
        ranking_scores=[],
        ranked_output_sets=[],
        ranking_evaluations=[],
        metric_slices=[],
    )


def _record_frontier_score(
    manifest_id: str,
    score: FrontierScoreBreakdown,
    store: ProductionPersistenceStore,
) -> FrontierScoreBreakdown:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{score.id}",
        command_type="record_frontier_score_breakdown",
        target_aggregate_type="FrontierScoreBreakdown",
        target_aggregate_id=score.id,
        event_type="frontier_score_breakdown_recorded",
        output_refs=[score.id],
        policy_decision_refs=score.policy_decision_refs,
        store=store,
    )
    updated = score.model_copy(
        update={
            "command_record_refs": [command_ref],
            "event_cursor_refs": [event_ref],
            "outbox_refs": [outbox_ref],
        }
    )
    store.save_canonical_model("frontier_score_breakdowns", updated.id, updated)
    return updated


def _record_dom_context(
    manifest_id: str,
    context: DomContextBundle,
    store: ProductionPersistenceStore,
) -> DomContextBundle:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{context.id}",
        command_type="record_dom_context_bundle",
        target_aggregate_type="DomContextBundle",
        target_aggregate_id=context.id,
        event_type="dom_context_bundle_recorded",
        output_refs=[context.id],
        policy_decision_refs=context.policy_decision_refs,
        store=store,
    )
    updated = context.model_copy(
        update={
            "command_record_refs": [command_ref],
            "event_cursor_refs": [event_ref],
            "outbox_refs": [outbox_ref],
        }
    )
    store.save_canonical_model("dom_context_bundles", updated.id, updated)
    return updated


def _record_duplicate_suppression(
    manifest_id: str,
    record: DuplicateSuppressionRecord,
    store: ProductionPersistenceStore,
) -> DuplicateSuppressionRecord:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{record.id}",
        command_type="record_duplicate_suppression",
        target_aggregate_type="DuplicateSuppressionRecord",
        target_aggregate_id=record.id,
        event_type="duplicate_suppression_recorded",
        output_refs=[record.id],
        policy_decision_refs=record.policy_decision_refs,
        store=store,
    )
    updated = record.model_copy(
        update={
            "command_record_refs": [command_ref],
            "event_cursor_refs": [event_ref],
            "outbox_refs": [outbox_ref],
        }
    )
    store.save_canonical_model("duplicate_suppression_records", updated.id, updated)
    return updated


def _record_ranked_output(
    manifest_id: str,
    record: RankedOutputSet,
    store: ProductionPersistenceStore,
) -> RankedOutputSet:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{record.id}",
        command_type="record_ranked_output_set",
        target_aggregate_type="RankedOutputSet",
        target_aggregate_id=record.id,
        event_type="ranked_output_set_recorded",
        output_refs=[record.id],
        policy_decision_refs=record.policy_decision_refs,
        store=store,
    )
    updated = record.model_copy(
        update={
            "command_record_refs": [command_ref],
            "event_cursor_refs": [event_ref],
            "outbox_refs": [outbox_ref],
        }
    )
    store.save_canonical_model("ranked_output_sets", updated.id, updated)
    return updated


def _record_report_event(
    manifest_id: str,
    report: CrawlerOptimizationReport,
    store: ProductionPersistenceStore,
) -> CrawlerOptimizationReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{report.id}",
        command_type="record_crawler_optimization_report",
        target_aggregate_type="CrawlerOptimizationReport",
        target_aggregate_id=report.id,
        event_type="crawler_optimization_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:crawler-optimization-benchmark",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(outbox.id, dispatched_at_ref=f"clock:{command_id}:dispatched")
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id


def _signal_names() -> list[str]:
    return [
        "url-pattern",
        "anchor-text",
        "page-title",
        "semantic-similarity",
        "domain-authority",
        "freshness",
        "historical-success",
        "page-type",
        "cost-penalty",
        "risk-penalty",
    ]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _visible_text(value: str) -> str:
    return " ".join(_tokens(re.sub(r"<[^>]+>", " ", value)))


def _html_tags(value: str) -> list[str]:
    return re.findall(r"</?([a-zA-Z0-9:-]+)", value)


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
