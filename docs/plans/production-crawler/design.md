# Production-grade AI crawler — design document

| | |
|---|---|
| Status | **SUPERSEDED** by `docs/plans/production-authorized-source-crawler/design.md` |
| Reason | Phase 2 anti-bot direction (curl_cffi TLS impersonation, Cloudflare 5s challenge handling, stealth fingerprint expansion) violates `docs/09-target-capability-model.md` §Safety Boundary which forbids "WAF evasion, stealth automation, ban-avoidance proxy tactics". Codex review iteration 1 surfaced 5 critical + 11 important findings; the redesign starts from a charter-compliant frame. |
| Date | 2026-05-07 |
| Supersedes | _none_ |
| Related plans | `docs/plans/p0-fix-pack/` (security & infra baseline) |
| Anchor docs | `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md` |

> **DO NOT IMPLEMENT FROM THIS FILE.** It is kept for traceability so the
> codex review record (5 critical + 11 important + 2 minor findings) and
> the architectural lessons remain reachable. The successor design at
> `docs/plans/production-authorized-source-crawler/design.md` is the
> active source of truth.

---

## 1. Executive summary

VeraCrawl's hexagonal scaffolding is solid (ports, contracts, replay,
fixture suite) and the recent P0 fix-pack closed the most acute safety
gaps (RAW_RESPONSE_LEAK, tool-gateway rubber stamp, urllib transport,
fixture-only runtime). However a production crawler audit shows the
crawler stack itself sits at roughly **20% production readiness**, and
the AI integration is at roughly **15%** (one OpenAI provider, no
structured output, dictionary-based "extraction"). The remaining 80%
is concentrated in:

- anti-bot survival (Cloudflare / DataDome / PerimeterX / Akamai),
- session continuity (BrowserContext reuse, cookie warming),
- compliance (robots.txt + crawl_delay actually enforced),
- adapter fallback (official-API → browser → HTTP chain),
- AI-driven planning, extraction, verification, and recovery,
- live regression (zero `@pytest.mark.live` tests today).

This document specifies the target capability surface, the architectural
changes required to reach it, and a six-phase delivery plan that ships
useful capability at each phase boundary so the project can stop at any
phase with a stable, runnable system.

## 2. Goals & non-goals

**Goals**

- Cross every site in the V1 corpus (general-purpose static/HTML, sitemap,
  RSS, listing/detail) without per-site special-casing.
- Survive Cloudflare-class WAFs on at least 80% of corpus targets without
  CAPTCHA solver involvement; surface clean escalation hooks for the rest.
- Make every fetch attempt cost-bounded, replay-deterministic, and
  evidence-complete (HAR + headers + timing on disk for every attempt).
- Make extraction LLM-driven with anchor-grounded field provenance and
  per-field confidence, not dictionary lookup.
- Drive the next-URL decision via the AI agent loop the architecture
  already names (observe → think → act → verify), with token / call
  budget enforced at the gateway.
- Ship a real live regression suite that fails CI when an external
  target's anti-bot posture shifts under us.

**Non-goals**

- Solving residential proxy rotation, CAPTCHA solving, or paid
  unblocking services in-process. Surface escalation hooks and let
  deployment supply those.
- Replacing the contract / replay layer. The fixture suite is the
  correctness gold standard and stays.
- Building one-off scrapers for sites outside the V1 corpus.
- Solving multi-tenant isolation, billing, or auth (out of crawler scope).

## 3. Current state baseline

