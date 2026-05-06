# Production-grade AI crawler — design document

| | |
|---|---|
| Status | DRAFT (pre-review) |
| Owner | _to fill_ |
| Date | 2026-05-07 |
| Supersedes | _none_ |
| Related plans | `docs/plans/p0-fix-pack/` (security & infra baseline, complete) |
| Anchor docs | `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md` |

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

Each phase ends with a runnable system. Stopping at phase N is fine —
it leaves a strictly better state than today.

### Phase 1 — crawler safety net (1.5–2 weeks)

Ship: BrowserContext reuse + storage_state, robots.txt + crawl_delay,
per-host token bucket, HAR capture, evidence headers (request +
response, redacted), live test fixtures (#1–#3 above). 5 commits, 50+
tests.

After phase 1: VeraCrawl can crawl polite / cooperative sites at
production rate without leaking sessions or losing fingerprints
between fetches.

### Phase 2 — anti-bot & TLS (1 week)

Ship: curl_cffi opt-in transport, additional stealth init scripts
(canvas / WebGL / hardware), Cloudflare 5s challenge handling,
DataDome / PerimeterX detection table, CAPTCHA escalation hook,
proxy_url plumbing through `HttpClientConfig` + `ProxyPort`. 4
commits, 30+ tests.

After phase 2: ≥80% of corpus targets unblock without proxy / solver.
Surfaces `AccessControlBlocked` cleanly when not.

### Phase 3 — adapter fallback chain (1 week)

Ship: real `source_coverage_gate` decision loop (official → HTTP →
browser), eBay token cache, Amazon pagination + token refresh, retry
budget per chain step. 3 commits, 25+ tests.

After phase 3: a single "fetch this product" call walks the chain
and produces the cheapest viable evidence.

### Phase 4 — LLM provider port v2 + extraction (1.5–2 weeks)

Ship: `ModelProviderPort` v2 with messages / tools / structured
output, OpenAI Responses adapter updated, Anthropic + Bedrock
adapters added, prompt registry (`PromptRegistryPort`), token /
cost outbox, real LLM-driven extraction in `schema_runtime.py`,
field-oracle eval against ground-truth corpus. 6 commits, 60+ tests.

After phase 4: extraction is no longer dictionary lookup; it is a
real LLM call with anchor-grounded citations and per-field
confidence.

### Phase 5 — AI planning + recovery (1.5 weeks)

Ship: frontier scoring wired to LLM signals, agent loop that picks
the next URL, recovery loop on typed failure, budget enforcement on
every step. 4 commits, 40+ tests.

After phase 5: the agent runtime drives the crawl rather than the
caller.

### Phase 6 — live regression + observability (1 week)

Ship: 7 live integration tests in nightly CI, OTel observability
adapter, presidio PII adapter, DR live drill. 4 commits, 15+ tests
(half are `@pytest.mark.live`).

After phase 6: nightly CI fails when an external target's anti-bot
posture shifts, when a provider regresses, or when latency / cost
trends move beyond their bands.

**Total**: 6 phases, ~6–8 calendar weeks for a single engineer, ~25
focused commits.

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
