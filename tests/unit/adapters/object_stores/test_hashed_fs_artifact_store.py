"""Unit tests for ``HashedFsArtifactStore`` (s15)."""

from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.adapters.object_stores.hashed_fs_artifact_store import (
    HashedFsArtifactStore,
)


def test_write_returns_sha256_ref(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    ref = store.write(b"hello")
    assert ref.startswith("artifact:sha256:")
    # SHA-256 hex digest is 64 chars; the prefix adds 16.
    assert len(ref) == len("artifact:sha256:") + 64


def test_write_same_bytes_returns_same_ref(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    a = store.write(b"identical")
    b = store.write(b"identical")
    assert a == b


def test_write_different_bytes_returns_different_ref(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    a = store.write(b"alpha")
    b = store.write(b"beta")
    assert a != b


def test_read_round_trip_byte_equal(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    payload = b"\x00\x01\x02 round-trip me \xff\xfe"
    ref = store.write(payload)
    assert store.read(ref) == payload


def test_exists_true_after_write(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    ref = store.write(b"hello")
    assert store.exists(ref) is True


def test_read_raises_key_error_for_unknown_ref(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.read("artifact:sha256:" + "0" * 64)


def test_exists_false_for_unknown_or_malformed_ref(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    assert store.exists("artifact:sha256:" + "0" * 64) is False
    assert store.exists("not-a-ref") is False


def test_sidecar_metadata_isolated_from_content_hash(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    ref_a = store.write(b"same", metadata={"created_at": "2026-05-15T12:00:00"})
    ref_b = store.write(b"same", metadata={"created_at": "2099-01-01T00:00:00"})
    # Metadata differs but content is identical → same ref.
    assert ref_a == ref_b
    # And the second write's metadata is stored.
    assert store.metadata_for(ref_a)["created_at"] == "2099-01-01T00:00:00"


def test_persists_across_reopen(tmp_path: Path) -> None:
    a = HashedFsArtifactStore(root=tmp_path)
    ref = a.write(b"durable")
    b = HashedFsArtifactStore(root=tmp_path)
    assert b.read(ref) == b"durable"


def test_metadata_for_unknown_ref_raises_key_error(tmp_path: Path) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.metadata_for("artifact:sha256:" + "0" * 64)


def test_metadata_for_known_ref_without_sidecar_returns_empty(
    tmp_path: Path,
) -> None:
    store = HashedFsArtifactStore(root=tmp_path)
    ref = store.write(b"bare")  # no metadata
    assert store.metadata_for(ref) == {}
