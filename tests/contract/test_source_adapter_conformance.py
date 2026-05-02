from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.factories import source_adapter_command, source_adapter_spec
from veracrawl.adapters.sources.fetch_like_stub import FetchLikeSourceAdapter
from veracrawl.adapters.sources.non_fetch_stub import NonFetchSourceAdapter
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    SourceAdapterResultType,
)
from veracrawl.contracts.registry import SOURCE_ADAPTER_TYPES
from veracrawl.contracts.source_adapter import SourceAdapterResult


def test_all_target_adapter_types_are_registered() -> None:
    assert set(SOURCE_ADAPTER_TYPES) == {item.value for item in AdapterType}


def test_fetch_like_adapter_conformance() -> None:
    result = FetchLikeSourceAdapter().execute(source_adapter_command(AdapterType.HTTP))
    assert result.status == AdapterResultStatus.SUCCEEDED
    assert result.result_type == SourceAdapterResultType.FETCH_RESULT
    assert result.output_refs[0].startswith("fetch:")
    assert result.replay_event_refs


def test_non_fetch_adapter_does_not_fake_fetch_semantics() -> None:
    result = NonFetchSourceAdapter().execute(source_adapter_command(AdapterType.MANUAL_SEED))
    assert result.result_type == SourceAdapterResultType.SEED_PLAN
    assert all(not ref.startswith(("fetch:", "page_snapshot:")) for ref in result.output_refs)


def test_adapter_result_mapping_rejects_mismatch() -> None:
    with pytest.raises(ValidationError):
        SourceAdapterResult(
            id="source-result:mismatch",
            run_id="run:1",
            adapter_spec_id=source_adapter_spec(AdapterType.MANUAL_SEED).id,
            adapter_type=AdapterType.MANUAL_SEED,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=["fetch:bad"],
            idempotency_key="idem",
            status=AdapterResultStatus.SUCCEEDED,
        )


def test_blocked_result_requires_policy_ref() -> None:
    with pytest.raises(ValidationError):
        SourceAdapterResult(
            id="source-result:blocked",
            run_id="run:1",
            adapter_spec_id="adapter:http",
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.BLOCKED_SOURCE,
            idempotency_key="idem",
            status=AdapterResultStatus.BLOCKED,
        )
