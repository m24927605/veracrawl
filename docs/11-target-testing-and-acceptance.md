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

Target website pattern coverage fixture contract:

```text
veracrawl-website-patterns run tests/fixtures/<website_pattern_fixture_id> --profile target --out .veracrawl-test-runs/<website_pattern_fixture_id>
```

Required website pattern coverage fixtures:

| Fixture | Required acceptance |
| --- | --- |
| website-pattern-coverage-success | all 12 target website patterns produce source-backed coverage records and a pass report |
| website-pattern-runtime-unavailable | contract-only website pattern coverage reports needs-review with missing runtime refs |
| website-pattern-missing-pattern | missing target website pattern fails with typed missing-pattern diagnostics |
| website-pattern-unsupported-pattern | unsupported pattern fails before target pass |
| website-pattern-single-site-assumption | single-site or fixed-selector coverage cannot claim target completion |
| website-pattern-scaffold-only | manifest-only or scaffold-only fixture coverage fails |
| website-pattern-missing-source-adapter | missing source adapter refs fail |
| website-pattern-missing-site-model | missing site model or page type refs fail |
| website-pattern-missing-output-evidence | missing output/evidence oracle refs fail |
| website-pattern-missing-pattern-specific-refs | missing feed/listing/search/form/browser/auth/API/document/language/drift/scale refs fail |
| website-pattern-unsafe-interaction | unsafe browser/form/auth interaction refs fail |
| website-pattern-missing-replay | missing command, event, outbox, or replay refs fail |

