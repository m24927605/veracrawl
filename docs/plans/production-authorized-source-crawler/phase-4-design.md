# Phase 4 design supplement — LLM provider port v2 + extraction

## Status

| Field | Value |
|---|---|
| Phase | 4 (of 0..6) |
| Sub-steps | 7 (4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7) |
| Plan-review iter | drafted (no formal codex plan-review yet — supplement is JIT, written under the front-load-design workflow) |
| Implementation status | NOT STARTED |
| Authoritative parent spec | `design.md` §4 Phase 4 |
| Depends on | Phase 0 contracts (`TokenUsage`, `TokenBudget`, `LLMExtractionCandidate`, `LLMFieldCitation`, `LLMFieldConfidence`, `ResponseFormat`); Phase 1 (`NetworkAttemptEvidence`) for extraction inputs; Phase 2 step 2.3 (`RedactedPromptContext`) for prompt-leak boundary |

## Why

`design.md` §4 Phase 4 is ~65 lines of deliverables. The Phase 0 →
Phase 2 implementation experience showed that 600-1500 line design
supplements per phase reduce iter-1 codex rejection rate from ~100%
to ~50% by surfacing security / threat-model / contract-integration
concerns at design time instead of at code-review time.

This supplement is also the **scope-honesty** document for Phase 4:
several `design.md` acceptance items (calibration metrics on a Tier
A gold corpus, nightly Brier / ECE thresholds, ≥95% gold coverage,
provider-swap tests against real OpenAI / Anthropic) **fundamentally
require operational infrastructure** that this attempt cannot
provision (real API keys, multi-day calibration runs, manual gold
labelling). Phase 4 sub-step deliverables in this attempt are
therefore **building-block-only**: ports, fixture-mode adapters,
production gates, and the runtime call surface. Operational
acceptance items are recorded as Phase 6 reservations.

## Scope — In (this attempt)

- `ModelProviderPort` v2 (4.1) — Pydantic-validated request /
  response shape, provider-blind; refuses prompts containing
  credentials at the boundary; FIXTURE-only test impl;
  PRODUCTION mode raises `ProductionRuntimeNotImplemented`.
- `OpenAIResponsesAdapter` v2 (4.2) — wire shape against OpenAI
  Responses API (HTTP only; no SDK dependency); fixture-mode
  via `httpx.MockTransport`; production mode gated.
- `AnthropicMessagesAdapter` (4.3) — analogous to v2 OpenAI;
  proves provider-blind contract.
- `PromptRegistryPort` + `YamlPromptRegistry` (4.4) —
  `prompts/<role>/<name>.<vN>.yml`; immutable version refs;
  refuses templates whose rendered output contains credentials
  (consumes Phase 2 step 2.3 `RedactedPromptContext`).
- `TokenBudgetPort` + `OutboxBackedBudget` (4.5) — per-run
  budget decremented by `TokenUsage` events the adapter emits;
  exceeding raises `TokenBudgetExceeded`; durable via outbox.
- `schema_runtime` LLM-driven extraction (4.6) — replaces V1
  heuristic `processing.ExtractionCandidate`; reclaims the
  bare `ExtractionCandidate` / `FieldCitation` / `FieldConfidence`
  names (Phase 0 step 0.2 reservation pull-forward).
- Calibration scaffolding (4.7) — `CalibrationPort` interface +
  `IdentityCalibrator` (no-op pass-through) + `PlattCalibrator`
  shell that takes a fitted-model artifact ref. Full corpus
  fitting + nightly metrics deferred to Phase 6.

## Scope — Out (deferred)

- **Real LLM API calls + nightly calibration runs**: Phase 6
  step 6.1 (production runtime backends). Requires real API
  keys, multi-day runs, OTLP collector — not buildable in a
  fresh code attempt.
- **Manual Tier A gold corpus** (~200 entries across V1 patterns):
  Phase 6 step 6.5 (corpus authoring + adjudication policy).
  Phase 4 ships the calibration **scaffolding** (port + identity
  default + Platt shell) so Phase 6 can drop in a fitted model
  without contract churn.
- **Tier B weak labels (official-API mirrors with adjudication)**:
  Phase 6 step 6.5.
- **Bedrock / Gemini adapters**: out of scope per `design.md`
  §5 decision log (P1 follow-up).
- **Provider-swap acceptance test against real APIs**: Phase 6
  step 6.5; Phase 4 includes a fixture-mode swap test that
  asserts identical contract shape across `OpenAIResponsesAdapter`
  and `AnthropicMessagesAdapter`.
- **Calibration metrics regression** (nightly Brier ≤ 0.15, ECE
  ≤ 0.10, abstention precision-recall AUC ≥ 0.85): Phase 6
  step 6.5 + production runtime.
