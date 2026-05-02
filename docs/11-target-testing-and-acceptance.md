# Target Testing And Acceptance

This document defines how VeraCrawl target architecture capability is tested and accepted. It exists to prevent vague claims, partial demos, or false completion.

## Testing Principles

- Test target capabilities, not just happy paths.
- Acceptance must prove implementation, replay, policy, evidence, security, observability, and recovery.
- A feature without automated tests is not target-ready.
- A feature without replay evidence is not target-ready.
- A feature without operational signals is not production-ready.
- Benchmarks must include synthetic local fixtures so tests are deterministic.
- External websites may supplement tests, but cannot be the only acceptance proof.

## Test Suite Layers

| Layer | Purpose | Examples |
| --- | --- | --- |
| Unit tests | Validate cohesive domain rules | ID rules, state transitions, evidence coverage validation |
| Contract tests | Validate schemas, ports, events, commands, and adapter boundaries | AgentToolSpec, SourceAdapterSpec, CommandEnvelope, GraphBuildManifest |
| Adapter tests | Validate concrete integrations through ports | Postgres repo, object store, queue, browser engine, model provider |
| Integration tests | Validate cross-package flows without full production scale | objective-to-plan, fetch-to-snapshot, candidate-to-output |
| End-to-end tests | Validate user-visible workflows | approved plan to published output and replay report |
| Replay tests | Reconstruct decisions and outputs from recorded events and artifacts | run replay, projection rebuild, agent trace replay |
| Evidence tests | Verify every published output has source-backed evidence | raw-to-normalized anchor checks, coverage maps |
| Policy tests | Verify scope, rate, budget, credentials, prompt taint, and publication gates | blocked source report, credential redaction |
| Security tests | Verify sandbox, egress, prompt injection, secret handling, artifact privacy | SSRF denial, DNS rebinding defense, prompt injection fixture |
| Memory tests | Verify scoped retrieval, freshness, invalidation, and evidence backrefs | stale memory exclusion, current evidence re-anchor |
| Graph tests | Verify graph build, rebuild, quality metrics, and graph-influenced explanations | URL graph, entity graph, temporal projection |
| Chaos tests | Verify crash/retry/resume and partial failure recovery | worker crash, orphan artifact, projection lag |
| Load tests | Verify fairness, backpressure, queue behavior, and storage growth | high-volume site, mixed small/large jobs |
| Operations tests | Verify dashboards, alerts, quality reports, and runbooks | cost anomaly, drift alert, failed export |

## Synthetic Benchmark Sites

Target acceptance requires a local deterministic benchmark suite. Each fixture must run in CI and emit stable HTML, feeds, documents, redirects, failures, or browser behavior.

| Fixture | Required coverage |
| --- | --- |
| static-basic | linked pages, canonical URLs, records, tables, facts |
| sitemap-rss | sitemap discovery, RSS freshness, feed deltas |
| listing-detail | listing/detail pages, pagination, duplicate details, canonical handling |
| js-rendered | JavaScript-rendered DOM, delayed content, screenshot/DOM artifacts |
| forms-search | bounded search and non-destructive form interactions |
| auth-scoped | scoped credentials, session expiry, redaction, audit |
| documents | PDF/HTML document metadata, extracted text anchors, file lifecycle |
| api-like | structured endpoint discovery and provenance |
| drifted-site | selector change, template change, missing field, repair workflow |
| conflicting-facts | contradictory evidence, conflict record, review/adjudication |
| prompt-injection | malicious page instructions, secret request, tool misuse attempt |
| blocked-source | robots/terms/scope denial and blocked-source reporting |
| high-volume | large frontier, queue fairness, backpressure, retry, dedup |
| multilingual | language metadata and language-aware field extraction |
| export-withdrawal | delivery receipt, correction, withdrawal propagation |

## Benchmark Fixture Contract

Every benchmark fixture must include a manifest:

```yaml
BenchmarkFixtureManifest:
  id: string
  name: string
  profile_refs: list
  source_server_ref: string
  seed_urls: list
  source_adapter_refs: list
  auth_fixture_ref: string
  expected_crawl_graph_ref: string
  expected_page_type_ref: string
  expected_output_ref: string
  expected_evidence_coverage_ref: string
  expected_event_sequence_ref: string
  expected_replay_bundle_ref: string
  expected_artifact_hashes_ref: string
  failure_injection_ref: string
  thresholds_ref: string
```

Deterministic fixture layout:

```text
tests/fixtures/<fixture_id>/
  manifest.yaml
  source/
    server.yaml
    public/
    auth/
    documents/
    api/
  oracles/
    expected_outputs.yaml
    expected_events.yaml
    expected_graph.yaml
    expected_evidence.yaml
    expected_replay.yaml
    thresholds.yaml
    failure_injection.yaml
  artifacts/
    expected_hashes.yaml
  README.md
```

Fixture runner contract:

```text
veracrawl-fixture run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

Runner requirements:

- starts deterministic local fixture servers and auth stubs
- writes all generated artifacts under `.veracrawl-test-runs/<fixture_id>/`
- compares exact values by canonical JSON serialization
- compares normalized text by whitespace/case rules declared in the fixture
- compares tolerance values only when `comparison_mode: tolerance` and threshold fields are explicit
- validates event cursors, replay bundle, artifact hashes, graph oracle, evidence oracle, and output oracle
- exits non-zero on any missing required oracle or undeclared tolerance

Target runtime spine fixture contract:

```text
veracrawl-runtime run tests/fixtures/<runtime_fixture_id> --profile target --out .veracrawl-test-runs/<runtime_fixture_id>
```

Required runtime spine fixtures:

| Fixture | Required acceptance |
| --- | --- |
| runtime-record-success | approved objective reaches published output, output manifest, and replay-complete report |
| runtime-blocked-source | source policy denial produces blocked result and no publication |
| runtime-missing-evidence | missing field evidence produces needs-review and no publication |
| runtime-verification-conflict | verification conflict produces conflict status and no publication |
| runtime-adapter-mismatch | invalid adapter natural-result mapping fails before publication |
| runtime-replay-gap | missing replay refs fail publication gate |
| runtime-boundary-violation | wrong-owner mutation is rejected and evented |

Runtime spine acceptance requires:

- `veracrawl-contracts validate --format json` reports no registry errors
- `pytest tests/contract/test_runtime_contract_registry.py`
- `pytest tests/contract/test_runtime_command_event_contracts.py`
- `pytest tests/contract/test_runtime_import_boundaries.py`
- `pytest tests/contract/test_agent_recommendation_contracts.py`
- `pytest tests/unit/test_runtime_completion_gates.py`
- `pytest tests/unit/test_evidence_publication_gates.py`
- `pytest tests/unit/test_runtime_replay_validation.py`
- `pytest tests/integration/test_objective_to_output_runtime.py`
- `pytest tests/integration/test_runtime_negative_fixtures.py`

The runtime spine is accepted only as the executable target architecture spine. It
must not be described as full crawler completion until browser, graph, memory,
export, distributed persistence, queueing, operational recovery, and production
scale acceptance suites are implemented and pass.

Durable runtime and scheduler fixture contract:

```text
veracrawl-durable run tests/fixtures/<durable_fixture_id> --profile target --out .veracrawl-test-runs/<durable_fixture_id>
```

Required durable fixtures:

| Fixture | Required acceptance |
| --- | --- |
| durable-runtime-success | durable command, event cursor, outbox, artifact, frontier, lease, and recovery refs reload with `pass` |
| durable-duplicate-command | duplicate command returns original result and does not duplicate event or outbox records |
| durable-event-gap | event cursor gap is detected and recovery fails |
| durable-pending-outbox | pending outbox is visible and recovery requires review |
| durable-stale-lease | expired lease is retry-visible and recovery requires review |
| durable-invalid-lease | wrong lease token is rejected and recovery fails |
| durable-missing-artifact | missing artifact ref blocks durable recovery |

Durable scheduler acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_durable_contract_registry.py`
- `pytest tests/contract/test_durable_ports_and_boundaries.py`
- `pytest tests/contract/test_scheduler_contracts.py`
- `pytest tests/unit/test_durable_command_idempotency.py`
- `pytest tests/unit/test_durable_event_outbox.py`
- `pytest tests/unit/test_scheduler_leases.py`
- `pytest tests/unit/test_durable_replay_recovery.py`
- `pytest tests/integration/test_durable_runtime_persistence.py`
- `pytest tests/integration/test_durable_negative_fixtures.py`