Website pattern coverage acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_website_pattern_coverage_contract_registry.py`
- `pytest tests/contract/test_website_pattern_coverage_contracts.py`
- `pytest tests/contract/test_website_pattern_coverage_import_boundaries.py`
- `pytest tests/unit/test_website_pattern_coverage_gate.py`
- `pytest tests/integration/test_website_pattern_coverage_fixtures.py`

This acceptance proves deterministic target website pattern benchmark coverage,
single-site/scaffold rejection, pattern-specific safety/evidence refs, and replay
refs. It does not prove production browser fleets, production external
websites, managed credential vaults, production parser farms, production queue
scale, or production scale readiness.

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

Production persistence and queue runtime fixture contract:

```text
veracrawl-persistence run tests/fixtures/<persistence_fixture_id> --profile target --out .veracrawl-test-runs/<persistence_fixture_id>
```

Required persistence fixtures:

| Fixture | Required acceptance |
| --- | --- |
| persistence-transaction-success | adapter, transaction, command, event cursor, outbox, artifact, idempotency, queue, policy, and replay refs complete with `pass` |
| idempotent-replay-success | reopened adapter dedupes duplicate command with 0 duplicate events and 0 duplicate outbox records |
| queue-lease-recovery-success | persisted queue lease heartbeat, nack, dead-letter, failure, and recovery refs complete with `pass` |
| non-atomic-commit | missing atomic transaction refs fail |
| idempotency-not-persisted | missing idempotency refs fail duplicate-safe replay |
| event-log-gap | missing event cursor refs fail replay |
| outbox-dispatch-missing | unrecovered outbox refs fail |
| artifact-index-missing | missing artifact index refs fail replay and lineage |
| lease-heartbeat-missing | missing lease heartbeat/queue operation refs fail |

This acceptance proves production-facing adapter semantics through a reference
filesystem adapter. It does not prove concrete database, broker, cloud, metrics,
tracing, deployment, or production worker readiness.

Concrete persistence adapter fixture contract:

```text
veracrawl-persistence-adapter run tests/fixtures/<persistence_adapter_fixture_id> --profile target --out .veracrawl-test-runs/<persistence_adapter_fixture_id>
```

Required persistence adapter fixtures:

| Fixture | Required acceptance |
| --- | --- |
| sqlite-adapter-conformance-success | SQLite adapter proves adapter, transaction, migration, command, idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay refs with `pass` |
| sqlite-reopen-idempotency-success | reopened SQLite adapter dedupes duplicate command with 0 duplicate events and 0 duplicate outbox records |
| sqlite-queue-recovery-success | SQLite adapter persists heartbeat, nack, dead-letter, failure, and recovery queue operation refs with `pass` |
| postgres-adapter-contract-harness | Postgres descriptor returns `needs_review` with `contract_only_refs` and does not claim operational pass |
| postgres-adapter-conformance-success | live Postgres adapter proves adapter, transaction, migration, command, idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay refs with `pass` |
| postgres-reopen-idempotency-success | reopened live Postgres adapter dedupes duplicate command with 0 duplicate events and 0 duplicate outbox records |
| postgres-queue-recovery-success | live Postgres adapter persists heartbeat, nack, dead-letter, failure, and recovery queue operation refs with `pass` |
| postgres-runtime-unavailable | no live DSN/runtime returns `needs_review` and must not claim operational pass |
| adapter-missing-capability | missing capability blocks conformance pass |
| sqlite-idempotency-gap | missing SQLite idempotency refs fail |
| sqlite-event-cursor-gap | missing SQLite event cursor refs fail |
| sqlite-outbox-gap | missing SQLite outbox visibility refs fail |
| sqlite-migration-missing | missing SQLite migration refs fail |

This acceptance proves executable SQLite adapter semantics, Postgres adapter
contract boundaries, and operational Postgres adapter semantics when a live DSN
or Docker-backed live gate is executed. It does not prove external queue
brokers, object storage, cloud deployment, metrics/tracing backends, managed
Postgres operations, production observability, or production worker readiness.

Operational queue broker adapter fixture contract:

```text
veracrawl-queue-broker run tests/fixtures/<queue_broker_fixture_id> --profile target --out .veracrawl-test-runs/<queue_broker_fixture_id>
```

Required queue broker fixtures:

| Fixture | Required acceptance |
| --- | --- |
| redis-broker-conformance-success | live Redis adapter proves enqueue, lease, heartbeat, ack, nack, dead-letter, fencing, retry, fairness, backpressure, policy, and replay refs with `pass` |
| redis-broker-idempotency-success | reopened live Redis adapter dedupes duplicate enqueue and does not create a second queued item |
| redis-broker-dead-letter-success | live Redis adapter moves retry-exhausted work to dead letter with failure and recovery refs |
| redis-broker-runtime-unavailable | no live URL/runtime returns `needs_review` and must not claim operational pass |
| broker-missing-fencing-token | missing fencing token refs fail |
| broker-missing-heartbeat | missing heartbeat refs fail |
| broker-missing-dead-letter | missing dead-letter refs fail |

This acceptance proves operational Redis/Valkey-style queue broker semantics
only when a live URL or Docker-backed live gate is executed. It does not prove
managed Redis operations, Kafka, cloud queues, production autoscaling,
deployment, production worker fleets, metrics/tracing backends, or production
observability.

Operational object store adapter fixture contract:

```text
veracrawl-object-store run tests/fixtures/<object_store_fixture_id> --profile target --out .veracrawl-test-runs/<object_store_fixture_id>
```

Required object store fixtures:

| Fixture | Required acceptance |
| --- | --- |
| s3-object-store-conformance-success | live S3-compatible adapter proves put, get, head, list, delete, digest, lifecycle, retention, privacy, policy, and replay refs with `pass` |
| s3-object-store-idempotency-success | reopened live S3-compatible adapter dedupes duplicate put and does not create a second object |
| s3-object-store-delete-success | live S3-compatible adapter deletes the object, records delete/lifecycle refs, and leaves zero fixture objects |
| s3-object-store-runtime-unavailable | no live endpoint/runtime returns `needs_review` and must not claim operational pass |
| object-store-missing-digest | missing digest refs fail |
| object-store-missing-read-after-write | missing read-after-write refs fail |
| object-store-missing-delete-marker | missing delete marker or lifecycle refs fail |

This acceptance proves operational S3-compatible/MinIO object store semantics
only when a live endpoint or Docker-backed MinIO gate is executed. It does not
prove managed S3 operations, cloud IAM, CDN behavior, encryption key
management, deployment, metrics/tracing backends, or production observability.

Operational runtime infrastructure gate fixture contract:

```text
veracrawl-infrastructure run tests/fixtures/<infrastructure_fixture_id> --profile target --out .veracrawl-test-runs/<infrastructure_fixture_id>
```

Required runtime infrastructure fixtures:

| Fixture | Required acceptance |
| --- | --- |
| operational-infrastructure-success | live Postgres, Redis/Valkey, and S3-compatible adapters contribute persistence, queue, object, policy, and replay refs in one `pass` report |
| operational-infrastructure-idempotency-success | duplicate command, enqueue, and put after adapter reopen are deduped across live adapters |
| operational-infrastructure-runtime-unavailable | no live runtimes return `needs_review` and must not claim integrated operational pass |
| infrastructure-missing-persistence-refs | missing persistence refs fail |
| infrastructure-missing-queue-refs | missing queue refs fail |
| infrastructure-missing-object-refs | missing object refs fail |
| infrastructure-missing-replay-refs | missing replay refs fail |

This acceptance proves the operational infrastructure substrate only when
Postgres, Redis/Valkey, and S3-compatible runtimes all contribute live refs in
the same gate. It does not prove managed cloud operations, deployment,
production worker fleets, metrics/tracing backends, production observability,
browser rendering, model SDK integration, or concrete agent framework
integration.

Operational disaster recovery gate fixture contract:

```text
veracrawl-dr run tests/fixtures/<dr_fixture_id> --profile target --out .veracrawl-test-runs/<dr_fixture_id>
```

Required operational DR fixtures:

| Fixture | Required acceptance |
| --- | --- |
| dr-restore-success | live integrated infrastructure report plus DR plan, run, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, queue recovery, failure/recovery, policy, command, event cursor, outbox, validation, and replay refs produce one `pass` report |
| dr-restore-runtime-unavailable | no live integrated infrastructure returns `needs_review` with contract-only refs and must not claim operational DR pass |
| dr-restore-missing-metadata | missing metadata restore refs fail |
| dr-restore-missing-artifact-reachability | missing artifact reachability refs fail |
| dr-restore-missing-event-replay | missing event replay refs fail |
| dr-restore-missing-projection-rebuild | missing projection rebuild refs fail |
| dr-restore-missing-export-reconciliation | missing export reconciliation refs fail |
| dr-restore-unresolved-refs | unresolved refs fail |
| dr-restore-data-loss | detected data loss fails |
| dr-restore-unsafe-recovery-without-approval | side-effecting recovery without approval fails |

This acceptance proves operational DR only when live Postgres, Redis/Valkey,
and S3-compatible infrastructure refs feed the same DR restore gate. It does
not prove managed cloud backup, cross-region replication, deployment
automation, production observability, alerting backends, on-call runbook
automation, or production worker fleet readiness.

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

Network and browser acquisition fixture contract:

```text
veracrawl-network run tests/fixtures/<network_fixture_id> --profile target --out .veracrawl-test-runs/<network_fixture_id>
```

Required network/browser fixtures:

| Fixture | Required acceptance |
| --- | --- |
| network-http-success | actual local HTTP request produces raw HTML artifact, response metadata, source acquisition report, and replay-complete network report |
| network-http-redirect | actual local HTTP redirect records redirect hop refs and replay-complete acquisition lineage |
| network-browser-readonly | read-only browser observation records sandbox policy, browser step, DOM, screenshot, network metadata, and replay refs |
| network-robots-blocked | robots policy denial produces typed blocked report and no accepted raw artifact |
| network-private-denied | private-network denial blocks execution before acquisition |
| network-egress-denied | egress allowlist denial blocks execution before acquisition |
| network-rate-budget | exhausted rate budget produces needs-review status with typed diagnostics |
| network-size-budget | oversized response is rejected as a typed failure |
| network-redirect-denied | redirect target policy denial produces typed failure |
| network-timeout | runtime timeout budget produces typed failure |
| network-browser-unsafe-side-effect | unsafe browser side effect is blocked before DOM/screenshot artifacts are accepted |

Network/browser acquisition acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_network_browser_contract_registry.py`
- `pytest tests/contract/test_network_browser_contracts.py`
- `pytest tests/contract/test_network_browser_import_boundaries.py`
- `pytest tests/unit/test_network_policy_gates.py`
- `pytest tests/unit/test_browser_sandbox_gates.py`
- `pytest tests/unit/test_network_browser_replay.py`
- `pytest tests/integration/test_network_acquisition_runtime.py`
- `pytest tests/integration/test_network_browser_negative_fixtures.py`

