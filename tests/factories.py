from __future__ import annotations

from veracrawl.contracts.agent import AgentRunRequest
from veracrawl.contracts.command import CommandEnvelope
from veracrawl.contracts.enums import AdapterType, AgentRole, ReplayMissingRefBehavior
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.replay import ReplayBundleManifest
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterSpec
from veracrawl.policy.gates import decision_for


def command(command_id: str = "cmd:1") -> CommandEnvelope:
    return CommandEnvelope(
        id=command_id,
        command_type="execute_source_adapter",
        target_aggregate_type="SourceAdapterResult",
        target_aggregate_id="source-result:1",
        expected_version=1,
        idempotency_key="idem:1",
        actor_ref="actor:test",
        payload_ref="payload:1",
    )


def event(sequence: int = 1, event_id: str | None = None) -> CrawlRunEvent:
    return CrawlRunEvent(
        id=event_id or f"event:{sequence}",
        run_id="run:1",
        objective_id="objective:1",
        crawl_plan_id="plan:1",
        sequence=sequence,
        event_type="command_committed",
        event_type_spec_id="event-type:command_committed",
        payload_ref=f"payload:{sequence}",
        causation_id="cmd:1",
        correlation_id="corr:1",
        trace_id=f"trace:{sequence}",
        idempotency_key=f"idem:{sequence}",
        state_before={"status": "accepted"},
        state_after={"status": "committed"},
    )


def policy_decision(allow: bool = True) -> PolicyDecision:
    return decision_for(
        decision_id="policy:1",
        run_id="run:1",
        objective_id="objective:1",
        decision_type="source_adapter",
        subject_ref="source:1",
        allow=allow,
        reasons=[] if allow else ["blocked by test"],
    )


def full_replay_manifest() -> ReplayBundleManifest:
    return ReplayBundleManifest(
        id="replay:1",
        run_id="run:1",
        objective_id="objective:1",
        crawl_plan_id="plan:1",
        event_cursor_refs=["cursor:1"],
        event_schema_versions=["1.0"],
        contract_schema_versions=["1.0"],
        artifact_hash_refs=["artifact-hash:1"],
        source_adapter_result_refs=["source-result:1"],
        command_result_refs=["command-result:1"],
        agent_action_trace_refs=["agent-trace:1"],
        model_call_trace_refs=["model-trace:1"],
        tool_call_trace_refs=["tool-trace:1"],
        context_bundle_trace_refs=["context-trace:1"],
        policy_decision_refs=["policy:1"],
        deterministic_clock_ref="clock:fixed",
        randomness_seed_ref="random:1",
        redaction_map_ref="redaction:1",
    )


def missing_replay_manifest(
    behavior: ReplayMissingRefBehavior = ReplayMissingRefBehavior.FAIL_REPLAY,
) -> ReplayBundleManifest:
    return ReplayBundleManifest(
        id="replay:missing",
        run_id="run:1",
        objective_id="objective:1",
        crawl_plan_id="plan:1",
        missing_ref_behavior=behavior,
    )


def source_adapter_spec(adapter_type: AdapterType = AdapterType.HTTP) -> SourceAdapterSpec:
    return SourceAdapterSpec(
        id=f"adapter:{adapter_type.value}",
        name=f"{adapter_type.value} adapter",
        version="1",
        adapter_type=adapter_type,
        supported_source_types=["fixture"],
        metadata_schema_ref="metadata:fixture",
        transformation_schema_ref="transform:fixture",
        policy_refs=["policy:source"],
        idempotency_key_template="{adapter}:{source}",
    )


def source_adapter_command(adapter_type: AdapterType = AdapterType.HTTP) -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:source",
        adapter_spec=source_adapter_spec(adapter_type),
        source_ref="source:fixture",
        policy_snapshot_ref="policy:snapshot",
        deterministic_clock_ref="clock:fixed",
        randomness_seed_ref="random:1",
    )


def agent_request(request_id: str = "agent-request:1") -> AgentRunRequest:
    return AgentRunRequest(
        id=request_id,
        run_id="run:1",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="runtime:fixture",
        objective_ref="objective:1",
        context_bundle_id="context:1",
        allowed_tool_spec_refs=["tool:read"],
        required_output_schema_ref="schema:planner",
        loop_budget_ref="budget:1",
        policy_decision_refs=["policy:prompt_context"],
    )