| Capability area | Done | Status |
|-----------------|------|--------|
| HTTP transport (httpx, retry, redirect SSRF) | P0-1 | ~60% |
| Browser stealth (UA + 5 init scripts + wait strategy) | P0-2 | ~25% |
| BrowserContext reuse + storage_state | — | 0% |
| Anti-bot (Cloudflare / DataDome / PerimeterX / Akamai) | — | ~5% |
| TLS / JA3 fingerprint | — | 0% |
| Robots.txt systematic enforcement | — | ~10% |
| Sitemap / RSS discovery | — | 0% |
| Per-host rate limit / token bucket | — | 0% |
| Proxy pool integration | — | 0% (stub) |
| Adapter fallback chain | — | 0% |
| HAR / headers in evidence | — | ~30% |
| LLM-driven extraction (anchor-grounded) | — | ~15% (dictionary lookup) |
| LLM-driven planning (frontier scoring) | — | ~10% (scoring exists, not wired) |
| LLM-driven recovery (blocked → alternative) | — | 0% |
| Multi-provider LLM (Anthropic / Bedrock / Gemini) | — | 0% (only OpenAI) |
| Structured output (json_schema + Pydantic) | — | 0% |
| Token / cost tracking (persistent outbox) | — | 0% (in-memory dict) |
| Field-oracle ground-truth eval | — | ~15% (fixture-vs-fixture) |
| Live integration tests | — | 0% (marker registered, 0 tests) |

Anchor docs claim a target architecture that exceeds this; the gap is
the surface this design closes.

## 4. Target capability model

### 4.1 Crawl loop (the AI part)

```
                 ┌─────────────────────────────────────────┐
                 │             AgentRunRequest              │
                 │  goal • corpus refs • cost budget        │
                 └────────────────────┬────────────────────┘
                                      ▼
              ┌─────────────────────────────────────────────┐
              │  observe   (fetch + evidence)                │
              │   - frontier picker                          │
              │   - HTTP / browser / official-API adapter    │
              │   - HAR + headers + screenshot evidence      │
              └─────────────────────┬───────────────────────┘
                                    ▼
              ┌─────────────────────────────────────────────┐
              │  think     (LLM reasoning)                   │
              │   - extract: anchor-grounded fields + conf   │
              │   - decide: next URL, escalate, or stop      │
              └─────────────────────┬───────────────────────┘
                                    ▼
              ┌─────────────────────────────────────────────┐
              │  act       (mutate the world)                │
              │   - tool gateway: allowlist + quota + audit  │
              │   - canonical command emit                   │
              └─────────────────────┬───────────────────────┘
                                    ▼
              ┌─────────────────────────────────────────────┐
              │  verify    (replay + ground-truth)           │
              │   - replay determinism check                 │
              │   - field oracle confidence floor            │
              │   - escalate to recovery on miss             │
              └─────────────────────────────────────────────┘
```

Each phase emits replay-bundle entries; the agent runtime owns the
loop, the adapters own I/O, the gateway owns mutations, the contracts
own evidence shape.

### 4.2 Adapter fallback chain

```
target URL
    │
    ▼  is the host covered by an authorized API adapter?
    ├── yes ──► OfficialAPIAdapter (eBay / Amazon SP-API / etc.)
    │                │           
    │                └─ on rate limit / outage:
    │                     fall through ───────────┐
    │                                              ▼
    └── no  ──► HTTPAdapter (httpx, real Chrome UA, retry, SSRF)
                     │
                     └─ on 403 / 429-with-no-Retry-After / WAF-detected /
                        body-too-small / known-blocklist:
                          escalate ──────────────┐
                                                  ▼
                                BrowserAdapter (Playwright + stealth +
                                 BrowserContext reuse + storage_state)
                                                  │
                                                  └─ on access-control-page:
                                                       emit AccessControlBlocked
                                                       (caller decides:
                                                        proxy rotate / cooldown /
                                                        give up)
```

Each step records evidence. The `source_coverage_gate` becomes the
arbiter: it knows the active escalation, the budget left for this run,
and the reason for the previous step's failure.

### 4.3 Stealth & TLS posture

- Browser: real Chrome UA + 5 init scripts (shipped) + canvas / WebGL /
  hardware-concurrency / device-memory / timezone / screen patches
  (this design adds), via `playwright-stealth` or hand-rolled init
  scripts; BrowserContext reuse keeps cookies, language headers, and
  WebGL-spoofed canvas-noise consistent across navigations within a
  run.