This acceptance proves actual deterministic local HTTP acquisition, browser
observation contracts, sandbox gates, typed safety failures, adapter
replaceability, and replay lineage. It does not prove full JavaScript rendering,
production browser fleet operation, authenticated crawling, distributed storage,
distributed queueing, graph/memory intelligence, export delivery, or production
scale readiness.

Normalize and extract fixture contract:

```text
veracrawl-process run tests/fixtures/<process_fixture_id> --profile target --out .veracrawl-test-runs/<process_fixture_id>
```

Required normalize/extract fixtures:

| Fixture | Required acceptance |
| --- | --- |
| process-static-basic | raw HTML acquisition produces normalized document, normalization manifest, text anchors, anchor map, page type classification, site model, extraction strategy, candidate, and replay-complete process report |
| process-link-provenance | discovered links include resolved href, source anchor refs, policy refs, and site model refs |
| process-anchored-candidate | extraction candidate fields all point to text anchors and remain unpublished |
| process-missing-raw | missing raw artifact produces typed failure and no normalized document claim |
| process-empty-content | empty normalized content produces needs-review status with typed diagnostics |
| process-anchor-gap | candidate field without anchor is rejected before process completion |

Normalize/extract acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_process_contract_registry.py`
- `pytest tests/contract/test_process_contracts.py`
- `pytest tests/contract/test_process_import_boundaries.py`
- `pytest tests/unit/test_normalization_pipeline.py`
- `pytest tests/unit/test_extraction_candidate_guards.py`
- `pytest tests/unit/test_process_replay.py`
- `pytest tests/integration/test_process_fixtures.py`

This acceptance proves normalized document replay lineage, anchor map creation,
link provenance, page type classification, site model records, extraction
strategy records, anchored candidates, typed process failures, adapter
replaceability through existing acquisition ports, and replay refs. It does not
prove evidence packet construction, publication completion, graph/memory
intelligence, export delivery, distributed storage, distributed queueing,
production browser rendering, or production scale readiness.

Evidence and publication fixture contract:

```text
veracrawl-evidence run tests/fixtures/<evidence_fixture_id> --profile target --out .veracrawl-test-runs/<evidence_fixture_id>
```

Required evidence/publication fixtures:

| Fixture | Required acceptance |
| --- | --- |
| evidence-field-coverage | candidate fields produce source-backed evidence anchors, coverage result, evidence packet, evidence manifest, and no publication attempt |
| evidence-verification-review | complete evidence produces accepted verification and review decisions with policy refs |
| evidence-publication-success | evidence coverage, verification, review, publication policy, privacy refs, and replay refs produce output manifest and published output |
| evidence-missing-anchor | missing field evidence produces needs-review and no output manifest |
| evidence-verification-conflict | conflict verification blocks publication and records conflict diagnostics |
| evidence-policy-denied | publication policy denial blocks publication and records typed failure |
| evidence-replay-gap | missing command/event/outbox/replay refs block publication |
| evidence-candidate-direct-publication | direct candidate publication is rejected before output manifest creation |

Evidence/publication acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_evidence_publication_contract_registry.py`
- `pytest tests/contract/test_evidence_publication_contracts.py`
- `pytest tests/contract/test_evidence_publication_import_boundaries.py`
- `pytest tests/unit/test_evidence_coverage.py`
- `pytest tests/unit/test_verification_review.py`
- `pytest tests/unit/test_publication_gates.py`
- `pytest tests/unit/test_publication_replay.py`
- `pytest tests/integration/test_evidence_publication_fixtures.py`

This acceptance proves field evidence coverage, source-backed evidence anchors,
evidence manifests, verification/review decisions, publication policy gates,
direct candidate publication rejection, immutable output manifests, typed
publication failures, and replay refs. It does not prove graph intelligence,
memory intelligence, export delivery, distributed storage, distributed queueing,
production browser rendering, review UI, or production scale readiness.

Target output type coverage fixture contract:

```text
veracrawl-output-coverage run tests/fixtures/<output_type_coverage_fixture_id> --profile target --out .veracrawl-test-runs/<output_type_coverage_fixture_id>
```

Required output type coverage fixtures:

| Fixture | Required acceptance |
| --- | --- |
| output-type-coverage-success | all seven target output types produce source-backed coverage records and a pass publication gate report |
| output-type-coverage-runtime-unavailable | contract-only output coverage reports needs-review with missing runtime refs and no published output |
| output-type-coverage-missing-output-type | missing target output type fails with typed missing-output diagnostics |
| output-type-coverage-unsupported-output-type | unsupported output type fails before publication |
| output-type-coverage-derived-context-as-evidence | candidate, graph, memory, agent reasoning, or temporal KG refs used as evidence fail publication |
| output-type-coverage-candidate-as-evidence | candidate refs used as source evidence fail publication |
| output-type-coverage-graph-as-evidence | graph refs used as source evidence fail publication |
| output-type-coverage-memory-as-evidence | memory refs used as source evidence fail publication |
| output-type-coverage-agent-reasoning-as-evidence | agent reasoning refs used as source evidence fail publication |
| output-type-coverage-temporal-kg-as-evidence | temporal KG refs used as source evidence fail publication |
| output-type-coverage-missing-table-cell-evidence | table output without row/cell evidence refs fails |
| output-type-coverage-missing-file-lifecycle | file output without artifact hash or lifecycle refs fails |
| output-type-coverage-missing-dataset-item-evidence | dataset output without item evidence refs fails |
| output-type-coverage-missing-fact-verification | fact output without fact verification refs fails |
| output-type-coverage-missing-replay | output coverage without command, event, outbox, and replay refs fails |

