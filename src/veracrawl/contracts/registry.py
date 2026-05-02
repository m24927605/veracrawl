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
    "VerificationDecision": _contract(
        "VerificationDecision",
        OwnerService.VERIFY,
        "verification",
        mutation_allowed=True,
        tests=["tests/unit/test_evidence_publication_gates.py"],
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
        materialized=["ReplayBundleManifest"],
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
        materialized=["EvidencePacket", "EvidenceCoverageResult"],
    ),
    "verification": _target_area(
        "verification",
        OwnerService.VERIFY,
        "materialized",
        materialized=["VerificationDecision"],
    ),
    "publication": _target_area(
        "publication",
        OwnerService.PUBLISH,
        "materialized",
        materialized=["PublishedOutput", "OutputManifest"],
    ),
    "projection": _target_area(
        "projection",
        OwnerService.PROJECTION,
        "foundation_placeholder",
        placeholders=["ProjectionWatermark"],
    ),
    "graph": _target_area(
        "graph",
        OwnerService.GRAPH,
        "foundation_placeholder",
        placeholders=["GraphBuildManifest"],
    ),
    "memory": _target_area(
        "memory",
        OwnerService.MEMORY,
        "foundation_placeholder",
        placeholders=["MemoryEvent"],
    ),
    "export": _target_area(
        "export",
        OwnerService.EXPORT,
        "foundation_placeholder",
        placeholders=["ExportJob"],
    ),
    "ops": _target_area(
        "ops",
        OwnerService.OPS,
        "foundation_placeholder",
        placeholders=["FailureRecord", "DRRestoreReport"],
    ),
    "artifact_lifecycle": _target_area(
        "artifact_lifecycle",
        OwnerService.ARTIFACT_LIFECYCLE,
        "materialized",
        materialized=["RuntimeArtifactRef"],
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