- HTTP: TLS / JA3 fingerprint via `curl_cffi` (Chrome impersonation),
  Accept-Language / Sec-Ch-Ua header set consistent with the chosen
  Chrome major version. The transport layer becomes pluggable so the
  default stays httpx (fast path) and curl_cffi is opt-in for
  fingerprint-sensitive hosts.
- Egress: optional proxy URL per `HttpClientConfig` (already a stub);
  rotation policy lives outside the adapter, in a `ProxyPort`
  implementation that the acquisition factory consults per run.

### 4.4 Compliance

- `robots.txt` is fetched once per host per run, parsed by
  `urllib.robotparser`, and enforced both at the initial URL and on
  every redirect. Same UA used for the robots check and the actual
  fetch (single source-of-truth UA per run).
- `crawl_delay()` and `request_rate()` feed the per-host token bucket.
- Sitemap discovery via `Sitemap:` directives in robots.txt; sitemap
  index recursion capped by `max_sitemap_urls`.
- RSS / Atom feeds via content-type sniff at the adapter layer.

### 4.5 Rate / concurrency

- Per-host token bucket sized from `crawl_delay` (or default 1 req / 2s
  for unknown hosts), with a global concurrency cap (default 16
  per-host, 64 global).
- Adaptive: a host returning 429 narrows its token bucket by half until
  10 successful requests at the new rate; 503 narrows by 4x and cools
  for 60s.
- Implemented as a `RateLimiterPort` that the acquisition layer consults
  before every fetch attempt.

### 4.6 Evidence

Every attempt writes:

- request method / URL / headers (Authorization / Cookie redacted via
  `RedactSensitiveProcessor` already shipped),
- response status / final URL / headers (same redaction),
- per-attempt elapsed_ms, attempt_number, failure_class,
- raw body artifact ref (existing) + content_digest (existing),
- HAR sidecar via Playwright tracing for browser observations.

Inline `NetworkAttemptEvidence` (per the original P0-1 v3 plan) lands
on `NetworkClientResult.attempt_evidences`. The artifact_store integration
(persisting evidence as ref-backed blobs) is staged separately so the
inline list ships first and the persistence wiring follows.

### 4.7 LLM integration

#### Provider port v2

```python
class ModelProviderPort(Protocol):
    def complete(
        self, request: ModelRequest, *, stream: bool = False
    ) -> ModelResponse: ...
    def supports(self, capability: ModelCapability) -> bool: ...
```

`ModelRequest` gains:
- `messages: list[Message]` (replaces the side-channel
  `set_context_payload`),
- `tools: list[ToolSpec] | None`,
- `tool_choice: ToolChoice | None`,
- `response_format: ResponseFormat | None` (json_schema + Pydantic
  class so the adapter validates returned text before handing back),
- `temperature`, `top_p`, `max_output_tokens`,
- `metadata: dict[str, str]` for cost-attribution.

`ModelResponse` gains:
- `parsed: BaseModel | None` (filled when response_format was
  json_schema and validation succeeded),
- `tool_calls: list[ToolCall]`,
- `usage: TokenUsage` (input / output / cached),
- `provider_request_id: str | None` (the upstream debugging anchor).

Adapters: OpenAI Responses API (shipped), Anthropic Messages API
(this design adds), Bedrock Converse (this design adds), Gemini
generateContent (this design adds). All four implement
`ModelProviderPort`; the agent runtime is provider-blind.

#### Cost / budget

- Per-run `TokenBudget` (input / output / cost USD) carried in
  `AgentRunRequest`.
- Adapters emit `TokenUsageEvent` to the project outbox after every
  successful call; an in-process aggregator decrements the run's
  remaining budget. Exceeding budget yields
  `TokenBudgetExceeded` (a `PolicyViolation` subclass — see §4.8).

#### Prompt registry

- Prompts live as versioned YAML files under `prompts/<role>/<name>.<vN>.yml`
  with explicit input schema, output schema (Pydantic class path),
  variable list, and changelog. The agent runtime resolves
  `prompt_template_ref` to a registry entry; provider adapters never
  see raw prompt strings.

