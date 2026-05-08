# Production-grade authorized-source AI crawler — design document

| | |
|---|---|
| Status | DRAFT v2 (post-codex-review-of-v1) |
| Date | 2026-05-07 |
| Supersedes | `docs/plans/production-crawler/design.md` (v1) |
| Baseline | `master @ 096cd97` (P0 fix-pack merged 2026-05-07) |
| Related plans | `docs/plans/p0-fix-pack/STATUS.md` |
| Anchor docs | `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `AGENTS.md` |

---

## 0. What this design changes from v1

v1 was rejected by codex review with 5 critical + 11 important + 2 minor
findings. The most consequential were:

1. **Charter violation.** v1's Phase 2 (curl_cffi TLS impersonation,
   stealth fingerprint expansion, Cloudflare 5s challenge handling) is
   verbatim what `docs/09-target-capability-model.md` §Safety Boundary
   forbids: *"WAF evasion, stealth automation, ban-avoidance proxy
   tactics, ... CAPTCHA solving, paywall bypass, login-wall
   circumvention"*. v2 reframes the entire crawler stack as
   **authorized-source-only**.
2. **Gate / orchestration confusion.** v1 put the adapter fallback
   chain inside `source_coverage_gate`. The gate's job is to validate
   evidence completeness, not run live decision loops. v2 introduces a
   separate `AdapterEscalationPort` and keeps the gate purely
   evaluative.
3. **Baseline drift.** v1 referenced "P0 already shipped httpx /
   structured logging / scoped tool gateway" — true in workspace,
   false on master. P0 fix-pack has now been fast-forwarded into
   master at `096cd97`; this document treats that as ground truth.
4. **Capability frame.** v1 used "general production crawler"
   benchmarks (anti-bot survival, proxy rotation, JA3 evasion).
   VeraCrawl's charter is **authorized-source-only**, so the right
   benchmarks are credential vault hygiene, official-API priority,
   access-control classification (not evasion), and replay
   completeness. The "20% production readiness" framing in earlier
   discussion compared against the wrong target.
5. **Domain exception clash.** v1 proposed
   `RetryableError` / `FatalError` / `PolicyViolation` as a parallel
   hierarchy that would have broken existing
   `except ValueError` catch sites. v2 uses multiple-inheritance
   mixins so existing catches stay matched.

The codex critical/important findings v2 must address are tracked
inline in §11.

## 1. Goals & non-goals

### 1.1 Hard non-goals (charter, `docs/09:116`, do not negotiate)

VeraCrawl will **not** implement, ship, or surface configuration for:

- WAF evasion (Cloudflare 5s solver, Turnstile bypass, DataDome /
  PerimeterX / Akamai bypass)
- Stealth automation (`navigator.webdriver` patches,
  navigator.plugins / languages / chrome.runtime / Permissions API
  fingerprint patches; the `_stealth.py` module shipped in P0-2 is
  retracted on master at `096cd97`)
- TLS / JA3 fingerprint impersonation as a production capability
  (`curl_cffi --impersonate` at production-grade level)
- Ban-avoidance proxy tactics (residential proxy rotation policies
  framed as evasion)
- CAPTCHA solving / paywall bypass / login-wall circumvention
- Robots.txt / ToS / customer authorization bypass

These are surfaced by the `AccessControlClassifier` (§4.4) and routed
to authorized fallback or terminal failure, not evaded.

### 1.2 Goals

- **Cooperative web crawling**: static, sitemap, RSS, listing/detail,
  search-results within policy, forms within policy. The full V1
  pattern set in `docs/09-target-capability-model.md` §Website
  Pattern Coverage.
- **Authorized session subsystem** (the docs/09 capability area
  VeraCrawl is *required* to support but P0 ignored): customer-
  provided credentials used through vault, scope, audit, and replay.
- **Official-API priority**: where an authorized source-of-record API
  exists (eBay, Amazon SP-API, etc.) the chain prefers it; HTTP /
  browser is a fallback for sources without an API.
- **Access-control classification**: detect WAF / CAPTCHA / login
  walls, surface them as typed `AccessControlBlocked` failures with
  vendor + evidence ref, route to authorized session or terminal.
- **Cost-bounded, replay-deterministic, evidence-complete fetches**.
- **LLM-driven planning, extraction, verification, recovery** as the
  agent loop in `docs/06-agent-system-design.md`, with
  anchor-grounded citations and per-field confidence calibration.
- **Real production-runtime backends** for observability,
  disaster recovery, security/privacy (RuntimeMode.PRODUCTION paths
  flip from `NotImplementedError` to actual SDK calls).
- **Live regression** that fails CI when external targets, providers,
  or budgets drift.

### 1.3 Non-goals (out-of-scope but legal)

- Multi-tenant isolation, billing, customer auth at the API surface
- One-off scrapers for sites outside the V1 corpus
- In-process residential proxy rotation (deployment supplies via
  `ProxyPort`)
- LangChain / LangGraph / CrewAI / AutoGen / Semantic Kernel
  integration as core dependencies (`AGENTS.md` Python And Agent
  Framework Boundary)

## 2. Current state baseline (verified against master `@ 096cd97`)

| Capability area | master state | Verification |
|-----------------|--------------|--------------|
| HTTP transport (httpx + retry + redirect SSRF opt-in) | ✅ shipped | `src/veracrawl/adapters/network/stdlib_http.py` |
| Browser rendering stability (real Chrome UA, locale, wait strategy) | ✅ shipped | `src/veracrawl/adapters/browser/playwright.py`; stealth scripts retracted |
| Structured logging + redaction + correlation_id | ✅ shipped | `src/veracrawl/runtime_support/{logging,_log_redaction}.py` |
| RuntimeMode (FIXTURE / PRODUCTION boundary) + 4 gates wired | ✅ shipped | `src/veracrawl/runtime_support/runtime_mode.py` |
| Tool gateway allowlist + quota + audit (legacy mode preserved) | ✅ shipped | `src/veracrawl/agents/tool_gateway.py` |
| OpenAI adapter: httpx + retry + RAW_RESPONSE_LEAK fix + ModelProviderError | ✅ shipped | `src/veracrawl/adapters/model_providers/openai_responses.py` |
| optimization producer/consumer cycle broken | ✅ shipped | `src/veracrawl/contracts/optimization_runtime.py` |
| CI workflows + dependabot + live marker | ✅ shipped | `.github/workflows/{ci,nightly}.yml`, `.github/dependabot.yml` |
| BrowserContext reuse + storage_state | ❌ | nothing on master |
| Robots.txt systematic enforcement | ❌ | only `urllib.robotparser` ad-hoc in benchmarks |
| Per-host rate limiter | ❌ | refs only |
| Authorized session subsystem | ❌ | contract types but no live wiring |
| Adapter escalation chain | ❌ | refs only |
| Access-control classifier (typed) | ❌ | only string-match `_is_access_control_page` |
| LLM provider port v2 (messages / tools / response_format) | ❌ | port still v1, OpenAI adapter still side-channel `set_context_payload` |
| Multi-provider (Anthropic / etc.) | ❌ | only OpenAI adapter |
| Prompt registry | ❌ | only `prompt_template_ref` strings |
| Token / cost outbox | ❌ | only in-memory dict |
| LLM-driven extraction (anchor-grounded, calibrated confidence) | ❌ | dictionary lookup |
| LLM-driven planning / recovery loop | ❌ | scoring fields exist but unwired |
| Real OTel / Presidio / DR backends | ❌ | gates raise `ProductionRuntimeNotImplemented` |
| Live integration tests | ❌ | marker registered, 0 tests |

This list is the gap v2 closes.

## 3. Architectural overview

### 3.1 Crawl loop (the AI part)

The agent loop lives in `agents/runtime.py` (today: ref aggregator;
v2: real loop):

```
                AgentRunRequest
                 (objective • corpus • RunBudget • policy)
                          │
                          ▼
            ┌──────────────────────────────┐
            │ observe (fetch + evidence)    │
            │   FrontierPicker              │
            │   ↓                           │
            │   AdapterEscalationPort       │
            │     official-API → HTTP →     │
            │     authorized-session-API →  │
            │     browser                   │
            │   ↓                           │
            │   AccessControlClassifier     │
            │     classify or pass-through  │
            └────────────┬─────────────────┘
                         ▼
            ┌──────────────────────────────┐
            │ think (LLM reasoning)        │
            │   ExtractionAgent             │
            │     anchor-grounded fields +  │
            │     citations + per-field     │
            │     calibrated confidence     │
            │   PlannerAgent                │
            │     next URL / abandon /      │
            │     authorized-session-       │
            │     escalate                  │
            └────────────┬─────────────────┘
                         ▼
            ┌──────────────────────────────┐
            │ act (mutate the world)        │
            │   ToolGateway (already shipped)│
            │   CommandEnvelope emit        │
            └────────────┬─────────────────┘
                         ▼
            ┌──────────────────────────────┐
            │ verify (replay + ground-truth)│
            │   replay determinism check   │
            │   field oracle (calibrated)  │
            │   on miss → RecoveryPort      │
            └──────────────────────────────┘