- **Field oracle ≥95% gold coverage**: Phase 6 step 6.5.

## Rollback

Each sub-step lands as a single atomic commit (or 1 + post-iter-5
fix-up). Rollback strategy:

- **4.1, 4.2, 4.3** are pure module additions. Revert the commit
  to roll back. The existing `OpenAIResponsesModelProviderRuntimeAdapter`
  ships at `src/veracrawl/adapters/model_providers/openai_responses.py`
  and stays operational throughout — Phase 4 introduces v2 alongside;
  the v1 surface is deprecated (DeprecationWarning) for one release.
- **4.4** writes prompt YAML files at `prompts/<role>/<name>.<vN>.yml`.
  Rollback: revert + delete the prompt files (no schema migration).
- **4.5** uses the existing outbox machinery from Phase 2 step
  2.4b (`OutboxRepositoryPort`) — no new persistence shape, just
  a new `dispatch_topic = "token-usage"`.
- **4.6** retires `processing.ExtractionCandidate` via a deprecation
  layer for one release. Phase 0 step 0.2 reservation called
  this out: Phase 4 step 4.6 reclaims the bare name across
  `contracts/agent.py` (already aliased) + the foundation
  registry. Rollback: keep the alias, do not delete the V1
  module yet.
- **4.7** is pure scaffolding (no operational behavior change).
  Revert the commit.

## Open Questions

1. **`ModelProviderPort` v2 input shape — anchors as primitives vs
   contract refs?** The provider should not import
   `NetworkAttemptEvidence` directly (couples LLM layer to
   network layer). Resolution: input takes `anchors: list[Anchor]`
   where `Anchor` is a pure-data Pydantic model living in
   `contracts/llm_input.py` (new). The `schema_runtime` step 4.6
   builds `Anchor` from `NetworkAttemptEvidence` at the call site.

2. **HTTP client choice for OpenAI / Anthropic adapters**: SDK
   vs raw `httpx`. The existing v1 adapter uses raw httpx (no
   SDK dep). Continuing with raw httpx keeps the dependency
   surface tight and lets us share the cooperative HTTP
   transport stack. Provider SDKs are deferred unless a future
   provider's auth shape demands it.

3. **Prompt template engine**: Python `string.Formatter`
   (already used by `RedactedPromptContext`) vs Jinja2 vs
   strict-allowlist DSL. Resolution: `string.Formatter` with
   the credential-aware boundary from Phase 2 step 2.3 — adding
   Jinja2 reopens the prompt-injection / SSTI surface that
   Phase 2 step 2.3 explicitly closed via the structural walk +
   credential-aware formatter. Templates that need iteration
   pre-render the iteration in Python and pass strings only.

4. **Token cost table source**: model prices change. Resolution:
   ship a `prompts/_meta/provider_prices.<vN>.yml` snapshot pinned
   per release; a `ProviderPriceTable` Pydantic model loads it.
   Step 4.5 acceptance includes a regression test that the
   pinned table doesn't accidentally drift on adapter changes.

5. **Calibration corpus storage**: gold corpus must be auditable
   (which entries calibrated which model version?). Resolution:
   Phase 4 ships the `CalibrationPort` with a `fit_artifact_ref`
   field. Phase 6 step 6.5 ships the actual corpus + the artifact
   loader. The port shape lets Phase 5 (recovery) consume calibrated
   confidence without waiting for the corpus.

## Test Strategy

Per sub-step. All unit / contract tests are deterministic
(`httpx.MockTransport` for adapters; in-memory outbox repo for
budget; in-memory file system mocks for prompt registry where
relevant). No `@pytest.mark.live` tests in Phase 4 — live LLM
calls land at Phase 6 step 6.5 alongside the gold corpus.

Property tests:

- Token budget: `OutboxBackedBudget.charge(usage)` is monotone
  decreasing; the sum of charged usages plus the remaining
  budget always equals the initial cap (within float tolerance
  for cost cap).
- Provider-swap (fixture mode): same `ProviderRequest` against
  `OpenAIResponsesAdapter._fixture_handler` and
  `AnthropicMessagesAdapter._fixture_handler` produces the same
  `ProviderResponse.text` shape (both adapters validate against
  the same Pydantic model).
- Prompt registry: rendering a template that references a
  `CredentialValue` raises `PromptCredentialLeakError` regardless
  of the field-access path (covered by Phase 2 step 2.3 already;
  step 4.4 adds a registry-level integration test).

Boundary tests:

- `mypy --strict` clean for all new modules.
- Charter regression test stays green (no stealth-script patterns).
- New ports declared `@runtime_checkable` `Protocol` + listed in
  the foundation registry.