#### Extraction

`schema_runtime.py` switches from "anchor-text → field" dictionary
lookup to a real LLM call:

1. Build a context bundle of DOM anchors + screenshots + URL.
2. LLM returns `ExtractionCandidate` with field values, citations
   (anchor refs the LLM grounded each field on), confidence, and
   per-field abstention reasons.
3. Adapter validates returned JSON against the field schema (Pydantic).
4. Field-oracle eval compares against the corpus's ground-truth set;
   confidence floors trigger escalation (re-extract with different
   prompt, re-fetch with browser, or abstain).

#### Planning / recovery

- Frontier scoring takes LLM signals
  (`url_pattern_score`, `anchor_text_score`, `page_title_score`,
  `semantic_similarity_score`) — most exist as fields today; this
  design wires them to a real scoring run rather than fixture values.
- Recovery loop: when an attempt yields a typed failure
  (`NetworkFailureType` / `AccessControlBlocked` / extraction
  abstention), the agent re-plans: pick a different URL, escalate
  the adapter (HTTP → Browser), or surface a request-for-review
  candidate. Cap the recovery depth at `max_recovery_iterations`
  (default 3) to bound cost.

### 4.8 Domain exception classes

Introduce three categories that callers can switch on:

- `RetryableError` — transient transport / rate limit; caller may
  retry under the same policy.
- `FatalError` — permanent (404, 410, dead host); abandon URL.
- `PolicyViolation` — budget exhausted, allowlist denied, schema
  validation failed, robots blocked.

`NetworkAdapterError` (shipped) and `ModelProviderError` (shipped) get
re-classified under this hierarchy in a follow-up commit.

### 4.9 Observability & live-wiring

- `runtime_support/observability.py` wires to a real OTel SDK
  (`opentelemetry-sdk` + `opentelemetry-exporter-otlp`), exporting
  spans / metrics / logs over OTLP. Existing `TraceSpan` / `MetricSample`
  / `AlertRecord` models become the in-process shape; the gate flips
  from "scenario lookup" to "real export attempt" when
  `RuntimeMode.PRODUCTION` (already shipped).
- `runtime_support/disaster_recovery.py` adds a real Postgres / Redis /
  S3 restore drill (live test only); fixture mode unchanged.
- `runtime_support/security_privacy.py` adds a real PII scrubber pass
  using `presidio-analyzer` + `presidio-anonymizer` for live mode.

### 4.10 Live regression

- `tests/integration/live/test_real_world_corpus.py` runs in the
  nightly CI workflow and exercises:
  1. `httpbin.org/headers` — Chrome UA reaches origin, proves transport
     fingerprint OK.
  2. `httpbin.org/redirect-to` — redirect chain recorded with hop
     evidence.
  3. `example.com` — basic DOM + screenshot.
  4. A Cloudflare-protected demo URL — passes 5s challenge or surfaces
     `AccessControlBlocked` cleanly.
  5. eBay browse-by-keyword — official API adapter returns ≥1 product
     within budget.
  6. Amazon SP-API or product-page browser fallback — within budget.
  7. End-to-end: query "cordless drill" → product candidates → top-1
     extraction → field oracle confidence ≥ 0.8 on price + title.
- Failures upload artifacts (HAR + screenshot + extraction trace).
- Skipped under `pytest -m "not live"` (the default CI job already
  shipped in P0-6).

## 5. Architectural changes

### 5.1 New ports

| Port | Purpose | Default impl |
|------|---------|--------------|
| `ProxyPort` | rotate proxy URL per request | `NoProxyAdapter` (returns None) |
| `RateLimiterPort` | per-host token bucket | `InMemoryTokenBucket` |
| `RobotsPort` | parse + cache robots.txt | `UrllibRobotsParser` |
| `SitemapPort` | discover URLs via sitemap | `XmlSitemapParser` |
| `PromptRegistryPort` | resolve prompt_template_ref | `YamlPromptRegistry` |
| `TokenBudgetPort` | per-run budget tracking | `OutboxBackedBudget` |

