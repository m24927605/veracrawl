"""Runtime source adapter execution boundary."""

from __future__ import annotations

from veracrawl.artifact_lifecycle.runtime import InMemoryArtifactStore
from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    ArtifactType,
    OwnerService,
    PolicyDecisionValue,
    SourceAdapterResultType,
)
from veracrawl.contracts.objective import CrawlRun
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.source_adapter import SourceAdapterResult
from veracrawl.control.runtime import RuntimeScenario, require_owner


def _result_type_for_adapter(adapter_type: AdapterType) -> SourceAdapterResultType:
    if adapter_type == AdapterType.DOCUMENT_SOURCE:
        return SourceAdapterResultType.DOCUMENT_ARTIFACT
    if adapter_type == AdapterType.FILE_IMPORT:
        return SourceAdapterResultType.FILE_ARTIFACT
    if adapter_type == AdapterType.MANUAL_SEED:
        return SourceAdapterResultType.SEED_PLAN
    if adapter_type == AdapterType.PRIOR_SNAPSHOT:
        return SourceAdapterResultType.PRIOR_SNAPSHOT_REF
    if adapter_type == AdapterType.API_SOURCE:
        return SourceAdapterResultType.API_PAYLOAD
    if adapter_type == AdapterType.BROWSER_SNAPSHOT:
        return SourceAdapterResultType.BROWSER_SNAPSHOT
    if adapter_type in {AdapterType.SITEMAP, AdapterType.RSS}:
        return SourceAdapterResultType.DISCOVERED_LINKS
    return SourceAdapterResultType.FETCH_RESULT


def execute_source_adapter_fixture(
    *,
    run: CrawlRun,
    policy_decision: PolicyDecision,
    artifact_store: InMemoryArtifactStore,
    scenario: RuntimeScenario,
    adapter_type: AdapterType = AdapterType.HTTP,
    owner: OwnerService = OwnerService.FETCH,
) -> tuple[SourceAdapterResult, RuntimeArtifactRef | None]:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.FETCH,
        target_ref=f"source:{run.id}",
    )

    if policy_decision.decision != PolicyDecisionValue.ALLOW:
        return (
            SourceAdapterResult(
                id=f"source-result:{run.id}",
                run_id=run.id,
                adapter_spec_id=f"adapter:{adapter_type.value}:fixture",
                adapter_type=adapter_type,
                result_type=SourceAdapterResultType.BLOCKED_SOURCE,
                output_refs=[],
                policy_decision_refs=[policy_decision.id],
                replay_event_refs=[],
                idempotency_key=f"source:{run.id}",
                status=AdapterResultStatus.BLOCKED,
            ),
            None,
        )

    if scenario == "adapter-mismatch":
        SourceAdapterResult(
            id=f"source-result:{run.id}:invalid",
            run_id=run.id,
            adapter_spec_id="adapter:http-invalid",
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.DOCUMENT_ARTIFACT,
            output_refs=["document:invalid"],
            policy_decision_refs=[policy_decision.id],
            replay_event_refs=[],
            idempotency_key=f"source:{run.id}:invalid",
            status=AdapterResultStatus.SUCCEEDED,
        )

    result_type = _result_type_for_adapter(adapter_type)
    raw_artifact = artifact_store.write(
        artifact_id=f"artifact:{run.id}:raw",
        artifact_type=ArtifactType.RAW_SOURCE,
        producer_service=OwnerService.FETCH,
        source_ref="source:fixture",
        content='{"name":"Fixture Product","price":"19.99","currency":"USD"}',
    )
    return (
        SourceAdapterResult(
            id=f"source-result:{run.id}",
            run_id=run.id,
            adapter_spec_id=f"adapter:{adapter_type.value}:fixture",
            adapter_type=adapter_type,
            result_type=result_type,
            output_refs=[raw_artifact.id],
            policy_decision_refs=[policy_decision.id],
            replay_event_refs=[],
            idempotency_key=f"source:{run.id}",
            status=AdapterResultStatus.SUCCEEDED,
        ),
        raw_artifact,
    )
