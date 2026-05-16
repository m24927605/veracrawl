"""Tests for ``PersistedRuntimeArtifactStore`` (s15 reconciliation)."""

from __future__ import annotations

from pathlib import Path

from veracrawl.adapters.object_stores.hashed_fs_artifact_store import (
    HashedFsArtifactStore,
)
from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)
from veracrawl.artifact_lifecycle.persisted_runtime_artifact_store import (
    PersistedRuntimeArtifactStore,
)
from veracrawl.contracts.enums import ArtifactType, OwnerService, PrivacyClassification


def _write(store: PersistedRuntimeArtifactStore, *, artifact_id: str, content: str) -> None:
    store.write(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.RAW_SOURCE,
        producer_service=OwnerService.FETCH,
        source_ref=f"source:{artifact_id}",
        content=content,
        privacy_classification=PrivacyClassification.INTERNAL,
    )


def test_write_returns_runtime_artifact_ref_with_rich_metadata() -> None:
    byte_store = InMemoryBytesArtifactStore()
    store = PersistedRuntimeArtifactStore(byte_store=byte_store)
    ref = store.write(
        artifact_id="art:1",
        artifact_type=ArtifactType.RAW_SOURCE,
        producer_service=OwnerService.FETCH,
        source_ref="source:1",
        content="hello world",
    )
    assert ref.id == "art:1"
    assert ref.artifact_type is ArtifactType.RAW_SOURCE
    assert ref.producer_service is OwnerService.FETCH
    assert ref.size_bytes == len("hello world")
    assert ref.lifecycle_state_ref == "lifecycle:art:1:active"


def test_read_round_trips_content_via_in_memory_bytes_store() -> None:
    byte_store = InMemoryBytesArtifactStore()
    store = PersistedRuntimeArtifactStore(byte_store=byte_store)
    _write(store, artifact_id="art:1", content="hello round trip")
    assert store.read("art:1") == "hello round trip"


def test_read_returns_none_for_unknown_artifact_id() -> None:
    store = PersistedRuntimeArtifactStore(byte_store=InMemoryBytesArtifactStore())
    assert store.read("art:never-written") is None


def test_list_refs_returns_all_written_artifacts() -> None:
    store = PersistedRuntimeArtifactStore(byte_store=InMemoryBytesArtifactStore())
    _write(store, artifact_id="art:1", content="a")
    _write(store, artifact_id="art:2", content="b")
    ids = {r.id for r in store.list_refs()}
    assert ids == {"art:1", "art:2"}


def test_get_ref_returns_runtime_artifact_ref() -> None:
    store = PersistedRuntimeArtifactStore(byte_store=InMemoryBytesArtifactStore())
    _write(store, artifact_id="art:1", content="hello")
    ref = store.get_ref("art:1")
    assert ref is not None
    assert ref.id == "art:1"
    assert ref.size_bytes == 5


def test_works_against_hashed_fs_byte_store(tmp_path: Path) -> None:
    """The reconciliation actually unlocks ``HashedFsArtifactStore`` —
    the runtime's rich-metadata API works on top of the durable
    content-addressed byte store.
    """

    byte_store = HashedFsArtifactStore(root=tmp_path)
    store = PersistedRuntimeArtifactStore(byte_store=byte_store)
    _write(store, artifact_id="art:1", content="durable bytes")
    assert store.read("art:1") == "durable bytes"
    # And the bytes really live on disk (under the hashed-fs layout).
    files = list(tmp_path.rglob("*.bin"))
    assert len(files) >= 1


def test_content_addressed_dedup_via_byte_store(tmp_path: Path) -> None:
    """Same content → same byte-store ref even across runtime IDs."""

    byte_store = HashedFsArtifactStore(root=tmp_path)
    store = PersistedRuntimeArtifactStore(byte_store=byte_store)
    _write(store, artifact_id="art:run-a", content="identical content")
    _write(store, artifact_id="art:run-b", content="identical content")
    # Both runtime IDs read back the same content.
    assert store.read("art:run-a") == store.read("art:run-b") == "identical content"
    # Only ONE blob file lives on disk (content-addressed dedup).
    files = list(tmp_path.rglob("*.bin"))
    assert len(files) == 1
