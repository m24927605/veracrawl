# Target Readiness Review Log

This log records Staff-level review for the target architecture documents. It is a working quality gate, not a ceremonial approval record.

## Review Scope

Documents under review:

- [09-target-capability-model.md](09-target-capability-model.md)
- [10-target-implementation-design.md](10-target-implementation-design.md)
- [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md)
- related references in [README.md](../README.md), [README.md](README.md), [AGENTS.md](../AGENTS.md), and existing VeraCrawl design docs

Review goals:

- VeraCrawl target capability is not intentionally weakened to V1.
- Target architecture is implementable, not only aspirational.
- Python, low coupling, high cohesion, framework-neutral agent runtime, evidence, replay, graph, memory, browser, export, scale, and operations requirements are explicit.
- Testing and acceptance criteria are concrete enough to drive implementation.
- The documents do not claim completion before implementation and validation exist.

## Staff Reviewers

| Reviewer | Focus |
| --- | --- |
| Bacon | Product strategy, market ambition, target capability, truthful product claims |
| Poincare | Architecture, modularity, Python implementation, low coupling/high cohesion |
| Dirac | AI agents, graph intelligence, evidence, memory, target capability realism |
| Peirce | Data contracts, platform readiness, tests, acceptance, replay, failure modes |

## Review Protocol

Each round must produce one of:

- `APPROVED`
- `NEEDS_CHANGES`

Rules:

- If any reviewer returns `NEEDS_CHANGES`, blockers must be fixed before the next round starts.
- Fixes must be written into the documents, not only discussed.
- The log must summarize concrete blockers and fixes.
- Approval means the reviewer accepts the documents as implementable guidance for the stated scope, not that the product has already been built.
- Target capability remains incomplete until implementation and acceptance tests pass.

## Round 1

Status: completed. Verdict: NEEDS_CHANGES, then fixed and approved to proceed.

Reviewer verdicts:

| Reviewer | Verdict | Blockers |
| --- | --- | --- |
| Bacon | NEEDS_CHANGES | missing target buyer/user/value model; technical acceptance did not prove target product workflows |
| Poincare | NEEDS_CHANGES | target adapters missing from data contracts; ports/adapters not implementation-ready; durable agent/runtime outputs not contracted; scale/reliability architecture missing |
| Dirac | NEEDS_CHANGES | top-level wording implied completed product capability; agent reasoning quality not accepted; temporal KG underspecified; memory poisoning/taint not accepted |
| Peirce | NEEDS_CHANGES | target capability and data contracts inconsistent; agent replay outputs missing schemas; storage/projection/migration matrix missing; benchmark fixtures lacked manifests, oracles, thresholds |

Fixes applied before Round 2:

- Added target buyer, user, jobs-to-be-done, buying triggers, target workflow, and value mapping to [09-target-capability-model.md](09-target-capability-model.md).
- Added target product acceptance gates and agent reasoning acceptance gates to [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).
- Changed top-level README wording from achieved-state claims to planned/target-state wording in [README.md](../README.md), [README.md](README.md), and [01-product-definition.md](01-product-definition.md).
- Added target contract profile, target adapter/export/graph types, agent trace contracts, source adapter companion contracts, temporal KG contracts, and memory trust/taint fields to [07-data-contracts.md](07-data-contracts.md).
- Added target port matrix, storage/projection/replay/migration matrix, agent reasoning requirements, temporal KG requirements, memory trust/taint requirements, and scale/reliability architecture to [10-target-implementation-design.md](10-target-implementation-design.md).
- Added benchmark fixture manifest, expected oracles, and minimum target thresholds to [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).
- Fixed temporal KG derivation so [10-target-implementation-design.md](10-target-implementation-design.md) derives KG state only from `VerifiedFact`, accepted `PublishedOutput` records, and canonical verification/publication/supersession/conflict/expiration/invalidation events. `EvidencePacket` refs are lineage-only unless attached to accepted verified outputs.

Recheck result:

| Reviewer | Recheck verdict |
| --- | --- |
| Bacon | APPROVED_TO_PROCEED |
| Poincare | APPROVED_TO_PROCEED |
| Dirac | APPROVED_TO_PROCEED after temporal KG derivation fix |
| Peirce | APPROVED_TO_PROCEED |

Open issues before Round 2: none.

## Round 2

Status: completed. Verdict: NEEDS_CHANGES, then fixed and approved to proceed.

Reviewer verdicts:

| Reviewer | Verdict | Blockers |
| --- | --- | --- |
| Bacon | NEEDS_CHANGES | target profiles omitted export/correction and security/privacy/lifecycle; product gates measured activity but lacked pass/fail thresholds |
| Poincare | NEEDS_CHANGES | ownership contracts did not match target package model; artifact lifecycle owner missing; policy taxonomy too narrow; scale/DR concepts lacked contracts |
| Dirac | NEEDS_CHANGES | graph signal evidence boundary had an escape hatch; temporal KG identity derivation could be polluted; browser/session side-effect policy was not machine-enforceable; multi-agent orchestration contract missing |
| Peirce | NEEDS_CHANGES | event/state/ownership taxonomy incomplete; replay bundle was checklist not contract; migration/rebuild execution contracts missing; fixture oracles and quantitative gates too abstract |

Fixes applied before Round 2 recheck:

- Added Export And Correction Profile and Security, Privacy, And Lifecycle Profile to [09-target-capability-model.md](09-target-capability-model.md) and [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).
- Converted product readiness measurement bullets into pass/fail gates in [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).
- Aligned `ServiceOwnershipSpec`, `ProcessingTask`, state machine scope, event ordering scope, and ownership coverage with target package owners in [07-data-contracts.md](07-data-contracts.md).
- Added explicit artifact lifecycle owner, lifecycle commands/events, and projection cleanup behavior in [07-data-contracts.md](07-data-contracts.md) and [10-target-implementation-design.md](10-target-implementation-design.md).
- Expanded policy decision taxonomy for source adapter, browser interaction, authorized session, export, withdrawal, artifact lifecycle, memory retrieval, graph signal use, and recovery actions.
- Added queue, shard lease, retry/dead-letter, backpressure, autoscaling, projection mismatch, and DR restore contracts.
- Tightened graph signal boundary so graph signals are never source evidence and cannot satisfy evidence coverage.
- Added temporal KG identity derivation rules, false-merge/false-split requirements, and identity invalidation behavior.
- Added browser interaction side-effect classification, explicit approval refs, credential scope, and destructive/out-of-scope blocking rules.
- Added `MultiAgentWorkflow`, `AgentHandoff`, and `CoordinationDecision` contracts plus multi-agent repair acceptance.
- Added `ReplayBundleManifest`, replay completeness checks, target event taxonomy matrix, projection/migration/backfill contracts, fixture oracle schemas, `ThresholdSpec`, and numeric target gates.

Recheck result:

| Reviewer | Recheck verdict |
| --- | --- |
| Bacon | APPROVED_TO_PROCEED |
| Poincare | APPROVED_TO_PROCEED |
| Dirac | APPROVED_TO_PROCEED |
| Peirce | APPROVED_TO_PROCEED |

Open issues before Round 3: none.

## Round 3

Status: completed. Verdict: NEEDS_CHANGES, then fixed and approved to proceed.

Reviewer verdicts:

| Reviewer | Verdict | Blockers |
| --- | --- | --- |
| Bacon | NEEDS_CHANGES | target profiles lacked source adapter / website pattern / output coverage profile; value mapping did not cover all target profiles |
| Poincare | NEEDS_CHANGES | target ownership not authoritative for all contracts; approval/review gates narrower than policy gates; agent/model/context contracts underspecified; artifact lifecycle conflated lifecycle status with legal hold |
| Dirac | NEEDS_CHANGES | publication temporal KG mixed with operational crawler memory; cross-site/cross-project memory tunnels lacked policy/taint boundary; multi-agent coordination records lacked lifecycle replay |
| Peirce | NEEDS_CHANGES | event taxonomy omitted new replay-critical records; replay/rebuild/migration ranges did not support multi-scope ordering; state machine coverage missed lifecycle-bearing contracts; failure/recovery taxonomy too narrow; output oracle omitted `document` |

Fixes applied before Round 3 recheck:

- Added Source Adapter, Website Pattern, And Output Coverage Profile to [09-target-capability-model.md](09-target-capability-model.md) and [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).
- Updated value mapping so source/pattern/output coverage and security/privacy/lifecycle have explicit user and buyer value.
- Added `ContextRef`, `ContextBundle`, `AgentRunRequest`, `AgentRunResult`, `ModelRequest`, and `ModelResponse` contracts; added `ContextStorePort` to implementation design.
- Expanded `ApprovalDecision.subject_type` and `ReviewItem.item_type` to cover target policy gates and reviewable actions.
- Made target ownership authoritative across `ServiceOwnershipSpec`, target ownership coverage, and implementation design; split `publish` from `export`; replaced ambiguous artifact owner with `artifact_lifecycle`.
- Split artifact lifecycle status from legal hold status and added lifecycle invariants plus legal-hold acceptance.
- Added `EventCursor` and replaced unscoped replay/rebuild/migration ranges with scoped cursor refs.
- Expanded event taxonomy for multi-agent workflows, handoffs, coordination decisions, queue/lease/dead-letter, migrations, backfills, projection mismatch, backpressure, autoscaling, and DR restore.
- Expanded state machine coverage for lifecycle-bearing target contracts.
- Expanded failure and recovery enums to cover browser/session/credential/model/agent/tool/queue/lease/memory/migration/artifact lifecycle/backpressure/DR cases.
- Split publication temporal KG from `OperationalTemporalMemoryRecord`; updated MemPalace research and target design so operational records cannot support publication evidence or authoritative entity identity.
- Added `CrossScopeMemoryTunnel` and cross-scope memory acceptance rules.
- Aligned `ExpectedOutputOracle` with `PublishedOutput.output_type`, including `document`, and added per-output oracle requirements.
- Expanded the authoritative target ownership matrix in [07-data-contracts.md](07-data-contracts.md) to include policy, approval, runtime security, resource budgets, commands/results, projections, migrations, backfills, failures, recovery, and artifact lifecycle with writer service, mutation path, and consistency semantics.

Recheck result:

| Reviewer | Recheck verdict |
| --- | --- |
| Bacon | APPROVED_TO_PROCEED |
| Poincare | APPROVED_TO_PROCEED after authoritative ownership matrix expansion |
| Dirac | APPROVED_TO_PROCEED |
| Peirce | APPROVED_TO_PROCEED |

Open issues before Round 4: none.

## Round 4

Status: completed. Verdict: NEEDS_CHANGES, then fixed and approved to proceed.

Reviewer verdicts:

| Reviewer | Verdict | Blockers |
| --- | --- | --- |
| Bacon | APPROVED | no blocker |
| Poincare | NEEDS_CHANGES | generic projection infrastructure was collapsed into graph; target source adapters were broader than fetch-shaped `SourceAdapterPort` |
| Dirac | NEEDS_CHANGES | evidence coverage not bound to verification per coverage entry; cross-scope memory tunnel missing policy/approval enum coverage; authorized-session credential exposure semantics inconsistent |
| Peirce | NEEDS_CHANGES | command surface under-specified; state machines lacked executable transition matrix; projection watermarks not aligned with scoped cursors; event payload schemas unspecified; fixture refs opaque |

Fixes applied before Round 4 recheck:

- Introduced generic `projection` owner/package and `ProjectionStorePort`; kept `graph` responsible only for graph-specific records and signals.
- Updated ownership, event taxonomy, command taxonomy, implementation design, lifecycle cleanup, and projection semantics to use `projection` for generic projection watermarks, rebuilds, and mismatch reports.
- Added `SourceAdapterResult` and changed target adapter implementation design so adapters return natural typed outputs instead of faking fetch/page-snapshot semantics.
- Added per-entry accepted support refs to `EvidenceCoverageMap` and required `OutputVerificationAggregate` to validate every required coverage entry against accepted verification decisions or allowed prior-output support.
- Added `cross_scope_memory_tunnel` to policy and approval subject types.
- Added credential delivery mode and exposure class semantics to `CredentialUseAudit`, with target rules for scoped headers, scoped cookies, request signing, vault-brokered form fill, and blocked raw-secret form fill.
- Added `CommandTypeSpec` and target command taxonomy mapping command family, owner, required gates, emitted events, and failure behavior.
- Added target state transition matrix for core lifecycle-bearing entities.
- Added `EventCursor` usage to projection watermarks and cursor-based replay/rebuild/migration behavior.
- Added event payload registry with payload schemas, required refs, state fields, redaction behavior, and replay-critical fields.
- Added deterministic fixture layout, runner command, output locations, comparison rules, and CI-style fixture runner requirements.

Additional fixes after first Round 4 recheck:

- Integrated `SourceAdapterResult` across the target manifest, ownership matrix, command registry, state machine, event enum, event taxonomy, replay bundle manifest, and payload registry.
- Added executable per-command registry rows for run lifecycle, queue/lease operations, source adapters, browser actions, publication, export, migration, projection rebuild, backfill, recovery, memory, review, conflict, and ops commands.
- Expanded the state transition matrix to cover all lifecycle-bearing `StateMachineSpec` entities, including derived/immutable terminal trace records and projection/migration/backfill records.
- Added per-event payload requirements for every `CrawlRunEvent.event_type`, with required refs, state requirements, replay-critical fields, and redaction rules.
- Aligned credential safety language across root README, docs README, target capability, implementation design, and `CredentialUseAudit`: raw secrets must not enter agents, prompts, logs, replay bundles, captured page artifacts, or untrusted page text; customer-authorized origin presentation is allowed only through audited scoped delivery modes.
- Replaced remaining fetch-shaped source-adapter proof/replay wording with `SourceAdapterResult`, `source_adapter_result_recorded`, adapter-native output refs, and fetch attempts only where applicable.
- Added command registry rows for artifact lifecycle commands: classify, redact, tombstone, delete, legal hold placement/release, and projection cleanup propagation.
- Added command registry rows and state matrix triggers for cancel/revoke/expire lifecycle branches, including task/workflow/export/withdrawal/rebuild/backfill cancellation and cross-scope memory tunnel revoke/expiry.
- Aligned credential acceptance tests so credential fixtures prove raw secrets do not enter prompts, logs, replay bundles, captured artifacts, untrusted page text, or agent-visible state.

Round 4 recheck verdicts:

| Reviewer | Verdict |
| --- | --- |
| Bacon | APPROVED_TO_PROCEED after source-adapter proof/replay wording fix |
| Poincare | APPROVED_TO_PROCEED |
| Dirac | APPROVED_TO_PROCEED after credential wording fix |
| Peirce | APPROVED_TO_PROCEED after artifact lifecycle and cancel/revoke/expire command registry expansion |

Open issues before Round 5: none.

## Round 5

Status: completed. Verdict: NEEDS_CHANGES, then fixed and approved final.

Reviewer verdicts:

| Reviewer | Verdict | Blockers |
| --- | --- | --- |
| Bacon | APPROVED_FINAL | no blocker |
| Poincare | NEEDS_CHANGES | projection cleanup crossed ownership boundary; export withdrawal reused artifact delete event; session/credential writer ownership not authoritative |
| Dirac | APPROVED_FINAL | no blocker |
| Peirce | NEEDS_CHANGES | command payload schema refs unresolved; event payload schema refs unresolved; TransitionSpec rows incomplete; fixture/oracle schemas opaque; DR restore report not executable enough |

Fixes applied before final recheck:

- Made `propagate_projection_cleanup` projection-owned and removed `ProjectionWatermark` mutation from `artifact_lifecycle`.
- Split export withdrawal propagation into export-owned `export_withdrawal_completed` and `export_withdrawal_failed`; kept `delete_propagated` scoped to artifact lifecycle.
- Added explicit ownership rows for `AuthorizedSessionSpec`, `CredentialUseAudit`, and `DRRestorePlan`/`DRRestoreRun`/`DRRestoreReport`.
- Added `Command Payload Schema Registry` covering every command payload schema used by the command registry.
- Added event payload schema definitions for every event payload family and kept per-event registry coverage aligned with `CrawlRunEvent.event_type`.
- Added generated-test-ready `TransitionSpec Registry` rows for every compact state-matrix entity/command pair.
- Replaced opaque fixture/oracle refs with concrete schemas for expected output items, field coverage, evidence anchors, event ordering, event payload expectations, graph node/edge expectations, failure injections, replay bundle oracles, and DR restore oracles.
- Added executable DR restore contracts: `DRRestorePlan`, `DRRestoreRun`, `DRRestoreReport`, restore commands, state transitions, implementation rules, and oracle fields.

Final recheck verdicts:

| Reviewer | Verdict |
| --- | --- |
| Bacon | APPROVED_FINAL |
| Poincare | APPROVED_FINAL |
| Dirac | APPROVED_FINAL |
| Peirce | APPROVED_FINAL |

## Final Readiness Statement

Status: approved for Spec Kit implementation planning.

The documents are complete enough to drive target architecture implementation specs, plans, tasks, tests, and acceptance criteria. This approval is not a claim that VeraCrawl has implemented the target architecture; it means the planning documents now define the target capability, architecture, contracts, tests, review gates, and non-deceptive completion rules at an implementable level.