Output type coverage acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_output_type_coverage_contract_registry.py`
- `pytest tests/contract/test_output_type_coverage_contracts.py`
- `pytest tests/contract/test_output_type_coverage_import_boundaries.py`
- `pytest tests/unit/test_output_type_coverage_gate.py`
- `pytest tests/integration/test_output_type_coverage_fixtures.py`

This acceptance proves that the target publication boundary can cover records,
tables, document metadata, documents, files, datasets, and facts without using
derived context as source evidence. It does not prove external export delivery,
warehouse/database/object-store writes, production persistence, review UI,
production browser rendering, or production scale readiness.

Basic site graph fixture contract:

```text
veracrawl-graph run tests/fixtures/<graph_fixture_id> --profile target --out .veracrawl-test-runs/<graph_fixture_id>
```

Required graph fixtures:

| Fixture | Required acceptance |
| --- | --- |
| graph-url-hyperlink | URL nodes and hyperlink edges are deduplicated, provenance-backed, manifested, watermarked, and replay-complete |
| graph-canonical-redirect | canonical and redirect edges are recorded with acquisition/canonical provenance refs |
| graph-page-structure | page type and page-structure graph records are built from site model refs |
| graph-missing-input | missing graph input refs fail graph build |
| graph-rebuild-mismatch | rebuild hash mismatch fails graph replay |
| graph-as-evidence | graph refs used as source evidence are rejected |

Basic graph acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_graph_contract_registry.py`
- `pytest tests/contract/test_graph_contracts.py`
- `pytest tests/contract/test_graph_import_boundaries.py`
- `pytest tests/unit/test_graph_build.py`
- `pytest tests/unit/test_graph_replay.py`
- `pytest tests/unit/test_graph_evidence_boundary.py`
- `pytest tests/integration/test_graph_fixtures.py`

This acceptance proves basic URL/hyperlink/canonical/redirect/page-structure
graph records, provenance refs, manifest refs, projection watermarks, typed graph
failures, and graph-as-evidence rejection. It does not prove advanced graph
intelligence, graph store adapters, graph-driven frontier scheduling, memory,
export delivery, distributed storage, distributed queueing, production browser
rendering, or production scale readiness.

Advanced graph projection fixture contract:

```text
veracrawl-projection run tests/fixtures/<advanced_graph_fixture_id> --profile target --out .veracrawl-test-runs/<advanced_graph_fixture_id>
```

Required advanced graph projection fixtures:

| Fixture | Required acceptance |
| --- | --- |
| projection-rebuild-success | projection spec, rebuild job, watermark, delta, quality, signal, temporal record, and replay report are complete |
| graph-signal-frontier-review | frontier and review graph signals include source graph refs, explanations, bounded scores, and policy refs |
| temporal-graph-foundation | temporal graph records derive from verified output refs, evidence packet refs, valid-time refs, identity refs, and watermark refs |
| projection-missing-watermark | missing projection watermark fails projection replay |
| projection-mismatch | rebuild hash mismatch emits projection mismatch report and fails pass claim |
| graph-signal-as-evidence | graph signal used as source evidence is rejected |

Advanced graph projection acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_advanced_graph_projection_contract_registry.py`
- `pytest tests/contract/test_advanced_graph_projection_contracts.py`
- `pytest tests/contract/test_advanced_graph_projection_import_boundaries.py`
- `pytest tests/unit/test_advanced_graph_projection.py`
- `pytest tests/unit/test_advanced_graph_replay.py`
- `pytest tests/unit/test_graph_signal_evidence_boundary.py`
- `pytest tests/integration/test_advanced_graph_projection_fixtures.py`

This acceptance proves target architecture graph projection contracts,
deterministic rebuilds, mismatch reports, graph delta and quality reports, graph
signals, temporal records, projection replay refs, and graph-signal-as-evidence
rejection. It does not prove production graph store adapters, concrete
graph-driven scheduling, memory, export delivery, distributed storage,
distributed queueing, production browser rendering, graph explorer UI, or
production scale readiness.

Graph-driven frontier/review runtime fixture contract:

```text
veracrawl-graph-frontier-review run tests/fixtures/<graph_frontier_review_fixture_id> --profile target --out .veracrawl-test-runs/<graph_frontier_review_fixture_id>
```

Required graph frontier/review fixtures:

| Fixture | Required acceptance |
| --- | --- |
| graph-frontier-review-success | graph signals produce frontier priority, retry, retire, expand, and review route decisions with source graph, explanation, policy, command, event/outbox, and replay refs |
| graph-frontier-review-runtime-unavailable | missing live graph/scheduler/review runtime refs return `needs_review` with contract-only and missing-runtime refs |
| graph-frontier-review-signal-as-evidence | graph signal used as source evidence fails |
| graph-frontier-review-missing-source-graph | missing source graph refs fail |
| graph-frontier-review-missing-explanation | missing explanation refs fail |
| graph-frontier-review-unauthorized-frontier-mutation | unauthorized frontier mutation fails |
| graph-frontier-review-missing-review-route | missing review route decision refs fail |
| graph-frontier-review-missing-replay | missing replay refs fail |
| graph-frontier-review-unsupported-signal | unsupported graph signal type fails |

Graph frontier/review acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_graph_frontier_review_contract_registry.py`
- `pytest tests/contract/test_graph_frontier_review_contracts.py`
- `pytest tests/contract/test_graph_frontier_review_import_boundaries.py`
- `pytest tests/unit/test_graph_frontier_review_gate.py`
- `pytest tests/integration/test_graph_frontier_review_fixtures.py`

This acceptance proves graph-driven frontier/review decision records, dynamic
fixture execution, core import boundaries, source graph/explanation completeness,
unauthorized mutation blocking, and graph-signal-as-evidence rejection. It does
not prove production graph stores, production queue backends, review UI, memory,
export delivery, distributed storage, distributed queueing, or production scale
readiness.

Temporal KG identity projection fixture contract:

```text
veracrawl-temporal-kg run tests/fixtures/<temporal_kg_fixture_id> --profile target --out .veracrawl-test-runs/<temporal_kg_fixture_id>
```

Required temporal KG fixtures:

| Fixture | Required acceptance |
| --- | --- |
| temporal-kg-projection-success | authoritative identity and bitemporal projection derive from verified fact, published output, canonical event, evidence packet, watermark, policy, command, event/outbox, and replay refs |
| temporal-kg-false-merge-adjudicated | false merge produces conflict, adjudication, invalidation, source event, policy, command, event/outbox, and replay refs |
| temporal-kg-false-split-superseded | false split produces adjudication, resulting identity, superseded identity/projection, source event, policy, command, event/outbox, and replay refs |
| temporal-kg-runtime-unavailable | missing live temporal KG runtime refs return `needs_review` with contract-only and missing-runtime refs |
| temporal-kg-provisional-identity | provisional graph cluster cannot become authoritative temporal KG identity |
| temporal-kg-projection-as-evidence | temporal KG projection used as source evidence fails |
| temporal-kg-missing-canonical-source | missing verified fact, published output, canonical event, or evidence packet lineage fails |
| temporal-kg-missing-bitemporal-refs | missing valid-time or transaction-time refs fail |
| temporal-kg-false-merge-without-adjudication | false merge without adjudication/invalidation/supersession refs fails |
| temporal-kg-false-split-without-supersession | false split without resulting/supersession refs fails |
| temporal-kg-missing-replay | missing command/event/outbox/replay refs fail |

Temporal KG acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_temporal_kg_contract_registry.py`
- `pytest tests/contract/test_temporal_kg_contracts.py`
- `pytest tests/contract/test_temporal_kg_import_boundaries.py`
- `pytest tests/unit/test_temporal_kg_gate.py`
- `pytest tests/integration/test_temporal_kg_fixtures.py`

This acceptance proves executable temporal KG identity/projection semantics,
false-merge and false-split repair refs, bitemporal required refs, core import
boundaries, and temporal-KG-as-evidence rejection. It does not prove production
graph stores, graph query APIs, graph explorer UI, vector search, memory stores,
export delivery, distributed storage, distributed queueing, or production scale
readiness.

Memory kernel fixture contract:

```text
veracrawl-memory run tests/fixtures/<memory_fixture_id> --profile target --out .veracrawl-test-runs/<memory_fixture_id>
```

Required memory fixtures:

| Fixture | Required acceptance |
| --- | --- |
| memory-write-retrieve-success | memory event, retrieval trace, operational temporal memory record, policy refs, and replay refs are complete |
| memory-invalidation-exclusion | invalidated memory is excluded from retrieved refs and replay explains exclusion |
| cross-scope-sanitized-memory | cross-scope retrieval uses authorization, policy refs, sanitized-only transfer, evidence anchoring, and taint exclusion rules |
| poisoned-memory-blocked | tainted or prompt-forbidden memory cannot enter prompt/tool context |
| unauthorized-cross-scope-memory | cross-scope retrieval without authorization fails |
| memory-as-evidence | memory refs used as source evidence are rejected and must re-anchor to evidence |

Memory kernel acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_memory_contract_registry.py`
- `pytest tests/contract/test_memory_contracts.py`
- `pytest tests/contract/test_memory_import_boundaries.py`
- `pytest tests/unit/test_memory_kernel.py`
- `pytest tests/unit/test_memory_retrieval.py`
- `pytest tests/unit/test_memory_replay.py`
- `pytest tests/unit/test_memory_evidence_boundary.py`
- `pytest tests/unit/test_cross_scope_memory_policy.py`
- `pytest tests/integration/test_memory_fixtures.py`

This acceptance proves memory event contracts, scoped retrieval traces,
invalidated memory exclusion, cross-scope sanitized tunnel contracts,
operational temporal memory records, replay refs, tainted-memory blocking, and
memory-as-evidence rejection. It does not prove production memory stores,
vector/search retrieval, export delivery, distributed storage, distributed
queueing, production browser rendering, memory UI, or production scale
readiness.

Multi-agent repair fixture contract:

```text
veracrawl-agent-workflow run tests/fixtures/<multi_agent_fixture_id> --profile target --out .veracrawl-test-runs/<multi_agent_fixture_id>
```

Required multi-agent fixtures:

| Fixture | Required acceptance |
| --- | --- |
| multi-agent-repair-success | workflow, handoffs, coordination decision, repair signal, agent traces, policy refs, and replay refs are complete |
| coordination-arbitration-success | conflicting repair proposals are resolved by explicit coordination decision and owner command ref |
| repair-loop-evidence-success | repair loop includes before evidence, after evidence, rollback path, and policy refs |
| owner-service-bypass | agent direct durable mutation is rejected |
| unresolved-coordination-conflict | conflicting recommendations without coordination fail replay |
| agent-reasoning-as-evidence | agent reasoning refs used as source evidence are rejected |

Multi-agent repair acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_multi_agent_contract_registry.py`
- `pytest tests/contract/test_multi_agent_contracts.py`
- `pytest tests/contract/test_multi_agent_import_boundaries.py`
- `pytest tests/unit/test_multi_agent_orchestration.py`
- `pytest tests/unit/test_multi_agent_repair_boundary.py`
- `pytest tests/unit/test_multi_agent_replay.py`
- `pytest tests/integration/test_multi_agent_fixtures.py`

This acceptance proves framework-neutral workflow records, handoffs,
coordination decisions, repair signals, replay refs, owner-service mutation
boundaries, and agent-reasoning-as-evidence rejection. It does not prove concrete
agent framework integration, model SDK integration, review UI, export delivery,
distributed storage, distributed queueing, production browser rendering, or
production scale readiness.

Model provider adapter operational gate fixture contract:

```text
veracrawl-model-providers run tests/fixtures/<model_provider_fixture_id> --profile target --out .veracrawl-test-runs/<model_provider_fixture_id>
```

Required model provider adapter fixtures:

| Fixture | Required acceptance |
| --- | --- |
| model-provider-adapter-success | OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and FutureProvider produce canonical model request, response, trace, context, agent run, command, policy, observability, security/privacy, and replay refs through one adapter contract |
| model-provider-adapter-runtime-unavailable | missing live provider runtime/API credentials return `needs_review` with contract-only and missing-runtime refs |
| model-provider-adapter-raw-prompt-leak | raw prompt persistence fails |
| model-provider-adapter-raw-response-leak | raw response persistence fails |
| model-provider-adapter-provider-state-canonical | provider-native canonical transcript state fails |
| model-provider-adapter-missing-context-trace | missing context trace refs fail |
| model-provider-adapter-missing-replay | missing replay refs fail |
| model-provider-adapter-missing-security-privacy | missing security/privacy refs fail |
| model-provider-adapter-unsafe-tool-suggestion | unsafe tool suggestions fail |
| model-provider-adapter-unsupported-provider | unsupported provider names fail |

Model provider adapter acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_model_provider_adapter_contract_registry.py`
- `pytest tests/contract/test_model_provider_adapter_contracts.py`
- `pytest tests/contract/test_model_provider_adapter_import_boundaries.py`
- `pytest tests/unit/test_model_provider_adapter_gate.py`
- `pytest tests/integration/test_model_provider_adapter_fixtures.py`

