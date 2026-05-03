# Feature Specification: Production Crawl Quality Benchmark Roadmap

**Feature Branch**: `057-production-quality-benchmark-roadmap`  
**Created**: 2026-05-03  
**Status**: Draft Roadmap Amendment  
**Input**: User request: "更大的真實網站 corpus、JS/browser crawl、多頁深爬、欄位級 oracle、precision/recall、repair success rate、成本/延遲/穩定性指標。請先落筆好specs"

## Purpose

This spec amends the post-037 production roadmap after spec 056. Specs 055 and
056 prove that VeraCrawl can run a small authorized public corpus and that real
LLM/model calls can participate in crawl planning, site understanding,
extraction candidate generation, and verification/repair through
framework-neutral ports. They do not yet prove production-grade crawl quality.

This roadmap fixes the next bounded spec set for proving production crawl
quality without allowing open-ended spec invention.

## Constitution Alignment

- **General-purpose crawler impact**: The roadmap expands quality validation
  across website types, navigation patterns, rendering modes, extraction schemas,
  repair cases, and operational metrics. It does not introduce single-site
  scraper logic or domain-specific parsing shortcuts.
- **Target/V1 boundary**: This is target architecture quality validation after
  rows 055 and 056. It does not weaken target architecture and does not mark
  production readiness until the aggregate release gate passes.
- **Evidence and replay impact**: Every planned spec must preserve source
  artifacts, content hashes, source anchors, evidence packets, verification
  decisions, command/event/outbox refs, model/agent/tool/context traces where AI
  is involved, and replay bundles.
- **Safety and policy impact**: Public crawling remains manifest-declared,
  allowlisted, robots-aware, private-network denied, rate-budgeted, read-only,
  and non-evasive. CAPTCHA solving, paywall bypass, login-wall circumvention,
  WAF evasion, stealth automation, and robots/terms bypass remain non-goals.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, `README.md`,
  and `specs/038-production-runtime-closure/spec.md`.

## Roadmap Rules

- **RR-001**: Specs 058-064 are the approved production crawl quality benchmark
  specs after spec 056.
- **RR-002**: No spec after 056 may claim production-grade crawl quality unless
  it is listed in this roadmap or this roadmap and `docs/08-build-roadmap.md`
  are amended first.
- **RR-003**: Quality claims must be metric-backed. "LLM participated" is not a
  substitute for evidence, oracle, precision/recall, repair, latency, cost, and
  stability results.
- **RR-004**: LLM/agent output may guide planning, extraction candidates, and
  repair decisions, but it must never be source evidence or a direct publication
  path.
- **RR-005**: Every planned quality spec must include positive fixtures,
  negative fixtures, replay tests, import-boundary tests where AI/browser
  adapters are involved, focused tests, full pytest, Docker-backed pytest, and
  real validation results recorded in that spec's `tasks.md`.
- **RR-006**: External website validation must be authorized, low-impact,
  robots/terms bounded, and resilient to drift through typed `needs_review` or
  failure diagnostics; fake success is forbidden.

## Approved Quality Specs

| Spec | Name | Purpose | Blocking Dependencies | Completion Gate |
| --- | --- | --- | --- | --- |
| 058 | Expanded Real-World Public Corpus Benchmark | Expand the real public corpus from a smoke test into a diverse quality corpus with website pattern coverage, origin budgets, drift handling, and public-corpus oracles. | 055, 056, 057 | `veracrawl-real-quality-corpus` runs an authorized quality-tier corpus with at least 40 public targets, 15 origins, and 10 website/source pattern families; observation, policy, artifact, hash, command/event/outbox, and replay refs gate pass. |
| 059 | JavaScript Browser Crawl Quality Benchmark | Prove browser rendering changes crawl quality when static HTTP is insufficient, while preserving sandboxing, prompt-taint, budget, and replay boundaries. | 043, 055, 056, 058 | `veracrawl-browser-quality-benchmark` passes only when JS-required targets produce browser DOM/screenshot/network/console/timing artifacts, source anchors, AI decision traces where used, and HTTP-only degradation evidence. |
| 060 | Multi-Page Deep Crawl Frontier Benchmark | Prove VeraCrawl can plan, execute, and replay bounded multi-page crawls across pagination, detail pages, canonicalization, duplicate suppression, and frontier prioritization. | 045, 050, 051, 052, 058, 059 | `veracrawl-deep-crawl-benchmark` crawls depth-limited public/fixture sites with frontier decisions, graph refs, page coverage oracles, duplicate/canonical controls, rate budgets, and replayable stop reasons. |
| 061 | Field-Level Oracle Extraction Benchmark | Move from coarse candidate existence to field-level extraction quality with schema-specific expected values, field anchors, normalization rules, and verification gates. | 046, 047, 048, 058, 060 | `veracrawl-field-oracle-benchmark` evaluates at least 8 schemas and 200 expected fields; every accepted field has source anchors, content hashes, evidence packet refs, normalized value refs, and typed mismatch diagnostics. |
| 062 | Precision Recall Quality Benchmark | Compute precision, recall, F1, false-positive, false-negative, unsupported-field, and abstention metrics from published outputs against field-level oracles. | 061 | `veracrawl-quality-metrics` publishes a metric report with corpus-level and per-pattern precision/recall/F1, confidence calibration, no direct LLM evidence, and release-blocking thresholds. |
| 063 | Repair Success Rate Benchmark | Measure crawl, extraction, verification, drift, and replay repair success under seeded failures without owner-service bypass or policy weakening. | 050, 061, 062 | `veracrawl-repair-quality-benchmark` runs seeded repair cases and reports repair success rate, attempts, model/tool traces, before/after evidence, rollback refs, unresolved escalation, and no unsafe repair bypass. |
| 064 | Cost Latency Stability Release Gate | Aggregate quality, cost, latency, throughput, token/call usage, retry behavior, and multi-run stability into the production crawl quality release decision. | 058-063 | `veracrawl-quality-release-gate` passes only when all prior quality benchmark reports exist, SLO/cost budgets are met, three-run stability is acceptable, replay is complete, and no false-ready status is emitted. |

## Activation Policy

When one of specs 058-064 is activated:

1. Keep its reserved spec number and directory.
2. Run Spec Kit specify, clarify, plan, tasks, implementation, analysis where
   available, and validation.
3. Record all real validation results in that spec's `tasks.md`.
4. Merge the activated spec before moving to the next blocking spec.
5. Do not weaken acceptance thresholds because of time, API cost, staffing, or
   implementation convenience.

## Non-Goals

- This roadmap spec does not implement runtime code.
- This roadmap spec does not claim production-grade crawl quality.
- This roadmap spec does not authorize unsafe crawling, evasive automation,
  CAPTCHA solving, paywall bypass, credential misuse, robots/terms bypass, or
  source evidence fabrication.

## Success Criteria

- **SC-001**: Specs 058-064 exist as planned spec files with fixed purpose,
  dependencies, functional requirements, non-goals, and measurable completion
  gates.
- **SC-002**: `docs/08-build-roadmap.md` and
  `specs/038-production-runtime-closure/spec.md` are amended to list specs
  057-064 and prevent ad hoc production quality spec creation.
- **SC-003**: `AGENTS.md` points the active Spec Kit context to this roadmap
  while quality specs are planned.
- **SC-004**: The planned specs explicitly distinguish current 056 capability
  from production-grade crawl quality acceptance.