### 5.2 New adapters

| Adapter | Replaces / extends |
|---------|-------------------|
| `CurlCffiSourceAdapter` | optional fingerprint-sensitive HTTP path |
| `AnthropicMessagesAdapter` | new |
| `BedrockConverseAdapter` | new |
| `GeminiAdapter` | new |
| `OtelObservabilityAdapter` | wires `runtime_support/observability.py` |
| `PresidioPiiAdapter` | wires `runtime_support/security_privacy.py` |

### 5.3 Contract additions

- `Message`, `ToolCall`, `ToolSpec`, `ResponseFormat`, `TokenUsage`,
  `TokenBudget`, `ExtractionCandidate`, `FieldCitation`,
  `AccessControlBlocked`, `NetworkAttemptEvidence` — added to
  `contracts/agent.py` and `contracts/network.py` per the
  consolidations already shipped.

### 5.4 Backwards compatibility

- All new ports have default implementations that match today's
  behavior (NoProxy, no-op rate limiter, missing-robots passes
  through, etc.) so the 1500+ existing tests continue to pass.
- `ModelProviderPort` v2 is a strict superset of v1 by adding optional
  fields; the existing OpenAI adapter is updated to fill them. The
  side-channel `set_context_payload` is deprecated but kept for one
  release.
- Hexagonal boundary is preserved: every new dependency lives in
  `adapters/`. The agent runtime / domain layer never imports
  Anthropic, Bedrock, OTel, or curl_cffi.

## 6. Phased delivery

VeraCrawl is implemented by AI agents; throughput is not a planning
constraint. Phases are **dependency-ordered capability cliffs**, not
effort estimates. Each phase ends with a runnable system whose
acceptance criteria can be machine-verified, so stopping at phase N
leaves a strictly better state than today and the work to date is
never thrown away.

The phase boundaries answer two questions:

1. *What does phase N+1 require from phase N?* (the dependency edge)
2. *What capability does the system gain when phase N closes?* (the
   cliff)

If a phase's acceptance criteria pass while phase N+1 is in flight,
that is fine — phases may run in parallel where their dependency
graphs allow it (see §6.7 below).

### Phase 1 — crawler safety net

**Inputs**: P0 fix-pack already on main (httpx transport, structured
logging, RuntimeMode, scoped tool gateway).

**Capability cliff**: VeraCrawl can crawl polite / cooperative sites
at production rate without leaking sessions or losing fingerprints
between fetches; every attempt produces full evidence (HAR + headers,
both redacted) and respects per-host crawl delay.

**Deliverables**:

- BrowserContext reuse + per-run `storage_state.json` persistence in
  `PlaywrightBrowserObservationAdapter`.
- `RobotsPort` (default `UrllibRobotsParser`) — fetch once per host
  per run, parse, enforce on initial URL and every redirect target,
  feed `crawl_delay()` to the token bucket.
- `RateLimiterPort` (default `InMemoryTokenBucket`) — per-host
  bucket sized from `crawl_delay` or default 1 req / 2s, plus a
  global concurrency cap.
- HAR capture via Playwright tracing on every browser observation,
  written to the artifact store as a sidecar.
- Evidence: request and response headers (redacted via the
  `RedactSensitiveProcessor` already shipped in P0-5), per-attempt
  `elapsed_ms`, attempt_number, attached as
  `NetworkAttemptEvidence` on `NetworkClientResult`.
- Live tests #1–#3 in §4.10 (httpbin.org/headers,
  httpbin.org/redirect-to, example.com).

**Acceptance**:

- `pytest -m live -k phase1` 100% green on three consecutive nightly
  runs.
- Boundary test: redirect to a host outside the egress allowlist is
  rejected at the adapter (existing per-hop check) **and** logged with
  the `RobotsPort` decision when robots.txt forbids the path.
- Property test: a 100-fetch run against a single fixture host respects
  `crawl_delay=2s` to within 100ms of expected wall time.