This acceptance proves deterministic durable and scheduler semantics only. It does
not prove production persistence adapters, distributed queueing, browser crawling,
graph/memory intelligence, export delivery, or production scale readiness.

Source adapter and fetch runtime fixture contract:

```text
veracrawl-source run tests/fixtures/<source_fixture_id> --profile target --out .veracrawl-test-runs/<source_fixture_id>
```

Required source acquisition fixtures:

| Fixture | Required acceptance |
| --- | --- |
| source-http-success | HTTP-family adapter result produces fetch result, page snapshot, raw artifact ref, scheduler completion, and replay-complete report |
| source-sitemap-success | sitemap-family adapter result produces discovered-link result lineage and replay-complete report |
| source-rss-success | RSS-family adapter result produces discovered-link result lineage and replay-complete report |
| source-api-success | API-like adapter result produces API payload lineage and replay-complete report |
| source-document-success | document-source adapter result produces document artifact lineage and replay-complete report |
| source-blocked | source policy denial produces blocked-source failure and no raw artifact claim |
| source-rate-limited | rate limit decision produces needs-review operator-visible status with retry-after lineage |
| source-adapter-mismatch | adapter natural-result mismatch is rejected before acquisition is marked complete |
| source-malformed-response | malformed response is typed as malformed and fails acquisition without publication claim |
| source-retry-exhausted | exhausted retry lineage is reported as failed acquisition |
| source-missing-artifact | missing raw artifact ref fails replay completeness and records missing artifact status |

Source acquisition acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_source_acquisition_contract_registry.py`
- `pytest tests/contract/test_source_adapter_runtime_contracts.py`
- `pytest tests/contract/test_source_adapter_import_boundaries.py`
- `pytest tests/unit/test_source_policy_and_retry_gates.py`
- `pytest tests/unit/test_source_replay_recovery.py`
- `pytest tests/integration/test_source_acquisition_runtime.py`
- `pytest tests/integration/test_source_negative_fixtures.py`

This acceptance proves deterministic source acquisition contracts, adapter
replaceability, policy/rate/retry failure typing, raw artifact preservation, and
replay lineage. It does not prove production network crawling, browser execution,
distributed storage, distributed queueing, graph/memory intelligence, export
delivery, or production scale readiness.

Oracle schemas:

```yaml
ExpectedOutputOracle:
  id: string
  fixture_id: string
  expected_output_type: record | table | document_metadata | document | file | dataset | fact
  expected_items: list[ExpectedOutputItem]
  required_field_coverage: list[FieldCoverageExpectation]
  required_evidence_level: field | row | cell | section | file | item
  allowed_optional_misses: list
  forbidden_outputs: list
  comparison_mode: exact | normalized | tolerance
```

```yaml
ExpectedEventSequenceOracle:
  id: string
  fixture_id: string
  required_event_types: list
  forbidden_event_types: list
  ordering_constraints: list[EventOrderingConstraint]
  required_payloads: list[EventPayloadExpectation]
  event_cursor_refs: list
  replay_required_event_types: list
