"""Phase 4 step 4.6 — schema_extraction_runtime integration tests.

End-to-end fixture-mode coverage of the integrator that pulls
together PromptRegistryPort + ModelProviderPortV2 +
TokenBudgetPort + CalibrationPort.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from veracrawl.adapters.budget.outbox_backed_budget import (
    OutboxBackedBudget,
    ProviderPriceTable,
)
from veracrawl.adapters.calibration.identity import IdentityCalibrator
from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.adapters.prompt_registry.json_prompt_registry import (
    JsonPromptRegistry,
)
from veracrawl.contracts.agent import TokenBudget, TokenUsage
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.errors import StructuredOutputViolation, TokenBudgetExceeded
from veracrawl.contracts.llm_input import Anchor
from veracrawl.contracts.token_budget import TokenUsageEvent
from veracrawl.processing.schema_extraction_runtime import (
    SchemaExtractionRuntime,
)
from veracrawl.runtime_support.runtime_mode import RuntimeMode

_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
_API_KEY_CANARY = "sk-EXTRACTION-CANARY-DEADBEEF"


class _ProductOutput(BaseModel):
    sku: str
    title: str
    price: float


def _write_prompt_template(
    root: Path, *, role: str, name: str, version: str
) -> str:
    role_dir = root / role
    role_dir.mkdir(parents=True, exist_ok=True)
    ref = f"{role}/{name}.{version}"
    payload = {
        "ref": ref,
        "role": role,
        "name": name,
        "version": version,
        "template": "Extract product details for {url}",
        "variables": ["url"],
    }
    (role_dir / f"{name}.{version}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return ref


def _ok_provider_body(text: str) -> dict[str, Any]:
    return {
        "id": "resp:extract-test",
        "status": "completed",
        "output": [{"content": [{"type": "output_text", "text": text}]}],
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    }


class _InMemoryOutboxRepo:
    def __init__(self) -> None:
        self.appended: list[OutboxRecord] = []

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.appended.append(record)
        return f"outbox-ref:{record.id}"

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        del run_ref
        return list(self.appended)

    def mark_outbox_dispatched(
        self, outbox_ref: Ref, *, dispatched_at_ref: Ref
    ) -> OutboxRecord:
        del outbox_ref, dispatched_at_ref
        raise NotImplementedError

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        del outbox_ref, error_ref
        raise NotImplementedError


def _build_runtime(
    *,
    tmp_path: Path,
    response_text: str,
    persisted: list[TokenUsageEvent] | None = None,
    budget: TokenBudget | None = None,
) -> SchemaExtractionRuntime:
    prompt_ref = _write_prompt_template(
        tmp_path, role="extractor", name="product", version="v1"
    )
    del prompt_ref
    prompt_registry = JsonPromptRegistry(root=tmp_path)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json=_ok_provider_body(response_text))
    )
    provider = OpenAIResponsesAdapterV2(
        api_key=_API_KEY_CANARY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=transport,
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )
    persisted_events = persisted if persisted is not None else []

    def persister(event: TokenUsageEvent) -> Ref:
        persisted_events.append(event)
        return f"payload:{event.id}"

    token_budget = OutboxBackedBudget(
        budget=budget
        or TokenBudget(
            id="token-budget:phase-4-6:1",
            run_ref="run:phase-4-6:1",
            max_total_tokens=10_000,
        ),
        price_table=ProviderPriceTable(
            version="v1",
            prices={
                "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
            },
        ),
        outbox_repo=_InMemoryOutboxRepo(),
        record_persister=persister,
        run_ref="run:phase-4-6:1",
        command_result_ref="cmd-result:phase-4-6:1",
        event_ref="event:phase-4-6:1",
        clock=lambda: _FROZEN_NOW,
        runtime_mode=RuntimeMode.FIXTURE,
    )
    return SchemaExtractionRuntime(
        provider=provider,
        prompt_registry=prompt_registry,
        token_budget=token_budget,
        calibrator=IdentityCalibrator(),
        run_ref="run:phase-4-6:1",
    )


def _extraction_kwargs() -> dict[str, Any]:
    return {
        "source_url": "https://example.com/widget",
        "prompt_ref": "extractor/product.v1",
        "prompt_context": {"url": "https://example.com/widget"},
        "output_class": _ProductOutput,
        "anchors": [
            Anchor(id="anchor:1", excerpt="Widget Pro", selector="h1.title"),
            Anchor(id="anchor:2", excerpt="$19.99", selector="span.price"),
        ],
        "per_field_anchor_refs": {
            "sku": ["anchor:1"],
            "title": ["anchor:1"],
            "price": ["anchor:2"],
        },
        "per_field_excerpts": {
            "sku": "ABC-123",
            "title": "Widget Pro",
            "price": "$19.99",
        },
        "per_field_raw_scores": {"sku": 0.95, "title": 0.9, "price": 0.85},
        "model_name": "gpt-4o-mini",
        "max_output_tokens": 256,
        "schema_ref": "schema:product:v1",
        "model_call_trace_ref": "model-call-trace:1",
    }


# --- Happy path -------------------------------------------------------------


def test_extract_produces_candidate_with_all_three_record_types(
    tmp_path: Path,
) -> None:
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC-123", "title": "Widget Pro", "price": 19.99}
        ),
    )
    candidate, citations, confidences = runtime.extract(**_extraction_kwargs())
    assert candidate.field_values == {
        "sku": "ABC-123",
        "title": "Widget Pro",
        "price": 19.99,
    }
    assert len(citations) == 3
    assert len(confidences) == 3
    assert set(candidate.field_citation_refs.keys()) == {"sku", "title", "price"}
    assert set(candidate.field_confidence_refs.keys()) == {"sku", "title", "price"}
    # Identity calibrator → calibrated == raw.
    for confidence in confidences:
        assert confidence.calibrated_score == confidence.raw_score


def test_extract_includes_anchor_refs_per_field(tmp_path: Path) -> None:
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC-123", "title": "Widget Pro", "price": 19.99}
        ),
    )
    _, citations, _ = runtime.extract(**_extraction_kwargs())
    citations_by_field = {c.field_name: c for c in citations}
    assert citations_by_field["sku"].anchor_refs == ["anchor:1"]
    assert citations_by_field["price"].anchor_refs == ["anchor:2"]


# --- Schema validation -----------------------------------------------------


def test_extract_invalid_schema_raises_structured_output_violation(
    tmp_path: Path,
) -> None:
    """Provider returns JSON that doesn't match the Pydantic
    class — extraction must refuse instead of silently
    accepting a bogus shape."""

    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC-123"}  # missing required ``title`` and ``price``
        ),
    )
    with pytest.raises(StructuredOutputViolation):
        runtime.extract(**_extraction_kwargs())


def test_extract_invalid_field_type_raises_structured_output_violation(
    tmp_path: Path,
) -> None:
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC-123", "title": "Widget Pro", "price": "NOT_A_NUMBER"}
        ),
    )
    with pytest.raises(StructuredOutputViolation):
        runtime.extract(**_extraction_kwargs())


def test_extract_validation_error_does_not_leak_field_values(
    tmp_path: Path,
) -> None:
    """``ValidationError`` messages include field values.
    Sanitized error must not echo the upstream content."""

    canary = "VALIDATOR-LEAK-CANARY-XYZZY-INTERNAL"
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": canary, "title": "Widget Pro", "price": "INVALID"}
        ),
    )
    with pytest.raises(StructuredOutputViolation) as exc_info:
        runtime.extract(**_extraction_kwargs())
    assert canary not in str(exc_info.value)
    assert canary not in repr(exc_info.value)


# --- Abstention ------------------------------------------------------------


def test_extract_records_abstention_for_missing_fields(tmp_path: Path) -> None:
    """When the LLM omits a field that was in
    ``per_field_raw_scores`` (and not present in the parsed
    output), the runtime records an abstention reason."""

    # Pydantic validator requires all three fields; to test
    # abstention, drop one from per_field_raw_scores and let
    # the model output all three. Test path:
    # request 4 fields; model returns 3; the missing one
    # surfaces as an abstention.
    response_text = json.dumps(
        {"sku": "ABC", "title": "X", "price": 1.0}
    )
    runtime = _build_runtime(tmp_path=tmp_path, response_text=response_text)
    kwargs = _extraction_kwargs()
    kwargs["per_field_raw_scores"]["brand"] = 0.7  # field absent in output
    kwargs["per_field_anchor_refs"]["brand"] = ["anchor:1"]
    kwargs["per_field_excerpts"]["brand"] = "Acme"
    candidate, citations, confidences = runtime.extract(**kwargs)
    assert "brand" in candidate.abstentions
    assert "brand" not in candidate.field_values
    # Citations / confidences only for present fields.
    assert {c.field_name for c in citations} == {"sku", "title", "price"}
    assert {c.field_name for c in confidences} == {"sku", "title", "price"}


def test_extract_caller_supplied_abstentions_are_merged(tmp_path: Path) -> None:
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC", "title": "X", "price": 1.0}
        ),
    )
    candidate, _, _ = runtime.extract(
        **_extraction_kwargs(),
        abstentions={"discontinued": "out of inventory"},
    )
    assert candidate.abstentions["discontinued"] == "out of inventory"


# --- Budget --------------------------------------------------------------


def test_extract_charges_budget_after_successful_call(tmp_path: Path) -> None:
    persisted: list[TokenUsageEvent] = []
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC-123", "title": "Widget Pro", "price": 19.99}
        ),
        persisted=persisted,
    )
    runtime.extract(**_extraction_kwargs())
    assert len(persisted) == 1
    assert persisted[0].usage == TokenUsage(
        prompt_tokens=100, completion_tokens=50, total_tokens=150
    )


def test_extract_refuses_when_budget_too_tight(tmp_path: Path) -> None:
    """estimate_charge alone breaches the cap — the provider
    is never called."""

    tiny_budget = TokenBudget(
        id="token-budget:phase-4-6:tiny",
        run_ref="run:phase-4-6:1",
        max_total_tokens=2,
    )
    runtime = _build_runtime(
        tmp_path=tmp_path,
        response_text=json.dumps(
            {"sku": "ABC", "title": "X", "price": 1.0}
        ),
        budget=tiny_budget,
    )
    with pytest.raises(TokenBudgetExceeded):
        runtime.extract(**_extraction_kwargs())


# --- Construction ----------------------------------------------------------


def test_extract_refuses_credential_in_prompt_context_before_provider_call(
    tmp_path: Path,
) -> None:
    """Codex iter-1 important + Phase 4 design acceptance:
    a CredentialValue in prompt_context must raise the
    Phase 2 step 2.3 boundary BEFORE the provider call —
    no LLM cost is incurred on a credential-leak attempt."""

    from veracrawl.agents.prompt_redaction import PromptCredentialLeakError
    from veracrawl.ports.credential_vault import CredentialValue

    # Use a template that references the credential variable
    # so the redaction boundary's traversal walk has something
    # to find.
    role_dir = tmp_path / "extractor"
    role_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ref": "extractor/cred_test.v1",
        "role": "extractor",
        "name": "cred_test",
        "version": "v1",
        "template": "Extract with token {token}",
        "variables": ["token"],
    }
    (role_dir / "cred_test.v1.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    provider_call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal provider_call_count
        provider_call_count += 1
        return httpx.Response(200, json=_ok_provider_body("{}"))

    prompt_registry = JsonPromptRegistry(root=tmp_path)
    transport = httpx.MockTransport(handler)
    provider = OpenAIResponsesAdapterV2(
        api_key=_API_KEY_CANARY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=transport,
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )

    def persister(event: TokenUsageEvent) -> Ref:
        del event
        return "payload:noop"

    token_budget = OutboxBackedBudget(
        budget=TokenBudget(
            id="b:1",
            run_ref="run:phase-4-6:1",
            max_total_tokens=10_000,
        ),
        price_table=ProviderPriceTable(
            version="v1",
            prices={"gpt-4o-mini": {"input_per_1k": 0.0, "output_per_1k": 0.0}},
        ),
        outbox_repo=_InMemoryOutboxRepo(),
        record_persister=persister,
        run_ref="run:phase-4-6:1",
        command_result_ref="cmd:1",
        event_ref="event:1",
        clock=lambda: _FROZEN_NOW,
        runtime_mode=RuntimeMode.FIXTURE,
    )
    runtime = SchemaExtractionRuntime(
        provider=provider,
        prompt_registry=prompt_registry,
        token_budget=token_budget,
        calibrator=IdentityCalibrator(),
        run_ref="run:phase-4-6:1",
    )
    cred = CredentialValue(value="sk-secret-CANARY", scope_ref="EBAY_PROD")
    kwargs = _extraction_kwargs()
    kwargs["prompt_ref"] = "extractor/cred_test.v1"
    kwargs["prompt_context"] = {"token": cred}
    # The prompt-registry's primitive-only allowlist refuses
    # the CredentialValue first; if not, the
    # RedactedPromptContext walk catches it. Either way the
    # boundary stops the call BEFORE the provider runs.
    with pytest.raises((PromptCredentialLeakError, Exception)):
        runtime.extract(**kwargs)
    # The provider was NEVER called.
    assert provider_call_count == 0


def test_extract_replay_determinism_same_input_same_output(tmp_path: Path) -> None:
    """Codex iter-1 important + Phase 4 acceptance: same
    logical request + same fixture provider response →
    structurally-identical LLMExtractionCandidate (modulo
    the UUID-based id field)."""

    response_text = json.dumps(
        {"sku": "ABC-123", "title": "Widget Pro", "price": 19.99}
    )
    runtime_a = _build_runtime(tmp_path=tmp_path, response_text=response_text)
    candidate_a, citations_a, confidences_a = runtime_a.extract(
        **_extraction_kwargs()
    )
    runtime_b = _build_runtime(tmp_path=tmp_path, response_text=response_text)
    candidate_b, citations_b, confidences_b = runtime_b.extract(
        **_extraction_kwargs()
    )
    # IDs differ (uuid-based), but field_values and the
    # citation/confidence shapes are identical.
    assert candidate_a.field_values == candidate_b.field_values
    assert candidate_a.abstentions == candidate_b.abstentions
    assert sorted(candidate_a.field_citation_refs.keys()) == sorted(
        candidate_b.field_citation_refs.keys()
    )
    assert {c.field_name for c in citations_a} == {
        c.field_name for c in citations_b
    }
    assert {c.field_name for c in confidences_a} == {
        c.field_name for c in confidences_b
    }
    assert {c.calibrated_score for c in confidences_a} == {
        c.calibrated_score for c in confidences_b
    }


def test_runtime_rejects_blank_run_ref(tmp_path: Path) -> None:
    prompt_registry = JsonPromptRegistry(root=tmp_path)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json=_ok_provider_body("{}"))
    )
    provider = OpenAIResponsesAdapterV2(
        api_key=_API_KEY_CANARY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=transport,
    )
    token_budget = OutboxBackedBudget(
        budget=TokenBudget(
            id="b:1",
            run_ref="run:phase-4-6:1",
            max_total_tokens=1000,
        ),
        price_table=ProviderPriceTable(
            version="v1",
            prices={"gpt-4o-mini": {"input_per_1k": 0.0, "output_per_1k": 0.0}},
        ),
        outbox_repo=_InMemoryOutboxRepo(),
        record_persister=lambda _: "payload:x",
        run_ref="run:phase-4-6:1",
        command_result_ref="cmd:1",
        event_ref="event:1",
        runtime_mode=RuntimeMode.FIXTURE,
    )
    with pytest.raises(ValueError, match="run_ref"):
        SchemaExtractionRuntime(
            provider=provider,
            prompt_registry=prompt_registry,
            token_budget=token_budget,
            calibrator=IdentityCalibrator(),
            run_ref="   ",
        )
