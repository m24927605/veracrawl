# Phase 6 design supplement — Live regression + production runtime backends

## Status

| Field | Value |
|---|---|
| Phase | 6 (of 0..6) |
| Sub-steps | 5 (6.1, 6.2, 6.3, 6.4, 6.5) |
| Plan-review iter | drafted (JIT supplement) |
| Implementation status | NOT STARTED in this attempt — Phase 6 is the **production-deployment phase** that requires multi-day operational infrastructure (real API keys, OTLP collector, Postgres / Redis / S3, gold corpus authoring, three consecutive green nightly runs) outside this attempt's scope |
| Authoritative parent spec | `design.md` §4 Phase 6 |
| Depends on | Phase 0–5 (all building blocks) |

## Why

Phase 6 is the **V1 production spine gate** (`design.md`
§4 Phase 6 capability cliff). It composes the building
blocks from Phase 0–5 into a real production deployment +
the live regression suite that gates V1 release. This
supplement is the **scope-honesty** document recording why
Phase 6 cannot land in this attempt and what the deferred
work consists of.

The Phase 6 acceptance gate per `design.md` §7:

> **Three consecutive green nightly runs**, where green
> requires:
> - 100% pass on the live regression suite (8 tests above).
> - 0 charter-regression test failures.
> - Latency p95 ≤ 6s per fetch.
> - LLM cost p95 ≤ $0.01 per extraction.
> - Calibration: nightly Brier ≤ 0.15 on gold tier;
>   ECE ≤ 0.10; abstention precision-recall AUC ≥ 0.85.
> - Field oracle ≥95% gold coverage.

None of those are buildable in a single code-attempt
session. They require a deployed system, an operations team
authoring + adjudicating a gold corpus, and three nights of
clean nightly runs. The phase-by-phase reservations across
Phases 0–5 in `STATUS.md` already point at Phase 6 as the
landing zone for the corresponding operational acceptance
items.

## Sub-step breakdown

### 6.1 Production runtime backends

Wire the runtime-mode-gated production paths that previous
phases declared via ``ProductionRuntimeNotImplemented``:

* `OutboxRepositoryPort` → real Postgres-backed implementation.
* `EvidenceArtifactStorePort` → real S3 / encrypted-at-rest store.
* `OutboxBackedBudget._production_persist` → real outbox
  + idempotency.
* `CredentialUseAuditPort` → real outbox-backed writer.
* `OpenAIResponsesAdapterV2` / `AnthropicMessagesAdapter` →
  real network egress (PRODUCTION mode lifts the gate).
* `ModelProviderPortV2.complete` recovery dispatcher → real
  ``SchemaExtractionRuntime``-backed
  ``LLMBackedRecovery._llm_decision_fn``.
* `OtelObservabilityAdapter` → OTLP export.
* `PresidioPiiAdapter` → real PII redaction.

### 6.2 Charter regression test

Scan `src/` for the five forbidden stealth patterns from
`docs/09 §Safety Boundary`. Phase 1 sub-steps already
introduced placeholder boundary tests; Phase 6.2 hardens
them into a CI gate.

### 6.3 DR drill

Real Postgres / Redis / S3 restore drill. Validates that the
outbox + artifact store + cookie jar + budget audits all
restore consistently from a backup snapshot. Acceptance:
restore + replay reproduces a known run's
``LLMExtractionCandidate`` byte-for-byte.

### 6.4 Live regression suite (8 tests)

Per `design.md` §4 Phase 6:

1. `httpbin.org/headers` — Phase 1 step 1.6a (already DONE).
2. `httpbin.org/redirect-to` — Phase 1 step 1.6b (DONE).
3. `example.com` — Phase 1 step 1.6c (DONE).
4. Cooperative sitemap target.
5. Cloudflare-protected demo URL — yields
   `AccessControlBlocked` cleanly (NOT evaded).
6. eBay browse-by-keyword (official API).
7. Amazon SP-API or product browser-rendered fallback.
8. Authorized-session live test (test API we control —
   replaces the fixture-mode integration test from Phase 2
   step 2.5b).

Each red failure is tagged
``external_target_drift`` / ``provider_outage`` /
``our_regression`` / ``flake`` per the typed-category
protocol. Quarantine for ``flake`` requires owner approval.

### 6.5 Calibration corpus + nightly metrics

Author the Tier A gold corpus (~200 entries across V1
patterns). Fit Platt coefficients on the corpus. Wire the
nightly Brier / ECE / abstention precision-recall metrics
into the regression dashboard. Cost regression: per-extraction
p95 ≤ $0.01 measured via
``tests/integration/live/_artifacts/<run-id>/token_usage.json``
with provider price table version pinned.

This is also where the cheap-classifier corpus (Phase 5
step 5.4) gets its production data — measure ≥80% hit rate
on real failure shapes.

## Acceptance — phase level

The three-consecutive-green-nightly-runs gate (per
`design.md` §7) is the V1 production spine release
criterion. Phase 6 is "done" when:

- All 8 live tests pass on three consecutive nightly runs.
- Latency p95, LLM cost p95, calibration metrics, field
  oracle coverage all meet the published thresholds.
- Charter regression stays green.
- DR restore drill passes.
- 0 unaddressed reservations from Phases 0–5.

## Reservations (this attempt)

Every Phase 6 sub-step is deferred. The phase-by-phase
reservations across Phases 0–5 already point at the right
landing slot in Phase 6:

| Source | Sub-step assignment |
|---|---|
| Phase 1 step 1.2 high-concurrency DNS | 6.1 (production fetcher) |
| Phase 1 step 1.4 EvidenceArtifactStore production hardening | 6.1 |
| Phase 1 step 1.5 streaming-spool conditional cache | 6.1 |
| Phase 1 step 1.6a 304 round-trip live assertion | 6.4 |
| Phase 2 step 2.1 CredentialValue capability-secure hardening | 6.1 |
| Phase 2 step 2.4b outbox-writer transactionality | 6.1 |
| Phase 2 step 2.4b Phase1ComposedTransport mechanical enforcement | 6.1 |
| Phase 2 step 2.5b live test against controlled API | 6.4 |
| Phase 3 step 3.5b SP-API live integration | 6.4 |
| Phase 4 step 4.1 ModelCapability adapter-time additions | 6.1 / 6.5 |
| Phase 4 step 4.2 real OpenAI API + cost regression | 6.5 |
| Phase 4 step 4.3 multi-turn real-API + tool-call symmetric refusal | 6.5 |
| Phase 4 step 4.4 YAML migration + content-digest drift | 6.5 |
| Phase 4 step 4.5 real tokenizer + outbox transactionality | 6.1 |
| Phase 4 step 4.7 Platt fit path + isotonic | 6.5 |
| Phase 5 step 5.1 real LLM recovery dispatcher | 6.1 |
| Phase 5 step 5.2 persistent rolling-7-day caps | 6.1 |
| Phase 5 step 5.4 production cheap-classifier corpus | 6.5 |

This attempt's deliverable is therefore the **complete
building-block set** for Phase 6 to consume — every port,
every adapter, every contract surface that Phase 6
production wiring needs is in place and fixture-mode-tested
across Phases 0–5. Phase 6 itself is operational work that
the next attempt or release cycle picks up.