- `RuntimeMode.PRODUCTION` raises `ProductionRuntimeNotImplemented`
  for: (a) `OpenAIResponsesAdapter._production_call`, (b)
  `AnthropicMessagesAdapter._production_call`, (c)
  `OutboxBackedBudget._production_persist` (until Phase 6 wires
  the real outbox repo).

## Acceptance Criteria — Phase-level (this attempt)

The following must pass when all 7 sub-steps complete:

- All sub-step acceptance test lists pass (mechanically: `uv run pytest`).
- `mypy --strict` passes for all new modules.
- Charter regression test stays green.
- Provider-swap test (fixture mode) passes — same `ProviderRequest`
  produces structurally-identical `ProviderResponse`.
- Token-budget property test passes — exhausting the budget raises
  `TokenBudgetExceeded` exactly once and the outbox sum matches the
  cap.
- Structured-output test passes — a deliberately malformed mock
  response raises `StructuredOutputViolation`.
- `processing.ExtractionCandidate` deprecation surfaces a
  `DeprecationWarning` on import; `contracts.agent.ExtractionCandidate`
  is the canonical name.
- Phase 5 step 5.1 can begin without Phase 4 reservations blocking it.

**Operational acceptance items deferred to Phase 6** (see "Scope — Out"):

- Calibration metrics on the gold corpus.
- Field-oracle ≥95% gold coverage.
- Live provider-swap test against real OpenAI / Anthropic APIs.
- Nightly cost regression (per-extraction p95 ≤ $0.01).

---

## Background

`design.md` §4 Phase 4 (~65 lines) defines the LLM extraction
capability. Phase 0 already shipped the data contracts that Phase
4 produces (`TokenUsage`, `TokenBudget`, `LLMExtractionCandidate`,
`LLMFieldCitation`, `LLMFieldConfidence`, `ResponseFormat`,
`AgentToolSpec`); Phase 1 supplied the inputs that the runtime
extraction step consumes (`NetworkAttemptEvidence` with anchors +
screenshot ref); Phase 2 step 2.3 supplied the prompt-leak
boundary (`RedactedPromptContext` + `PromptCredentialLeakError`).
Phase 4 wires the LLM-call runtime + provider adapters + budget
enforcement on top.

The existing v1 `OpenAIResponsesModelProviderRuntimeAdapter` ships
under `src/veracrawl/adapters/model_providers/openai_responses.py`
(320 lines) and uses raw httpx with retry / Retry-After / 429
backoff. Phase 4 introduces a v2 surface that:

- Is **provider-blind** at the call site (orchestrator picks
  provider via config; same code path).
- Validates structured output via Pydantic (`ResponseFormat.JSON_SCHEMA`).
- Refuses prompts whose rendered context contains credentials.
- Records token usage durably via the outbox (Phase 2 step 2.4b
  `OutboxRepositoryPort`).
- Calls the calibration layer to translate raw LLM confidence
  into a calibrated `FieldConfidence`.

The v1 adapter stays operational throughout this attempt; Phase 4
adds v2 alongside and emits a `DeprecationWarning` from the v1
constructor. v1 retires in a separate release after callers
migrate (out of scope for this phase).

## Capability cliff

A single `extract(url, schema)` call:

1. Resolves the `PromptTemplateRef` from the registry (4.4).
2. Renders the template against a `RedactedPromptContext` —
   refuses if any context value contains a `CredentialValue`
   (Phase 2 step 2.3 boundary).
3. Builds a `ProviderRequest` (`messages`, `tools`, `response_format`,
   `max_output_tokens`, etc.).
4. Charges the rendered request against the run's `TokenBudget`
   estimate via `OutboxBackedBudget.estimate_charge` (4.5);
   refuses if the estimate exceeds the cap.
5. Calls `ModelProviderPort.complete(request)` (4.1) — the
   provider-blind boundary.
6. Validates the response against the schema (4.1 + 4.6); raises
   `StructuredOutputViolation` on mismatch.
7. Translates the LLM's raw self-reported confidence through
   `CalibrationPort.calibrate` (4.7) into a calibrated
   `FieldConfidence`.
8. Persists the `LLMExtractionCandidate` + `FieldCitation` +
   `FieldConfidence` records.
9. Charges the actual `TokenUsage` against the budget (4.5);
   raises `TokenBudgetExceeded` if the cap is now breached.

Steps 1-9 are deterministic given the input + provider response.
Replay determinism: the recorded `(request, response)` pair plus
the calibration artifact reproduces every output by construction.

## Codebase ground-truth (verified at draft time)