This acceptance proves provider-neutral adapter mapping, dynamic adapter loading,
core import boundaries, raw prompt/response/credential blocking, provider-native
transcript boundary, and canonical context/security/replay completeness. It does
not prove production model provider accounts, vendor uptime, token billing,
model selection optimization, review UI, export delivery, distributed storage,
distributed queueing, production browser rendering, or production scale
readiness.

Source coverage adapter operational gate fixture contract:

```text
veracrawl-source-coverage run tests/fixtures/<source_coverage_fixture_id> --profile target --out .veracrawl-test-runs/<source_coverage_fixture_id>
```

Required source coverage adapter fixtures:

| Fixture | Required acceptance |
| --- | --- |
| source-coverage-adapter-success | HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot produce canonical source result, natural output, adapter-specific, command, policy, observability, security/privacy, event/outbox, and replay refs through one adapter contract |
| source-coverage-adapter-runtime-unavailable | missing live source/browser/parser/session/API runtime refs return `needs_review` with contract-only and missing-runtime refs |
| source-coverage-adapter-native-state-canonical | adapter-native canonical state fails |
| source-coverage-adapter-raw-secret-leak | raw secret persistence fails |
| source-coverage-adapter-missing-browser-refs | missing browser interaction refs fail |
| source-coverage-adapter-missing-credential-audit | missing credential audit refs fail |
| source-coverage-adapter-missing-document-artifact | missing document artifact refs fail |
| source-coverage-adapter-missing-api-payload | missing API payload refs fail |
| source-coverage-adapter-missing-replay | missing replay refs fail |
| source-coverage-adapter-unsafe-browser-side-effect | unsafe browser side effects fail |
| source-coverage-adapter-unsupported-adapter | unsupported source adapter fails |

Source coverage adapter acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_source_coverage_contract_registry.py`
- `pytest tests/contract/test_source_coverage_contracts.py`
- `pytest tests/contract/test_source_coverage_import_boundaries.py`
- `pytest tests/unit/test_source_coverage_gate.py`
- `pytest tests/integration/test_source_coverage_fixtures.py`

This acceptance proves broad target source adapter mapping, dynamic adapter
loading, core import boundaries, raw secret blocking, adapter-native state
boundary, and canonical browser/session/document/API/security/replay
completeness. It does not prove production JavaScript rendering, managed
credential vaults, production parser farms, external API crawling, export
delivery, distributed storage, distributed queueing, or production scale
readiness.

Dynamic source adapter runtime foundation fixture contract:

```text
veracrawl-source-runtime run tests/fixtures/<dynamic_source_runtime_fixture_id> --profile target --out .veracrawl-test-runs/<dynamic_source_runtime_fixture_id>
```

Required dynamic source runtime fixtures:

| Fixture | Required acceptance |
| --- | --- |
| dynamic-source-runtime-success | HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot produce canonical source result, natural output, adapter-specific runtime, command, policy, observability, security/privacy, event/outbox, runtime, and replay refs |
| dynamic-source-runtime-runtime-unavailable | missing live source/browser/parser/session/API runtime refs return `needs_review` with contract-only and missing-runtime refs |
| dynamic-source-runtime-raw-secret-leak | raw secret persistence fails |
| dynamic-source-runtime-adapter-state-canonical | adapter-native canonical state fails |
| dynamic-source-runtime-missing-credential-audit | missing credential audit refs fail |
| dynamic-source-runtime-missing-document-artifact | missing document artifact refs fail |
| dynamic-source-runtime-missing-api-payload | missing API payload refs fail |
| dynamic-source-runtime-missing-replay | missing replay refs fail |
| dynamic-source-runtime-unsafe-browser-side-effect | unsafe browser side effects fail |
| dynamic-source-runtime-unsupported-adapter | unsupported source adapter fails |

Dynamic source runtime acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_dynamic_source_runtime_contract_registry.py`
- `pytest tests/contract/test_dynamic_source_runtime_contracts.py`
- `pytest tests/contract/test_dynamic_source_runtime_import_boundaries.py`
- `pytest tests/unit/test_dynamic_source_runtime_gate.py`
- `pytest tests/integration/test_dynamic_source_runtime_fixtures.py`

This acceptance proves target source runtime records, dynamic adapter loading,
core import boundaries, raw secret blocking, adapter-native state boundary,
non-fetch native refs, and canonical browser/session/document/API/file/seed/
prior/security/replay completeness. It does not prove production JavaScript
rendering, managed credential vaults, production parser farms, external API
crawling, export delivery, distributed storage, distributed queueing, or
production scale readiness.

Agent runtime adapter operational gate fixture contract:

```text
veracrawl-agent-adapters run tests/fixtures/<agent_adapter_fixture_id> --profile target --out .veracrawl-test-runs/<agent_adapter_fixture_id>
```

Required agent runtime adapter fixtures:

| Fixture | Required acceptance |
| --- | --- |
| agent-runtime-adapter-success | OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and FutureFramework produce canonical agent run, model, tool, context, command, policy, observability, security/privacy, and replay refs through one adapter contract |
| agent-runtime-adapter-runtime-unavailable | missing live SDK/runtime refs return `needs_review` with contract-only and missing-runtime refs |
| agent-runtime-adapter-raw-prompt-leak | raw prompt persistence fails |
| agent-runtime-adapter-framework-state-canonical | framework-native canonical state fails |
| agent-runtime-adapter-missing-model-trace | missing model call trace refs fail |
| agent-runtime-adapter-missing-tool-trace | missing tool call trace refs fail |
| agent-runtime-adapter-missing-replay | missing replay refs fail |
| agent-runtime-adapter-missing-security-privacy | missing security/privacy refs fail |
| agent-runtime-adapter-unsupported-framework | unsupported framework names fail |