```

### 3.2 Adapter escalation chain (corrected per codex critical #1)

```
target URL + objective
   │
   ▼
AdapterEscalationPort.next_attempt(prior_evidence, policy, budget)
   │
   ├─ Step 1: OfficialAPIAdapter (if covered)
   │            on rate limit / outage:
   │              return next_attempt = HTTP_PUBLIC
   │            on auth issue:
   │              return next_attempt = AUTHORIZED_SESSION (if vault entry exists)
   │
   ├─ Step 2: HTTPAdapter (httpx; real Chrome UA; rate-limited)
   │            on AccessControlBlocked(vendor=...):
   │              policy decides:
   │                - authorized session available? → AUTHORIZED_SESSION
   │                - no? → terminal AccessControlBlocked (do NOT evade)
   │            on 4xx fatal (401/403/404/410/422):
   │              terminal — do NOT escalate (this was a v1 mistake)
   │            on 429 / 5xx exhausted:
   │              decide: cooldown + retry HTTP, or terminal
   │
   ├─ Step 3: AuthorizedSessionAdapter (only if customer provided creds)
   │            uses CredentialVaultPort to retrieve scoped credential
   │            session lifetime tracked, audited, replayable
   │            on access denied with valid credential: terminal
   │
   └─ Step 4: BrowserAdapter (rendering only; no stealth)
                only invoked when:
                  - rendering JS is required for the document, AND
                  - HTTP-equivalent path is unavailable, AND
                  - policy allows browser observation
                NOT invoked as anti-bot escalation