| Symbol | Actual location | Notes |
|---|---|---|
| `Ref` | `veracrawl.contracts.common` | OK |
| `TokenUsage`, `TokenBudget`, `ResponseFormat` | `veracrawl.contracts.agent` (Phase 0) | OK |
| `LLMExtractionCandidate`, `LLMFieldCitation`, `LLMFieldConfidence` | `veracrawl.contracts.agent` (Phase 0) | aliased to bare `ExtractionCandidate` etc. via module-level binding (line 931); step 4.6 retires V1 + makes the bare names canonical |
| `TokenBudgetExceeded`, `StructuredOutputViolation` | `veracrawl.contracts.errors` (Phase 0.4) | OK |
| `RedactedPromptContext`, `PromptCredentialLeakError` | `veracrawl.runtime_support.prompt_redaction` (Phase 2 step 2.3) | OK |
| `OutboxRepositoryPort`, `OutboxRecord` | `veracrawl.contracts.durable` (Phase 2 step 2.4b) | dispatch_topic for Phase 4 = `"token-usage"` |
| `ProductionRuntimeNotImplemented` | `veracrawl.runtime_support.runtime_mode` | OK |
| `OpenAIResponsesModelProviderRuntimeAdapter` | `veracrawl.adapters.model_providers.openai_responses` | v1 — Phase 4 introduces v2 alongside; v1 emits `DeprecationWarning` |
| `processing.ExtractionCandidate` | `veracrawl.processing.*` | V1 heuristic class — step 4.6 retires |

The foundation registry (`src/veracrawl/foundation/registry.py`)
lists all Phase 0 contracts; Phase 4 adds the new ports there per
contract conventions (`@runtime_checkable` Protocols) and bumps
the v1 OpenAI adapter to its `legacy_v1` slot.

## Substep boundaries

Total = 7 sub-steps. Order matters: 4.1 (port) blocks 4.2 / 4.3
(adapters); 4.4 (registry) blocks 4.6 (extraction); 4.5 (budget)
also blocks 4.6; 4.7 (calibration) is parallel to 4.4 / 4.5 and
lands before 4.6.

```
4.1 ModelProviderPort v2
  ├── 4.2 OpenAIResponsesAdapter v2
  └── 4.3 AnthropicMessagesAdapter
4.4 PromptRegistryPort + YamlPromptRegistry
4.5 TokenBudgetPort + OutboxBackedBudget
4.7 CalibrationPort + IdentityCalibrator + PlattCalibrator shell
                              │
                              ▼
                            4.6 schema_runtime LLM-driven extraction
                                (consumes 4.1, 4.4, 4.5, 4.7)
```

## Step 4.1 — `ModelProviderPort` v2 + `ProviderRequest` / `ProviderResponse`

### Port interface

```python
# src/veracrawl/ports/model_provider_v2.py

from typing import Protocol, runtime_checkable

from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
)


@runtime_checkable
class ModelProviderPortV2(Protocol):
    """Provider-blind LLM call surface (Phase 4).

    Adapters implement this against OpenAI Responses, Anthropic
    Messages, etc. The orchestrator picks the adapter via config;
    the call site does not branch on provider.

    Boundary invariants enforced at the port level:

    * ``request`` is a Pydantic-validated ``ProviderRequest`` —
      the redaction boundary (Phase 2 step 2.3) ran before
      construction; any rendered ``messages[i].content`` containing
      a ``CredentialValue`` would have raised before reaching here.
    * ``response.usage`` is a Pydantic-validated ``TokenUsage``;
      the adapter must populate it from provider headers /
      response body — never None.
    * Structured-output validation is the adapter's responsibility
      when ``request.response_format.kind == JSON_SCHEMA``;
      mismatches raise ``StructuredOutputViolation``.
    """

    def complete(self, request: ProviderRequest) -> ProviderResponse: ...
```

### Contracts

`ProviderRequest` and `ProviderResponse` are new Pydantic models in
`contracts/llm_input.py` (new module — keeps LLM-specific shapes
out of `contracts/agent.py`):

```python
# src/veracrawl/contracts/llm_input.py

class Anchor(VeraModel):
    """Pure-data anchor for LLM grounding (no network coupling)."""

    id: str
    selector: str | None = None
    excerpt: str
    screenshot_region_ref: Ref | None = None


class ProviderRequest(VeraModel):
    id: str
    run_ref: Ref
    model_name: str
    messages: list[Message]
    tools: list[AgentToolSpec] = Field(default_factory=list)
    response_format: ResponseFormat
    max_output_tokens: int
    temperature: float = 0.0
    anchors: list[Anchor] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_request(self) -> ProviderRequest:
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be in [0, 2]")
        if not self.messages:
            raise ValueError("provider request requires at least one message")
        # Identifier-shape guards (codex recurring concerns #6).
        for name, value in (("id", self.id), ("run_ref", self.run_ref), ("model_name", self.model_name)):
            if not value or not value.strip():
                raise ValueError(f"{name} must be a non-blank identifier")
        return self


class ProviderResponse(VeraModel):
    id: str
    request_ref: Ref
    text: str
    usage: TokenUsage
    finish_reason: ProviderFinishReason
    parsed_output: dict[str, Any] | None = None
    raw_response_ref: Ref | None = None  # opaque audit ref
```