Agent runtime adapter acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_agent_runtime_adapter_contract_registry.py`
- `pytest tests/contract/test_agent_runtime_adapter_contracts.py`
- `pytest tests/contract/test_agent_runtime_adapter_import_boundaries.py`
- `pytest tests/unit/test_agent_runtime_adapter_gate.py`
- `pytest tests/integration/test_agent_runtime_adapter_fixtures.py`

This acceptance proves framework-neutral adapter mapping, dynamic adapter loading,
core import boundaries, raw prompt/response blocking, framework-state boundary,
and canonical trace/security/replay completeness. It does not prove production
model provider accounts, vendor service uptime, review UI, export delivery,
distributed storage, distributed queueing, production browser rendering, or
production scale readiness.

Security/privacy lifecycle gate fixture contract:

```text
veracrawl-security-privacy run tests/fixtures/<security_privacy_fixture_id> --profile target --out .veracrawl-test-runs/<security_privacy_fixture_id>
```

Required security/privacy fixtures:

| Fixture | Required acceptance |
| --- | --- |
| security-privacy-success | security checks, credential audit, prompt taint boundary, artifact lifecycle action, projection cleanup, redacted replay, observability, policy, command, event cursor, outbox, failure/recovery, redaction, and replay refs are complete with leakage count 0 |
| security-privacy-policy-only | ordinary policy refs alone return `needs_review` and cannot claim pass |
| security-privacy-unsafe-network | missing or unsafe egress/private-network policy check fails |
| security-privacy-prompt-injection | missing prompt-taint/tool-misuse boundary fails |
| security-privacy-credential-leakage | credential prompt leakage or raw secret leak refs fail |
| security-privacy-missing-lifecycle | missing artifact lifecycle propagation fails |
| security-privacy-legal-hold-delete | delete under active legal hold fails |
| security-privacy-missing-projection-cleanup | missing projection cleanup refs fail |
| security-privacy-missing-redacted-replay | missing redacted replay refs fail |
| security-privacy-missing-observability | missing observability refs fail |

Security/privacy lifecycle acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_security_privacy_contract_registry.py`
- `pytest tests/contract/test_security_privacy_contracts.py`
- `pytest tests/contract/test_security_privacy_import_boundaries.py`
- `pytest tests/unit/test_security_privacy_gate.py`
- `pytest tests/integration/test_security_privacy_fixtures.py`

This acceptance proves target security/privacy lifecycle refs, policy-only
rejection, credential leak blocking, prompt-taint boundaries, artifact
lifecycle/projection cleanup propagation, redacted replay, and backend-neutral
observability linkage. It does not prove managed DLP, SIEM/SOAR integrations,
production compliance workflows, production browser fleets, cloud security
accounts, CAPTCHA solving, paywall bypass, WAF evasion, stealth automation, or
credential bypass behavior.

Review/replay/ops console fixture contract:

```text
veracrawl-ops run tests/fixtures/<ops_fixture_id> --profile target --out .veracrawl-test-runs/<ops_fixture_id>
```

Required ops fixtures:

| Fixture | Required acceptance |
| --- | --- |
| review-console-success | review item, replay audit view, quality report, dashboard snapshot, failure/recovery refs, DR restore report, policy refs, and replay refs are complete |
| replay-audit-success | replay bundle, commands, event cursors, artifact hashes, projection watermarks, redaction, and policy refs are complete |
| quality-dashboard-success | quality report, cost summary, open review refs, projection watermarks, and dashboard snapshot are complete |
| missing-review-evidence | missing review evidence input refs fail and emit failure record |
| unresolved-failure-without-recovery | operational failure without recovery/review path fails |
| stale-dashboard-projection | stale projection watermark fails dashboard pass claim |
| unsafe-recovery-without-review | side-effecting recovery without approval/review fails |

