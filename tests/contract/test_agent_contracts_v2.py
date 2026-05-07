"""Contract tests for v2 agent contracts (Phase 0 step 0.2).

Phase 0 of the production-authorized-source-crawler design adds the
following framework-neutral contract types under
``veracrawl.contracts.agent``:

* ``Message``, ``ToolCall``, ``ToolSpec``, ``ResponseFormat``,
  ``TokenUsage``, ``TokenBudget`` — building blocks for the
  ``ModelProviderPort`` v2 surface (Phase 4).
* ``LLMExtractionCandidate``, ``LLMFieldCitation``,
  ``LLMFieldConfidence`` — outputs of the LLM-driven extraction
  rewrite (Phase 4). Named with the ``LLM`` prefix to avoid colliding
  with the existing heuristic-driven ``processing.ExtractionCandidate``
  contract that the registry and many runtime modules already
  reference. The semantic intent matches design.md §3.5; the rename
  is documented in STATUS.md as a P0-fix-pack reservation.
* ``RecoveryDecision``, ``RecoveryTrace`` — outputs of the
  ``RecoveryPort`` (Phase 5).

These contracts ship behavior-free in Phase 0 — only the type
surface and pydantic validators land here. Phase 4 / Phase 5 wire
them into adapters and runtimes. Each test asserts one acceptance
criterion: either a constructor accepts a minimal valid payload, or
the validator rejects a deliberately malformed payload.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.agent import (
    LLMExtractionCandidate,
    LLMFieldCitation,
    LLMFieldConfidence,
    Message,
    RecoveryDecision,
    RecoveryTrace,
    ResponseFormat,
    TokenBudget,
    TokenUsage,
    ToolCall,
    ToolSpec,
)
from veracrawl.contracts.enums import (
    CalibrationMethod,
    MessageRole,
    RecoveryDecisionKind,
    RecoveryDecisionSource,
    RecoveryTerminationReason,
    ResponseFormatKind,
)

# Message -----------------------------------------------------------


def test_message_user_minimal_valid() -> None:
    msg = Message(role=MessageRole.USER, content="hello")
    assert msg.role is MessageRole.USER
    assert msg.content == "hello"
    assert msg.tool_calls == []
    assert msg.tool_call_id is None
    assert msg.name is None


def test_message_assistant_with_tool_calls_allows_empty_content() -> None:
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        tool_calls=[ToolCall(id="call_1", name="search", arguments={"q": "x"})],
    )
    assert len(msg.tool_calls) == 1


def test_message_tool_role_requires_tool_call_id() -> None:
    with pytest.raises(ValidationError):
        Message(role=MessageRole.TOOL, content="result", name="search")


def test_message_tool_role_requires_name() -> None:
    with pytest.raises(ValidationError):
        Message(role=MessageRole.TOOL, content="result", tool_call_id="call_1")


def test_message_user_rejects_tool_call_id() -> None:
    with pytest.raises(ValidationError):
        Message(role=MessageRole.USER, content="hi", tool_call_id="call_1")


def test_message_user_rejects_tool_calls() -> None:
    with pytest.raises(ValidationError):
        Message(
            role=MessageRole.USER,
            content="hi",
            tool_calls=[ToolCall(id="call_1", name="x", arguments={})],
        )


def test_message_assistant_without_tool_calls_requires_non_empty_content() -> None:
    with pytest.raises(ValidationError):
        Message(role=MessageRole.ASSISTANT, content="")


# ToolCall ---------------------------------------------------------


def test_tool_call_minimal_valid() -> None:
    call = ToolCall(id="call_1", name="search", arguments={"q": "x"})
    assert call.id == "call_1"
    assert call.name == "search"
    assert call.arguments == {"q": "x"}


def test_tool_call_arguments_default_empty_dict() -> None:
    call = ToolCall(id="call_1", name="ping")
    assert call.arguments == {}


def test_tool_call_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        ToolCall(id="call_1", name="", arguments={})


def test_tool_call_rejects_blank_id() -> None:
    with pytest.raises(ValidationError):
        ToolCall(id="", name="search", arguments={})


# ToolSpec ---------------------------------------------------------


def test_tool_spec_minimal_valid() -> None:
    spec = ToolSpec(
        name="search",
        description="Search the index for a query.",
        parameters_schema={"type": "object", "properties": {"q": {"type": "string"}}},
    )
    assert spec.strict is False
    assert spec.name == "search"


def test_tool_spec_rejects_schema_without_type() -> None:
    with pytest.raises(ValidationError):
        ToolSpec(
            name="search",
            description="Search.",
            parameters_schema={"properties": {"q": {"type": "string"}}},
        )


def test_tool_spec_rejects_blank_description() -> None:
    with pytest.raises(ValidationError):
        ToolSpec(
            name="search",
            description="",
            parameters_schema={"type": "object"},
        )


# ResponseFormat ---------------------------------------------------


def test_response_format_text_minimal() -> None:
    rf = ResponseFormat(kind=ResponseFormatKind.TEXT)
    assert rf.json_schema is None
    assert rf.schema_name is None
    assert rf.strict is False


def test_response_format_json_schema_requires_schema_and_name() -> None:
    rf = ResponseFormat(
        kind=ResponseFormatKind.JSON_SCHEMA,
        schema_name="ProductRecord",
        json_schema={"type": "object", "properties": {"price": {"type": "number"}}},
        strict=True,
    )
    assert rf.strict is True


def test_response_format_json_schema_without_schema_rejected() -> None:
    with pytest.raises(ValidationError):
        ResponseFormat(kind=ResponseFormatKind.JSON_SCHEMA, schema_name="ProductRecord")


def test_response_format_json_schema_without_name_rejected() -> None:
    with pytest.raises(ValidationError):
        ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            json_schema={"type": "object"},
        )


def test_response_format_text_with_schema_rejected() -> None:
    with pytest.raises(ValidationError):
        ResponseFormat(
            kind=ResponseFormatKind.TEXT,
            json_schema={"type": "object"},
        )


# TokenUsage -------------------------------------------------------


def test_token_usage_minimal_valid() -> None:
    usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    assert usage.cached_input_tokens == 0
    assert usage.reasoning_tokens == 0


def test_token_usage_with_cached_and_reasoning() -> None:
    usage = TokenUsage(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cached_input_tokens=80,
        reasoning_tokens=20,
    )
    assert usage.cached_input_tokens == 80


def test_token_usage_rejects_negative_tokens() -> None:
    with pytest.raises(ValidationError):
        TokenUsage(prompt_tokens=-1, completion_tokens=5, total_tokens=4)


def test_token_usage_rejects_total_mismatch() -> None:
    with pytest.raises(ValidationError):
        TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=20)


def test_token_usage_rejects_cached_exceeds_prompt() -> None:
    with pytest.raises(ValidationError):
        TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            cached_input_tokens=11,
        )


def test_token_usage_rejects_reasoning_exceeds_completion() -> None:
    with pytest.raises(ValidationError):
        TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            reasoning_tokens=6,
        )


# TokenBudget ------------------------------------------------------


def test_token_budget_with_total_cap() -> None:
    budget = TokenBudget(id="budget:run:1", run_ref="run:1", max_total_tokens=1000)
    assert budget.max_input_tokens is None
    assert budget.max_cost_usd is None


def test_token_budget_with_cost_cap() -> None:
    budget = TokenBudget(id="budget:run:1", run_ref="run:1", max_cost_usd=5.0)
    assert budget.max_cost_usd == 5.0


def test_token_budget_rejects_no_caps() -> None:
    with pytest.raises(ValidationError):
        TokenBudget(id="budget:run:1", run_ref="run:1")


def test_token_budget_rejects_negative_cap() -> None:
    with pytest.raises(ValidationError):
        TokenBudget(id="budget:run:1", run_ref="run:1", max_total_tokens=-1)


def test_token_budget_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        TokenBudget(id="budget:run:1", run_ref="run:1", max_cost_usd=-0.01)


# LLMExtractionCandidate / FieldCitation / FieldConfidence --------


def _valid_llm_candidate(**overrides: object) -> LLMExtractionCandidate:
    defaults: dict[str, object] = {
        "id": "llm-candidate:1",
        "run_ref": "run:1",
        "source_url": "https://example.test/p/123",
        "schema_ref": "schema:product",
        "model_call_trace_ref": "model-trace:1",
        "field_values": {"price": "9.99", "title": "Widget"},
        "field_citation_refs": {"price": "citation:price", "title": "citation:title"},
        "field_confidence_refs": {
            "price": "confidence:price",
            "title": "confidence:title",
        },
    }
    defaults.update(overrides)
    return LLMExtractionCandidate.model_validate(defaults)


def test_llm_extraction_candidate_minimal_valid() -> None:
    candidate = _valid_llm_candidate()
    assert candidate.field_values["price"] == "9.99"
    assert candidate.abstentions == {}


def test_llm_extraction_candidate_with_abstention() -> None:
    candidate = _valid_llm_candidate(
        field_values={"price": "9.99"},
        field_citation_refs={"price": "citation:price"},
        field_confidence_refs={"price": "confidence:price"},
        abstentions={"title": "no anchor matched the schema"},
    )
    assert candidate.abstentions["title"] == "no anchor matched the schema"


def test_llm_extraction_candidate_rejects_field_without_citation() -> None:
    with pytest.raises(ValidationError):
        _valid_llm_candidate(field_citation_refs={"price": "citation:price"})


def test_llm_extraction_candidate_rejects_field_without_confidence() -> None:
    with pytest.raises(ValidationError):
        _valid_llm_candidate(field_confidence_refs={"price": "confidence:price"})


def test_llm_extraction_candidate_rejects_abstention_overlapping_field_values() -> None:
    with pytest.raises(ValidationError):
        _valid_llm_candidate(
            abstentions={"price": "abstained but value present"},
        )


def test_llm_extraction_candidate_rejects_blank_abstention_reason() -> None:
    with pytest.raises(ValidationError):
        _valid_llm_candidate(
            field_values={"price": "9.99"},
            field_citation_refs={"price": "citation:price"},
            field_confidence_refs={"price": "confidence:price"},
            abstentions={"title": ""},
        )


def test_llm_field_citation_minimal_valid() -> None:
    citation = LLMFieldCitation(
        id="citation:price",
        candidate_ref="llm-candidate:1",
        field_name="price",
        anchor_refs=["anchor:price-span"],
        excerpt="$9.99",
    )
    assert citation.selector is None
    assert citation.screenshot_region_ref is None


def test_llm_field_citation_rejects_empty_anchor_refs() -> None:
    with pytest.raises(ValidationError):
        LLMFieldCitation(
            id="citation:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            anchor_refs=[],
            excerpt="$9.99",
        )


def test_llm_field_citation_rejects_blank_excerpt() -> None:
    with pytest.raises(ValidationError):
        LLMFieldCitation(
            id="citation:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            anchor_refs=["anchor:price-span"],
            excerpt="",
        )


def test_llm_field_confidence_minimal_valid_with_no_calibration() -> None:
    score = LLMFieldConfidence(
        id="confidence:price",
        candidate_ref="llm-candidate:1",
        field_name="price",
        raw_score=0.8,
        calibrated_score=0.8,
        calibration_method=CalibrationMethod.NONE,
    )
    assert score.calibration_version is None


def test_llm_field_confidence_with_platt_calibration() -> None:
    score = LLMFieldConfidence(
        id="confidence:price",
        candidate_ref="llm-candidate:1",
        field_name="price",
        raw_score=0.8,
        calibrated_score=0.65,
        calibration_method=CalibrationMethod.PLATT,
        calibration_version="platt:2026-01-15",
    )
    assert score.calibration_version == "platt:2026-01-15"


def test_llm_field_confidence_rejects_raw_out_of_range() -> None:
    with pytest.raises(ValidationError):
        LLMFieldConfidence(
            id="confidence:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            raw_score=1.5,
            calibrated_score=0.5,
            calibration_method=CalibrationMethod.NONE,
        )


def test_llm_field_confidence_rejects_calibrated_negative() -> None:
    with pytest.raises(ValidationError):
        LLMFieldConfidence(
            id="confidence:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            raw_score=0.5,
            calibrated_score=-0.1,
            calibration_method=CalibrationMethod.NONE,
        )


def test_llm_field_confidence_calibrated_method_requires_version() -> None:
    with pytest.raises(ValidationError):
        LLMFieldConfidence(
            id="confidence:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            raw_score=0.5,
            calibrated_score=0.4,
            calibration_method=CalibrationMethod.ISOTONIC,
        )


def test_llm_field_confidence_none_method_with_score_divergence_rejected() -> None:
    """If calibration_method is NONE the calibrated score must equal
    the raw score; otherwise an unrecorded transformation snuck in."""
    with pytest.raises(ValidationError):
        LLMFieldConfidence(
            id="confidence:price",
            candidate_ref="llm-candidate:1",
            field_name="price",
            raw_score=0.8,
            calibrated_score=0.5,
            calibration_method=CalibrationMethod.NONE,
        )


# RecoveryDecision -------------------------------------------------


def test_recovery_decision_different_url_minimal_valid() -> None:
    decision = RecoveryDecision(
        id="recovery-decision:1",
        kind=RecoveryDecisionKind.DIFFERENT_URL,
        reason="primary URL returned 404; sitemap suggests alternate",
        failure_signature="404:example.test",
        source=RecoveryDecisionSource.HEURISTIC,
        alternative_url="https://example.test/p/123-alt",
    )
    assert decision.escalation_target is None
    assert decision.cost_usd == 0.0


def test_recovery_decision_escalate_adapter_minimal_valid() -> None:
    decision = RecoveryDecision(
        id="recovery-decision:1",
        kind=RecoveryDecisionKind.ESCALATE_ADAPTER,
        reason="HTTP adapter returned access_control_blocked; escalate to authorized",
        failure_signature="access_control_blocked:cloudflare:example.test",
        source=RecoveryDecisionSource.LLM_RECOVERY,
        escalation_target="authorized_session",
        cost_usd=0.0042,
    )
    assert decision.cost_usd == 0.0042


def test_recovery_decision_different_url_requires_alternative() -> None:
    with pytest.raises(ValidationError):
        RecoveryDecision(
            id="recovery-decision:1",
            kind=RecoveryDecisionKind.DIFFERENT_URL,
            reason="primary URL returned 404",
            failure_signature="404:example.test",
            source=RecoveryDecisionSource.HEURISTIC,
        )


def test_recovery_decision_escalate_adapter_requires_target() -> None:
    with pytest.raises(ValidationError):
        RecoveryDecision(
            id="recovery-decision:1",
            kind=RecoveryDecisionKind.ESCALATE_ADAPTER,
            reason="cloudflare wall",
            failure_signature="access_control_blocked:cloudflare",
            source=RecoveryDecisionSource.LLM_RECOVERY,
        )


def test_recovery_decision_abandon_minimal_valid() -> None:
    decision = RecoveryDecision(
        id="recovery-decision:1",
        kind=RecoveryDecisionKind.ABANDON,
        reason="repeated_signature_hard_stop",
        failure_signature="404:example.test",
        source=RecoveryDecisionSource.CHEAP_CLASSIFIER,
    )
    assert decision.alternative_url is None


def test_recovery_decision_abandon_rejects_alternative_url() -> None:
    """An ABANDON decision must not also propose a URL — that contradicts
    the kind. The test guards against an LLM emitting both fields by
    accident."""
    with pytest.raises(ValidationError):
        RecoveryDecision(
            id="recovery-decision:1",
            kind=RecoveryDecisionKind.ABANDON,
            reason="hard stop",
            failure_signature="404",
            source=RecoveryDecisionSource.HEURISTIC,
            alternative_url="https://example.test/x",
        )


def test_recovery_decision_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        RecoveryDecision(
            id="recovery-decision:1",
            kind=RecoveryDecisionKind.ABANDON,
            reason="x",
            failure_signature="x",
            source=RecoveryDecisionSource.HEURISTIC,
            cost_usd=-0.01,
        )


def test_recovery_decision_rejects_blank_signature() -> None:
    with pytest.raises(ValidationError):
        RecoveryDecision(
            id="recovery-decision:1",
            kind=RecoveryDecisionKind.ABANDON,
            reason="x",
            failure_signature="",
            source=RecoveryDecisionSource.HEURISTIC,
        )


# RecoveryTrace ----------------------------------------------------


def test_recovery_trace_completed_minimal() -> None:
    trace = RecoveryTrace(
        id="recovery-trace:1",
        agent_run_request_ref="agent-run-request:1",
        terminated_by=RecoveryTerminationReason.COMPLETED,
    )
    assert trace.decision_refs == []
    assert trace.total_cost_usd == 0.0


def test_recovery_trace_with_decisions() -> None:
    trace = RecoveryTrace(
        id="recovery-trace:1",
        agent_run_request_ref="agent-run-request:1",
        decision_refs=["recovery-decision:1", "recovery-decision:2"],
        total_cost_usd=0.0042,
        terminated_by=RecoveryTerminationReason.COMPLETED,
    )
    assert len(trace.decision_refs) == 2


def test_recovery_trace_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        RecoveryTrace(
            id="recovery-trace:1",
            agent_run_request_ref="agent-run-request:1",
            terminated_by=RecoveryTerminationReason.COMPLETED,
            total_cost_usd=-0.01,
        )


def test_recovery_trace_repeated_signature_requires_decisions() -> None:
    """A trace terminated for repeated-signature hard-stop must record
    at least the two decisions whose signature collided; an empty trace
    contradicts the termination reason."""
    with pytest.raises(ValidationError):
        RecoveryTrace(
            id="recovery-trace:1",
            agent_run_request_ref="agent-run-request:1",
            terminated_by=RecoveryTerminationReason.REPEATED_SIGNATURE_HARD_STOP,
            decision_refs=[],
        )


def test_recovery_trace_max_iterations_requires_decisions() -> None:
    with pytest.raises(ValidationError):
        RecoveryTrace(
            id="recovery-trace:1",
            agent_run_request_ref="agent-run-request:1",
            terminated_by=RecoveryTerminationReason.MAX_ITERATIONS_EXCEEDED,
            decision_refs=[],
        )
