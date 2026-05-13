"""Unit tests for ``LocalFsCrawlArtifactStore``.

The store backs the external crawl runtime's ``CrawlArtifactStorePort``
contract. Tests cover round-trip fidelity, sidecar metadata, the
fixed ``<root>/<run_id>/{artifacts,reports,events,outputs}/`` layout,
and path-traversal hygiene.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    CrawlArtifactStoreError,
    LocalFsCrawlArtifactStore,
)


def _store(tmp_path: Path) -> LocalFsCrawlArtifactStore:
    return LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-demo")


def _meta(**overrides: str) -> dict[str, str]:
    base = {
        "source_url": "https://demo.example/page",
        "privacy_classification": "internal",
        "replay_ref": "replay:demo",
    }
    base.update(overrides)
    return base


def test_constructor_creates_run_directory_layout(tmp_path: Path) -> None:
    _store(tmp_path)
    run_root = tmp_path / "run-demo"
    for child in ("artifacts", "reports", "events", "outputs"):
        assert (run_root / child).is_dir(), child
    for sub in ("raw-html", "documents", "normalized", "screenshots", "metadata"):
        assert (run_root / "artifacts" / sub).is_dir(), sub


def test_put_bytes_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    payload = b"<html><body>hi</body></html>"
    result = store.put_bytes(
        "raw-html/abc",
        payload,
        content_type="text/html",
        metadata=_meta(),
    )
    assert result.size_bytes == len(payload)
    assert result.content_digest == hashlib.sha256(payload).hexdigest()
    assert result.artifact_ref == "raw-html/abc"
    assert store.get_bytes("raw-html/abc") == payload


def test_put_text_round_trip_uses_utf8(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = store.put_text(
        "documents/page",
        "héllo wörld",
        content_type="text/plain; charset=utf-8",
        metadata=_meta(),
    )
    assert store.get_bytes("documents/page") == "héllo wörld".encode()
    assert result.size_bytes == len("héllo wörld".encode())


def test_exists_reflects_writes(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert not store.exists("raw-html/x")
    store.put_bytes("raw-html/x", b"x", content_type="text/plain", metadata=_meta())
    assert store.exists("raw-html/x")


def test_sidecar_metadata_records_evidence_fields(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.put_bytes(
        "raw-html/abc",
        b"data",
        content_type="text/html",
        metadata=_meta(extra="custom"),
    )
    sidecar = tmp_path / "run-demo" / "artifacts" / "raw-html" / "abc.meta.json"
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text("utf-8"))
    assert payload["artifact_ref"] == "raw-html/abc"
    assert payload["content_type"] == "text/html"
    assert payload["content_digest"] == hashlib.sha256(b"data").hexdigest()
    assert payload["size_bytes"] == 4
    assert payload["metadata"]["source_url"] == "https://demo.example/page"
    assert payload["metadata"]["extra"] == "custom"
    assert "created_at" in payload


def test_missing_required_metadata_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    bad = _meta()
    bad.pop("source_url")
    with pytest.raises(CrawlArtifactStoreError, match="source_url"):
        store.put_bytes("raw-html/y", b"y", content_type="text/plain", metadata=bad)


def test_path_traversal_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(CrawlArtifactStoreError, match="artifact_ref"):
        store.put_bytes("../escape", b"x", content_type="text/plain", metadata=_meta())
    with pytest.raises(CrawlArtifactStoreError, match="artifact_ref"):
        store.put_bytes(
            "raw-html/../../escape",
            b"x",
            content_type="text/plain",
            metadata=_meta(),
        )


def test_absolute_artifact_ref_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(CrawlArtifactStoreError, match="artifact_ref"):
        store.put_bytes("/etc/passwd", b"x", content_type="text/plain", metadata=_meta())


def test_get_bytes_missing_raises(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(CrawlArtifactStoreError, match="not found"):
        store.get_bytes("raw-html/nope")


def test_re_put_same_ref_is_idempotent_when_bytes_identical(tmp_path: Path) -> None:
    store = _store(tmp_path)
    payload = b"same"
    a = store.put_bytes("raw-html/k", payload, content_type="text/plain", metadata=_meta())
    b = store.put_bytes("raw-html/k", payload, content_type="text/plain", metadata=_meta())
    assert a.content_digest == b.content_digest
    assert store.get_bytes("raw-html/k") == payload


def test_re_put_same_ref_with_different_bytes_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.put_bytes("raw-html/k", b"first", content_type="text/plain", metadata=_meta())
    with pytest.raises(CrawlArtifactStoreError, match="digest"):
        store.put_bytes("raw-html/k", b"second", content_type="text/plain", metadata=_meta())


def test_symlink_in_run_root_refused(tmp_path: Path) -> None:
    # If an attacker plants a symlink at the expected artifact path,
    # the store must refuse to read through it rather than leak the
    # symlink target's bytes back.
    store = _store(tmp_path)
    store.put_bytes("raw-html/k", b"real", content_type="text/plain", metadata=_meta())
    target = tmp_path / "run-demo" / "artifacts" / "raw-html" / "k"
    target.unlink()
    decoy = tmp_path / "decoy"
    decoy.write_bytes(b"attacker")
    target.symlink_to(decoy)
    with pytest.raises(CrawlArtifactStoreError, match="symlink"):
        store.get_bytes("raw-html/k")