Review/replay/ops console acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_ops_contract_registry.py`
- `pytest tests/contract/test_ops_contracts.py`
- `pytest tests/contract/test_ops_import_boundaries.py`
- `pytest tests/unit/test_ops_console.py`
- `pytest tests/unit/test_ops_replay.py`
- `pytest tests/unit/test_ops_review_recovery_boundary.py`
- `pytest tests/integration/test_ops_fixtures.py`

This acceptance proves executable review queue, replay audit, operational
failure/recovery, DR restore, quality dashboard, and ops console replay refs.
It does not prove production dashboard frontend, production observability
backend, alerting system, export delivery, distributed storage, distributed
queueing, production browser rendering, or production scale readiness.

Export connector fixture contract:

```text
veracrawl-export run tests/fixtures/<export_fixture_id> --profile target --out .veracrawl-test-runs/<export_fixture_id>
```

Required export fixtures:

| Fixture | Required acceptance |
| --- | --- |
| export-file-success | file target dispatch, receipt, destination mapping, withdrawal, correction, policy refs, and replay refs are complete |
| export-api-success | API target dispatch remains destination-neutral and receipt-backed |
| export-correction-withdrawal-success | correction includes superseded output, replacement output, withdrawal job, replacement export job, mappings, receipts, and policy refs |
| export-missing-receipt | export dispatch without delivery receipt fails |
| duplicate-export-idempotency | duplicate idempotency cannot create duplicate accepted downstream records |
| withdrawal-missing-mapping | withdrawal without external object mappings fails |
| destination-unsupported-withdrawal | unsupported withdrawal produces reviewable `destination_unsupported` needs-review |
| correction-without-withdrawal | correction propagation without withdrawal linkage fails |

Export connector acceptance requires:

- `veracrawl-contracts validate --format json`
- `pytest tests/contract/test_export_contract_registry.py`
- `pytest tests/contract/test_export_contracts.py`
- `pytest tests/contract/test_export_import_boundaries.py`
- `pytest tests/unit/test_export_runtime.py`
- `pytest tests/unit/test_export_replay.py`
- `pytest tests/unit/test_export_policy_boundaries.py`
- `pytest tests/integration/test_export_fixtures.py`

This acceptance proves destination-neutral export contracts, idempotent
dispatch, receipt reconciliation, withdrawal propagation, correction linkage,
and replay refs. It does not prove concrete export adapters, external
destination delivery, production export worker fleets, distributed storage,
distributed queueing, production browser rendering, or production scale
readiness.

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
- graph signals can influence frontier and review routing with explanations through `GraphFrontierReviewRuntimeReport`
- graph signals cannot satisfy publication evidence requirements
- `EvidencePacket.graph_signal_refs` cannot satisfy required evidence coverage; only source artifacts and source anchors in `source_evidence_refs` can do so
- temporal KG records preserve valid time, transaction time, identity evidence, supersession, conflict, invalidation, and projection watermark fields through `TemporalKGRuntimeReport`
- temporal KG projection fixtures prove records derive only from verified facts, published outputs, canonical events, evidence packet refs, and projection watermarks
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
- `SecurityPrivacyReport` pass requires security policy checks, credential audit refs, prompt taint boundary refs, artifact lifecycle actions, projection cleanup, redacted replay, observability, policy, command, event cursor, outbox, failure/recovery, redaction, and replay refs with leakage count 0
- `security-privacy-policy-only` must remain `needs_review`; ordinary policy refs alone cannot claim security/privacy lifecycle pass
- negative fixtures for unsafe network access, prompt-injection/tool misuse, credential leakage, missing lifecycle propagation, legal-hold delete, missing projection cleanup, missing redacted replay, and missing observability refs must fail deterministically
- agent runtime adapter fixtures prove OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and future frameworks map into canonical VeraCrawl agent request/result, action trace, model trace, tool trace, context trace, command, policy, observability, security/privacy, and replay refs without core framework coupling
- no-runtime agent adapter fixtures must remain `needs_review` and contract-only; missing live SDK/runtime refs cannot be labeled operational pass
- negative agent adapter fixtures for raw prompt persistence, framework-native canonical state, missing model/tool trace refs, missing replay refs, missing security/privacy refs, and unsupported frameworks must fail deterministically
- model provider adapter fixtures prove OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and future providers map into canonical VeraCrawl model request/response, model trace, context trace, agent run, command, policy, observability, security/privacy, and replay refs without core provider SDK coupling
- no-runtime model provider fixtures must remain `needs_review` and contract-only; missing live provider runtime/API credentials cannot be labeled operational pass
- negative model provider fixtures for raw prompt/response/credential persistence, provider-native canonical transcript state, unsafe tool suggestions, missing context refs, missing replay refs, missing security/privacy refs, and unsupported providers must fail deterministically

### Scale And Reliability Profile

Acceptance gates:

- load tests prove site fairness and backpressure
- crash tests prove idempotent retry and resume
- projection lag is visible and bounded by SLO
- disaster recovery restores canonical state and rebuilds projections
- one bad site cannot starve unrelated jobs
- queue topology fixtures prove all target queues and shard key parts are declared
- lease fixtures prove active leases include heartbeat, expiry, fencing token, and policy refs
- backpressure/autoscaling fixtures prove capacity changes are policy-visible and throughput-only
- dead-letter/recovery fixtures prove exhausted retries create failure records and recovery action refs
- replay fixtures prove passing scale reports include queue topology, queue item, shard lease, backpressure, autoscaling, dead-letter, failure, recovery, DR restore, policy, command, event cursor, outbox, and replay refs
- negative fixtures for stale leases, unfair site starvation, autoscaling without policy, missing dead-letter failure records, and replay missing scale refs must fail deterministically
- persistence transaction fixtures prove command, event, outbox, artifact index, idempotency, queue operation, policy, and replay refs commit together
- idempotency fixtures prove duplicate commands after adapter reopen create 0 duplicate events and 0 duplicate outbox records
- queue persistence fixtures prove enqueue, lease, heartbeat, ack, nack, dead-letter, failure, and recovery refs are durable and replay-visible
- negative fixtures for non-atomic commits, missing idempotency persistence, event log gaps, unrecovered pending outbox, missing artifact indexes, and missing lease heartbeat refs must fail deterministically
- reference filesystem persistence is accepted only as an adapter-contract proof; concrete database, queue broker, object store, cloud, metrics, tracing, and deployment readiness require separate adapter specs and gates
- concrete persistence adapter fixtures prove SQLite operational conformance through migrations, transactions, idempotency, event cursor, outbox, artifact index, queue lease/recovery, policy, and replay refs
- Postgres adapter contract fixtures must remain `needs_review` and contract-only
- operational Postgres adapter fixtures must pass only through a live DSN or Docker-backed Postgres conformance gate
- operational queue broker fixtures prove Redis/Valkey-style enqueue, lease, heartbeat, ack, nack, dead-letter, fencing, retry, fairness, backpressure, policy, and replay refs only through a live URL or Docker-backed gate
- operational object store fixtures prove S3-compatible put, duplicate put after reopen, get, head, list, delete, content digest, lifecycle, retention, privacy, policy, and replay refs only through a live endpoint or Docker-backed MinIO gate
- no-runtime object store fixtures must remain `needs_review` and contract-only
- negative object store fixtures for missing digest, missing read-after-write, and missing delete marker/lifecycle refs must fail deterministically
- operational infrastructure fixtures prove live Postgres, Redis/Valkey, and S3-compatible refs in one runtime report only through explicit live runtimes or a Docker-backed integrated gate
- no-runtime infrastructure fixtures must remain `needs_review` and contract-only
- negative infrastructure fixtures for missing persistence, queue, object, and replay refs must fail deterministically
- operational DR fixtures prove ordered restore plans, restore runs, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, queue recovery, failure/recovery, policy, command, event cursor, outbox, validation, and replay refs only through a live integrated infrastructure report or Docker-backed gate
- no-runtime DR fixtures must remain `needs_review` and contract-only
- negative DR fixtures for missing metadata, artifact reachability, event replay, projection rebuild, export reconciliation, unresolved refs, data loss, and unsafe recovery without approval must fail deterministically
- operational observability fixtures prove metrics, traces, alerts, runbooks, quality/cost signals, dashboard watermarks, failure/recovery refs, DR refs, policy, command, event cursor, outbox, redaction, collector handoff, telemetry backend, and replay refs through canonical VeraCrawl observability contracts
- no-runtime observability and data-surface-only observability fixtures must remain `needs_review` and contract-only; an ops console report alone cannot be labeled operational observability pass
- negative observability fixtures for missing metrics, missing traces, missing alerts, missing runbook actions, stale dashboard watermarks, missing DR refs, missing redaction refs, missing replay refs, secret leakage, and unsafe runbook without approval must fail deterministically

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
