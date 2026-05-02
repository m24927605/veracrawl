"""Executable foundation contract registry."""

from __future__ import annotations

import importlib
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import TimestampedModel, canonical_json
from veracrawl.contracts.enums import AdapterType, OwnerService, SourceAdapterResultType


class ContractRegistration(TimestampedModel):
    contract_name: str
    owner_service: OwnerService
    python_model: str
    schema_ref: str
    source_doc_ref: str
    mutation_allowed: bool
    replay_required: bool
    privacy_lifecycle_required: bool = False
    test_refs: list[str] = Field(default_factory=list)


class CommandTypeRegistration(TimestampedModel):
    command_type: str
    owner_service: OwnerService
    target_aggregate_type: str
    payload_schema_ref: str
    required_policy_decision_types: list[str] = Field(default_factory=list)
    approval_required: bool = False
    expected_version_required: bool = False
    lease_required: bool = False
    emitted_event_types: list[str] = Field(default_factory=list)
    failure_contract_ref: str | None = None


class EventTypeRegistration(TimestampedModel):
    event_type: str
    event_version: str
    payload_schema_ref: str
    owner_service: OwnerService
    state_before_required: bool = False
    state_after_required: bool = False
    replay_critical_refs: list[str] = Field(default_factory=list)
    redaction_policy: str = "stable_ref"


class SourceAdapterTypeRegistration(TimestampedModel):
    adapter_type: AdapterType
    owner_service: OwnerService
    natural_result_types: list[SourceAdapterResultType]
    required_policy_decision_types: list[str] = Field(default_factory=list)
    companion_contracts: list[str] = Field(default_factory=list)
    fixture_refs: list[str] = Field(default_factory=list)


class AgentAdapterFixtureRegistration(TimestampedModel):
    fixture_id: str
    framework_name: str
    runtime_spec_ref: str
    input_request_ref: str
    expected_result_ref: str
    expected_trace_refs: list[str] = Field(default_factory=list)
    forbidden_core_imports: list[str] = Field(default_factory=list)


class FixtureOracleRegistration(TimestampedModel):
    fixture_id: str
    manifest_ref: str
    expected_outputs_ref: str | None = None
    expected_evidence_ref: str | None = None
    expected_events_ref: str | None = None
    expected_graph_ref: str | None = None
    expected_dr_restore_ref: str | None = None
    expected_replay_ref: str | None = None
    expected_artifact_hashes_ref: str | None = None
    failure_injection_ref: str | None = None
    thresholds_ref: str | None = None
    negative_case: bool = False


class TargetContractAreaCoverageRegistration(TimestampedModel):
    contract_area: str
    owner_service: OwnerService
    coverage_status: str
    materialized_contract_refs: list[str] = Field(default_factory=list)
    placeholder_contract_refs: list[str] = Field(default_factory=list)
    canonical_store_impact: str
    artifact_store_impact: str
    event_refs: list[str] = Field(default_factory=list)
    projection_refs: list[str] = Field(default_factory=list)
    replay_impact: str
    privacy_lifecycle_impact: str
    required_test_refs: list[str] = Field(default_factory=list)
    followup_spec_gate: str | None = None


class RegistryValidationReport(TimestampedModel):
    id: str = "registry-validation:foundation"
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _contract(
    name: str,
    owner: OwnerService,
    module: str,
    *,
    mutation_allowed: bool = False,
    replay_required: bool = True,
    privacy: bool = False,
    tests: list[str] | None = None,
) -> ContractRegistration:
    return ContractRegistration(
        contract_name=name,
        owner_service=owner,
        python_model=f"veracrawl.contracts.{module}.{name}",
        schema_ref=name,
        source_doc_ref=f"docs/07-data-contracts.md#{name}",
        mutation_allowed=mutation_allowed,
        replay_required=replay_required,
        privacy_lifecycle_required=privacy,
        test_refs=tests or [f"tests/contract/test_contract_registry.py::{name}"],
    )


