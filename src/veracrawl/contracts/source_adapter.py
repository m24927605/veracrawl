"""Source adapter contract models."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AdapterResultStatus, AdapterType, SourceAdapterResultType

ADAPTER_RESULT_MAPPING: dict[AdapterType, set[SourceAdapterResultType]] = {
    AdapterType.HTTP: {
        SourceAdapterResultType.FETCH_RESULT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.SITEMAP: {
        SourceAdapterResultType.DISCOVERED_LINKS,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.RSS: {
        SourceAdapterResultType.DISCOVERED_LINKS,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.BROWSER_SNAPSHOT: {
        SourceAdapterResultType.BROWSER_SNAPSHOT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.AUTHORIZED_SESSION: {
        SourceAdapterResultType.SESSION_STATE,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.API_SOURCE: {
        SourceAdapterResultType.API_PAYLOAD,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.DOCUMENT_SOURCE: {
        SourceAdapterResultType.DOCUMENT_ARTIFACT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.FILE_IMPORT: {SourceAdapterResultType.FILE_ARTIFACT},
    AdapterType.MANUAL_SEED: {SourceAdapterResultType.SEED_PLAN},
    AdapterType.PRIOR_SNAPSHOT: {SourceAdapterResultType.PRIOR_SNAPSHOT_REF},
}


class SourceAdapterSpec(TimestampedModel):
    id: str
    name: str
    version: str
    adapter_type: AdapterType
    supported_source_types: list[str] = Field(default_factory=list)
    metadata_schema_ref: Ref
    transformation_schema_ref: Ref
    default_rate_limits: dict[str, object] = Field(default_factory=dict)
    credential_requirements: list[str] = Field(default_factory=list)
    policy_refs: list[Ref] = Field(default_factory=list)
    idempotency_key_template: str
    freshness_semantics: dict[str, object] = Field(default_factory=dict)


class SourceAdapterResult(TimestampedModel):
    id: str
    run_id: str
    adapter_spec_id: str
    adapter_type: AdapterType
    result_type: SourceAdapterResultType
    output_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_event_refs: list[Ref] = Field(default_factory=list)
    idempotency_key: str
    status: AdapterResultStatus

    @model_validator(mode="after")
    def validate_result_mapping(self) -> SourceAdapterResult:
        if self.result_type not in ADAPTER_RESULT_MAPPING[self.adapter_type]:
            raise ValueError(
                f"{self.adapter_type.value} cannot emit result_type {self.result_type.value}"
            )
        if self.status == AdapterResultStatus.BLOCKED:
            if self.result_type != SourceAdapterResultType.BLOCKED_SOURCE:
                raise ValueError("blocked adapter results must use blocked_source result_type")
            if not self.policy_decision_refs:
                raise ValueError("blocked adapter results require policy_decision_refs")
        if self.status == AdapterResultStatus.SUCCEEDED and not self.output_refs:
            raise ValueError("succeeded adapter results require output_refs")
        if self.result_type in {
            SourceAdapterResultType.SEED_PLAN,
            SourceAdapterResultType.PRIOR_SNAPSHOT_REF,
            SourceAdapterResultType.DOCUMENT_ARTIFACT,
            SourceAdapterResultType.FILE_ARTIFACT,
            SourceAdapterResultType.SESSION_STATE,
        }:
            forbidden = [
                ref for ref in self.output_refs if ref.startswith(("fetch:", "page_snapshot:"))
            ]
            if forbidden:
                raise ValueError("non-fetch adapter result must not emit fetch/page snapshot refs")
        return self


class SourceAdapterCommand(TimestampedModel):
    command_envelope_id: str
    adapter_spec: SourceAdapterSpec
    source_ref: Ref
    policy_snapshot_ref: Ref
    deterministic_clock_ref: Ref | None = None
    randomness_seed_ref: Ref | None = None
    credential_scope_ref: Ref | None = None