```

`source_coverage_gate` returns to its evaluative role: given a chain
of `SourceAdapterResult` records, does the evidence cover what the
gate requires? It does not run decision loops.

### 3.3 New ports

| Port | Purpose | Default impl |
|------|---------|--------------|
| `AdapterEscalationPort` | run the chain decision | `PolicyDrivenEscalator` |
| `RobotsPort` | parse + cache robots.txt | `UrllibRobotsParser` |
| `RateLimiterPort` | per-(origin, route class, adapter) token bucket with AIMD | `InMemoryAimdLimiter` |
| `SitemapPort` | discover URLs via sitemap / robots Sitemap directive | `XmlSitemapParser` |
| `ProxyPort` | per-request proxy URL (deployment-supplied) | `NoProxyAdapter` |
| `CredentialVaultPort` | retrieve scoped customer credentials | `EnvVarVault` (test) / `OutboxVaultClient` (prod) |
| `SessionScopePolicy` | enforce credential scope (host, path-pattern, action) | `StrictAllowlistScope` |
| `AccessControlClassifier` | detect WAF / CAPTCHA / login wall and emit typed evidence | `HeuristicClassifier` |
| `PromptRegistryPort` | resolve `prompt_template_ref` to versioned content + schema | `YamlPromptRegistry` |
| `TokenBudgetPort` | per-run token / cost budget | `OutboxBackedBudget` |
| `RecoveryPort` | encapsulate next-action decision on typed failure | `LLMBackedRecovery` |
| `EvidenceArtifactStorePort` | persist HAR + screenshots + DOM + headers (redacted) | `LocalFsArtifactStore` |

All ports default to no-ops or test-only impls so existing tests pass
unchanged.

### 3.4 New adapters

| Adapter | Notes |
|---------|-------|
| `AnthropicMessagesAdapter` | required in phase 4; conformance benchmark for `ModelProviderPort` v2 |
| `BedrockConverseAdapter` | deferred to a P1 (largest divergence from OpenAI Responses; see §11) |
| `GeminiAdapter` | deferred to a P1 |
| `OtelObservabilityAdapter` | wires `runtime_support/observability.py` PRODUCTION mode |
| `PresidioPiiAdapter` | wires `runtime_support/security_privacy.py` PRODUCTION mode |
| `CredentialVaultClient` | wires `CredentialVaultPort` to a real vault (HashiCorp / AWS Secrets Manager / customer-supplied) |

Note: `CurlCffiSourceAdapter` is **NOT** in v2. Charter prevents it as
a production unblock surface.

### 3.5 New / extended contracts

Added under `contracts/`:

- `Message`, `ToolCall`, `ToolSpec`, `ResponseFormat`, `TokenUsage`,
  `TokenBudget` — `agent.py`
- `FieldCitation`, `FieldConfidence` — `agent.py` (no collision; ship
  under spec names in Phase 0).
- `LLMExtractionCandidate` (canonical class) + `ExtractionCandidate`
  (alias) — `agent.py`. The bare name `ExtractionCandidate` is
  already taken at registry / package-export level by the
  heuristic-driven `processing.ExtractionCandidate` that ~13 V1
  modules import for the heuristic extraction path. Phase 0 ships
  the v2 LLM-driven shape under the implementation-only name
  `LLMExtractionCandidate` plus a module-local alias
  `ExtractionCandidate` inside `agent.py`, so Phase 4 code following
  the design's import path (`from veracrawl.contracts.agent import
  ExtractionCandidate`) resolves to the v2 shape. Phase 4 retires
  the heuristic class in `processing.py`, swaps the package-level
  re-export and registry entry to point at `agent.py`, and reclaims
  the bare name as the canonical registry/package surface (see
  Phase 4 step 4.6 deliverables).
- `AccessControlBlocked`, `NetworkAttemptEvidence` —
  `network.py`
- `AdapterEscalationDecision`, `AdapterEscalationPolicy` —
  `source_adapter.py`
- `CredentialScope`, `CredentialUseRecord` —
  `security_privacy.py`
- `RecoveryDecision`, `RecoveryTrace` — `agent.py`

`ModelRequest` v2 gains optional fields (extras forbidden remains
intact via Pydantic union with v1):

```python
class ModelRequestV2(ModelRequest):
    messages: list[Message] | None = None     # if set, takes priority over template+context
    tools: list[ToolSpec] = Field(default_factory=list)
    tool_choice: ToolChoice | None = None
    response_format: ResponseFormat | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_output_tokens: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
```

Adapters dispatch on the presence of v2 fields. v1 callers continue
to work; the `set_context_payload` side-channel is deprecated for
one release and a boundary test rejects new uses outside the
deprecation surface.

### 3.6 Domain exception hierarchy (corrected per codex critical #5)

```python
# Mixin protocols (no state, no __init__)
class RetryableError: ...
class FatalError: ...
class PolicyViolation: ...

# Existing classes get multiple inheritance:
class NetworkAdapterError(ValueError):
    """existing P0-1 base"""

class NetworkTimeoutError(NetworkAdapterError, RetryableError): ...
class RetryExhaustedError(NetworkAdapterError, FatalError): ...
class RedirectDeniedError(NetworkAdapterError, PolicyViolation): ...
class EgressDeniedError(NetworkAdapterError, PolicyViolation): ...
class AccessControlBlocked(NetworkAdapterError, PolicyViolation): ...

class ModelProviderError(RuntimeError):
    """existing P0-3 base"""

class ProviderAuthFailed(ModelProviderError, FatalError): ...
class ProviderRateLimited(ModelProviderError, RetryableError): ...
class TokenBudgetExceeded(ModelProviderError, PolicyViolation): ...
class StructuredOutputViolation(ModelProviderError, PolicyViolation): ...
```

Every existing `except ValueError:` catch in
`fetch/acquisition.py` keeps matching `NetworkAdapterError` and
its descendants. New code can dispatch on the mixin:

```python
try:
    adapter.execute(...)
except RetryableError as e:
    schedule_retry(...)
except PolicyViolation as e:
    record_audit_and_terminate(...)
except FatalError:
    abandon(...)