FOUNDATION_CONTRACTS: dict[str, ContractRegistration] = {
    "CommandEnvelope": _contract(
        "CommandEnvelope", OwnerService.CONTRACTS, "command", mutation_allowed=True
    ),
    "CommandResult": _contract(
        "CommandResult", OwnerService.CONTRACTS, "command", mutation_allowed=True
    ),
    "CommandTypeSpec": _contract("CommandTypeSpec", OwnerService.CONTRACTS, "command"),
    "BaseCommandPayload": _contract("BaseCommandPayload", OwnerService.CONTRACTS, "command"),
    "CrawlRunEvent": _contract(
        "CrawlRunEvent", OwnerService.RUNTIME_EVENTS, "event", mutation_allowed=True
    ),
    "EventTypeSpec": _contract("EventTypeSpec", OwnerService.RUNTIME_EVENTS, "event"),
    "PolicyDecision": _contract(
        "PolicyDecision",
        OwnerService.POLICY,
        "policy",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_policy_gates.py"],
    ),
    "SourceAdapterSpec": _contract("SourceAdapterSpec", OwnerService.PORTS, "source_adapter"),
    "SourceAdapterResult": _contract(
        "SourceAdapterResult",
        OwnerService.PORTS,
        "source_adapter",
        mutation_allowed=True,
        tests=["tests/contract/test_source_adapter_conformance.py"],
    ),
    "SourceAdapterCommand": _contract("SourceAdapterCommand", OwnerService.PORTS, "source_adapter"),
    "AgentToolSpec": _contract("AgentToolSpec", OwnerService.AGENTS, "agent"),
    "AgentRuntimeSpec": _contract("AgentRuntimeSpec", OwnerService.AGENTS, "agent"),
    "ContextRef": _contract("ContextRef", OwnerService.AGENTS, "agent", privacy=True),
    "ContextBundle": _contract("ContextBundle", OwnerService.AGENTS, "agent", privacy=True),
    "AgentRunRequest": _contract("AgentRunRequest", OwnerService.AGENTS, "agent"),
    "AgentRunResult": _contract("AgentRunResult", OwnerService.AGENTS, "agent"),
    "ModelRequest": _contract("ModelRequest", OwnerService.AGENTS, "agent", privacy=True),
    "ModelResponse": _contract("ModelResponse", OwnerService.AGENTS, "agent", privacy=True),
    "AgentActionTrace": _contract("AgentActionTrace", OwnerService.AGENTS, "agent"),
    "ModelCallTrace": _contract("ModelCallTrace", OwnerService.AGENTS, "agent", privacy=True),
    "ToolCallTrace": _contract("ToolCallTrace", OwnerService.AGENTS, "agent"),
    "ContextBundleTrace": _contract(
        "ContextBundleTrace", OwnerService.AGENTS, "agent", privacy=True
    ),
    "AgentRecommendation": _contract("AgentRecommendation", OwnerService.AGENTS, "agent"),
    "MultiAgentWorkflow": _contract(
        "MultiAgentWorkflow",
        OwnerService.AGENTS,
        "agent",
        mutation_allowed=True,
        tests=["tests/contract/test_multi_agent_contracts.py"],
    ),
    "AgentHandoff": _contract(
        "AgentHandoff",
        OwnerService.AGENTS,
        "agent",
        mutation_allowed=True,
        tests=["tests/unit/test_multi_agent_orchestration.py"],
    ),
    "CoordinationDecision": _contract(
        "CoordinationDecision",
        OwnerService.AGENTS,
        "agent",
        mutation_allowed=True,
        tests=["tests/unit/test_multi_agent_orchestration.py"],
    ),
    "DriftRepairSignal": _contract(
        "DriftRepairSignal",
        OwnerService.AGENTS,
        "agent",
        mutation_allowed=True,
        tests=["tests/unit/test_multi_agent_repair_boundary.py"],
    ),
    "MultiAgentRepairReport": _contract(
        "MultiAgentRepairReport",
        OwnerService.REVIEW_REPLAY,
        "agent",
        mutation_allowed=True,
        tests=["tests/unit/test_multi_agent_replay.py"],
    ),
    "MultiAgentFixtureManifest": _contract(
        "MultiAgentFixtureManifest",
        OwnerService.TESTS,
        "agent",
        tests=["tests/integration/test_multi_agent_fixtures.py"],
    ),
    "ReviewItem": _contract(
        "ReviewItem",
        OwnerService.REVIEW_REPLAY,
        "ops",
        mutation_allowed=True,
        tests=["tests/contract/test_ops_contracts.py"],
    ),
    "ReplayAuditView": _contract(
        "ReplayAuditView",
        OwnerService.REVIEW_REPLAY,
        "ops",
        mutation_allowed=True,
        tests=["tests/unit/test_ops_replay.py"],
    ),
    "FailureRecord": _contract(
        "FailureRecord",
        OwnerService.OPS,
        "ops",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_ops_review_recovery_boundary.py"],
    ),
    "RecoveryAction": _contract(
        "RecoveryAction",
        OwnerService.OPS,
        "ops",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_ops_review_recovery_boundary.py"],
    ),
    "DRRestoreReport": _contract(
        "DRRestoreReport",
        OwnerService.OPS,
        "ops",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/contract/test_ops_contracts.py"],
    ),
    "QualityReport": _contract(
        "QualityReport",
        OwnerService.OPS,
        "ops",
        mutation_allowed=True,
        tests=["tests/contract/test_ops_contracts.py"],
    ),
    "OpsDashboardSnapshot": _contract(
        "OpsDashboardSnapshot",
        OwnerService.OPS,
        "ops",
        mutation_allowed=True,
        tests=["tests/unit/test_ops_console.py"],
    ),
    "OpsConsoleReport": _contract(
        "OpsConsoleReport",
        OwnerService.REVIEW_REPLAY,
        "ops",
        mutation_allowed=True,
        tests=["tests/unit/test_ops_replay.py"],
    ),
    "OpsFixtureManifest": _contract(
        "OpsFixtureManifest",
        OwnerService.TESTS,
        "ops",
        tests=["tests/integration/test_ops_fixtures.py"],
    ),
    "ExportTargetSpec": _contract(
        "ExportTargetSpec",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/contract/test_export_contracts.py"],
    ),
    "ExportJob": _contract(
        "ExportJob",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        tests=["tests/contract/test_export_contracts.py"],
    ),
    "ExportAttempt": _contract(
        "ExportAttempt",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_export_runtime.py"],
    ),
    "ExportDeliveryReceipt": _contract(
        "ExportDeliveryReceipt",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_export_runtime.py"],
    ),
    "ExportWithdrawalJob": _contract(
        "ExportWithdrawalJob",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        tests=["tests/unit/test_export_policy_boundaries.py"],
    ),
    "ExportWithdrawalAttempt": _contract(
        "ExportWithdrawalAttempt",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_export_policy_boundaries.py"],
    ),
    "ExportCorrectionRecord": _contract(
        "ExportCorrectionRecord",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        tests=["tests/unit/test_export_policy_boundaries.py"],
    ),
    "ExportReconciliationReport": _contract(
        "ExportReconciliationReport",
        OwnerService.EXPORT,
        "export",
        mutation_allowed=True,
        tests=["tests/unit/test_export_replay.py"],
    ),
    "ExportFixtureManifest": _contract(
        "ExportFixtureManifest",
        OwnerService.TESTS,
        "export",
        tests=["tests/integration/test_export_fixtures.py"],
    ),
    "QueueTopologySpec": _contract(
        "QueueTopologySpec",
        OwnerService.SCHEDULER,
        "scale",
        mutation_allowed=True,
        tests=["tests/contract/test_scale_contracts.py"],
    ),
    "QueueItem": _contract(
        "QueueItem",
        OwnerService.SCHEDULER,
        "scale",
        mutation_allowed=True,
        tests=["tests/contract/test_scale_contracts.py"],
    ),
    "ShardLease": _contract(
        "ShardLease",
        OwnerService.SCHEDULER,
        "scale",
        mutation_allowed=True,
        tests=["tests/unit/test_scale_hardening.py"],
    ),
    "RetryDeadLetterRecord": _contract(
        "RetryDeadLetterRecord",
        OwnerService.SCHEDULER,
        "scale",
        mutation_allowed=True,
        tests=["tests/unit/test_scale_policy_boundaries.py"],
    ),
    "BackpressureSignal": _contract(
        "BackpressureSignal",
        OwnerService.OPS,
        "scale",
        mutation_allowed=True,
        tests=["tests/unit/test_scale_policy_boundaries.py"],
    ),
    "AutoscalingDecision": _contract(
        "AutoscalingDecision",
        OwnerService.OPS,
        "scale",
        mutation_allowed=True,
        tests=["tests/unit/test_scale_policy_boundaries.py"],
    ),
    "ScaleRecoveryReport": _contract(
        "ScaleRecoveryReport",
        OwnerService.REVIEW_REPLAY,
        "scale",
        mutation_allowed=True,
        tests=["tests/unit/test_scale_replay.py"],
    ),
    "ScaleFixtureManifest": _contract(
        "ScaleFixtureManifest",
        OwnerService.TESTS,
        "scale",
        tests=["tests/integration/test_scale_fixtures.py"],
    ),
    "PersistenceAdapterSpec": _contract(
        "PersistenceAdapterSpec",
        OwnerService.PORTS,
        "persistence",
        mutation_allowed=True,
        tests=["tests/contract/test_persistence_contracts.py"],
    ),
    "PersistenceMigrationRecord": _contract(
        "PersistenceMigrationRecord",
        OwnerService.RUNTIME_EVENTS,
        "persistence",
        mutation_allowed=True,
        tests=["tests/contract/test_persistence_adapter_contracts.py"],
    ),
    "PersistenceAdapterConformanceReport": _contract(
        "PersistenceAdapterConformanceReport",
        OwnerService.REVIEW_REPLAY,
        "persistence",
        mutation_allowed=True,
        tests=["tests/contract/test_persistence_adapter_contracts.py"],
    ),
    "PersistenceAdapterFixtureManifest": _contract(
        "PersistenceAdapterFixtureManifest",
        OwnerService.TESTS,
        "persistence",
        tests=["tests/integration/test_persistence_adapter_fixtures.py"],
    ),
    "PersistenceTransactionRecord": _contract(
        "PersistenceTransactionRecord",
        OwnerService.RUNTIME_EVENTS,
        "persistence",
        mutation_allowed=True,
        tests=["tests/contract/test_persistence_contracts.py"],
    ),
    "IdempotencyPersistenceRecord": _contract(
        "IdempotencyPersistenceRecord",
        OwnerService.RUNTIME_EVENTS,
        "persistence",
        mutation_allowed=True,
        tests=["tests/unit/test_persistence_reference_store.py"],
    ),
    "PersistentQueueOperationRecord": _contract(
        "PersistentQueueOperationRecord",
        OwnerService.SCHEDULER,
        "persistence",
        mutation_allowed=True,
        tests=["tests/unit/test_persistence_reference_store.py"],
    ),
    "PersistenceRuntimeReport": _contract(
        "PersistenceRuntimeReport",
        OwnerService.REVIEW_REPLAY,
        "persistence",
        mutation_allowed=True,
        tests=["tests/unit/test_persistence_replay.py"],
    ),
    "PersistenceFixtureManifest": _contract(
        "PersistenceFixtureManifest",
        OwnerService.TESTS,
        "persistence",
        tests=["tests/integration/test_persistence_fixtures.py"],
    ),
    "ReplayBundleManifest": _contract(
        "ReplayBundleManifest",
        OwnerService.REVIEW_REPLAY,
        "replay",
        tests=["tests/unit/test_replay_validation.py"],
    ),
    "BenchmarkFixtureManifest": _contract(
        "BenchmarkFixtureManifest", OwnerService.TESTS, "fixture"
    ),
    "ExpectedOutputOracle": _contract("ExpectedOutputOracle", OwnerService.TESTS, "fixture"),
    "ExpectedEvidenceCoverageOracle": _contract(
        "ExpectedEvidenceCoverageOracle", OwnerService.TESTS, "fixture"
    ),
    "ExpectedEventSequenceOracle": _contract(
        "ExpectedEventSequenceOracle", OwnerService.TESTS, "fixture"
    ),
    "ExpectedGraphOracle": _contract("ExpectedGraphOracle", OwnerService.TESTS, "fixture"),
    "FailureInjectionPlan": _contract("FailureInjectionPlan", OwnerService.TESTS, "fixture"),
    "DRRestoreOracle": _contract("DRRestoreOracle", OwnerService.TESTS, "fixture"),
    "ReplayBundleOracle": _contract("ReplayBundleOracle", OwnerService.TESTS, "fixture"),
    "CrawlObjective": _contract(
        "CrawlObjective",
        OwnerService.CONTROL,
        "objective",
        mutation_allowed=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "CrawlPlan": _contract(
        "CrawlPlan",
        OwnerService.CONTROL,
        "objective",
        mutation_allowed=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "CrawlRun": _contract(
        "CrawlRun",
        OwnerService.CONTROL,
        "objective",
        mutation_allowed=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "RunPlanSnapshot": _contract("RunPlanSnapshot", OwnerService.CONTROL, "objective"),
    "RuntimeCompletionGate": _contract(
        "RuntimeCompletionGate",
        OwnerService.CONTROL,
        "objective",
        mutation_allowed=True,
        tests=["tests/unit/test_runtime_completion_gates.py"],
    ),
    "RuntimeArtifactRef": _contract(
        "RuntimeArtifactRef",
        OwnerService.ARTIFACT_LIFECYCLE,
        "artifact",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "NormalizedDocument": _contract(
        "NormalizedDocument",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "ExtractionCandidate": _contract(
        "ExtractionCandidate",
        OwnerService.EXTRACT,
        "processing",
        mutation_allowed=True,
        tests=["tests/contract/test_runtime_command_event_contracts.py"],
    ),
    "EvidenceCoverageResult": _contract(
        "EvidenceCoverageResult",
        OwnerService.EVIDENCE,
        "evidence",
        mutation_allowed=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
    ),
    "EvidencePacket": _contract(
        "EvidencePacket",
        OwnerService.EVIDENCE,
        "evidence",
        mutation_allowed=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
    ),
    "EvidenceAnchor": _contract(
        "EvidenceAnchor",
        OwnerService.EVIDENCE,
        "evidence",
        mutation_allowed=True,
        tests=["tests/contract/test_evidence_publication_contracts.py"],
    ),
    "EvidencePacketManifest": _contract(
        "EvidencePacketManifest",
        OwnerService.EVIDENCE,
        "evidence",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/contract/test_evidence_publication_contracts.py"],
    ),
    "EvidencePublicationFixtureManifest": _contract(
        "EvidencePublicationFixtureManifest",
        OwnerService.TESTS,
        "evidence",
        tests=["tests/integration/test_evidence_publication_fixtures.py"],
    ),
    "VerificationDecision": _contract(
        "VerificationDecision",
        OwnerService.VERIFY,
        "verification",
        mutation_allowed=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
    ),
    "ReviewDecision": _contract(
        "ReviewDecision",
        OwnerService.VERIFY,
        "verification",
        mutation_allowed=True,
        tests=["tests/contract/test_evidence_publication_contracts.py"],
    ),
    "OutputManifest": _contract(
        "OutputManifest",
        OwnerService.PUBLISH,
        "publication",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
    ),
    "PublishedOutput": _contract(
        "PublishedOutput",
        OwnerService.PUBLISH,
        "publication",
        mutation_allowed=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
    ),
    "PublicationReport": _contract(
        "PublicationReport",
        OwnerService.REVIEW_REPLAY,
        "publication",
        mutation_allowed=True,
        tests=["tests/unit/test_publication_replay.py"],
    ),
    "GraphNode": _contract(
        "GraphNode",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/contract/test_graph_contracts.py"],
    ),
    "GraphEdge": _contract(
        "GraphEdge",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/contract/test_graph_contracts.py"],
    ),
    "GraphEdgeProvenance": _contract(
        "GraphEdgeProvenance",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/contract/test_graph_contracts.py"],
    ),
    "GraphBuildManifest": _contract(
        "GraphBuildManifest",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_graph_build.py"],
    ),
    "ProjectionWatermark": _contract(
        "ProjectionWatermark",
        OwnerService.PROJECTION,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_graph_build.py"],
    ),
    "GraphBuildReport": _contract(
        "GraphBuildReport",
        OwnerService.REVIEW_REPLAY,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_graph_replay.py"],
    ),
    "GraphFixtureManifest": _contract(
        "GraphFixtureManifest",
        OwnerService.TESTS,
        "graph",
        tests=["tests/integration/test_graph_fixtures.py"],
    ),
    "ProjectionSpec": _contract(
        "ProjectionSpec",
        OwnerService.PROJECTION,
        "graph",
        mutation_allowed=True,
        tests=["tests/contract/test_advanced_graph_projection_contracts.py"],
    ),
    "ProjectionRebuildJob": _contract(
        "ProjectionRebuildJob",
        OwnerService.PROJECTION,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_projection.py"],
    ),
    "ProjectionMismatchReport": _contract(
        "ProjectionMismatchReport",
        OwnerService.PROJECTION,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_projection.py"],
    ),
    "GraphSignal": _contract(
        "GraphSignal",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_graph_signal_evidence_boundary.py"],
    ),
    "GraphDeltaReport": _contract(
        "GraphDeltaReport",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_projection.py"],
    ),
    "GraphQualityReport": _contract(
        "GraphQualityReport",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_projection.py"],
    ),
    "TemporalGraphProjectionRecord": _contract(
        "TemporalGraphProjectionRecord",
        OwnerService.GRAPH,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_projection.py"],
    ),
    "AdvancedGraphProjectionReport": _contract(
        "AdvancedGraphProjectionReport",
        OwnerService.REVIEW_REPLAY,
        "graph",
        mutation_allowed=True,
        tests=["tests/unit/test_advanced_graph_replay.py"],
    ),
    "AdvancedGraphFixtureManifest": _contract(
        "AdvancedGraphFixtureManifest",
        OwnerService.TESTS,
        "graph",
        tests=["tests/integration/test_advanced_graph_projection_fixtures.py"],
    ),
    "MemoryEvent": _contract(
        "MemoryEvent",
        OwnerService.MEMORY,
        "memory",
        mutation_allowed=True,
        tests=["tests/contract/test_memory_contracts.py"],
    ),
    "MemoryRetrievalTrace": _contract(
        "MemoryRetrievalTrace",
        OwnerService.MEMORY,
        "memory",
        mutation_allowed=True,
        tests=["tests/unit/test_memory_retrieval.py"],
    ),
    "CrossScopeMemoryTunnel": _contract(
        "CrossScopeMemoryTunnel",
        OwnerService.MEMORY,
        "memory",
        mutation_allowed=True,
        tests=["tests/unit/test_cross_scope_memory_policy.py"],
    ),
    "OperationalTemporalMemoryRecord": _contract(
        "OperationalTemporalMemoryRecord",
        OwnerService.MEMORY,
        "memory",
        mutation_allowed=True,
        tests=["tests/unit/test_memory_kernel.py"],
    ),
    "MemoryKernelReport": _contract(
        "MemoryKernelReport",
        OwnerService.REVIEW_REPLAY,
        "memory",
        mutation_allowed=True,
        tests=["tests/unit/test_memory_replay.py"],
    ),
    "MemoryFixtureManifest": _contract(
        "MemoryFixtureManifest",
        OwnerService.TESTS,
        "memory",
        tests=["tests/integration/test_memory_fixtures.py"],
    ),
    "UnitOfWorkRecord": _contract(
        "UnitOfWorkRecord",
        OwnerService.RUNTIME_EVENTS,
        "durable",
        mutation_allowed=True,
        tests=["tests/contract/test_scheduler_contracts.py"],
    ),
    "DurableCommandRecord": _contract(
        "DurableCommandRecord",
        OwnerService.RUNTIME_EVENTS,
        "durable",
        mutation_allowed=True,
        tests=["tests/unit/test_durable_command_idempotency.py"],
    ),
    "OutboxRecord": _contract(
        "OutboxRecord",
        OwnerService.RUNTIME_EVENTS,
        "durable",
        mutation_allowed=True,
        tests=["tests/unit/test_durable_event_outbox.py"],
    ),
    "EventCursorRecord": _contract(
        "EventCursorRecord",
        OwnerService.RUNTIME_EVENTS,
        "durable",
        mutation_allowed=True,
        tests=["tests/unit/test_durable_event_outbox.py"],
    ),
    "DurableFixtureManifest": _contract(
        "DurableFixtureManifest",
        OwnerService.TESTS,
        "durable",
        tests=["tests/integration/test_durable_runtime_persistence.py"],
    ),
    "FrontierItem": _contract(
        "FrontierItem",
        OwnerService.SCHEDULER,
        "scheduler",
        mutation_allowed=True,
        tests=["tests/unit/test_scheduler_leases.py"],
    ),
    "QueueLease": _contract(
        "QueueLease",
        OwnerService.SCHEDULER,
        "scheduler",
        mutation_allowed=True,
        tests=["tests/unit/test_scheduler_leases.py"],
    ),
    "SchedulerRecoveryReport": _contract(
        "SchedulerRecoveryReport",
        OwnerService.SCHEDULER,
        "scheduler",
        mutation_allowed=True,
        tests=["tests/unit/test_scheduler_leases.py"],
    ),
    "DurableReplayRecoveryReport": _contract(
        "DurableReplayRecoveryReport",
        OwnerService.REVIEW_REPLAY,
        "recovery",
        mutation_allowed=True,
        tests=["tests/unit/test_durable_replay_recovery.py"],
    ),
    "FetchAttempt": _contract(
        "FetchAttempt",
        OwnerService.FETCH,
        "fetch",
        mutation_allowed=True,
        tests=["tests/contract/test_source_adapter_runtime_contracts.py"],
    ),
    "FetchResult": _contract(
        "FetchResult",
        OwnerService.FETCH,
        "fetch",
        mutation_allowed=True,
        tests=["tests/contract/test_source_adapter_runtime_contracts.py"],
    ),
    "PageSnapshot": _contract(
        "PageSnapshot",
        OwnerService.FETCH,
        "fetch",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/integration/test_source_acquisition_runtime.py"],
    ),
    "DocumentArtifact": _contract(
        "DocumentArtifact",
        OwnerService.FETCH,
        "fetch",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/integration/test_source_acquisition_runtime.py"],
    ),
    "RateLimitDecision": _contract(
        "RateLimitDecision",
        OwnerService.POLICY,
        "source_runtime",
        mutation_allowed=True,
        tests=["tests/unit/test_source_policy_and_retry_gates.py"],
    ),
    "SourceFailureReport": _contract(
        "SourceFailureReport",
        OwnerService.FETCH,
        "source_runtime",
        mutation_allowed=True,
        tests=["tests/unit/test_source_policy_and_retry_gates.py"],
    ),
    "SourceAcquisitionReport": _contract(
        "SourceAcquisitionReport",
        OwnerService.FETCH,
        "source_runtime",
        mutation_allowed=True,
        tests=["tests/unit/test_source_replay_recovery.py"],
    ),
    "SourceFixtureManifest": _contract(
        "SourceFixtureManifest",
        OwnerService.TESTS,
        "source_runtime",
        tests=["tests/integration/test_source_acquisition_runtime.py"],
    ),
    "NormalizationManifest": _contract(
        "NormalizationManifest",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/contract/test_process_contracts.py"],
    ),
    "TextAnchor": _contract(
        "TextAnchor",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/contract/test_process_contracts.py"],
    ),
    "AnchorMap": _contract(
        "AnchorMap",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/contract/test_process_contracts.py"],
    ),
    "LinkProvenance": _contract(
        "LinkProvenance",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/unit/test_normalization_pipeline.py"],
    ),
    "PageTypeClassification": _contract(
        "PageTypeClassification",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/unit/test_normalization_pipeline.py"],
    ),
    "SiteModel": _contract(
        "SiteModel",
        OwnerService.NORMALIZE,
        "processing",
        mutation_allowed=True,
        tests=["tests/unit/test_normalization_pipeline.py"],
    ),
    "ExtractionStrategy": _contract(
        "ExtractionStrategy",
        OwnerService.EXTRACT,
        "processing",
        mutation_allowed=True,
        tests=["tests/unit/test_extraction_candidate_guards.py"],
    ),
    "NormalizeExtractReport": _contract(
        "NormalizeExtractReport",
        OwnerService.REVIEW_REPLAY,
        "processing",
        mutation_allowed=True,
        tests=["tests/unit/test_process_replay.py"],
    ),
    "ProcessFixtureManifest": _contract(
        "ProcessFixtureManifest",
        OwnerService.TESTS,
        "processing",
        tests=["tests/integration/test_process_fixtures.py"],
    ),
    "NetworkRequest": _contract(
        "NetworkRequest",
        OwnerService.FETCH,
        "network",
        mutation_allowed=True,
        tests=["tests/contract/test_network_browser_contracts.py"],
    ),
    "NetworkResponse": _contract(
        "NetworkResponse",
        OwnerService.FETCH,
        "network",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/contract/test_network_browser_contracts.py"],
    ),
    "RedirectHop": _contract(
        "RedirectHop",
        OwnerService.FETCH,
        "network",
        mutation_allowed=True,
        tests=["tests/contract/test_network_browser_contracts.py"],
    ),
    "NetworkAcquisitionReport": _contract(
        "NetworkAcquisitionReport",
        OwnerService.FETCH,
        "network",
        mutation_allowed=True,
        tests=["tests/unit/test_network_browser_replay.py"],
    ),
    "NetworkFixtureManifest": _contract(
        "NetworkFixtureManifest",
        OwnerService.TESTS,
        "network",
        tests=["tests/integration/test_network_acquisition_runtime.py"],
    ),
    "BrowserSandboxPolicy": _contract(
        "BrowserSandboxPolicy",
        OwnerService.BROWSER,
        "browser",
        tests=["tests/unit/test_browser_sandbox_gates.py"],
    ),
    "BrowserInteractionStep": _contract(
        "BrowserInteractionStep",
        OwnerService.BROWSER,
        "browser",
        mutation_allowed=True,
        privacy=True,
        tests=["tests/unit/test_browser_sandbox_gates.py"],
    ),
    "TargetContractAreaCoverage": ContractRegistration(
        contract_name="TargetContractAreaCoverage",
        owner_service=OwnerService.CONTRACTS,
        python_model="veracrawl.contracts.registry.TargetContractAreaCoverageRegistration",
        schema_ref="TargetContractAreaCoverage",
        source_doc_ref="docs/07-data-contracts.md#Target Contract Profile",
        mutation_allowed=False,
        replay_required=True,
        privacy_lifecycle_required=False,
        test_refs=["tests/contract/test_contract_registry.py"],
    ),
}

COMMAND_TYPES: dict[str, CommandTypeRegistration] = {
    "execute_source_adapter": CommandTypeRegistration(
        command_type="execute_source_adapter",
        owner_service=OwnerService.FETCH,
        target_aggregate_type="SourceAdapterResult",
        payload_schema_ref="SourceAdapterCommand",
        required_policy_decision_types=["source_adapter"],
        emitted_event_types=["source_adapter_result_recorded", "command_committed"],
    ),
    "run_agent_runtime": CommandTypeRegistration(
        command_type="run_agent_runtime",
        owner_service=OwnerService.AGENTS,
        target_aggregate_type="AgentRunResult",
        payload_schema_ref="BaseCommandPayload",
        required_policy_decision_types=["prompt_context"],
        emitted_event_types=["agent_action_recorded", "model_called"],
    ),
    "execute_agent_tool": CommandTypeRegistration(
        command_type="execute_agent_tool",
        owner_service=OwnerService.CONTRACTS,
        target_aggregate_type="CommandResult",
        payload_schema_ref="BaseCommandPayload",
        required_policy_decision_types=["tool_call"],
        emitted_event_types=["tool_called", "command_committed"],
    ),
    "record_policy_decision": CommandTypeRegistration(
        command_type="record_policy_decision",
        owner_service=OwnerService.POLICY,
        target_aggregate_type="PolicyDecision",
        payload_schema_ref="BaseCommandPayload",
        emitted_event_types=["policy_evaluated"],
    ),
    "append_replay_manifest": CommandTypeRegistration(
        command_type="append_replay_manifest",
        owner_service=OwnerService.REVIEW_REPLAY,
        target_aggregate_type="ReplayBundleManifest",
        payload_schema_ref="BaseCommandPayload",
        emitted_event_types=["command_committed"],
    ),
    "validate_fixture_oracle": CommandTypeRegistration(
        command_type="validate_fixture_oracle",
        owner_service=OwnerService.REVIEW_REPLAY,
        target_aggregate_type="BenchmarkFixtureManifest",
        payload_schema_ref="BaseCommandPayload",
        emitted_event_types=["command_committed"],
    ),
}

COMMAND_TYPES.update(
    {
        "create_crawl_objective": CommandTypeRegistration(
            command_type="create_crawl_objective",
            owner_service=OwnerService.CONTROL,
            target_aggregate_type="CrawlObjective",
            payload_schema_ref="BaseCommandPayload",
            approval_required=True,
            emitted_event_types=["create_crawl_objective_committed"],
        ),
        "approve_crawl_plan": CommandTypeRegistration(
            command_type="approve_crawl_plan",
            owner_service=OwnerService.CONTROL,
            target_aggregate_type="CrawlPlan",
            payload_schema_ref="BaseCommandPayload",
            approval_required=True,
            emitted_event_types=["approve_crawl_plan_committed"],
        ),
        "start_crawl_run": CommandTypeRegistration(
            command_type="start_crawl_run",
            owner_service=OwnerService.CONTROL,
            target_aggregate_type="CrawlRun",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["start_crawl_run_committed"],
        ),
        "record_source_adapter_result": CommandTypeRegistration(
            command_type="record_source_adapter_result",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="SourceAdapterResult",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_source"],
            emitted_event_types=["record_source_adapter_result_committed"],
        ),
        "record_normalized_document": CommandTypeRegistration(
            command_type="record_normalized_document",
            owner_service=OwnerService.NORMALIZE,
            target_aggregate_type="NormalizedDocument",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["record_normalized_document_committed"],
        ),
        "record_extraction_candidate": CommandTypeRegistration(
            command_type="record_extraction_candidate",
            owner_service=OwnerService.EXTRACT,
            target_aggregate_type="ExtractionCandidate",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["record_extraction_candidate_committed"],
        ),
        "build_evidence_packet": CommandTypeRegistration(
            command_type="build_evidence_packet",
            owner_service=OwnerService.EVIDENCE,
            target_aggregate_type="EvidencePacket",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["build_evidence_packet_committed"],
        ),
        "record_verification_decision": CommandTypeRegistration(
            command_type="record_verification_decision",
            owner_service=OwnerService.VERIFY,
            target_aggregate_type="VerificationDecision",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_verification"],
            emitted_event_types=["record_verification_decision_committed"],
        ),
        "publish_output_manifest": CommandTypeRegistration(
            command_type="publish_output_manifest",
            owner_service=OwnerService.PUBLISH,
            target_aggregate_type="PublishedOutput",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_publication"],
            emitted_event_types=["publish_output_manifest_committed"],
        ),
        "record_replay_bundle": CommandTypeRegistration(
            command_type="record_replay_bundle",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="ReplayBundleManifest",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["record_replay_bundle_committed"],
        ),
        "accept_agent_recommendation": CommandTypeRegistration(
            command_type="accept_agent_recommendation",
            owner_service=OwnerService.AGENTS,
            target_aggregate_type="AgentRecommendation",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["prompt_context"],
            emitted_event_types=["accept_agent_recommendation_committed"],
        ),
        "durable_commit_command": CommandTypeRegistration(
            command_type="durable_commit_command",
            owner_service=OwnerService.RUNTIME_EVENTS,
            target_aggregate_type="DurableCommandRecord",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["durable_command_committed", "outbox_record_appended"],
        ),
        "enqueue_frontier_item": CommandTypeRegistration(
            command_type="enqueue_frontier_item",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="FrontierItem",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["frontier_item_enqueued"],
        ),
        "lease_frontier_item": CommandTypeRegistration(
            command_type="lease_frontier_item",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="QueueLease",
            payload_schema_ref="BaseCommandPayload",
            lease_required=True,
            emitted_event_types=["frontier_item_leased"],
        ),
        "complete_frontier_item": CommandTypeRegistration(
            command_type="complete_frontier_item",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="FrontierItem",
            payload_schema_ref="BaseCommandPayload",
            lease_required=True,
            emitted_event_types=["frontier_item_completed"],
        ),
        "record_durable_recovery": CommandTypeRegistration(
            command_type="record_durable_recovery",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="DurableReplayRecoveryReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["durable_recovery_reported"],
        ),
        "record_fetch_attempt": CommandTypeRegistration(
            command_type="record_fetch_attempt",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="FetchAttempt",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_source"],
            emitted_event_types=["fetch_attempt_recorded"],
        ),
        "record_fetch_result": CommandTypeRegistration(
            command_type="record_fetch_result",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="FetchResult",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_source"],
            emitted_event_types=["fetch_result_recorded"],
        ),
        "record_source_acquisition": CommandTypeRegistration(
            command_type="record_source_acquisition",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="SourceAcquisitionReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["source_acquisition_reported"],
        ),
        "execute_http_fetch": CommandTypeRegistration(
            command_type="execute_http_fetch",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="SourceAdapterResult",
            payload_schema_ref="SourceAdapterCommand",
            required_policy_decision_types=["source_adapter", "fetch"],
            lease_required=True,
            emitted_event_types=[
                "source_adapter_result_recorded",
                "network_request_recorded",
                "network_response_recorded",
                "snapshot_written",
            ],
        ),
        "record_network_acquisition": CommandTypeRegistration(
            command_type="record_network_acquisition",
            owner_service=OwnerService.FETCH,
            target_aggregate_type="NetworkAcquisitionReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["network_acquisition_reported"],
        ),
        "capture_browser_snapshot": CommandTypeRegistration(
            command_type="capture_browser_snapshot",
            owner_service=OwnerService.BROWSER,
            target_aggregate_type="BrowserInteractionStep",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["browser_interaction"],
            lease_required=True,
            emitted_event_types=["browser_step_executed", "snapshot_written"],
        ),
        "record_normalization_manifest": CommandTypeRegistration(
            command_type="record_normalization_manifest",
            owner_service=OwnerService.NORMALIZE,
            target_aggregate_type="NormalizationManifest",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["normalization_manifest_recorded"],
        ),
        "record_link_provenance": CommandTypeRegistration(
            command_type="record_link_provenance",
            owner_service=OwnerService.NORMALIZE,
            target_aggregate_type="LinkProvenance",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["link_provenance_recorded"],
        ),
        "record_extraction_strategy": CommandTypeRegistration(
            command_type="record_extraction_strategy",
            owner_service=OwnerService.EXTRACT,
            target_aggregate_type="ExtractionStrategy",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["extraction_strategy_recorded"],
        ),
        "record_process_report": CommandTypeRegistration(
            command_type="record_process_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="NormalizeExtractReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["process_report_recorded"],
        ),
        "record_evidence_anchor": CommandTypeRegistration(
            command_type="record_evidence_anchor",
            owner_service=OwnerService.EVIDENCE,
            target_aggregate_type="EvidenceAnchor",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_evidence"],
            emitted_event_types=["evidence_anchor_recorded"],
        ),
        "record_evidence_manifest": CommandTypeRegistration(
            command_type="record_evidence_manifest",
            owner_service=OwnerService.EVIDENCE,
            target_aggregate_type="EvidencePacketManifest",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_evidence"],
            emitted_event_types=["evidence_manifest_recorded"],
        ),
        "record_review_decision": CommandTypeRegistration(
            command_type="record_review_decision",
            owner_service=OwnerService.VERIFY,
            target_aggregate_type="ReviewDecision",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_verification"],
            emitted_event_types=["review_decision_recorded"],
        ),
        "record_publication_report": CommandTypeRegistration(
            command_type="record_publication_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="PublicationReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["publication_report_recorded"],
        ),
        "build_basic_site_graph": CommandTypeRegistration(
            command_type="build_basic_site_graph",
            owner_service=OwnerService.GRAPH,
            target_aggregate_type="GraphBuildManifest",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["graph"],
            emitted_event_types=[
                "graph_node_recorded",
                "graph_edge_recorded",
                "graph_manifest_recorded",
            ],
        ),
        "record_graph_report": CommandTypeRegistration(
            command_type="record_graph_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="GraphBuildReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["graph_report_recorded"],
        ),
        "build_advanced_graph_projection": CommandTypeRegistration(
            command_type="build_advanced_graph_projection",
            owner_service=OwnerService.GRAPH,
            target_aggregate_type="AdvancedGraphProjectionReport",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["graph", "projection"],
            emitted_event_types=[
                "projection_spec_recorded",
                "projection_rebuild_job_recorded",
                "projection_watermark_recorded",
                "graph_delta_recorded",
                "graph_quality_recorded",
                "graph_signal_recorded",
                "temporal_graph_recorded",
                "advanced_graph_projection_reported",
            ],
        ),
        "record_projection_mismatch": CommandTypeRegistration(
            command_type="record_projection_mismatch",
            owner_service=OwnerService.PROJECTION,
            target_aggregate_type="ProjectionMismatchReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["projection_mismatch_reported"],
        ),
        "write_memory_event": CommandTypeRegistration(
            command_type="write_memory_event",
            owner_service=OwnerService.MEMORY,
            target_aggregate_type="MemoryEvent",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["memory_retrieval"],
            emitted_event_types=["memory_written"],
        ),
        "retrieve_memory": CommandTypeRegistration(
            command_type="retrieve_memory",
            owner_service=OwnerService.MEMORY,
            target_aggregate_type="MemoryRetrievalTrace",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["memory_retrieval"],
            emitted_event_types=["memory_retrieved"],
        ),
        "record_memory_kernel_report": CommandTypeRegistration(
            command_type="record_memory_kernel_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="MemoryKernelReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["memory_kernel_reported"],
        ),
        "start_multi_agent_workflow": CommandTypeRegistration(
            command_type="start_multi_agent_workflow",
            owner_service=OwnerService.AGENTS,
            target_aggregate_type="MultiAgentWorkflow",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["prompt_context", "tool_call"],
            emitted_event_types=["multi_agent_workflow_started"],
        ),
        "record_agent_handoff": CommandTypeRegistration(
            command_type="record_agent_handoff",
            owner_service=OwnerService.AGENTS,
            target_aggregate_type="AgentHandoff",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["prompt_context"],
            emitted_event_types=["agent_handoff_completed"],
        ),
        "record_coordination_decision": CommandTypeRegistration(
            command_type="record_coordination_decision",
            owner_service=OwnerService.AGENTS,
            target_aggregate_type="CoordinationDecision",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["tool_call"],
            emitted_event_types=["coordination_decision_recorded"],
        ),
        "record_multi_agent_repair_report": CommandTypeRegistration(
            command_type="record_multi_agent_repair_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="MultiAgentRepairReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["multi_agent_workflow_completed"],
        ),
        "record_review_item": CommandTypeRegistration(
            command_type="record_review_item",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="ReviewItem",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["runtime_verification"],
            emitted_event_types=["review_item_recorded", "review_created"],
        ),
        "record_replay_audit_view": CommandTypeRegistration(
            command_type="record_replay_audit_view",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="ReplayAuditView",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["replay_audit_view_recorded"],
        ),
        "record_failure_record": CommandTypeRegistration(
            command_type="record_failure_record",
            owner_service=OwnerService.OPS,
            target_aggregate_type="FailureRecord",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["failure_recorded", "error_recorded"],
        ),
        "record_recovery_action": CommandTypeRegistration(
            command_type="record_recovery_action",
            owner_service=OwnerService.OPS,
            target_aggregate_type="RecoveryAction",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["ops_recovery"],
            approval_required=True,
            emitted_event_types=[
                "recovery_action_recorded",
                "recovery_action_started",
                "recovery_action_completed",
            ],
        ),
        "record_dr_restore_report": CommandTypeRegistration(
            command_type="record_dr_restore_report",
            owner_service=OwnerService.OPS,
            target_aggregate_type="DRRestoreReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["dr_restore_reported"],
        ),
        "record_quality_report": CommandTypeRegistration(
            command_type="record_quality_report",
            owner_service=OwnerService.OPS,
            target_aggregate_type="QualityReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["quality_report_recorded"],
        ),
        "record_ops_dashboard_snapshot": CommandTypeRegistration(
            command_type="record_ops_dashboard_snapshot",
            owner_service=OwnerService.OPS,
            target_aggregate_type="OpsDashboardSnapshot",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["ops_dashboard_snapshot_recorded"],
        ),
        "record_ops_console_report": CommandTypeRegistration(
            command_type="record_ops_console_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="OpsConsoleReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["ops_console_reported"],
        ),
        "record_export_target_spec": CommandTypeRegistration(
            command_type="record_export_target_spec",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportTargetSpec",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["export_dispatch"],
            emitted_event_types=["export_target_recorded"],
        ),
        "dispatch_export": CommandTypeRegistration(
            command_type="dispatch_export",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportJob",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["export_dispatch"],
            expected_version_required=True,
            emitted_event_types=["export_dispatched"],
        ),
        "complete_export": CommandTypeRegistration(
            command_type="complete_export",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportDeliveryReceipt",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["export_delivered"],
        ),
        "fail_export": CommandTypeRegistration(
            command_type="fail_export",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportAttempt",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["export_failed", "error_recorded"],
        ),
        "dispatch_withdrawal": CommandTypeRegistration(
            command_type="dispatch_withdrawal",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportWithdrawalJob",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["export_withdrawal"],
            expected_version_required=True,
            emitted_event_types=["export_withdrawal_attempted"],
        ),
        "complete_withdrawal": CommandTypeRegistration(
            command_type="complete_withdrawal",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportWithdrawalAttempt",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["export_withdrawal_completed"],
        ),
        "fail_withdrawal": CommandTypeRegistration(
            command_type="fail_withdrawal",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportWithdrawalAttempt",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["export_withdrawal_failed", "error_recorded"],
        ),
        "record_export_reconciliation": CommandTypeRegistration(
            command_type="record_export_reconciliation",
            owner_service=OwnerService.EXPORT,
            target_aggregate_type="ExportReconciliationReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["export_reconciliation_reported"],
        ),
        "record_queue_topology": CommandTypeRegistration(
            command_type="record_queue_topology",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="QueueTopologySpec",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["scheduler"],
            emitted_event_types=["queue_topology_recorded"],
        ),
        "record_queue_item": CommandTypeRegistration(
            command_type="record_queue_item",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="QueueItem",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["queue_item_recorded"],
        ),
        "record_shard_lease": CommandTypeRegistration(
            command_type="record_shard_lease",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="ShardLease",
            payload_schema_ref="BaseCommandPayload",
            lease_required=True,
            emitted_event_types=["shard_lease_recorded"],
        ),
        "record_backpressure_signal": CommandTypeRegistration(
            command_type="record_backpressure_signal",
            owner_service=OwnerService.OPS,
            target_aggregate_type="BackpressureSignal",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["backpressure"],
            emitted_event_types=["backpressure_signal_recorded"],
        ),
        "record_autoscaling_decision": CommandTypeRegistration(
            command_type="record_autoscaling_decision",
            owner_service=OwnerService.OPS,
            target_aggregate_type="AutoscalingDecision",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["autoscaling"],
            emitted_event_types=["autoscaling_decided"],
        ),
        "record_retry_dead_letter": CommandTypeRegistration(
            command_type="record_retry_dead_letter",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="RetryDeadLetterRecord",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["retry_dead_letter_recorded", "error_recorded"],
        ),
        "record_scale_recovery_report": CommandTypeRegistration(
            command_type="record_scale_recovery_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="ScaleRecoveryReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["scale_recovery_reported"],
        ),
        "record_persistence_adapter": CommandTypeRegistration(
            command_type="record_persistence_adapter",
            owner_service=OwnerService.PORTS,
            target_aggregate_type="PersistenceAdapterSpec",
            payload_schema_ref="BaseCommandPayload",
            required_policy_decision_types=["persistence"],
            emitted_event_types=["persistence_adapter_recorded"],
        ),
        "record_persistence_transaction": CommandTypeRegistration(
            command_type="record_persistence_transaction",
            owner_service=OwnerService.RUNTIME_EVENTS,
            target_aggregate_type="PersistenceTransactionRecord",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["persistence_transaction_recorded"],
        ),
        "record_persistence_migration": CommandTypeRegistration(
            command_type="record_persistence_migration",
            owner_service=OwnerService.RUNTIME_EVENTS,
            target_aggregate_type="PersistenceMigrationRecord",
            payload_schema_ref="BaseCommandPayload",
            expected_version_required=True,
            emitted_event_types=["persistence_migration_recorded"],
        ),
        "record_idempotency_persistence": CommandTypeRegistration(
            command_type="record_idempotency_persistence",
            owner_service=OwnerService.RUNTIME_EVENTS,
            target_aggregate_type="IdempotencyPersistenceRecord",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["idempotency_persisted"],
        ),
        "record_persistent_queue_operation": CommandTypeRegistration(
            command_type="record_persistent_queue_operation",
            owner_service=OwnerService.SCHEDULER,
            target_aggregate_type="PersistentQueueOperationRecord",
            payload_schema_ref="BaseCommandPayload",
            lease_required=True,
            emitted_event_types=["persistent_queue_operation_recorded"],
        ),
        "record_persistence_runtime_report": CommandTypeRegistration(
            command_type="record_persistence_runtime_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="PersistenceRuntimeReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["persistence_runtime_reported"],
        ),
        "record_persistence_adapter_conformance_report": CommandTypeRegistration(
            command_type="record_persistence_adapter_conformance_report",
            owner_service=OwnerService.REVIEW_REPLAY,
            target_aggregate_type="PersistenceAdapterConformanceReport",
            payload_schema_ref="BaseCommandPayload",
            emitted_event_types=["persistence_adapter_conformance_reported"],
        ),
    }
)

EVENT_TYPES: dict[str, EventTypeRegistration] = {
    name: EventTypeRegistration(
        event_type=name,
        event_version="1.0",
        payload_schema_ref="BaseCommandPayload",
        owner_service=OwnerService.RUNTIME_EVENTS,
        state_before_required=name in {"command_committed", "command_rejected"},
        state_after_required=name in {"command_committed", "command_rejected"},
        replay_critical_refs=["payload_ref", "causation_id", "correlation_id"],
    )
    for name in [
        "command_received",
        "command_committed",
        "command_rejected",
        "policy_evaluated",
        "agent_action_recorded",
        "model_called",
        "tool_called",
        "source_adapter_result_recorded",
        "review_created",
        "error_recorded",
    ]
}

EVENT_TYPES.update(
    {
        name: EventTypeRegistration(
            event_type=name,
            event_version="1.0",
            payload_schema_ref="BaseCommandPayload",
            owner_service=OwnerService.RUNTIME_EVENTS,
            state_before_required=name.endswith("_committed"),
            state_after_required=name.endswith("_committed"),
            replay_critical_refs=["payload_ref", "causation_id", "correlation_id"],
        )
        for name in [
            "create_crawl_objective_committed",
            "approve_crawl_plan_committed",
            "start_crawl_run_committed",
            "record_source_adapter_result_committed",
            "record_normalized_document_committed",
            "record_extraction_candidate_committed",
            "build_evidence_packet_committed",
            "record_verification_decision_committed",
            "publish_output_manifest_committed",
            "record_replay_bundle_committed",
            "accept_agent_recommendation_committed",
            "runtime_owner_violation_recorded",
            "durable_command_committed",
            "outbox_record_appended",
            "frontier_item_enqueued",
            "frontier_item_leased",
            "queue_lease_heartbeat_recorded",
            "frontier_item_completed",
            "queue_lease_released",
            "queue_lease_expired",
            "frontier_item_dead_lettered",
            "scheduler_recovery_reported",
            "durable_recovery_reported",
            "fetch_attempt_recorded",
            "fetch_result_recorded",
            "page_snapshot_recorded",
            "document_artifact_recorded",
            "source_acquisition_reported",
            "source_failure_reported",
            "network_request_recorded",
            "network_response_recorded",
            "network_acquisition_reported",
            "browser_step_executed",
            "snapshot_written",
            "normalization_manifest_recorded",
            "anchor_map_recorded",
            "link_provenance_recorded",
            "page_type_classified",
            "site_model_recorded",
            "extraction_strategy_recorded",
            "process_report_recorded",
            "evidence_anchor_recorded",
            "evidence_manifest_recorded",
            "review_decision_recorded",
            "publication_report_recorded",
            "graph_node_recorded",
            "graph_edge_recorded",
            "graph_manifest_recorded",
            "projection_watermark_recorded",
            "graph_report_recorded",
            "projection_spec_recorded",
            "projection_rebuild_job_recorded",
            "projection_mismatch_reported",
            "graph_delta_recorded",
            "graph_quality_recorded",
            "graph_signal_recorded",
            "temporal_graph_recorded",
            "advanced_graph_projection_reported",
            "memory_written",
            "memory_retrieved",
            "memory_kernel_reported",
            "multi_agent_workflow_started",
            "multi_agent_workflow_completed",
            "multi_agent_workflow_escalated",
            "multi_agent_workflow_failed",
            "agent_handoff_proposed",
            "agent_handoff_accepted",
            "agent_handoff_rejected",
            "agent_handoff_completed",
            "coordination_decision_recorded",
            "coordination_decision_applied",
            "review_item_recorded",
            "replay_audit_view_recorded",
            "failure_recorded",
            "recovery_action_recorded",
            "recovery_action_started",
            "recovery_action_completed",
            "dr_restore_reported",
            "quality_report_recorded",
            "ops_dashboard_snapshot_recorded",
            "ops_console_reported",
            "export_target_recorded",
            "export_dispatched",
            "export_delivered",
            "export_failed",
            "export_withdrawal_attempted",
            "export_withdrawal_completed",
            "export_withdrawal_failed",
            "export_reconciliation_reported",
            "queue_topology_recorded",
            "queue_item_recorded",
            "shard_lease_recorded",
            "backpressure_signal_recorded",
            "autoscaling_decided",
            "retry_dead_letter_recorded",
            "scale_recovery_reported",
            "persistence_adapter_recorded",
            "persistence_transaction_recorded",
            "persistence_migration_recorded",
            "idempotency_persisted",
            "persistent_queue_operation_recorded",
            "persistence_runtime_reported",
            "persistence_adapter_conformance_reported",
        ]
    }
)

SOURCE_ADAPTER_TYPES: dict[str, SourceAdapterTypeRegistration] = {
    "http": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.HTTP,
        owner_service=OwnerService.FETCH,
        natural_result_types=[
            SourceAdapterResultType.FETCH_RESULT,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["source_adapter", "fetch"],
        companion_contracts=["FetchAttempt", "FetchResult", "PageSnapshot"],
        fixture_refs=["foundation-fetch-like", "foundation-policy-blocked-source"],
    ),
    "sitemap": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.SITEMAP,
        owner_service=OwnerService.FETCH,
        natural_result_types=[
            SourceAdapterResultType.DISCOVERED_LINKS,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["source_adapter"],
        companion_contracts=["LinkProvenance"],
        fixture_refs=["foundation-fetch-like"],
    ),
    "rss": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.RSS,
        owner_service=OwnerService.FETCH,
        natural_result_types=[
            SourceAdapterResultType.DISCOVERED_LINKS,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["source_adapter"],
        companion_contracts=["LinkProvenance"],
        fixture_refs=["foundation-fetch-like"],
    ),
    "browser_snapshot": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.BROWSER_SNAPSHOT,
        owner_service=OwnerService.BROWSER,
        natural_result_types=[
            SourceAdapterResultType.BROWSER_SNAPSHOT,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["browser_interaction"],
        companion_contracts=["BrowserInteractionStep", "PageSnapshot"],
        fixture_refs=["foundation-policy-blocked-source"],
    ),
    "authorized_session": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.AUTHORIZED_SESSION,
        owner_service=OwnerService.CONTROL,
        natural_result_types=[
            SourceAdapterResultType.SESSION_STATE,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["authorized_session", "credential_use"],
        companion_contracts=["AuthorizedSessionSpec", "CredentialUseAudit"],
        fixture_refs=["foundation-policy-blocked-source"],
    ),
    "api_source": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.API_SOURCE,
        owner_service=OwnerService.FETCH,
        natural_result_types=[
            SourceAdapterResultType.API_PAYLOAD,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["source_adapter"],
        companion_contracts=["FetchAttempt", "FetchResult"],
        fixture_refs=["foundation-fetch-like"],
    ),
    "document_source": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.DOCUMENT_SOURCE,
        owner_service=OwnerService.NORMALIZE,
        natural_result_types=[
            SourceAdapterResultType.DOCUMENT_ARTIFACT,
            SourceAdapterResultType.BLOCKED_SOURCE,
        ],
        required_policy_decision_types=["artifact_lifecycle"],
        companion_contracts=["DocumentNormalizationArtifact"],
        fixture_refs=["foundation-non-fetch"],
    ),
    "file_import": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.FILE_IMPORT,
        owner_service=OwnerService.ARTIFACT_LIFECYCLE,
        natural_result_types=[SourceAdapterResultType.FILE_ARTIFACT],
        required_policy_decision_types=["artifact_lifecycle"],
        companion_contracts=["ArtifactLifecycleState"],
        fixture_refs=["foundation-non-fetch"],
    ),
    "manual_seed": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.MANUAL_SEED,
        owner_service=OwnerService.CONTROL,
        natural_result_types=[SourceAdapterResultType.SEED_PLAN],
        required_policy_decision_types=["source_adapter"],
        companion_contracts=["CrawlObjective", "CrawlPlan"],
        fixture_refs=["foundation-non-fetch"],
    ),
    "prior_snapshot": SourceAdapterTypeRegistration(
        adapter_type=AdapterType.PRIOR_SNAPSHOT,
        owner_service=OwnerService.CONTROL,
        natural_result_types=[SourceAdapterResultType.PRIOR_SNAPSHOT_REF],
        required_policy_decision_types=["source_adapter"],
        companion_contracts=["PageSnapshot", "RunPlanSnapshot"],
        fixture_refs=["foundation-non-fetch"],
    ),
}

AGENT_ADAPTER_FIXTURES: dict[str, AgentAdapterFixtureRegistration] = {
    "agent-openai-sdk-planner-conformance": AgentAdapterFixtureRegistration(
        fixture_id="agent-openai-sdk-planner-conformance",
        framework_name="OpenAI Agent SDK",
        runtime_spec_ref="runtime:openai-agent-sdk",
        input_request_ref="agent-request:planner",
        expected_result_ref="agent-result:openai-agent-sdk",
        expected_trace_refs=["agent-trace:openai-agent-sdk"],
        forbidden_core_imports=["openai", "agents"],
    ),
    "agent-langgraph-workflow-conformance": AgentAdapterFixtureRegistration(
        fixture_id="agent-langgraph-workflow-conformance",
        framework_name="LangGraph",
        runtime_spec_ref="runtime:langgraph",
        input_request_ref="agent-request:workflow",
        expected_result_ref="agent-result:langgraph",
        expected_trace_refs=["agent-trace:langgraph"],
        forbidden_core_imports=["langgraph", "langchain"],
    ),
}

for _framework in ["LangChain", "CrewAI", "AutoGen", "Semantic Kernel", "FutureFramework"]:
    AGENT_ADAPTER_FIXTURES[f"compatibility-target:{_framework.lower().replace(' ', '-')}"] = (
        AgentAdapterFixtureRegistration(
            fixture_id=f"compatibility-target:{_framework.lower().replace(' ', '-')}",
            framework_name=_framework,
            runtime_spec_ref="runtime:future-adapter-contract",
            input_request_ref="agent-request:compatibility",
            expected_result_ref="agent-result:compatibility",
            expected_trace_refs=["agent-trace:compatibility"],
            forbidden_core_imports=[_framework.lower().replace(" ", "_")],
        )
    )


def _fixture_registration(fixture_id: str, *, negative: bool = False) -> FixtureOracleRegistration:
    base = f"tests/fixtures/{fixture_id}"
    return FixtureOracleRegistration(
        fixture_id=fixture_id,
        manifest_ref=f"{base}/manifest.yaml",
        expected_outputs_ref=f"{base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{base}/oracles/expected_events.yaml",
        expected_graph_ref=f"{base}/oracles/expected_graph.yaml",
        expected_dr_restore_ref=f"{base}/oracles/expected_dr_restore.yaml",
        expected_replay_ref=f"{base}/oracles/expected_replay.yaml",
        expected_artifact_hashes_ref=f"{base}/artifacts/expected_hashes.yaml",
        failure_injection_ref=f"{base}/oracles/failure_injection.yaml",
        thresholds_ref=f"{base}/oracles/thresholds.yaml",
        negative_case=negative,
    )


FIXTURE_ORACLES: dict[str, FixtureOracleRegistration] = {
    "foundation-fetch-like": _fixture_registration("foundation-fetch-like"),
    "foundation-non-fetch": _fixture_registration("foundation-non-fetch"),
    "foundation-policy-blocked-source": _fixture_registration(
        "foundation-policy-blocked-source", negative=True
    ),
    "foundation-replay-missing-ref": _fixture_registration(
        "foundation-replay-missing-ref", negative=True
    ),
    "foundation-missing-evidence": _fixture_registration(
        "foundation-missing-evidence", negative=True
    ),
    "foundation-adapter-mismatch": FixtureOracleRegistration(
        fixture_id="foundation-adapter-mismatch",
        manifest_ref="tests/fixtures/foundation-adapter-mismatch/manifest.yaml",
        expected_events_ref="tests/fixtures/foundation-adapter-mismatch/oracles/expected_events.yaml",
        expected_replay_ref="tests/fixtures/foundation-adapter-mismatch/oracles/expected_replay.yaml",
        failure_injection_ref="tests/fixtures/foundation-adapter-mismatch/oracles/failure_injection.yaml",
        thresholds_ref="tests/fixtures/foundation-adapter-mismatch/oracles/thresholds.yaml",
        negative_case=True,
    ),
}

for _runtime_fixture, _negative in {
    "runtime-record-success": False,
    "runtime-blocked-source": True,
    "runtime-missing-evidence": True,
    "runtime-verification-conflict": True,
    "runtime-adapter-mismatch": True,
    "runtime-replay-gap": True,
    "runtime-boundary-violation": True,
}.items():
    _base = f"tests/fixtures/{_runtime_fixture}"
    FIXTURE_ORACLES[_runtime_fixture] = FixtureOracleRegistration(
        fixture_id=_runtime_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _durable_fixture, _negative in {
    "durable-runtime-success": False,
    "durable-duplicate-command": False,
    "durable-event-gap": True,
    "durable-pending-outbox": True,
    "durable-stale-lease": True,
    "durable-invalid-lease": True,
    "durable-missing-artifact": True,
}.items():
    _base = f"tests/fixtures/{_durable_fixture}"
    FIXTURE_ORACLES[_durable_fixture] = FixtureOracleRegistration(
        fixture_id=_durable_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _source_fixture, _negative in {
    "source-http-success": False,
    "source-sitemap-success": False,
    "source-rss-success": False,
    "source-api-success": False,
    "source-document-success": False,
    "source-blocked": True,
    "source-rate-limited": True,
    "source-adapter-mismatch": True,
    "source-malformed-response": True,
    "source-retry-exhausted": True,
    "source-missing-artifact": True,
}.items():
    _base = f"tests/fixtures/{_source_fixture}"
    FIXTURE_ORACLES[_source_fixture] = FixtureOracleRegistration(
        fixture_id=_source_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _network_fixture, _negative in {
    "network-http-success": False,
    "network-http-redirect": False,
    "network-browser-readonly": False,
    "network-robots-blocked": True,
    "network-private-denied": True,
    "network-egress-denied": True,
    "network-rate-budget": True,
    "network-size-budget": True,
    "network-redirect-denied": True,
    "network-timeout": True,
    "network-browser-unsafe-side-effect": True,
}.items():
    _base = f"tests/fixtures/{_network_fixture}"
    FIXTURE_ORACLES[_network_fixture] = FixtureOracleRegistration(
        fixture_id=_network_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _process_fixture, _negative in {
    "process-static-basic": False,
    "process-link-provenance": False,
    "process-anchored-candidate": False,
    "process-missing-raw": True,
    "process-empty-content": True,
    "process-anchor-gap": True,
}.items():
    _base = f"tests/fixtures/{_process_fixture}"
    FIXTURE_ORACLES[_process_fixture] = FixtureOracleRegistration(
        fixture_id=_process_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _evidence_fixture, _negative in {
    "evidence-field-coverage": False,
    "evidence-verification-review": False,
    "evidence-publication-success": False,
    "evidence-missing-anchor": True,
    "evidence-verification-conflict": True,
    "evidence-policy-denied": True,
    "evidence-replay-gap": True,
    "evidence-candidate-direct-publication": True,
}.items():
    _base = f"tests/fixtures/{_evidence_fixture}"
    FIXTURE_ORACLES[_evidence_fixture] = FixtureOracleRegistration(
        fixture_id=_evidence_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _graph_fixture, _negative in {
    "graph-url-hyperlink": False,
    "graph-canonical-redirect": False,
    "graph-page-structure": False,
    "graph-missing-input": True,
    "graph-rebuild-mismatch": True,
    "graph-as-evidence": True,
}.items():
    _base = f"tests/fixtures/{_graph_fixture}"
    FIXTURE_ORACLES[_graph_fixture] = FixtureOracleRegistration(
        fixture_id=_graph_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_graph_ref=f"{_base}/oracles/expected_graph.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _advanced_graph_fixture, _negative in {
    "projection-rebuild-success": False,
    "graph-signal-frontier-review": False,
    "temporal-graph-foundation": False,
    "projection-missing-watermark": True,
    "projection-mismatch": True,
    "graph-signal-as-evidence": True,
}.items():
    _base = f"tests/fixtures/{_advanced_graph_fixture}"
    FIXTURE_ORACLES[_advanced_graph_fixture] = FixtureOracleRegistration(
        fixture_id=_advanced_graph_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_graph_ref=f"{_base}/oracles/expected_graph.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _memory_fixture, _negative in {
    "memory-write-retrieve-success": False,
    "memory-invalidation-exclusion": False,
    "cross-scope-sanitized-memory": False,
    "poisoned-memory-blocked": True,
    "unauthorized-cross-scope-memory": True,
    "memory-as-evidence": True,
}.items():
    _base = f"tests/fixtures/{_memory_fixture}"
    FIXTURE_ORACLES[_memory_fixture] = FixtureOracleRegistration(
        fixture_id=_memory_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _multi_agent_fixture, _negative in {
    "multi-agent-repair-success": False,
    "coordination-arbitration-success": False,
    "repair-loop-evidence-success": False,
    "owner-service-bypass": True,
    "unresolved-coordination-conflict": True,
    "agent-reasoning-as-evidence": True,
}.items():
    _base = f"tests/fixtures/{_multi_agent_fixture}"
    FIXTURE_ORACLES[_multi_agent_fixture] = FixtureOracleRegistration(
        fixture_id=_multi_agent_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _ops_fixture, _negative in {
    "review-console-success": False,
    "replay-audit-success": False,
    "quality-dashboard-success": False,
    "missing-review-evidence": True,
    "unresolved-failure-without-recovery": True,
    "stale-dashboard-projection": True,
    "unsafe-recovery-without-review": True,
}.items():
    _base = f"tests/fixtures/{_ops_fixture}"
    FIXTURE_ORACLES[_ops_fixture] = FixtureOracleRegistration(
        fixture_id=_ops_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _export_fixture, _negative in {
    "export-file-success": False,
    "export-api-success": False,
    "export-correction-withdrawal-success": False,
    "export-missing-receipt": True,
    "duplicate-export-idempotency": True,
    "withdrawal-missing-mapping": True,
    "destination-unsupported-withdrawal": True,
    "correction-without-withdrawal": True,
}.items():
    _base = f"tests/fixtures/{_export_fixture}"
    FIXTURE_ORACLES[_export_fixture] = FixtureOracleRegistration(
        fixture_id=_export_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _scale_fixture, _negative in {
    "scale-sharding-success": False,
    "backpressure-autoscale-success": False,
    "dead-letter-recovery-success": False,
    "stale-lease-without-recovery": True,
    "unfair-site-starvation": True,
    "autoscale-without-policy": True,
    "dead-letter-missing-failure-record": True,
    "replay-missing-scale-refs": True,
}.items():
    _base = f"tests/fixtures/{_scale_fixture}"
    FIXTURE_ORACLES[_scale_fixture] = FixtureOracleRegistration(
        fixture_id=_scale_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _persistence_fixture, _negative in {
    "persistence-transaction-success": False,
    "idempotent-replay-success": False,
    "queue-lease-recovery-success": False,
    "non-atomic-commit": True,
    "idempotency-not-persisted": True,
    "event-log-gap": True,
    "outbox-dispatch-missing": True,
    "artifact-index-missing": True,
    "lease-heartbeat-missing": True,
}.items():
    _base = f"tests/fixtures/{_persistence_fixture}"
    FIXTURE_ORACLES[_persistence_fixture] = FixtureOracleRegistration(
        fixture_id=_persistence_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )

for _persistence_adapter_fixture, _negative in {
    "sqlite-adapter-conformance-success": False,
    "sqlite-reopen-idempotency-success": False,
    "sqlite-queue-recovery-success": False,
    "postgres-adapter-contract-harness": False,
    "adapter-missing-capability": True,
    "sqlite-idempotency-gap": True,
    "sqlite-event-cursor-gap": True,
    "sqlite-outbox-gap": True,
    "sqlite-migration-missing": True,
}.items():
    _base = f"tests/fixtures/{_persistence_adapter_fixture}"
    FIXTURE_ORACLES[_persistence_adapter_fixture] = FixtureOracleRegistration(
        fixture_id=_persistence_adapter_fixture,
        manifest_ref=f"{_base}/manifest.yaml",
        expected_outputs_ref=f"{_base}/oracles/expected_outputs.yaml",
        expected_evidence_ref=f"{_base}/oracles/expected_evidence.yaml",
        expected_events_ref=f"{_base}/oracles/expected_events.yaml",
        expected_replay_ref=f"{_base}/oracles/expected_replay.yaml",
        thresholds_ref=f"{_base}/oracles/thresholds.yaml",
        negative_case=_negative,
    )


def _target_area(
    area: str,
    owner: OwnerService,
    status: str,
    *,
    materialized: list[str] | None = None,
    placeholders: list[str] | None = None,
) -> TargetContractAreaCoverageRegistration:
    return TargetContractAreaCoverageRegistration(
        contract_area=area,
        owner_service=owner,
        coverage_status=status,
        materialized_contract_refs=materialized or [],
        placeholder_contract_refs=placeholders or [],
        canonical_store_impact="foundation registry only",
        artifact_store_impact="foundation fixture refs only",
        event_refs=["command_committed", "error_recorded"],
        projection_refs=[],
        replay_impact="must define replay refs before target-complete claim",
        privacy_lifecycle_impact="must define privacy lifecycle before target-complete claim",
        required_test_refs=["tests/contract/test_contract_registry.py"],
        followup_spec_gate=(
            None if status == "materialized" else f"follow-up spec required for {area}"
        ),
    )


TARGET_CONTRACT_AREAS: dict[str, TargetContractAreaCoverageRegistration] = {
    "source_adapters": _target_area(
        "source_adapters",
        OwnerService.PORTS,
        "materialized",
        materialized=["SourceAdapterSpec", "SourceAdapterResult", "SourceAdapterCommand"],
    ),
    "commands": _target_area(
        "commands",
        OwnerService.CONTRACTS,
        "materialized",
        materialized=["CommandEnvelope", "CommandResult", "CommandTypeSpec", "BaseCommandPayload"],
    ),
    "events": _target_area(
        "events",
        OwnerService.RUNTIME_EVENTS,
        "materialized",
        materialized=["CrawlRunEvent", "EventTypeSpec"],
    ),
    "replay": _target_area(
        "replay",
        OwnerService.REVIEW_REPLAY,
        "materialized",
        materialized=["ReplayBundleManifest", "ReplayAuditView", "OpsConsoleReport"],
    ),
    "agent_runtime": _target_area(
        "agent_runtime",
        OwnerService.AGENTS,
        "materialized",
        materialized=[
            "AgentRuntimeSpec",
            "AgentToolSpec",
            "AgentRunRequest",
            "AgentRunResult",
            "AgentActionTrace",
            "AgentRecommendation",
            "MultiAgentWorkflow",
            "AgentHandoff",
            "CoordinationDecision",
            "DriftRepairSignal",
            "MultiAgentRepairReport",
        ],
    ),
    "fixture_oracles": _target_area(
        "fixture_oracles",
        OwnerService.TESTS,
        "materialized",
        materialized=[
            "BenchmarkFixtureManifest",
            "ExpectedOutputOracle",
            "ExpectedEvidenceCoverageOracle",
            "ExpectedEventSequenceOracle",
            "ExpectedGraphOracle",
            "FailureInjectionPlan",
            "DRRestoreOracle",
            "ReplayBundleOracle",
        ],
    ),
    "evidence": _target_area(
        "evidence",
        OwnerService.EVIDENCE,
        "materialized",
        materialized=[
            "EvidencePacket",
            "EvidenceCoverageResult",
            "EvidenceAnchor",
            "EvidencePacketManifest",
        ],
    ),
    "verification": _target_area(
        "verification",
        OwnerService.VERIFY,
        "materialized",
        materialized=["VerificationDecision", "ReviewDecision"],
    ),
    "publication": _target_area(
        "publication",
        OwnerService.PUBLISH,
        "materialized",
        materialized=["PublishedOutput", "OutputManifest", "PublicationReport"],
    ),
    "evidence_publication": _target_area(
        "evidence_publication",
        OwnerService.EVIDENCE,
        "materialized",
        materialized=[
            "EvidenceCoverageResult",
            "EvidencePacket",
            "EvidenceAnchor",
            "EvidencePacketManifest",
            "VerificationDecision",
            "ReviewDecision",
            "PublishedOutput",
            "OutputManifest",
            "PublicationReport",
        ],
    ),
    "projection": _target_area(
        "projection",
        OwnerService.PROJECTION,
        "materialized",
        materialized=[
            "ProjectionSpec",
            "ProjectionWatermark",
            "ProjectionRebuildJob",
            "ProjectionMismatchReport",
        ],
    ),
    "graph": _target_area(
        "graph",
        OwnerService.GRAPH,
        "materialized",
        materialized=[
            "GraphNode",
            "GraphEdge",
            "GraphEdgeProvenance",
            "GraphBuildManifest",
            "GraphBuildReport",
            "GraphSignal",
            "GraphDeltaReport",
            "GraphQualityReport",
            "TemporalGraphProjectionRecord",
            "AdvancedGraphProjectionReport",
        ],
    ),
    "memory": _target_area(
        "memory",
        OwnerService.MEMORY,
        "materialized",
        materialized=[
            "MemoryEvent",
            "MemoryRetrievalTrace",
            "CrossScopeMemoryTunnel",
            "OperationalTemporalMemoryRecord",
            "MemoryKernelReport",
        ],
    ),
    "export": _target_area(
        "export",
        OwnerService.EXPORT,
        "materialized",
        materialized=[
            "ExportTargetSpec",
            "ExportJob",
            "ExportAttempt",
            "ExportDeliveryReceipt",
            "ExportWithdrawalJob",
            "ExportWithdrawalAttempt",
            "ExportCorrectionRecord",
            "ExportReconciliationReport",
        ],
    ),
    "ops": _target_area(
        "ops",
        OwnerService.OPS,
        "materialized",
        materialized=[
            "ReviewItem",
            "ReplayAuditView",
            "FailureRecord",
            "RecoveryAction",
            "DRRestoreReport",
            "QualityReport",
            "OpsDashboardSnapshot",
            "OpsConsoleReport",
        ],
    ),
    "artifact_lifecycle": _target_area(
        "artifact_lifecycle",
        OwnerService.ARTIFACT_LIFECYCLE,
        "materialized",
        materialized=["RuntimeArtifactRef"],
    ),
    "durable_persistence": _target_area(
        "durable_persistence",
        OwnerService.RUNTIME_EVENTS,
        "materialized",
        materialized=[
            "UnitOfWorkRecord",
            "DurableCommandRecord",
            "OutboxRecord",
            "EventCursorRecord",
            "DurableReplayRecoveryReport",
        ],
    ),
    "production_persistence_queue_runtime": _target_area(
        "production_persistence_queue_runtime",
        OwnerService.RUNTIME_EVENTS,
        "materialized",
        materialized=[
            "PersistenceAdapterSpec",
            "PersistenceTransactionRecord",
            "IdempotencyPersistenceRecord",
            "PersistentQueueOperationRecord",
            "PersistenceRuntimeReport",
        ],
    ),
    "concrete_persistence_adapters": _target_area(
        "concrete_persistence_adapters",
        OwnerService.PORTS,
        "materialized",
        materialized=[
            "PersistenceAdapterSpec",
            "PersistenceMigrationRecord",
            "PersistenceAdapterConformanceReport",
            "PersistenceAdapterFixtureManifest",
            "PersistenceTransactionRecord",
            "IdempotencyPersistenceRecord",
            "PersistentQueueOperationRecord",
        ],
    ),
    "scheduler": _target_area(
        "scheduler",
        OwnerService.SCHEDULER,
        "materialized",
        materialized=[
            "FrontierItem",
            "QueueLease",
            "SchedulerRecoveryReport",
            "QueueTopologySpec",
            "QueueItem",
            "ShardLease",
            "RetryDeadLetterRecord",
        ],
    ),
    "source_acquisition": _target_area(
        "source_acquisition",
        OwnerService.FETCH,
        "materialized",
        materialized=[
            "FetchAttempt",
            "FetchResult",
            "PageSnapshot",
            "DocumentArtifact",
            "RateLimitDecision",
            "SourceFailureReport",
            "SourceAcquisitionReport",
        ],
    ),
    "network_browser_acquisition": _target_area(
        "network_browser_acquisition",
        OwnerService.FETCH,
        "materialized",
        materialized=[
            "NetworkRequest",
            "NetworkResponse",
            "RedirectHop",
            "NetworkAcquisitionReport",
            "BrowserSandboxPolicy",
            "BrowserInteractionStep",
        ],
    ),
    "normalize_extract": _target_area(
        "normalize_extract",
        OwnerService.NORMALIZE,
        "materialized",
        materialized=[
            "NormalizedDocument",
            "NormalizationManifest",
            "TextAnchor",
            "AnchorMap",
            "LinkProvenance",
            "PageTypeClassification",
            "SiteModel",
            "ExtractionStrategy",
            "ExtractionCandidate",
            "NormalizeExtractReport",
        ],
    ),
    "scale_reliability": _target_area(
        "scale_reliability",
        OwnerService.OPS,
        "materialized",
        materialized=[
            "QueueTopologySpec",
            "QueueItem",
            "ShardLease",
            "RetryDeadLetterRecord",
            "BackpressureSignal",
            "AutoscalingDecision",
            "ScaleRecoveryReport",
        ],
    ),
}

REQUIRED_TARGET_AREAS = set(TARGET_CONTRACT_AREAS)


def _import_model(path: str) -> type[Any] | None:
    module_name, _, attr = path.rpartition(".")
    try:
        module = importlib.import_module(module_name)
        model = getattr(module, attr)
    except (ImportError, AttributeError):
        return None
    return model if isinstance(model, type) else None


def validate_registry() -> RegistryValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    for name, contract_registration in FOUNDATION_CONTRACTS.items():
        if contract_registration.contract_name != name:
            errors.append(f"contract key/name mismatch: {name}")
        if not contract_registration.test_refs:
            errors.append(f"{name} missing test_refs")
        model = _import_model(contract_registration.python_model)
        if model is None:
            errors.append(
                f"{name} python_model cannot be imported: "
                f"{contract_registration.python_model}"
            )
        elif not hasattr(model, "model_json_schema"):
            errors.append(f"{name} python_model does not expose JSON schema")

    schema_refs = set(FOUNDATION_CONTRACTS)
    for command_type, command_registration in COMMAND_TYPES.items():
        if command_type != command_registration.command_type:
            errors.append(f"command key/name mismatch: {command_type}")
        if command_registration.payload_schema_ref not in schema_refs:
            errors.append(
                f"{command_type} payload schema missing: "
                f"{command_registration.payload_schema_ref}"
            )
        for event_type in command_registration.emitted_event_types:
            if event_type not in EVENT_TYPES:
                errors.append(f"{command_type} emits unknown event {event_type}")

    for event_type, event_registration in EVENT_TYPES.items():
        if event_type != event_registration.event_type:
            errors.append(f"event key/name mismatch: {event_type}")
        if event_registration.payload_schema_ref not in schema_refs:
            errors.append(
                f"{event_type} payload schema missing: "
                f"{event_registration.payload_schema_ref}"
            )
        if not event_registration.replay_critical_refs:
            errors.append(f"{event_type} missing replay_critical_refs")

    if not {"foundation-fetch-like", "foundation-non-fetch"}.issubset(
        set().union(*(set(item.fixture_refs) for item in SOURCE_ADAPTER_TYPES.values()))
    ):
        errors.append("source adapter fixtures missing fetch-like or non-fetch coverage")

    target_area_keys = set(TARGET_CONTRACT_AREAS)
    if target_area_keys != REQUIRED_TARGET_AREAS:
        errors.append("target contract area set does not match required FR-003 coverage")
    for area, coverage in TARGET_CONTRACT_AREAS.items():
        if area != coverage.contract_area:
            errors.append(f"target area key/name mismatch: {area}")
        if coverage.coverage_status != "materialized" and not coverage.followup_spec_gate:
            errors.append(f"{area} missing followup_spec_gate")
        if not coverage.required_test_refs:
            errors.append(f"{area} missing required_test_refs")

    for fixture_id, fixture in FIXTURE_ORACLES.items():
        if fixture_id != fixture.fixture_id:
            errors.append(f"fixture key/name mismatch: {fixture_id}")
        if not fixture.manifest_ref:
            errors.append(f"{fixture_id} missing manifest_ref")
        if not fixture.expected_replay_ref:
            errors.append(f"{fixture_id} missing expected_replay_ref")

    if "agent-openai-sdk-planner-conformance" not in AGENT_ADAPTER_FIXTURES:
        errors.append("OpenAI Agent SDK conformance fixture missing")
    if "agent-langgraph-workflow-conformance" not in AGENT_ADAPTER_FIXTURES:
        errors.append("LangGraph conformance fixture missing")

    return RegistryValidationReport(ok=not errors, errors=errors, warnings=warnings)


def registry_json() -> str:
    payload = {
        "ok": validate_registry().ok,
        "contracts": FOUNDATION_CONTRACTS,
        "command_types": COMMAND_TYPES,
        "event_types": EVENT_TYPES,
        "source_adapter_types": SOURCE_ADAPTER_TYPES,
        "agent_adapter_fixtures": AGENT_ADAPTER_FIXTURES,
        "fixture_oracles": FIXTURE_ORACLES,
        "target_contract_areas": TARGET_CONTRACT_AREAS,
        "validation": validate_registry(),
    }
    return canonical_json(payload)
