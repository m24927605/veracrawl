from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.adapters.sources.deterministic import DeterministicSourceAdapter
from veracrawl.contracts.enums import (
    AdapterType,
    FetchResultStatus,
    SourceAdapterResultType,
)
from veracrawl.contracts.fetch import FetchAttempt, FetchResult, PageSnapshot
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec


def _command(adapter_type: AdapterType) -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id=f"cmd:{adapter_type.value}",
        adapter_spec=source_adapter_spec(adapter_type),
        source_ref=f"source:{adapter_type.value}",
        policy_snapshot_ref="policy:snapshot",
    )


def test_deterministic_adapters_emit_natural_result_types() -> None:
    expected = {
        AdapterType.HTTP: SourceAdapterResultType.FETCH_RESULT,
        AdapterType.SITEMAP: SourceAdapterResultType.DISCOVERED_LINKS,
        AdapterType.RSS: SourceAdapterResultType.DISCOVERED_LINKS,
        AdapterType.API_SOURCE: SourceAdapterResultType.API_PAYLOAD,
        AdapterType.DOCUMENT_SOURCE: SourceAdapterResultType.DOCUMENT_ARTIFACT,
    }
    for adapter_type, result_type in expected.items():
        result = DeterministicSourceAdapter(adapter_type=adapter_type).execute(
            _command(adapter_type)
        )
        assert result.result_type == result_type
        assert result.output_refs


def test_adapter_mismatch_is_rejected_by_source_result_contract() -> None:
    with pytest.raises(ValidationError):
        DeterministicSourceAdapter(
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.DOCUMENT_ARTIFACT,
        ).execute(_command(AdapterType.HTTP))


def test_fetch_contracts_require_attempt_and_artifact_refs() -> None:
    with pytest.raises(ValidationError):
        FetchAttempt(
            id="fetch-attempt:bad",
            run_ref="run:bad",
            frontier_item_ref="frontier:bad",
            lease_ref="lease:bad",
            adapter_spec_ref="adapter:http",
            source_ref="source:bad",
            attempt_number=0,
        )
    with pytest.raises(ValidationError):
        FetchResult(
            id="fetch-result:bad",
            attempt_ref="attempt:bad",
            source_ref="source:bad",
            status=FetchResultStatus.SUCCEEDED,
            result_type=SourceAdapterResultType.FETCH_RESULT,
        )
    with pytest.raises(ValidationError):
        PageSnapshot(
            id="page-snapshot:bad",
            fetch_result_ref="fetch-result:bad",
            source_ref="source:bad",
            raw_artifact_ref="",
            content_digest="",
            content_type="text/html",
            canonical_ref="canonical:bad",
            privacy_classification_ref="privacy:internal",
        )
