"""Non-fetch source adapter conformance stub."""

from __future__ import annotations

from veracrawl.contracts.enums import AdapterResultStatus, SourceAdapterResultType
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult


class NonFetchSourceAdapter:
    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:foundation",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=command.adapter_spec.adapter_type,
            result_type=SourceAdapterResultType.SEED_PLAN,
            output_refs=[f"seed_plan:{command.source_ref}"],
            policy_decision_refs=["policy:allow-source-adapter"],
            replay_event_refs=[f"event:{command.command_envelope_id}:source_adapter_result_recorded"],
            idempotency_key=f"{command.adapter_spec.id}:{command.source_ref}",
            status=AdapterResultStatus.SUCCEEDED,
        )