```

Acceptance: a contract test enumerates every existing
`raise NetworkAdapterError` / `raise ModelProviderError` site and
verifies the raised class is a subclass of one of the three mixins.

## 4. Phased delivery (dependency-ordered)

### Phase 0 — Shared contracts and exception hierarchy

**Capability cliff**: every later phase has stable contract types and
a uniform exception classification to dispatch on. No runtime
behavior changes; pure type-system additions.

**Inputs**: master `@ 096cd97` baseline.

**Deliverables**:

- All contract additions in §3.5.
- Exception mixins per §3.6; existing `NetworkAdapterError` /
  `ModelProviderError` get re-classified subclasses.
- Pre-Phase decision log answering the v1 open questions (§5).
- Boundary test: every `raise NetworkAdapterError` /
  `raise ModelProviderError` site classified under one mixin.
- Boundary test: every existing `except ValueError` catch in
  `fetch/`, `agents/`, `evidence/` continues to catch the new
  subclasses.

**Acceptance**: `pytest -q` green; new contract types covered by at
least one constructor / validator test each; mypy --strict clean.

### Phase 1 — Cooperative HTTP + browser baseline

**Inputs**: phase 0.

**Capability cliff**: VeraCrawl crawls cooperative sites at
production rate, respects robots / crawl_delay, recycles browser
session state across navigations within a run, and produces full
evidence (HAR + headers redacted) per attempt.

**Deliverables**:

- `BrowserContext` reuse + per-run `storage_state.json` persistence
  in `PlaywrightBrowserObservationAdapter`.
- `RobotsPort` (default `UrllibRobotsParser`): fetch once per host
  per run with TTL + on-disk cache; enforce on initial URL **and**
  every redirect target; same UA used for robots fetch and actual
  fetch (single source-of-truth UA per run); honor
  `crawl_delay()` and `request_rate()`.
- `RateLimiterPort` (default `InMemoryAimdLimiter`):
  per-(origin, route class, adapter type) bucket with AIMD —
  multiplicative decrease on 429 (factor 2, cooldown 60s with
  jitter), additive increase on 10 successful requests at the new
  rate. Floor: respect strictest of `Retry-After` /
  `crawl_delay` / `request_rate`. Cap: configurable
  `max_concurrency_per_origin` (default 4).
- HAR capture via Playwright `record_har_path` (BrowserContext
  constructor option); HAR JSON post-processed through structural
  redaction (`runtime_support.har_redaction.redact_har_payload`) and
  written to `EvidenceArtifactStorePort`. Note (2026-05-07 narrowing,
  reassessment-20260507T181555Z.md): step 1.4 ships HAR via
  `record_har_path` only; `context.tracing.start({snapshots,
  screenshots})` for snapshots / screenshots is deferred to a P1
  backlog item because (a) `record_har_path` produces the parseable
  HAR JSON the acceptance criterion requires, and (b) Playwright
  trace zips embed screenshots / DOM / network in a single archive
  that cannot be field-level redacted (trace retention is a Phase 6
  `ArtifactLifecycle` concern, not a Phase 1 capture concern). The
  per-page `screenshot()` and DOM snapshot already captured by
  `_observe_on_context` cover the screenshot / snapshot evidence
  surface for Phase 1.
- Per-attempt `NetworkAttemptEvidence` populated on
  `NetworkClientResult` (request method/URL/headers redacted,
  response status/headers redacted, elapsed_ms, attempt_number,
  failure_class).
- Cross-redirect Authorization / Cookie strip on cross-origin
  redirects (per RFC 7235 best practice).
- ETag / Last-Modified conditional fetch via
  `If-None-Match` / `If-Modified-Since`; 304 short-circuits to
  cached body.
- Cookie jar scoped per-run and per-origin; do not leak between
  runs or across origins.
- HAR PII redaction via structured parser (the
  `RedactSensitiveProcessor` already shipped) applied to header
  blocks and response bodies; regex-only is rejected as
  insufficient.
- Live tests #1–#3 (httpbin headers / redirect-to / example.com).

**Acceptance** (machine-verifiable):

- Property test: a 50-fetch run against fixture host with
  `crawl_delay=2s` produces wall time ≥ `49 × 2 ± 100ms`.
- Cross-redirect Authorization stripping property test: original
  request has `Authorization: Bearer x`; redirect to different
  origin records hop in evidence with header **stripped**.
- Conditional-fetch property test: second fetch with valid ETag
  yields `304` and reuses prior body artifact_ref.
- HAR sidecar: parse HAR JSON, assert no header value matches the
  configured Authorization or Cookie tokens (redaction applied);
  assert no request URL substring matches a list of canary tokens
  the test injects in inputs.
- Boundary test: `ProxyPort` / `RobotsPort` / `RateLimiterPort`
  have default no-op or in-memory impls so all existing tests pass
  without configuration.

### Phase 2 — Authorized session subsystem (the docs/09 capability v1 missed)

**Inputs**: phase 0.

**Capability cliff**: customer-provided credentials can be used for
authorized sites without entering prompts, logs, or LLM context;
every credential use is audited with vault access log + policy
decision + replay event per `docs/09:128`.

**Deliverables**:

- `CredentialVaultPort` with two impls:
  - `EnvVarVault` for tests / fixtures (reads
    `VERACRAWL_CRED_<scope>_<key>`).
  - `OutboxVaultClient` for production: retrieves a scoped
    credential, increments the audit counter, returns a value
    whose `__repr__` and `__str__` are
    `<credential:redacted:<scope>>`.
- `SessionScopePolicy` (default `StrictAllowlistScope`): enforces
  (host pattern, path pattern, allowed actions, expiry) per
  credential. Out-of-scope use raises `CredentialScopeViolation`
  (PolicyViolation).
- `RedactedPromptContext`: a wrapper that any credential value
  passing into `prompt_template_ref` resolution / model adapter is
  replaced with the literal `<credential:redacted:<scope>>` before
  the prompt enters the messages list. The `RedactSensitiveProcessor`
  (P0-5) is the implementation.
- `AuthorizedSessionAdapter`: HTTP adapter that injects credentials
  into the request from the vault, scoped to the credential's
  policy. On request emit, the adapter records a
  `CredentialUseRecord` to the outbox.
- Credential lifecycle: each `AgentRunRequest` carries a
  `credential_scope_refs` list; the agent runtime resolves them at
  start, holds the references (not values) for the run, and
  invalidates on completion.

**Acceptance**:

- Property test: a run that uses a credential N times produces
  exactly N `CredentialUseRecord` outbox events, each with the
  vault audit cookie present.
- Negative test: passing a credential value into a prompt template
  is rejected at registry resolve time (not at provider adapter
  time); test that the prompt registry refuses templates whose
  rendered output equals or contains a credential ref token.
- Negative test: out-of-scope use raises
  `CredentialScopeViolation`; the audit log records the attempt
  with `decision=denied`.
- Live test: an authorized session against a test API (controlled
  by us, not third-party) succeeds with vault audit, credential
  redaction, and replay event present.

### Phase 3 — Access-control classification + escalation

**Inputs**: phase 0 (escalation contracts) + phase 1 (transport) +
phase 2 (authorized session).

**Capability cliff**: a single `fetch this product` call walks
official-API → HTTP → authorized-session-API → browser, picks the
cheapest viable adapter, classifies access-control challenges
correctly, and **never tries to evade them**.

**Deliverables**:

- `AccessControlClassifier` (default `HeuristicClassifier`):
  detects Cloudflare interstitial / Turnstile, DataDome,
  PerimeterX, Akamai, generic login wall (HTTP 401 + `WWW-Authenticate`),
  generic CAPTCHA (HTML pattern + status combo). Output:
  `AccessControlBlocked(vendor, url, evidence_ref)`.
- `AdapterEscalationPort` with `PolicyDrivenEscalator`. Triggers:
  - Official-API rate-limited / outage → fall through.
  - HTTP transport-class `RetryableError` exhausted → cooldown +
    retry with same adapter (NOT browser).
  - HTTP returns `AccessControlBlocked` → escalate to authorized
    session if scope covers, else terminal.
  - HTTP `FatalError` (404 / 410 / 401) → terminal (codex
    critical #4 / important #7 fix: 403 / 401 / 404 are NOT
    escalated to browser).
  - Document is JS-rendered (HTTP returns shell HTML +
    `<script>` for content) AND policy permits browser → escalate
    to browser.
- eBay token cache (file-backed, TTL'd, lockable across worktree
  runs).
- Amazon SP-API pagination + token refresh on 401 once per run +
  partial-batch tolerance.
- Per-chain-step retry budget so a runaway browser fallback cannot
  consume more than its share.
- `source_coverage_gate` reverts to evaluative role: validates the
  recorded chain's evidence completeness; does not run live
  decisions.

**Acceptance**:

- Property test: for any sequence of typed failures from adapter A,
  the chain picks adapter B per `AdapterEscalationPolicy` and the
  remaining budget is monotonically non-increasing.
- Property test: HTTP `403` does not trigger browser escalation
  (regression for codex important #7).
- Property test: `AccessControlBlocked` does not trigger browser
  escalation **unless** an authorized session is available; in that
  case it routes to authorized session, not stealth/CAPTCHA solver.
- Replay test: a recorded chain run replayed against the fixture
  store reproduces the same final adapter and the same evidence
  digest.
- Live test #5 (eBay browse-by-keyword) returns ≥1 product within
  `RunBudget(calls=10, cost_usd=0.05)`.

### Phase 4 — LLM provider port v2 + extraction

**Inputs**: phase 0 (contracts) + phase 1 (evidence contracts; an
extraction takes DOM anchors + headers + screenshot ref as input,
which only phase 1 fully populates — codex important #14 fix).

**Capability cliff**: extraction is a real LLM call with anchor-
grounded citations, calibrated per-field confidence, and Pydantic-
validated structured output. Provider-blind (OpenAI / Anthropic
swap is a config change).

**Deliverables**:

- `ModelProviderPort` v2 (per §3.5).
- OpenAI Responses adapter updated to v2 surface; v1 callers via
  deprecated path emit `DeprecationWarning` for one release.
- `AnthropicMessagesAdapter`. Bedrock / Gemini deferred (rationale
  in §11 decision log).
- `PromptRegistryPort` (`YamlPromptRegistry`): prompts at
  `prompts/<role>/<name>.<vN>.yml` with explicit input schema,
  output schema (Pydantic class path), variable list, changelog;
  immutable version refs; experiment manifest support per
  §11 decision log.
- `TokenBudgetPort` (`OutboxBackedBudget`): per-run budget
  decremented by `TokenUsageEvent`s the adapter emits; exceeding
  raises `TokenBudgetExceeded`.
- `schema_runtime.py` rewritten to call the LLM:
  - Input: DOM anchors (from phase 1 evidence) + screenshot ref +
    URL + extraction schema (Pydantic).
  - Output: `ExtractionCandidate` with field values, per-field
    `FieldCitation` (anchor refs the LLM grounded on), per-field
    raw confidence, abstention reasons.
  - Adapter validates returned JSON against the schema; mismatches
    raise `StructuredOutputViolation`.
- **Calibrated** confidence: a calibration layer (Platt or isotonic)
  trained on the manual gold tier; the per-field score is the
  calibrated value, not the LLM's self-reported number. Brier /
  ECE / abstention precision-recall computed per nightly run.
- `field_oracle` ground-truth corpus: tiered approach per §11:
  - Tier A (gold): manually verified, versioned, ~200 entries
    across V1 patterns. Source of calibration.
  - Tier B (weak): official-API mirrors with adjudication policy.
    Used for coverage but adjudicated against gold conflicts.
  - Tier C: cross-provider agreement is **NOT** treated as ground
    truth (codex important #8 fix; agreement amplifies shared
    hallucinations).

**Acceptance**:

- Provider-swap test: same `AgentRunRequest` resolved against OpenAI
  vs Anthropic produces results that pass the same field-oracle
  confidence floor.
- Structured-output test: a deliberately malformed mock response
  raises `StructuredOutputViolation`.
- Token-budget property: a recorded run that exhausts the budget
  raises `TokenBudgetExceeded` exactly once and the outbox sum
  matches the cap.
- Calibration: nightly Brier ≤ 0.15 on the gold tier; ECE ≤ 0.10;
  abstention precision-recall AUC ≥ 0.85.
- Field oracle: ≥95% of corpus products meet calibrated
  `confidence ≥ 0.8` on price + title.
- Boundary test: prompt registry resolution refuses templates that
  contain a literal credential ref token (phase 2 cross-test).

### Phase 5 — AI planning + recovery

**Inputs**: phase 3 (typed failures + escalation) + phase 4 (LLM).

**Capability cliff**: agent runtime drives the crawl. Given an
objective and corpus refs, the runtime picks URLs, escalates
adapters, and recovers from typed failures, all under a declared
budget with hard cost caps.

**Deliverables**:

- Frontier scoring wired to LLM signals via `ModelProviderPort` v2;
  `RuntimeFrontierOptimizationDecision` becomes the agent's actual
  planning output.
- `RecoveryPort` (default `LLMBackedRecovery`): on a typed failure
  (`PolicyViolation` / `RetryableError` exhausted / extraction
  abstention), returns a `RecoveryDecision` of
  `{different_url, escalate_adapter, request_review,
  abandon}`.
- Cost gates (codex important #9):
  - `max_recovery_iterations` per attempt = 3.
  - Per-objective daily cost cap (default $5).
  - Per-host daily cost cap (default $1).
  - Repeated-same-failure-signature hard stop after N=2.
  - Cheap-classifier-before-LLM: a deterministic classifier
    (status + body length + content-type heuristics) decides
    whether the failure is even worth LLM-classifying. Many failures
    are obvious and never reach the LLM.
- `AgentRunResult.recovery_trace`: typed `RecoveryTrace` describing
  the decisions, cost, and outcome.

**Acceptance**:

- Property test: an `AgentRunRequest` with budget N and a fixture
  host that fails first M attempts terminates with smallest M+k
  call count satisfying goal, where k ≤ `max_recovery_iterations`.
- Property test: the same failure signature recurring N=2 times
  triggers a hard-stop, even with budget remaining.
- Property test: cheap classifier short-circuits ≥80% of obvious
  failures (404/410 dead host) without calling LLM.
- Replay determinism: same input request + fixture store reproduces
  the same `RecoveryTrace`.
- Cost regression: nightly per-objective cost stays within ±20% of
  the prior 7-day median.

### Phase 6 — Live regression + production runtime backends

**Inputs**: phases 0–5.

**Capability cliff** (renamed per codex important #13): **V1
production spine gate**. Not "full production AI crawler" — the
target capability model includes graph intelligence, memory
intelligence, multi-agent operations, scale and reliability, export
and correction (`docs/09 §Capability Areas`). v2 covers V1 spine;
V2/V3 capability layers are out of scope.

**Deliverables**:

- 7+ live integration tests in `tests/integration/live/`:
  1. `httpbin.org/headers` — Chrome UA reaches origin.
  2. `httpbin.org/redirect-to` — redirect chain hop evidence.
  3. `example.com` — basic DOM + screenshot.
  4. Cooperative sitemap target — sitemap discovery + frontier.
  5. Cloudflare-protected demo URL — yields `AccessControlBlocked`
     cleanly (NOT evaded).
  6. eBay browse-by-keyword (official API).
  7. Amazon SP-API or product browser-rendered fallback under
     authorized session.
  8. Authorized-session live test (test API we control).
- `OtelObservabilityAdapter` wiring `runtime_support/observability.py`
  PRODUCTION mode to OTLP export.
- `PresidioPiiAdapter` wiring `runtime_support/security_privacy.py`
  PRODUCTION mode.
- DR live drill: real Postgres / Redis / S3 restore.
- Live failure classification per codex important #16:
  - Each red failure is tagged `external_target_drift` /
    `provider_outage` / `our_regression` / `flake`.
  - Quarantine for `flake` requires owner approval (no auto-rerun
    to green).

**Acceptance** (codex important #15 fix — metrics artifact schema
defined):

- Latency: per-fetch p95 ≤ 6s. **Measured** via
  `tests/integration/live/_artifacts/<run-id>/latency_histogram.json`
  conforming to `MetricsArtifactSchema` (input bins, count, p50,
  p95, p99).
- LLM cost: per-extraction p95 ≤ $0.01. **Measured** via
  `tests/integration/live/_artifacts/<run-id>/token_usage.json`
  with provider price table version pinned in the same artifact.
- Trace coverage: local OTLP collector receives spans whose tree
  depth matches recorded `agent.run.depth` event count.
- Charter compliance: a final boundary test scans the entire
  `src/` tree for the five forbidden stealth-script patterns and
  fails if any reappears.
- Three consecutive green nightly runs gate (codex important #16
  fix):
  - **Each red failure** must produce a typed category, replay
    repro outcome (`reproduces_locally` true/false), and artifact
    completeness check.
  - Greens require: deterministic replay pass + live canary pass.
  - Reds **never auto-quarantine**; a `flake` tag requires a
    PR-style owner approval recorded in the artifact bundle.

### 4.7 Parallelism map (corrected per codex important #14)

```
Phase 0 (contracts + exception hierarchy)
   │  must complete first; everyone consumes the new types
   ▼