`ProviderFinishReason` is a new enum in `contracts/enums.py`:
`STOP / LENGTH / TOOL_CALL / CONTENT_FILTER / ERROR`.

### Threat model

- **Credential leak via prompt**: prevented by Phase 2 step 2.3
  boundary running before `ProviderRequest` construction. The
  port assumes inputs are already redaction-validated. Adapter
  must not log the raw `messages[].content` — only sanitized
  identifiers (`id`, `model_name`, `run_ref`, `usage`).
- **Schema escape via structured-output mismatch**: validation at
  4.1 contract level (Pydantic) + 4.2 / 4.3 adapter level (re-parse
  against `response_format.json_schema`). Mismatches raise
  `StructuredOutputViolation` with redacted message (the LLM
  output itself may contain extracted PII or, in malicious-prompt-
  injection cases, credentials).
- **Replay determinism**: `request.id` is the replay key. Adapters
  may not vary output for the same (request, model_name, temperature=0)
  triple. Live adapters that honor `temperature=0` only approximate
  determinism (provider-side stochasticity); fixture-mode adapters
  are byte-identical.

### Acceptance tests (`tests/contract/test_step_4_1_model_provider_port_v2.py`)

1. Port is `runtime_checkable` and registered in foundation registry.
2. `ProviderRequest` rejects empty messages list.
3. `ProviderRequest` rejects `temperature` outside `[0, 2]`.
4. `ProviderRequest` rejects whitespace-only identifiers (codex
   recurring concern #6).
5. `ProviderResponse.usage` is required (cannot be None).
6. `Anchor.excerpt` rejects whitespace-only.
7. `ProviderFinishReason` enum exposed at package root.

### Codex recurring concerns coverage

| # | Concern | Coverage in 4.1 |
|---|---------|-----------------|
| 1 | Redaction marker tuple | reuses `_REDACTABLE_MARKERS` from contracts/errors |
| 2 | PRODUCTION gate | not applicable (port is data-shape only); moves to 4.2 / 4.3 |
| 3 | `_private` slots discoverable | `__dir__` filter not relevant; no secret attrs on port |
| 4 | Recursion bounds | n/a |
| 5 | `from None` + `__context__` leak | adapter (4.2/4.3) re-raises must use capture-flag pattern |
| 6 | Identifier-shape validation | applied (whitespace-only refused) |
| 7 | Unbounded loops | n/a |
| 8 | `getattr` safety | n/a |
| 9 | URL handling | `Anchor.excerpt` is content-shaped, not URL-shaped |
| 10 | Dependency upper bounds | no new deps in 4.1 |
| 11 | Private modules | n/a |
| 12 | Path canonicalization | n/a |
| 13 | Free-form reasons | `ProviderFinishReason` enum (no free-form) |
| 14 | Exception `__dict__` | n/a (no new exceptions in 4.1) |
| 15 | Real-engine timing | n/a (no regex/timing in 4.1) |
| 16 | Doc/spec divergence | port docstring + design.md must agree on fixture-mode-only scope; checked in 4.1 acceptance |

## Step 4.2 — `OpenAIResponsesAdapter` v2

### Wire shape

OpenAI Responses API (`POST /v1/responses`):

```
Request body:
  {
    "model": "...",
    "input": [Message],
    "tools": [...],
    "response_format": {"type": "json_schema", "json_schema": {...}},
    "max_output_tokens": N,
    "temperature": 0.0
  }

Response body:
  {
    "id": "...",
    "output": [{"content": [{"text": "..."}]}],
    "usage": {"input_tokens": N, "output_tokens": M, "total_tokens": N+M},
    "status": "completed" | "incomplete"
  }
```

Adapter file: `src/veracrawl/adapters/model_providers/openai_responses_v2.py`
(new). Uses raw httpx (no SDK dep). Inherits retry / Retry-After /
backoff logic from the v1 adapter — shared as a module-level helper.

### Production gate

`RuntimeMode.PRODUCTION` causes `_production_call` to raise
`ProductionRuntimeNotImplemented` until Phase 6 step 6.1 wires
the real production deployment + observability. Fixture mode
(`RuntimeMode.FIXTURE`) routes through `httpx.MockTransport` for
deterministic tests.

### Boundary invariants

- `Authorization` header set from `CredentialVaultPort.reveal()` at
  request build time; never logged.
- Cross-redirect: OpenAI API doesn't redirect cross-origin; if it
  ever does, the cross-origin strip from Phase 1 step 1.5 applies
  via `Phase1ComposedTransport` (4.2 wires through the cooperative
  transport).
- Error handling: HTTP 4xx → `ModelProviderClientError`
  (mapped to `RetryableError` for 429 / 5xx, `FatalError` for
  401 / 403 / 404 / 422).

### Acceptance tests (`tests/integration/test_step_4_2_openai_responses_v2.py`)

1. Happy path with `MockTransport` returns parsed `ProviderResponse`.
2. JSON-schema mismatch raises `StructuredOutputViolation`.
3. 429 with `Retry-After` triggers single retry then succeeds.
4. 401 raises `ModelProviderClientFatal`.
5. Token usage from response body populates `TokenUsage`.
6. PRODUCTION mode raises `ProductionRuntimeNotImplemented`.
7. Authorization header value never appears in any structured log
   captured during the test (canary: `_CANARY_API_KEY = "sk-LIVE-CANARY-DEADBEEF"`).
8. v1 adapter constructor emits `DeprecationWarning`.

### Codex recurring concerns coverage

| # | Coverage in 4.2 |
|---|-----------------|
| 1 | redaction: structured-log fields via `_log_redaction` helper |
| 2 | PRODUCTION gate: explicit `_production_call` raises `ProductionRuntimeNotImplemented` |
| 5 | `from None` + `__context__`: capture-flag pattern for re-raise |
| 9 | URL handling: API base URL validated (http(s) + non-empty netloc) |
| 10 | Dependency upper bounds: no new deps |
| 14 | Exception `__dict__`: `ModelProviderClientError` redacts API URL on construction |

## Step 4.3 — `AnthropicMessagesAdapter`

Analogous to 4.2. Wire shape:

```
POST /v1/messages
  {"model": ..., "messages": [...], "tools": [...],
   "max_tokens": N, "temperature": 0.0}

Response:
  {"id": ..., "content": [{"text": "..."}],
   "usage": {"input_tokens": N, "output_tokens": M},
   "stop_reason": "end_turn" | "max_tokens" | ...}
```

Adapter file: `src/veracrawl/adapters/model_providers/anthropic_messages.py`
(new). API key under `Authorization: Bearer <api_key>` style.

### Provider-swap test (fixture mode only)

`tests/integration/test_step_4_3_provider_swap.py`:

```
Same ProviderRequest →
  OpenAIResponsesAdapter._fixture_handler → ProviderResponse_A
  AnthropicMessagesAdapter._fixture_handler → ProviderResponse_B

Assert:
  - both pass ProviderResponse Pydantic validation
  - both produce non-empty .text
  - both populate .usage with consistent total_tokens math
```

Real-API provider-swap test deferred to Phase 6 step 6.5.

## Step 4.4 — `PromptRegistryPort` + `YamlPromptRegistry`

### Layout

```
prompts/
  extractor/
    product_detail.v1.yml
    product_detail.v2.yml
  classifier/
    access_control.v1.yml
  _meta/
    provider_prices.v1.yml      # ProviderPriceTable snapshot
```

YAML structure:

```yaml
name: product_detail
version: v2
input_schema:
  type: object
  required: [url, anchors, screenshot_ref]
  properties:
    url: {type: string, format: uri}
    anchors: {type: array}
    screenshot_ref: {type: string}
output_schema:
  python_class: veracrawl.contracts.agent.ExtractionCandidate
variables:
  - url
  - anchors
  - screenshot_ref
template: |
  Extract product details from this page:
  URL: {url}
  Anchors:
  {anchors_rendered}
  ...
changelog:
  - {version: v1, date: 2026-04-01, summary: initial}
  - {version: v2, date: 2026-04-15, summary: added screenshot ref}
```

### Port interface

```python
# src/veracrawl/ports/prompt_registry.py

class PromptRegistryPort(Protocol):
    def resolve(self, ref: PromptTemplateRef) -> PromptTemplate: ...
    def render(self, ref: PromptTemplateRef, context: RedactedPromptContext) -> str: ...
```

`PromptTemplateRef` is `<role>/<name>.<version>` (e.g.
`extractor/product_detail.v2`). Refs are immutable: editing
`product_detail.v2.yml` is a contract violation; new versions
get a new file (`v3.yml`).

### Boundary invariants

- `render()` invokes the credential-aware formatter from Phase 2
  step 2.3. Templates that, after rendering, contain a
  `CredentialValue` raise `PromptCredentialLeakError`.
- `resolve()` validates the template's `input_schema` matches the
  variables actually used. Drift raises `PromptTemplateDriftError`.
- `output_schema.python_class` must be importable + a Pydantic
  model class. Drift raises `PromptOutputClassError`.
- File loading is fail-closed: malformed YAML, missing required
  keys, or non-importable output class → adapter refuses to
  resolve.

### Acceptance tests (`tests/contract/test_step_4_4_prompt_registry.py`)

1. Resolve a known template returns parsed `PromptTemplate`.
2. Resolve an unknown ref raises `PromptTemplateNotFoundError`.
3. Render a template with a `CredentialValue` in context raises
   `PromptCredentialLeakError`.
4. Mutating a `vN.yml` file changes the template content but the
   ref still points to a stable digest in `_meta/digests.yml`
   (registry refuses load on digest drift — replay-deterministic
   refs).
5. Importing `PromptRegistryPort` does not import any non-template
   code (boundary test — registry must not pull in `httpx`,
   `openai`, etc.).

## Step 4.5 — `TokenBudgetPort` + `OutboxBackedBudget`

### Port

```python
# src/veracrawl/ports/token_budget.py

class TokenBudgetPort(Protocol):
    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        """Pre-flight check; raises TokenBudgetExceeded if estimate
        exceeds remaining budget."""

    def charge(self, usage: TokenUsage, *, request_ref: Ref) -> None:
        """Record actual usage; raises TokenBudgetExceeded if the
        cumulative total now breaches the cap."""
```

`TokenUsageEstimate` is a new VeraModel in `contracts/agent.py`:
`prompt_tokens_estimate`, `completion_tokens_estimate`,
`cost_usd_estimate`, `model_name`, `request_ref`.

### Adapter — `OutboxBackedBudget`

`src/veracrawl/adapters/budget/outbox_backed_budget.py` (new).

- Holds the cap (`TokenBudget` from Phase 0 contract).
- Persists each `TokenUsage` event via `OutboxRepositoryPort` with
  `dispatch_topic="token-usage"` + `payload_ref` pointing to a
  durable `TokenUsageEvent` record.
- Maintains an in-memory running total (advisory; the durable
  outbox is the source of truth, mirroring step 2.5b's accounting
  policy).
- On `charge`, computes new total; if any cap breached, raises
  `TokenBudgetExceeded` AFTER persisting the durable event.
- `estimate_charge` uses provider-specific token counters
  (tiktoken-equivalent for OpenAI, anthropic-tokenizer for
  Anthropic) — both ship as fixture-mode stubs in Phase 4 (real
  tokenizers wired in Phase 6 step 6.1).

### Pricing table

`prompts/_meta/provider_prices.v1.yml` carries pinned per-1k-token
costs. `ProviderPriceTable.from_meta()` loads and validates. Step
4.5 acceptance asserts the price table version pinned in the
budget audit matches the table version on disk (drift = fail-closed
refusal).

### Acceptance tests

1. `charge` increments outbox + advisory counter together.
2. Cumulative sum equals initial cap exactly when budget exhausts.
3. `TokenBudgetExceeded` raised AFTER durable persist (replay can
   reconstruct the breach moment).
4. `estimate_charge` rejects when estimate alone exceeds remaining.
5. Provider-swap budget test: same logical request charged
   against OpenAI and Anthropic both fit under the same `TokenBudget`
   given pinned prices.
6. Price table digest drift refuses load.
7. PRODUCTION mode raises `ProductionRuntimeNotImplemented` for
   `_production_persist` (Phase 6 wires real outbox repo).

## Step 4.6 — `schema_runtime` LLM-driven extraction

### Module rewrite

`src/veracrawl/processing/schema_runtime.py` (existing — currently
heuristic V1) is rewritten to call the LLM:

1. Resolve prompt via `PromptRegistryPort`.
2. Build `RedactedPromptContext` from inputs (URL, anchors,
   screenshot ref, schema).
3. Render template; refuse if rendered output contains credentials.
4. `estimate_charge` against budget; refuse if would exceed.
5. `ModelProviderPortV2.complete(request)`.
6. Parse response; validate against schema.
7. Translate raw confidence → calibrated via `CalibrationPort`.
8. Build + return `LLMExtractionCandidate` + `FieldCitation` +
   `FieldConfidence` records.
9. `charge(actual_usage)` against budget.

### Reclaim bare names

Phase 0 step 0.2 reservation: `ExtractionCandidate` /
`FieldCitation` / `FieldConfidence` ship as `LLMExtractionCandidate`
/ etc. with module-level aliases at `contracts/agent.py:931`.

Step 4.6 retires the V1 heuristic class:

1. `processing.ExtractionCandidate` (V1 heuristic) gets
   `DeprecationWarning` on import.
2. The foundation registry's `"ExtractionCandidate"` slot points
   at `contracts.agent.ExtractionCandidate` (== alias to the v2
   class).
3. ~13 production import sites (`from veracrawl.processing import ExtractionCandidate`)
   keep working via the alias for one release.
4. Direct attribute access on V1's heuristic-only fields raises
   `AttributeError` on the v2 class — callers must migrate.

### Acceptance tests (`tests/integration/test_step_4_6_schema_runtime_llm.py`)

1. Extract on a fixture page produces `LLMExtractionCandidate` with
   per-field citations + calibrated confidence.
2. JSON-schema mismatch raises `StructuredOutputViolation`.
3. Prompt with a `CredentialValue` in context raises
   `PromptCredentialLeakError` before the LLM call.
4. Token-budget exhaustion raises `TokenBudgetExceeded`.
5. Replay determinism: same `(request, fixture_response)` produces
   byte-identical `LLMExtractionCandidate`.
6. V1 `processing.ExtractionCandidate` import emits `DeprecationWarning`.
7. `LLMExtractionCandidate` validator from Phase 0 catches missing
   citation / confidence refs.

## Step 4.7 — Calibration scaffolding

### Port

```python
# src/veracrawl/ports/calibration.py

class CalibrationPort(Protocol):
    def calibrate(self, raw_score: float, *, model_name: str, field_name: str) -> CalibratedScore: ...
```

`CalibratedScore` is a new VeraModel: `value` (in [0, 1]),
`raw_value`, `calibrator_id`, `fit_artifact_ref`.

### Adapters

- `IdentityCalibrator` (`adapters/calibration/identity.py`):
  pass-through `value = raw_value`. Default; lets Phase 4 tests
  run without a fitted model.
- `PlattCalibrator` (`adapters/calibration/platt.py`): shell that
  loads a fitted model via `fit_artifact_ref`. Phase 4 ships the
  load + apply path; Phase 6 step 6.5 ships the fit path + the
  actual artifact.

### Acceptance tests

1. `IdentityCalibrator.calibrate(0.7, ...)` returns
   `CalibratedScore(value=0.7, raw_value=0.7, calibrator_id="identity", ...)`.
2. `PlattCalibrator` with a missing artifact ref fails closed
   (refuses to load — Phase 6 dependency missing is explicit).
3. `CalibratedScore.value` validated in `[0, 1]`.

### Codex recurring concerns coverage

| # | Coverage in 4.7 |
|---|-----------------|
| 6 | Identifier-shape: `calibrator_id`, `model_name`, `field_name` whitespace-rejected |
| 14 | `__dict__` leak: no exceptions in 4.7; if a future Platt-load failure raises, redact `fit_artifact_ref` to length-only |
| 16 | Doc/spec divergence: port doc clearly states Phase 6 ships the fit path; Phase 4 ships the apply path only |

---

## Cross-cutting integration tests

Beyond per-step tests, Phase 4 ships two integration tests that
exercise the full extraction path:

1. `tests/integration/test_phase_4_extraction_e2e.py`:
   - Fixture page (HTML + anchors + screenshot ref).
   - Resolve `extractor/product_detail.v2`.
   - OpenAI fixture adapter returns a structured JSON response.
   - Assert: `LLMExtractionCandidate` returned with per-field
     citations + calibrated confidence; budget charged correctly;
     no credential canary in any structured log.
2. `tests/integration/test_phase_4_provider_swap_e2e.py`:
   - Same fixture page run against OpenAI fixture adapter and
     Anthropic fixture adapter.
   - Assert structurally-identical output shapes (field names,
     citation shape, confidence shape).

## Reservations + Phase 6 hand-off

Phase 4 leaves the following items as Phase 6 reservations:

| Item | Phase 6 step | Why deferred |
|---|---|---|
| Real OpenAI / Anthropic API calls in PRODUCTION | 6.1 | requires production deployment + secrets |
| Tier A gold corpus authoring + adjudication | 6.5 | manual labelling effort, multi-day |
| Platt / isotonic calibration fitting on the corpus | 6.5 | depends on corpus |
| Nightly Brier / ECE / abstention metrics | 6.5 | requires nightly pipeline (Phase 6) |
| Field-oracle ≥95% gold coverage | 6.5 | depends on corpus + calibration fit |
| Real provider-swap acceptance test | 6.5 | depends on real API access |
| Per-extraction p95 ≤ $0.01 cost regression | 6.5 | depends on real API access + nightly pipeline |
| Tokenizer-accurate `estimate_charge` (tiktoken / Anthropic) | 6.1 | depends on production runtime |

The contract surface (4.1, 4.4, 4.5, 4.7) is **stable enough** for
Phase 5 (recovery) to consume; calibration values are advisory in
Phase 5 (cheap-classifier-before-LLM) and authoritative only when
the Phase 6 fitted artifact is in place.

---

## Plan-review history

| Iter | Result | Key findings |
|---|---|---|
| draft | n/a | initial JIT supplement under the front-load-design workflow; no formal codex plan-review run yet (each Phase 4 sub-step gets its own task-stage codex review at implementation time per the gate cadence) |

When a Phase 4 sub-step lands, this supplement gets a "verified at
iter-N" line if codex flags any ground-truth correction.
