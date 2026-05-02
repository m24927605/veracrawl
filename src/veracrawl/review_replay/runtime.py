"""Runtime replay bundle construction for target spine fixtures."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.objective import CrawlObjective, CrawlPlan, CrawlRun
from veracrawl.contracts.replay import ReplayBundleManifest, ReplayValidationReport
from veracrawl.runtime_events.event_store import InMemoryEventStore
from veracrawl.runtime_events.replay import validate_runtime_replay_manifest


def build_runtime_replay_bundle(
    *,
    run: CrawlRun,
    objective: CrawlObjective,
    plan: CrawlPlan,
    event_store: InMemoryEventStore,
    command_result_refs: list[Ref],
    policy_decision_refs: list[Ref],
    source_adapter_result_refs: list[Ref],
    artifact_refs: list[Ref],
    normalized_document_refs: list[Ref],
    extraction_candidate_refs: list[Ref],
    evidence_packet_refs: list[Ref],
    verification_decision_refs: list[Ref],
    output_manifest_refs: list[Ref],
    force_gap: bool = False,
) -> tuple[ReplayBundleManifest, ReplayValidationReport, list[str]]:
    event_count = len(event_store.stream(run.id))
    redaction_ref = None if force_gap else f"redaction-map:{run.id}"
    manifest = ReplayBundleManifest(
        id=f"replay:{run.id}",
        run_id=run.id,
        objective_id=objective.id,
        crawl_plan_id=plan.id,
        event_cursor_refs=[f"event-cursor:{run.id}:1-{event_count}"] if event_count else [],
        event_schema_versions=["1.0"],
        contract_schema_versions=["1.0"],
        artifact_hash_refs=[f"artifact-hash:{artifact}" for artifact in artifact_refs],
        source_adapter_result_refs=source_adapter_result_refs,
        command_result_refs=command_result_refs,
        agent_action_trace_refs=[f"agent-trace:{run.id}:structural-none"],
        model_call_trace_refs=[f"model-trace:{run.id}:structural-none"],
        tool_call_trace_refs=[f"tool-trace:{run.id}:owner-commands"],
        context_bundle_trace_refs=[f"context-trace:{run.id}:runtime"],
        policy_decision_refs=policy_decision_refs,
        deterministic_clock_ref=f"clock:{run.id}:fixed",
        randomness_seed_ref=f"random:{run.id}:fixed",
        redaction_map_ref=redaction_ref,
        completeness_result=CompletenessResult.NEEDS_REVIEW,
    )
    runtime_refs = {
        "normalized_document_refs": normalized_document_refs,
        "extraction_candidate_refs": extraction_candidate_refs,
        "evidence_packet_refs": evidence_packet_refs,
        "verification_decision_refs": verification_decision_refs,
        "output_manifest_refs": [] if force_gap else output_manifest_refs,
    }
    report = validate_runtime_replay_manifest(manifest, runtime_refs=runtime_refs)
    return manifest, report, report.missing_ref_fields