- HAR sidecar present on disk for every browser observation; HAR
  contains zero `Authorization` / `Cookie` plaintext (regex check).

### Phase 2 — anti-bot & TLS

**Inputs**: phase 1 (`HttpClientConfig`, `RateLimiterPort`,
`RobotsPort` are stable).

**Capability cliff**: ≥80% of the V1 corpus unblocks without
residential proxy or paid solver; the remaining ≤20% surface
`AccessControlBlocked` with a typed reason that the deployment can
hand off to its escalation backend.

**Deliverables**:

- `CurlCffiSourceAdapter` (opt-in transport behind a per-host
  selector; default stays httpx).
- Stealth bundle expansion: canvas noise, WebGL vendor / renderer,
  hardware concurrency, device memory, timezone consistency, screen
  resolution. Decision: vendor `playwright-stealth` vs hand-rolled
  scripts is one of the open questions in §9 — both ship behind the
  same `stealth_init_scripts` constructor kwarg already in place.
- `AccessControlDetector` table covering Cloudflare 5s interstitial,
  Cloudflare Turnstile, DataDome, PerimeterX, Akamai. On match the
  adapter raises `AccessControlBlocked(vendor=..., url=..., evidence_ref=...)`.
- `ProxyPort` plumbed through `HttpClientConfig`; default
  `NoProxyAdapter` returns `None` so existing call sites unchanged.

**Acceptance**:

- Live test #4 (Cloudflare-protected demo URL) yields either
  successful navigation **or** `AccessControlBlocked` with
  `vendor="cloudflare-turnstile"` and a non-empty evidence ref.
- Per-host curl_cffi switch flips for at least one corpus target whose
  httpx fingerprint was previously blocked, verified by before / after
  status code in the live trace.
- Stealth detection benchmark: a fixture page that probes every
  stealth-checked surface returns "human-like" on ≥90% of probes.

### Phase 3 — adapter fallback chain

**Inputs**: phase 2 (escalation reasons are typed and the new TLS
adapter exists).

**Capability cliff**: a single "fetch this product" call walks
official-API → HTTP → browser, picks the cheapest viable adapter,
and produces unified evidence regardless of which adapter ultimately
served the response.

**Deliverables**:

- `source_coverage_gate` rewritten as a real decision loop, not a
  ref aggregator. Inputs: `AdapterEscalationPolicy`, prior attempt
  evidence, run budget. Output: next adapter to try or terminal
  failure.
- eBay OAuth token cache (file-backed, TTL'd, locked for concurrent
  runs); covers the 2× rate-limit burn the audit flagged.
- Amazon SP-API pagination, token refresh on 401 once per run,
  partial-batch tolerance (one row failing does not fail the batch).
- Per-chain-step retry budget so a runaway browser fallback cannot
  consume more than its share.

**Acceptance**:

- Property test: for any sequence of typed failures from adapter A,
  the chain picks adapter B per `AdapterEscalationPolicy` and the
  budget left is monotonically non-increasing.
- Live test #5 (eBay browse-by-keyword) returns ≥1 product within
  `RunBudget(calls=10, cost_usd=0.05)`.
- Replay determinism: a recorded chain run replayed against the
  fixture store reproduces the same final adapter and the same
  evidence digest.

### Phase 4 — LLM provider port v2 + extraction

**Inputs**: P0-3 OpenAI adapter (already migrated to httpx + retry).

**Capability cliff**: extraction is no longer dictionary lookup; it
is a real LLM call with anchor-grounded citations, per-field
confidence, and Pydantic-validated structured output. The agent
runtime is provider-blind; swapping OpenAI for Anthropic happens
through the adapter registry.

**Deliverables**:

- `ModelProviderPort` v2 (messages / tools / response_format /
  streaming / token usage). The `set_context_payload` side-channel is
  deprecated but kept for one release.
- Updated OpenAI Responses adapter to fill the v2 surface.
- New adapters: `AnthropicMessagesAdapter`, `BedrockConverseAdapter`.
  Gemini is staged depending on §9 question (1).
