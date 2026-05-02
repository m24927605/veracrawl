"""Deterministic source adapter fixtures.

These adapters intentionally avoid real network, browser, storage, queue, model,
or agent framework dependencies. They prove source-family semantics behind
SourceAdapterPort.
"""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult

RESULT_TYPE_BY_ADAPTER: dict[AdapterType, SourceAdapterResultType] = {
    AdapterType.HTTP: SourceAdapterResultType.FETCH_RESULT,
    AdapterType.SITEMAP: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.RSS: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.API_SOURCE: SourceAdapterResultType.API_PAYLOAD,
    AdapterType.DOCUMENT_SOURCE: SourceAdapterResultType.DOCUMENT_ARTIFACT,
}


@dataclass(frozen=True)
class DeterministicSourcePayload:
    artifact_ref: str
    content: str
    content_type: str
    metadata_ref: str


class DeterministicSourceAdapter:
    def __init__(
        self,
        *,
        adapter_type: AdapterType,
        result_type: SourceAdapterResultType | None = None,
        status: AdapterResultStatus = AdapterResultStatus.SUCCEEDED,
        malformed: bool = False,
    ) -> None:
        self.adapter_type = adapter_type
        self.result_type = result_type or RESULT_TYPE_BY_ADAPTER[adapter_type]
        self.status = status
        self.malformed = malformed

    def payload_for(self, command: SourceAdapterCommand) -> DeterministicSourcePayload:
        content = (
            "{malformed"
            if self.malformed
            else f"deterministic source payload for {self.adapter_type.value}:{command.source_ref}"
        )
        return DeterministicSourcePayload(
            artifact_ref=f"artifact:{command.command_envelope_id}:raw",
            content=content,
            content_type=(
                "application/json"
                if self.adapter_type == AdapterType.API_SOURCE
                else "text/html"
                if self.adapter_type == AdapterType.HTTP
                else "application/xml"
                if self.adapter_type in {AdapterType.SITEMAP, AdapterType.RSS}
                else "application/octet-stream"
            ),
            metadata_ref=f"metadata:{command.command_envelope_id}:{self.adapter_type.value}",
        )

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        payload = self.payload_for(command)
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:source-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=command.adapter_spec.adapter_type,
            result_type=self.result_type,
            output_refs=(
                [payload.artifact_ref]
                if self.status == AdapterResultStatus.SUCCEEDED
                else []
            ),
            policy_decision_refs=["policy:source-allow"],
            replay_event_refs=[f"event:{command.command_envelope_id}:source_adapter_result_recorded"],
            idempotency_key=f"{command.adapter_spec.id}:{command.source_ref}",
            status=self.status,
        )