```

```yaml
ExpectedGraphOracle:
  id: string
  fixture_id: string
  expected_nodes: list[GraphNodeExpectation]
  expected_edges: list[GraphEdgeExpectation]
  forbidden_edges: list[GraphEdgeExpectation]
  expected_projection_watermarks: list
  false_merge_cases: list
  false_split_cases: list
```

```yaml
FailureInjectionPlan:
  id: string
  fixture_id: string
  injected_failures: list[FailureInjection]
  expected_failure_records: list
  expected_recovery_actions: list
  expected_dead_letters: list
  expected_events: list
  expected_operator_visible_status: string
```

Concrete oracle item schemas:

```yaml
ExpectedOutputItem:
  item_id: string
  output_type: record | table | document_metadata | document | file | dataset | fact
  key_fields: object
  expected_values: object
  forbidden_values: object
  tolerance:
    numeric_abs: number
    numeric_pct: number
    timestamp_seconds: integer
  comparison_mode: exact | normalized | tolerance
```

```yaml
FieldCoverageExpectation:
  target_id: string
  target_type: field | row | cell | section | file | item
  required: boolean
  expected_evidence_anchor_ids: list
  accepted_verification_required: boolean
```

```yaml
EvidenceAnchorExpectation:
  anchor_id: string
  source_artifact_ref: string
  normalized_document_ref: string
  selector_or_span_ref: string
  expected_text_hash: string
  privacy_classification: public | internal | confidential | regulated
```

```yaml
EventOrderingConstraint:
  before_event_type: string
  after_event_type: string
  same_scope: run | source_adapter | frontier_item | processing_task | output | export_job | projection | artifact_lifecycle
  required: boolean
```

```yaml
EventPayloadExpectation:
  event_type: string
  required_payload_schema: string
  required_ref_types: list
  required_replay_fields: list
  state_before_required: boolean
  state_after_required: boolean
  redaction_expectation: none | stable_ref | hash_only
```

```yaml
GraphNodeExpectation:
  node_key: string
  node_type: url | template | entity | source_evidence | task | temporal
  required_properties: object
  forbidden_properties: object
  evidence_ref_required: boolean
```

```yaml
GraphEdgeExpectation:
  from_node_key: string
  to_node_key: string
  edge_type: hyperlink | redirect_canonical | page_structure | entity | source_evidence | temporal
  required_properties: object
  forbidden: boolean
```

```yaml
FailureInjection:
  injection_id: string
  injection_type: network_timeout | browser_crash | credential_denied | malformed_document | projection_mismatch | export_reject | event_log_gap | artifact_missing | backup_corrupt
  target_ref: string
  trigger_phase: source_adapter | browser | normalize | extract | verify | publish | export | projection | replay | dr_restore
  expected_failure_type: string
  expected_recovery_action: string
```

```yaml
ReplayBundleOracle:
  id: string
  fixture_id: string
  required_event_cursor_refs: list
  required_artifact_hash_refs: list
  required_source_adapter_result_refs: list
  required_command_result_refs: list
  allowed_redactions:
    - ref_type: string
      redaction_expectation: stable_ref | hash_only
  expected_completeness_result: pass | fail | needs_review
```

```yaml
DRRestoreOracle:
  id: string
  fixture_id: string
  restore_point_ref: string
  expected_phase_order: list
  required_validation_gates: list
  expected_unresolved_refs: list
  expected_result: pass | fail | needs_review
  max_restore_minutes: integer
```

```yaml
ThresholdSpec:
  id: string
  fixture_id: string
  min_page_type_f1: number
  min_template_cluster_f1: number
  min_required_field_precision: number
  min_required_field_recall: number
  max_projection_lag_seconds: integer
  max_recovery_time_seconds: integer
  max_dr_restore_time_seconds: integer
  max_queue_starvation_ratio: number
  max_duplicate_snapshot_rate: number
