"""Contract tests for ``ArtifactStorePort.read`` (s2.1)."""

from __future__ import annotations

import pytest

from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)
from veracrawl.ports.stores import ArtifactStorePort


# Test 26d
def test_artifact_store_port_has_read_method() -> None:
    assert hasattr(ArtifactStorePort, "read")


# Test 26e
def test_in_memory_artifact_store_read_round_trip() -> None:
    store = InMemoryBytesArtifactStore()
    ref = store.write(b"hello", metadata={"k": "v"})
    assert store.read(ref) == b"hello"


# Test 26f
def test_in_memory_artifact_store_read_raises_key_error_for_unknown() -> None:
    store = InMemoryBytesArtifactStore()
    with pytest.raises(KeyError):
        store.read("artifact:sha256:never_written")


def test_in_memory_artifact_store_write_is_content_addressed() -> None:
    store = InMemoryBytesArtifactStore()
    ref_a = store.write(b"same-bytes")
    ref_b = store.write(b"same-bytes")
    assert ref_a == ref_b


def test_in_memory_artifact_store_different_bytes_different_ref() -> None:
    store = InMemoryBytesArtifactStore()
    ref_a = store.write(b"alpha")
    ref_b = store.write(b"beta")
    assert ref_a != ref_b