Phase 1 (cooperative HTTP + browser)  ◄──── parallelizable with ────┐
   │                                                                 │
   ▼                                                                 │
Phase 2 (authorized session subsystem) ◄──── parallelizable with ───┤
   │                                                                 │
   ▼                                                                 │
Phase 3 (access control + escalation)                            Phase 4
   │   (depends on phase 1 transport + phase 2 sessions)         (LLM port v2 +
   │                                                              extraction)
   │                                                                 │
   ▼                                                                 │
Phase 5 (AI planning + recovery) ◄────── depends on phase 3 + phase 4
   │
   ▼
Phase 6 (live regression + production backends)
                requires every other phase complete
```

Corrections from v1:

- Phase 0 is the new mandatory serial milestone (codex important #14
  fix — Evidence/Attempt/AccessControl contracts must land before
  anything else).
- Phase 4 cannot start independently of phase 1 because LLM
  extraction inputs are `NetworkAttemptEvidence` (request/response
  headers redacted, anchors, screenshot ref) — those are phase 1
  deliverables, not P0-3 deliverables (codex important #14).
- Phase 2 and phase 4 can run in parallel after phase 0; each only
  consumes shared contracts.
- Phase 3 is the integration point; it cannot start until both
  phase 1 (transport) and phase 2 (sessions) are stable.

## 5. Pre-phase decision log (was open questions in v1)

The v1 design listed 6 open questions; codex minor #1 flagged them as
blocking architecture decisions agents would otherwise improvise. v2
closes them up front with default answers.

| v1 question | v2 default | Acceptance impact |
|-------------|-----------|-------------------|
| Multi-provider scope (Anthropic + Bedrock + Gemini together)? | OpenAI v2 + Anthropic in phase 4. Bedrock + Gemini are P1 follow-ups. Justification: Bedrock Converse diverges most from OpenAI Responses (tool use shape, structured-output enforcement, guardrails, stream events, region/credential model); proving the v2 contract on OpenAI + Anthropic before adding Bedrock keeps the contract clean. | Provider-swap test in phase 4 acceptance uses OpenAI ↔ Anthropic only. |
| `curl_cffi` switching policy? | **Removed.** Not in scope (charter). | n/a |
| `playwright-stealth` vs hand-rolled? | **Neither.** Not in scope (charter). | Charter regression test at phase 6. |
| Field-oracle ground truth source? | Tiered: Tier A manual gold (calibration), Tier B official-API weak labels with adjudication (coverage), Tier C cross-provider agreement explicitly **rejected** as ground truth. | Phase 4 acceptance uses Tier A for calibration metrics. |
| Rate limiter granularity? | Per-(origin, route class, adapter type). Route class is `listing / detail / search / api / file` per `docs/09 §Website Pattern Coverage`. AIMD with cooldown window + jitter; ceil = `max_concurrency_per_origin`; floor = strictest of `Retry-After` / `crawl_delay` / `request_rate`. | Phase 1 acceptance includes the property test on the AIMD curve. |
| Recovery-loop ownership? | **Agent runtime owns the loop**, but the next-action decision is encapsulated in `RecoveryPort`. Default `LLMBackedRecovery`; deterministic `HeuristicRecovery` for tests. | Phase 5 acceptance includes a deterministic-recovery property test. |

## 6. Risk register (expanded per codex important #12)

| Risk | Mitigation |
|------|-----------|
| Charter regression: an AI agent reintroduces stealth scripts because they "look helpful" | Charter regression test in phase 6 scans `src/` for the five forbidden patterns; CI reds; AGENTS.md and the v1 SUPERSEDED note keep the historical context discoverable. |
| Legal compliance — GDPR / customer ToS / robots / authorization | `RobotsPort` enforced systematically; `SessionScopePolicy` audited per credential use; HAR / screenshot retention policy (max 7 days for failed runs, encrypted at rest); withdrawal propagates per `docs/09 §Export And Correction`. |
| Prompt injection from extracted DOM | All extracted DOM content entering an LLM call passes through a `PromptInjectionSanitizer` that strips `<script>`, neutralizes anchor-based instructions, and adds a system-prompt fence reminding the model that the DOM is untrusted user input. The `RedactSensitiveProcessor` is applied to extraction context too. |
| Data poisoning — honeypot pages, SEO spam injecting fake records | Source-reputation signal per host (manual allowlist for V1 corpus + reputation table); extraction abstention required when the host is below reputation floor; crossover detection: a record claiming a price contradicting the source-of-record API by >20% is rejected with `ExtractionConflict`. |
| HAR / screenshot PII retention beyond redaction | Lifecycle policy: HAR encrypted with per-run key, stored in `EvidenceArtifactStorePort`, retention TTL 7 days for failed runs, 24h for successful runs, immediate purge on customer withdrawal. |
| Provider feature lock-in (OpenAI Responses API ↔ Anthropic ↔ Bedrock divergence) | `ModelProviderPort` v2 contract is the lowest-common-denominator + opt-in capability flags via `supports(capability: ModelCapability)`; provider adapters that don't support a capability return `False` and the agent runtime selects a different provider rather than hard-failing. |
| Live test flake vs regression confusion | Each live red yields a typed category (codex important #16); flakes need owner-approved quarantine, not auto-retry. |
| Authorized session credential leak via prompt / log / replay | Phase 2 negative tests cover prompt registry rejection, replay redaction, OutboxVaultClient `__repr__` returning a redacted token, and the `RedactSensitiveProcessor` boundary in `runtime_support/logging.py`. |
| Cost blow-up via recovery loop | Phase 5 cost gates: per-objective + per-host daily caps, repeated-failure hard stop, cheap classifier before LLM. Nightly cost regression test (±20% band). |
| Provider API breakage (OpenAI / Anthropic deprecates a field) | Provider-swap test in phase 4 acceptance; nightly live test per provider; adapter health check; v2 contract kept stable while adapter implementations adapt. |
| `runtime_support` PRODUCTION mode rolled out before backends ready | RuntimeMode (P0-8) defaults FIXTURE; phase 6 flips PRODUCTION only after `OtelObservabilityAdapter` / `PresidioPiiAdapter` / DR drill are green. |
| 24 worktrees in this repo diverging on master changes | Out of scope for this design; deployment / dev-loop concern. |

## 7. Acceptance criteria — V1 production spine gate

**Three consecutive green nightly runs**, where green requires:

- 100% pass on the live regression suite (8 tests above).
- 0 charter-regression test failures.
- 0 unredacted PII / credential / Authorization tokens in any
  emitted artifact.
- `field_oracle.calibration` metrics within bands:
  Brier ≤ 0.15, ECE ≤ 0.10, abstention PR-AUC ≥ 0.85.
- `field_oracle.coverage` ≥ 95% (Tier A + Tier B with adjudication).
- Per-fetch p95 latency ≤ 6s (per `latency_histogram.json` artifact).
- Per-extraction LLM cost p95 ≤ $0.01 (per `token_usage.json` with
  provider price table pinned).
- Token budget violations always raise `TokenBudgetExceeded`; never
  silent exhaustion.
- `VERACRAWL_RUNTIME_MODE=production` runs do not raise
  `ProductionRuntimeNotImplemented` for any path the live suite
  exercises.
- Trace coverage: local OTLP collector receives the spans the run
  declared.
- Reds **never auto-quarantine**; flakes require owner approval
  recorded in the artifact bundle.

These are the **V1 production spine gate** acceptance, not "full
production AI crawler" — the latter requires V2/V3 capability areas
beyond this design.

## 8. Backwards compatibility

- All new ports default to no-op or in-memory impls; the 1535+
  existing tests pass without configuration.
- `ModelProviderPort` v1 callers continue to work via a v2 adapter
  shim that maps v1 fields onto v2 surface; deprecation warning for
  one release.
- `set_context_payload` side-channel deprecated but functional for
  one release; boundary test forbids new uses.
- `NetworkAdapterError` and `ModelProviderError` classes unchanged;
  subclasses gain new mixins via multiple inheritance, every
  existing `except ValueError:` / `except RuntimeError:` continues
  to match.
- `source_coverage_gate` API surface unchanged for evidence
  evaluation; the new orchestration logic moves to a new
  `AdapterEscalationPort` (no caller of the existing gate is
  broken).

## 9. Observability & live-wiring (codex important #15 fix —
metrics artifact schema)

Every CI / live run emits a single `_artifacts/<run-id>/` directory
containing:

- `latency_histogram.json` — `MetricsArtifactSchema.LatencyHistogram`
  with bins, counts, p50/p90/p95/p99.
- `token_usage.json` — `MetricsArtifactSchema.TokenUsage` with
  per-provider input/output/cached tokens, provider price table
  version, total USD.
- `trace.json` — `MetricsArtifactSchema.TraceTree` with span tree;
  the local OTLP collector test asserts the same tree.
- `recovery_trace.json` — every `RecoveryDecision` taken with cost
  attribution.
- `evidence_index.json` — every `NetworkAttemptEvidence` ref + its
  on-disk path.
- `failure_classification.json` — typed category per failure
  (`external_target_drift` / `provider_outage` / `our_regression` /
  `flake`).

CI parses these artifacts and emits Pass/Fail per the §7 thresholds.
No threshold is a wall-clock or human estimate; each is a number in
a schema-defined artifact (codex important #15 fix).

## 10. Out of scope (V2/V3 capability layers)

Per `docs/09 §Capability Areas`, the following are NOT in this design:

- Site understanding (template / page-type classification, navigation
  inference)
- Adaptive frontier (failure-feedback / drift-aware retirement)
- Graph intelligence (canonical, redirect, citation, evidence,
  task, temporal graphs)
- Memory intelligence (cross-run memory, invalidation, replay)
- Multi-agent operations (Planner / SiteUnderstanding / Frontier /
  FetchAnalysis / Extractor / Verifier / Drift / Memory / Ops as
  separate agents)
- Drift and repair (template / selector / schema / content / graph
  drift detection)
- Review and operations (evidence viewer, replay console, review
  queue)
- Export and correction (downstream delivery, withdrawal
  propagation)
- Scale and resilience (sharded queues, autoscaling, chaos drills
  beyond DR)

Each is a separate target capability area; v3 production includes
them. v2 closes the V1 production spine.

## 11. Codex review iteration 1 mapping

Each finding from the v1 review and how v2 addresses it:

| Finding | Severity | v2 resolution |
|---------|----------|---------------|
| `source_coverage_gate` orchestration mixup | critical #1 | New `AdapterEscalationPort`; gate stays evaluative (§3.2, §3.3) |
| `ModelProviderPort` v2 contract migration plan absent | critical #2 | §3.5 v2 fields are optional, dispatch on presence; v1 callers shimmed; phase 0 contracts (§4.0) |
| Anti-bot direction violates safety boundary | critical #3 | §1.1 hard non-goals; v1's Phase 2 entirely removed; v2's Phase 2 is the authorized-session subsystem instead |
| Phase 1 capability cliff over-claim | critical #4 | §4.1 expanded deliverables: cross-redirect Authorization strip, conditional fetch, cookie jar scope, HAR PII via structured parser, AIMD with floor/ceil |
| Domain exception hierarchy breaks ValueError catch | critical #5 | §3.6 multiple-inheritance mixins; existing `except ValueError:` keeps matching |
| Rate limiter too coarse | important #6 | §4.1 + §5: per-(origin, route class, adapter type), AIMD with cooldown + jitter, floor = strictest of `Retry-After`/`crawl_delay`/`request_rate` |
| Fallback escalation triggers misfire | important #7 | §3.2 + §4.3: 401/403/404/410 are terminal, NOT browser-escalated; `AccessControlBlocked` routes to authorized session, not browser |
| Field-oracle ground truth undefined | important #8 | §5: tiered (gold / weak / rejected cross-provider); §4.4 calibration with Brier/ECE/abstention PR-AUC |
| Recovery cost gate too loose | important #9 | §4.5 cost gates: per-objective + per-host daily caps, repeated-failure hard stop, cheap classifier before LLM |
| Multi-provider scope un-justified | important #10 | §5: OpenAI v2 + Anthropic only; Bedrock / Gemini deferred with rationale |
| Prompt registry A/B workflow missing | important #11 | §3.5 + §4.4: PromptRegistryPort supports immutable version refs, experiment manifest, deterministic assignment by run/objective hash, shadow eval |
| Risk register missing core risks | important #12 | §6 expanded: charter regression, legal/GDPR, prompt injection, data poisoning, HAR PII lifecycle, provider lock-in, flake-vs-regression, authorized session leak |
| Phase 6 ≠ full production crawler | important #13 | Renamed to "V1 production spine gate"; §10 lists out-of-scope V2/V3 capabilities |
| Parallelism map errors | important #14 | §4.7 corrected: Phase 0 mandatory serial; Phase 4 depends on Phase 1 evidence contracts |
| Acceptance criteria not machine-verifiable | important #15 | §9 metrics artifact schema; §7 every threshold tied to a schema-defined artifact |
| 3-consecutive-green rule loose | important #16 | §7 + phase 6 §4.6: typed failure category, replay repro check, owner-approved quarantine for flakes |
| Baseline drift between design and code | important #17 | §2 baseline now verified against `master @ 096cd97` (P0 fix-pack merged); each row cites a path |
| Open questions all blocking | minor #1 | §5 pre-phase decision log; every v1 open question has a default answer + acceptance impact |
| Most likely to fail in prod | minor #2 | Resolved by §1.1 charter non-goals + §6 charter regression test; the v1-flagged failure mode (auto-escalate-to-stealth) is structurally impossible in v2 |