- `PromptRegistryPort` resolving `prompt_template_ref` to versioned
  YAML files under `prompts/<role>/<name>.<vN>.yml`. Provider adapters
  see only resolved messages, never raw template strings.
- `TokenBudgetPort` backed by the project outbox; per-run
  `TokenBudget` decremented by a `TokenUsageEvent` aggregator.
  Exceeding budget raises `TokenBudgetExceeded` (subclass of
  `PolicyViolation`).
- `schema_runtime.py` rewritten to call the LLM with a context bundle
  (DOM anchors + screenshot ref + URL) and return
  `ExtractionCandidate` (field values + per-field
  `FieldCitation` + per-field `confidence` + abstention reasons).
- `field_oracle` regression suite comparing extraction output against
  a ground-truth corpus (source decided in §9 question 4).

**Acceptance**:

- Provider-swap test: the same `AgentRunRequest` resolved against
  OpenAI vs Anthropic produces results that pass the same field-
  oracle confidence floor.
- Structured output validation: a deliberately malformed mock
  response does not bypass the Pydantic gate; the adapter raises
  `StructuredOutputViolation`.
- Token-budget property: a recorded run that exhausts the budget
  raises `TokenBudgetExceeded` exactly once and the outbox event
  total matches the budget cap.
- Field-oracle: ≥95% of corpus products meet `confidence ≥ 0.8`
  on price + title fields.

### Phase 5 — AI planning + recovery

**Inputs**: phase 4 (the agent loop has a real LLM that can return
structured decisions).

**Capability cliff**: the agent runtime — not the caller — drives
the crawl. Given a goal and a corpus, the runtime picks URLs,
escalates adapters, and recovers from typed failures, all under a
declared budget.

**Deliverables**:

- Frontier scoring wired to LLM signals via the now-real provider
  port; the existing `RuntimeFrontierOptimizationDecision`
  dataclass becomes the agent's actual planning output.
- Recovery loop: on a typed failure (NetworkFailureType /
  AccessControlBlocked / extraction abstention), the agent re-plans
  one of {different URL, escalate adapter, request review,
  abandon}. Capped by `max_recovery_iterations` (default 3).
- Budget enforcement on every loop iteration through the gateway.
- `AgentRunResult` carries a typed `RecoveryTrace` describing the
  decisions taken.

**Acceptance**:

- Property test: an `AgentRunRequest` with a budget of N calls and
  a fixture host that fails on the first M attempts terminates with
  the smallest M+k call count that satisfies the goal, where k ≤
  `max_recovery_iterations`.
- Replay determinism: the same input request + fixture store
  reproduces the same `RecoveryTrace`.
- A blocked Cloudflare path correctly escalates HTTP → Browser
  exactly once before raising `AccessControlBlocked`.

### Phase 6 — live regression + observability

**Inputs**: phases 1-5 (everything that the live tests must
exercise is implemented).

**Capability cliff**: nightly CI fails when an external target's
anti-bot posture shifts, when a provider regresses, or when latency
/ cost trends move outside their bands. Production runtime gates
(observability / DR / security_privacy) emit real telemetry.

**Deliverables**:

- 7 live integration tests in `tests/integration/live/` (per §4.10).
- `OtelObservabilityAdapter` wiring `runtime_support/observability.py`
  to OTLP export (production mode flips from `NotImplementedError` to
  real SDK calls).
- `PresidioPiiAdapter` wiring `runtime_support/security_privacy.py`
  to a real PII scrubber for production mode.
- Real DR drill (live test only) against a Postgres / Redis / S3
  triple; fixture mode unchanged.

**Acceptance**:

- 100% green on the live regression suite for three consecutive
  nightly runs.
- OTel exporter actually receives spans on a local collector under
  test; trace tree depth matches the agent loop depth in the run.
- DR live test demonstrates RPO / RTO within target bands documented
  in `docs/02-production-architecture.md`.

### 6.7 Parallelism map

The phases are dependency-ordered, but several do not strictly require
the previous one to be complete before they begin:

```
Phase 1 ──────┬─► Phase 2 ──┬─► Phase 3 ─┐
              │              │            │
              └─► Phase 4 ───┴─► Phase 5 ─┴─► Phase 6
```

- Phase 4 (LLM provider v2 + extraction) only depends on the
  contracts touched by P0-3, not on phase 1's transport changes —
  agents may begin phase 4 in parallel with phase 1.
- Phase 2 (anti-bot) and phase 3 (adapter chain) share only typed
  failure classes; they can also be parallelized once those
  classes land.
- Phase 5 (AI planning) is the first hard serial dependency: it
  requires phase 4's real LLM and phase 3's typed failures.
- Phase 6 (live regression) is the only phase that requires every
  other phase complete because its acceptance criteria exercise
  every layer.

## 7. Acceptance criteria

The system is "production AI crawler" when **every one of these holds
on three consecutive nightly runs**:

- live regression suite passes 100%, including 1 Cloudflare-protected
  target and the eBay-or-Amazon end-to-end flow;
- zero `RAW_RESPONSE_LEAK` / `UNREDACTED_HEADER` / `UNAUTHORIZED_TOOL`
  audit events;
- field-oracle confidence ≥ 0.8 on price + title for ≥ 95% of corpus
  products;
- 95th-percentile per-fetch latency ≤ 6s, per-extraction LLM cost ≤
  $0.01;
- budget violations always raise `PolicyViolation`, never silently
  exhaust;
- `VERACRAWL_RUNTIME_MODE=production` runs do not raise
  `ProductionRuntimeNotImplemented` for any path the live suite
  exercises;
- `pytest -m "not live"` covers every non-live behavior without
  hitting the network.

## 8. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Cloudflare / DataDome change detection patterns | Live regression catches it nightly; `AccessControlBlocked` escalation hook lets deployment swap solver without code change. |
| LLM cost blow-up during extraction | `TokenBudget` enforced per run; `field_oracle` regression catches prompt drift before it ships. |
| Provider API breaks (OpenAI / Anthropic) | Multi-provider adapters; nightly live test covers each provider; `AssistantRequestId` preserved for upstream support tickets. |
| Stealth patches detected by future WAF release | Stealth scripts isolated in `_stealth.py`; can swap for `playwright-stealth` / `patchright` without changing the adapter interface. |
| Session state in `storage_state.json` leaks between users | Per-run storage_state path enforced via `RunContext`; a dedicated cleanup gate runs at end of each agent run. |
| robots.txt outage breaks crawls | Cached robots.txt with TTL; on cache miss + 5xx, fail closed (skip the host until next nightly refresh). |

## 9. Open questions

1. Do we ship Anthropic + Bedrock + Gemini together in phase 4, or
   ship Anthropic alone and stage Bedrock / Gemini to phase 7?
2. `curl_cffi` is opt-in; what is the policy for *deciding* to switch
   transports per host? Heuristic table, LLM hint, or static config?
3. `playwright-stealth` vs hand-rolled scripts — accept the dep or
   stay vendor-free?
4. Field-oracle ground-truth source — manual gold set, weak labels
   from official APIs, or synthetic via cross-provider agreement?
5. Is the rate-limiter per-host or per-(host, path-pattern)? The
   latter handles "search" vs "detail" routes differently.
6. Where does the recovery loop live — agent runtime, or a dedicated
   `RecoveryPort` that the agent calls on typed failure? Both have
   precedent in the current codebase.

## 10. References

- `docs/01-product-definition.md`
- `docs/02-production-architecture.md`
- `docs/06-agent-system-design.md`
- `docs/07-data-contracts.md`
- `docs/08-build-roadmap.md`
- `docs/09-target-capability-model.md`
- `docs/10-target-implementation-design.md`
- `docs/11-target-testing-and-acceptance.md`
- `docs/plans/p0-fix-pack/STATUS.md`
- VeraCrawl repo `AGENTS.md` (Hard Constraints, Python And Agent Framework Boundary)
