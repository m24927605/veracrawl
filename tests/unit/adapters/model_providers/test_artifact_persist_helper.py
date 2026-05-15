"""Unit tests for ``_artifact_persist`` helpers (s2.1 tests 1-7c)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from veracrawl.adapters.model_providers._artifact_persist import (
    persist_provider_response,
    read_persisted_provider_response,
)
from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)

_T = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
_BYTES = b'{"id":"resp_x","output_text":"hi"}'


def _store() -> InMemoryBytesArtifactStore:
    return InMemoryBytesArtifactStore()


def _persist(store: InMemoryBytesArtifactStore, **overrides: object) -> str:
    kwargs: dict[str, object] = {
        "artifact_store": store,
        "raw_bytes": _BYTES,
        "provider_name": "openai-responses-v2",
        "request_id": "req:1",
        "upstream_id": "resp_x",
        "captured_at": _T,
    }
    kwargs.update(overrides)
    return persist_provider_response(**kwargs)  # type: ignore[arg-type]


# Test 1
def test_persist_returns_artifact_store_write_ref() -> None:
    store = _store()
    ref = _persist(store)
    assert ref.startswith("artifact:sha256:")
    assert store.exists(ref)


# Test 2
def test_persist_writes_raw_bytes_verbatim() -> None:
    store = _store()
    ref = _persist(store)
    assert store.read(ref) == _BYTES


# Test 3
def test_persist_metadata_contains_all_five_fields() -> None:
    store = _store()
    ref = _persist(store)
    meta = store.metadata_for(ref)
    assert set(meta.keys()) == {
        "provider", "request_id", "upstream_id", "captured_at", "bytes_len",
    }


# Test 4
def test_persist_captured_at_serialized_as_iso8601_utc() -> None:
    store = _store()
    ref = _persist(store)
    meta = store.metadata_for(ref)
    s = meta["captured_at"]
    assert isinstance(s, str)
    assert datetime.fromisoformat(s).tzinfo is not None
    assert s.endswith("+00:00")


# Test 5
def test_persist_rejects_blank_request_id() -> None:
    with pytest.raises(ValueError, match="request_id"):
        _persist(_store(), request_id="")


# Test 6
def test_persist_rejects_blank_upstream_id() -> None:
    with pytest.raises(ValueError, match="upstream_id"):
        _persist(_store(), upstream_id="")


# Test 7
def test_persist_rejects_naive_datetime() -> None:
    naive = datetime(2026, 5, 15, 12, 0)
    with pytest.raises(ValueError, match="captured_at must be UTC"):
        _persist(_store(), captured_at=naive)


# Test 7a
def test_persist_rejects_aware_non_utc_datetime() -> None:
    aware = datetime(2026, 5, 15, 12, 0, tzinfo=timezone(timedelta(hours=8)))
    with pytest.raises(ValueError, match="captured_at must be UTC"):
        _persist(_store(), captured_at=aware)


# Test 7b
def test_round_trip_read_returns_persisted_bytes_verbatim() -> None:
    store = _store()
    ref = _persist(store)
    out = read_persisted_provider_response(artifact_store=store, raw_response_ref=ref)
    assert out == _BYTES


# Test 7c
def test_read_raises_key_error_for_unknown_ref() -> None:
    store = _store()
    with pytest.raises(KeyError):
        read_persisted_provider_response(
            artifact_store=store, raw_response_ref="artifact:sha256:notreal",
        )