```

Each fixture must define these oracles:

- expected discovered URLs, redirects, canonical URLs, and retired/blocked URLs
- expected page types, template clusters, and graph edges
- expected extracted records, tables, document metadata, files, datasets, or facts
- expected evidence anchors and coverage level
- expected policy decisions and blocked-source reports
- expected command/result and event sequence
- expected replay bundle contents
- expected artifact hashes for deterministic raw/normalized fixtures
- expected failure records and recovery actions when failures are injected

Per-output oracle requirements:

| Output type | Required oracle checks |
| --- | --- |
| record | required fields, field evidence anchors, schema validators, conflict behavior |
| table | row/cell coverage, table structure, source anchors, normalization manifest |
| document_metadata | title/date/author/source metadata, document artifact refs, section anchors |
| document | document artifact lifecycle, normalized text/structure, section evidence coverage |
| file | artifact hash, MIME type, privacy classification, retention lifecycle |
| dataset | manifest items, item evidence coverage, delivery/export behavior |
| fact | subject/predicate/object, verified fact, temporal validity, evidence packet |

Every `FailureInjectionPlan` must map each injected failure to expected `FailureRecord.failure_type`, `RecoveryAction.action_type`, expected event types, replay bundle entries, and operator-visible status.

Minimum target thresholds:

| Metric | Gate |
| --- | --- |
| published output evidence coverage | 100% for required fields/items |
| replay completeness for mutating and publication-relevant actions | 100% |
| blocked unsafe access reporting | 100% of blocked attempts produce policy/report events |
| credential prompt leakage | 0 occurrences |
| graph projection rebuild determinism | 100% match or explicit mismatch report |
| memory invalidation enforcement | 100% invalidated/tainted forbidden memory excluded |
| duplicate publication from retry | 0 duplicates |
| silent conflict overwrite | 0 occurrences |
| export receipt reconciliation | 100% for accepted target fixtures |
| page type classification F1 on deterministic fixtures | >= 0.95 unless fixture-specific threshold is higher |
| template cluster F1 on deterministic fixtures | >= 0.95 unless fixture-specific threshold is higher |
| required field precision on deterministic fixtures | >= 0.98 |
| required field recall on deterministic fixtures | >= 0.95 |
| projection lag in benchmark harness | <= 60 seconds or fixture-specific stricter SLO |
| operator recovery completion for injected failures | <= 15 minutes in benchmark harness |
| DR restore validation in benchmark harness | <= 60 minutes for fixture dataset |
| queue starvation ratio between small and high-volume sites | <= 2x median wait time under load fixture |
| duplicate snapshot pollution per run | < 1% |

## Capability Acceptance Matrix

| Capability | Required tests | Acceptance gate |
| --- | --- | --- |
| Objective planning | unit, contract, integration, e2e | objective becomes approved plan with policy, ambiguity, and replay records |
| Source adapters | contract, adapter, integration, policy | each adapter emits canonical attempts/results and rejects forbidden access |
| Browser observation | adapter, security, integration, replay | sandboxed render produces artifacts, budget records, and no secret leakage |
| Authorized sessions | policy, security, e2e, replay | credential use is scoped, audited, redacted, and replayable |
| Frontier scheduling | unit, integration, chaos, load | transitions are idempotent, fair, replayable, and crash-safe |
| Normalization | unit, integration, evidence | raw-to-normalized maps preserve anchors and transformation refs |
| Extraction | unit, integration, evidence, benchmark | candidates map to schemas and carry field-level evidence anchors |
| Verification | unit, integration, evidence, conflict | accept/reject/review decisions obey policy and contradiction handling |
| Publication | contract, e2e, replay | only verified outputs publish with immutable manifests and evidence maps |
| Graph intelligence | unit, integration, replay, benchmark | projections rebuild from canonical state and explain graph-influenced decisions |
| Memory intelligence | unit, integration, replay, benchmark | retrieval is scoped, fresh, invalidatable, and never source evidence |
| Multi-agent orchestration | contract, policy, replay, e2e | agents use approved tools and cannot mutate durable stores directly |
| Drift repair | integration, benchmark, review | drift creates event, repair proposal, and reviewed/verified update |
| Export and withdrawal | integration, e2e, chaos | receipts, retries, corrections, and withdrawals reconcile to events |
| Operations | integration, chaos, load | dashboards, metrics, traces, alerts, and runbooks explain failures |
| Privacy lifecycle | security, integration, replay | retention, deletion, redaction, tombstone, and projection cleanup pass |

## Target Product Acceptance Gates

Technical acceptance does not equal product readiness. Target product readiness requires user-visible workflows to pass.

| Workflow | Acceptance gate | Buyer value proven |
| --- | --- | --- |
| Multi-site onboarding | user creates project, governed source scopes, policies, schemas, and objectives for at least three distinct fixture sites without custom scraper code | general-purpose onboarding and lower maintenance burden |
| Objective-to-plan approval | AI proposes plan, adapter choices, assumptions, alternatives, evidence requirements, and risks; operator can approve or request clarification | governed AI planning with human control |
| Dynamic/auth/document/API crawl | one run uses browser, authorized session, document, and API-like adapters under policy with replayable artifacts | broad source coverage without unsafe shortcuts |
| Evidence review | reviewer can inspect source, normalized text/DOM, anchors, candidates, evidence packets, and verification decisions for every accepted output | auditability and trust |
| Conflict resolution | conflicting evidence creates review/adjudication and no silent overwrite | safer data quality and governance |
| Drift repair | drifted-site fixture produces drift event, repair proposal, reviewed update, and verified recovery | lower long-term scraper maintenance |
| Memory reuse | later run retrieves scoped memory, excludes stale/tainted entries, and re-anchors publication to current or selected evidence | compounding agent learning without evidence pollution |
| Export and withdrawal | accepted outputs are delivered with receipts; correction/withdrawal propagates and reconciles | downstream governance and operational trust |
| Replay and audit | operator reconstructs plan, tool calls, policy decisions, evidence, verification, publication, and export from replay bundle | audit and incident response readiness |
| Operator recovery | worker crash, projection lag, failed export, and blocked source each produce visible failure records and recovery actions | production operations readiness |

Minimum product gates:

| Gate | Target acceptance threshold |
| --- | --- |
| Approved-plan creation | each target workflow produces an approvable plan in the benchmark harness with all required assumptions, alternatives, adapter choices, evidence requirements, policy decisions, and risk notes present |
| Reviewer time per output | evidence review fixture exposes all required context in one review path; reviewer can accept/reject using source, normalized anchor, evidence packet, and verification decision without querying raw stores manually |
| Drift repair success | drifted-site fixture restores required field extraction and evidence coverage after reviewed repair, with zero silent schema or selector changes |
| Operator recovery completion | every injected worker crash, projection lag, failed export, blocked source, and orphan artifact has an executable recovery action and replay-visible result |
| Export/withdrawal reconciliation | 100% of accepted export-withdrawal fixtures produce receipts, destination object mappings, correction or withdrawal events, and final reconciliation status |
| User-facing status accuracy | 0 instances where planned, scaffolded, failed, or degraded capability is labeled complete, verified, or operational |
| Buyer-value workflow pass | every row in Target Product Acceptance Gates must pass with evidence, replay, and operator-visible result refs |

## Agent Reasoning Acceptance Gates

Agent safety is not enough. Target agents must also produce useful, reviewable reasoning artifacts.

| Agent capability | Required reasoning artifact | Acceptance gate |
| --- | --- | --- |
| Objective interpretation | ambiguity list, assumptions, goal decomposition, schema/evidence needs | reviewer accepts that assumptions and ambiguities are explicit before plan approval |
| Plan generation | adapter alternatives, selected adapter rationale, budget/freshness tradeoffs, risks | selected plan matches fixture oracle or explains deviation for review |
| Site understanding | page type hypotheses, template evidence, uncertainty notes | page type F1 and template cluster checks meet fixture thresholds |
| Frontier recommendation | priority rationale, graph/memory/freshness inputs, expected value | priority order meets fixture oracle or produces reviewable exception |
| Extraction | field mapping rationale, selector/anchor choice, confidence and uncertainty | accepted candidates have required anchors and schema validator pass |
| Verification | source evidence analysis, contradiction analysis, freshness, prior-output boundary | accept/reject/review recommendation matches verifier oracle for fixture conflicts |
| Drift repair | detected change, affected schemas, repair alternatives, rollback path | repaired extraction passes before/after fixture gate |
| Ops reasoning | metric evidence, severity, blast radius, recommended operator action | operator action matches injected failure runbook |

Reasoning thresholds must be explicit in each feature spec. At target level, no agent workflow is accepted if it only produces tool-safe but shallow or unexplained decisions.

## Target Profile Acceptance

### Core Production Profile

Acceptance gates:

- approved crawl plan can run end to end
- every published output has evidence coverage
- every mutating and publication-relevant action has replay lineage
- interrupted runs resume without corrupting state
- failed and blocked sources are reported, not bypassed
- replay report reconstructs plan, fetches, extraction, evidence, verification, publication, and review decisions
- `ReplayBundleManifest` validates scoped event cursors, schema versions, artifact hashes, trace refs, projection watermarks, redaction map, deterministic clock/random seed, and missing-ref behavior

### Dynamic Web Profile

Acceptance gates:

- JavaScript fixture produces expected DOM and screenshot artifacts
- browser worker enforces egress, private network, size, runtime, and cost limits
- controlled interactions are policy-approved and replayable
- browser-derived outputs preserve evidence anchors

### Authorized Session Profile

Acceptance gates:

- credential scope is enforced by policy
- credential access is audited and never serialized into prompts
- `scoped_header`, `scoped_cookie`, `request_signing`, and `vault_brokered_form_fill` fixtures prove raw secrets never enter prompts, logs, replay bundles, captured artifacts, untrusted page text, or agent-visible state
- raw secret form-fill is blocked unless a future separately approved audited mode is added; current target acceptance treats `disallowed_raw_secret_form_fill` as blocked
- session failures produce reviewable failures, not bypass attempts
- authenticated artifact refs are privacy-classified and retained according to policy

### Source Adapter, Website Pattern, And Output Coverage Profile

Acceptance gates:

- HTTP, sitemap, RSS, browser snapshot, authorized session, API source, document source, file import, manual seed, and prior snapshot adapters each have contract, policy, replay, and fixture coverage
- static, sitemap/RSS/feed, listing/detail, search, non-destructive forms, JavaScript pages, authenticated sources, API-like endpoints, documents, multi-language pages, drifted sites, and high-volume sites each pass deterministic benchmark fixtures
- record, table, document metadata, document, file, dataset, and fact outputs each pass `ExpectedOutputOracle`, evidence coverage, verification, publication, replay, and lifecycle checks
- any scaffolded or untested adapter, pattern, or output type blocks full target capability claims

### Graph Intelligence Profile

Acceptance gates:

- URL, page-structure, entity, source/evidence, task, and temporal graph projections build from canonical events/artifacts
- projection watermarks and rebuild tests pass
- graph signals can influence frontier and review routing with explanations
- graph signals cannot satisfy publication evidence requirements
- `EvidencePacket.graph_signal_refs` cannot satisfy required evidence coverage; only source artifacts and source anchors in `source_evidence_refs` can do so
- temporal KG records preserve valid time, transaction time, identity evidence, supersession, conflict, invalidation, and projection watermark fields
- temporal KG projection fixtures prove records derive only from verified outputs and canonical events
- false-merge and false-split entity identity fixtures produce conflict, adjudication, supersession, or invalidation records

### Memory Intelligence Profile

Acceptance gates:

- memory writes include scope, provenance, freshness, and invalidation metadata
- memory writes include trust level, taint labels, promotion policy, poisoning check, sanitized context refs, and prompt-use restrictions
- cross-scope memory retrieval uses `CrossScopeMemoryTunnel` with authorization, policy decisions, taint exclusion, sanitized-only prompt use, and no raw customer data transfer
- operational temporal memory is distinct from publication temporal KG and cannot support publication evidence or authoritative entity identity
- retrieval traces show exactly which memories influenced agent actions
- memory-derived strategies re-anchor to evidence before publication
- invalidated memory is excluded from planning and replay explains exclusion
- poisoned-memory fixtures prove tainted or prompt-forbidden memory cannot steer unsafe tools, credential use, or publication
- cross-project memory fixture proves unauthorized tunnel attempts are blocked and logged

### Multi-agent Operations Profile

Acceptance gates:

- all target agents run through the framework-neutral runtime
- permission matrix prevents direct durable mutation
- tool calls validate against contracts and policy
- multi-agent repair loops use `MultiAgentWorkflow`, `AgentHandoff`, and `CoordinationDecision` records with loop budget, termination, escalation, arbitration, and replay refs
- repair-loop fixture requires Planner, Site Understanding, Extractor, Verifier, Drift, and Review coordination and resolves conflicting recommendations through arbitration
- framework-native state is diagnostic only and never canonical

### Export And Correction Profile

Acceptance gates:

- file, API, database, warehouse, object store, and queue target contract tests pass
- every dispatched export uses idempotency keys and produces delivery receipt or explicit destination failure
- duplicate dispatch creates 0 duplicate accepted downstream records
- correction and withdrawal propagate to every capable destination and reconcile external object mappings
- unsupported withdrawal semantics produce reviewable `destination_unsupported` results

### Security, Privacy, And Lifecycle Profile

Acceptance gates:

- unsafe network, prompt, credential, browser, memory, graph, export, recovery, and artifact lifecycle actions are blocked and logged
- `BrowserInteractionStep` blocks account-changing, purchase/cart, delete, destructive, message-send, and unknown side-effect submissions unless a future explicit approval policy permits a narrower audited mode
- credential prompt leakage remains 0 across all fixtures
- artifact classify, redact, tombstone, delete, legal hold, retention, and projection cleanup events propagate to every affected projection
- deletion is blocked while legal hold is active; redacted-under-hold and tombstoned-under-hold fixtures preserve hold metadata and replay lineage
- redacted replay remains structurally complete through `ReplayBundleManifest`
- poisoned-memory and prompt-injection fixtures cannot steer unsafe tools or publication

### Scale And Reliability Profile

Acceptance gates:

- load tests prove site fairness and backpressure
- crash tests prove idempotent retry and resume
- projection lag is visible and bounded by SLO
- disaster recovery restores canonical state and rebuilds projections
- one bad site cannot starve unrelated jobs

## Non-deceptive Completion Checklist

A target capability cannot be called complete unless all answers are yes:

- Is there production code behind the documented contracts?
- Are IDs, state transitions, commands, events, and storage rules implemented?
- Are policy decisions recorded and enforced?
- Are raw artifacts and derived artifacts preserved with lifecycle metadata?
- Are published outputs evidence-backed?
- Can replay reconstruct the capability's decisions and side effects?
- Are unit, contract, integration, replay, security, and acceptance tests passing?
- Are metrics, traces, alerts, and failure reports available?
- Is the capability documented as verified and operational, not merely planned?

## Review Acceptance

Staff review must check for:

- hidden V1-only weakening of target architecture
- vague words without contracts or acceptance tests
- agent framework coupling
- missing evidence or replay paths
- unowned state mutations
- missing storage or projection behavior
- missing failure and recovery paths
- untestable target claims
- unsafe crawling or access-control bypass implications
- schedule-based scope reduction

Each review round must record:

- reviewers
- verdicts
- blockers
- fixes made
- final approval or remaining issue

Do not proceed to the next review round until all blockers from the current round are fixed or explicitly documented as accepted risk by the user.
