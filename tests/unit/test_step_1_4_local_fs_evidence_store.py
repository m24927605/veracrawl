"""Unit tests for ``LocalFsEvidenceArtifactStore``.

design.md §4 Phase 1 step 1.4 production default for
``EvidenceArtifactStorePort``. Behaviors under test:

1. **Round-trip**: put / get returns the same bytes.
2. **Content addressing**: same payload → same artifact_ref + digest.
3. **Path-traversal hygiene**: ``run_ref="../../../etc/passwd"``
   never escapes the configured root.
4. **Atomic writes**: a concurrent reader never sees a partial file.
5. **Mode 0o600**: persisted files are owner-only on POSIX.
6. **Redaction gate**: ``put(kind=HAR, redaction_applied=False)``
   raises :class:`EvidenceRedactionRequired`.
7. **Idempotent put**: two ``put`` calls with the same payload land
   on the same path without erroring.
8. **get on unknown ref**: returns ``None``, never reads outside the
   configured root.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from veracrawl.adapters.object_stores.local_fs_evidence_store import (
    LocalFsEvidenceArtifactStore,
)
from veracrawl.ports.evidence_artifact_store import (
    ArtifactKind,
    EvidenceRedactionRequired,
)


@pytest.fixture
def store(tmp_path: Path) -> LocalFsEvidenceArtifactStore:
    return LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")


def test_round_trip_har_payload(store: LocalFsEvidenceArtifactStore) -> None:
    payload = b'{"log":{"version":"1.2","entries":[]}}'
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    assert result.size_bytes == len(payload)
    fetched = store.get(artifact_ref=result.artifact_ref)
    assert fetched == payload


def test_same_payload_yields_same_artifact_ref(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    payload = b'{"log":{}}'
    a = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    b = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    assert a.artifact_ref == b.artifact_ref
    assert a.content_digest_sha256 == b.content_digest_sha256


def test_different_payload_yields_different_artifact_ref(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    a = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{"a":1}}',
        content_type="application/json",
        redaction_applied=True,
    )
    b = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{"a":2}}',
        content_type="application/json",
        redaction_applied=True,
    )
    assert a.artifact_ref != b.artifact_ref


def test_path_traversal_run_ref_stays_inside_root(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    store = LocalFsEvidenceArtifactStore(root=root)
    # An attacker hands us a ref engineered to escape the root.
    result = store.put(
        run_ref="../../../etc/passwd",
        attempt_ref="../../also/bad",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    # The persisted file must live under root — verify by walking
    # the root tree.
    persisted = list(root.rglob("har-*.har.json"))
    assert len(persisted) == 1
    persisted_path = persisted[0]
    assert root in persisted_path.parents
    # No file should have leaked outside the root.
    assert not (tmp_path / "etc").exists()
    assert not (tmp_path.parent / "etc").exists()
    fetched = store.get(artifact_ref=result.artifact_ref)
    assert fetched == b'{"log":{}}'


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes only")
def test_persisted_file_is_owner_only(store: LocalFsEvidenceArtifactStore) -> None:
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    # Walk and find the persisted file.
    root = store._root  # noqa: SLF001 — test-only access
    files = list(root.rglob("*.har.json"))
    assert len(files) == 1
    mode = files[0].stat().st_mode
    # Owner-only: no group/other perms set.
    assert (mode & stat.S_IRWXG) == 0
    assert (mode & stat.S_IRWXO) == 0
    # Verify get round-trip still works.
    assert store.get(artifact_ref=result.artifact_ref) == b'{"log":{}}'


def test_put_rejects_unredacted_har_payload(store: LocalFsEvidenceArtifactStore) -> None:
    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:fixture",
            attempt_ref="attempt:1",
            kind=ArtifactKind.HAR,
            payload=b'{"log":{}}',
            content_type="application/json",
            redaction_applied=False,
        )


def test_put_rejects_unredacted_screenshot(store: LocalFsEvidenceArtifactStore) -> None:
    """Iter-2 #6: every kind requires attestation; screenshots can
    capture rendered PII / tokens, so the producer must affirm
    lifecycle policy was applied."""

    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:fixture",
            attempt_ref="attempt:1",
            kind=ArtifactKind.SCREENSHOT,
            payload=b"\x89PNG\r\n\x1a\n",
            content_type="image/png",
            redaction_applied=False,
        )


def test_put_accepts_attested_screenshot(store: LocalFsEvidenceArtifactStore) -> None:
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.SCREENSHOT,
        payload=b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
        redaction_applied=True,
    )
    fetched = store.get(artifact_ref=result.artifact_ref)
    assert fetched == b"\x89PNG\r\n\x1a\n"


def test_get_unknown_artifact_ref_returns_none(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    assert store.get(artifact_ref="artifact:evidence:har:x:y:nope") is None
    # Malformed ref shapes also return None — never a path read outside root.
    assert store.get(artifact_ref="not-an-evidence-ref") is None
    assert store.get(artifact_ref="artifact:evidence:har:..:..:digest") is None
    assert store.get(artifact_ref="artifact:evidence:har:run/escape:attempt:digest") is None


def test_idempotent_put_same_payload_overwrites_atomically(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    # Two writers landing identical bytes on the same path: must
    # succeed without raising and the file must stay valid.
    payload = b'{"log":{"x":1}}'
    a = store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    b = store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    assert a.artifact_ref == b.artifact_ref
    assert store.get(artifact_ref=a.artifact_ref) == payload


def test_no_partial_file_on_disk_during_atomic_write(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    """After ``put`` returns, no ``.tmp`` staging file remains."""

    store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    root = store._root  # noqa: SLF001
    leftovers = list(root.rglob("*.tmp"))
    assert leftovers == []


def test_two_run_refs_produce_distinct_buckets(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    """Step 1.1 collision pattern: ``run:a:b`` vs ``run:a/b`` must not
    collide, because the bucket is the digest, not the prefix."""

    a = store.put(
        run_ref="run:a:b",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    b = store.put(
        run_ref="run:a/b",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    # Same payload but different run_ref → different artifact_ref
    # because the run-component is part of the ref.
    assert a.artifact_ref != b.artifact_ref


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX directory modes only")
def test_evidence_root_directory_mode_owner_only(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    LocalFsEvidenceArtifactStore(root=root)
    mode = root.stat().st_mode
    assert (mode & stat.S_IRWXG) == 0
    assert (mode & stat.S_IRWXO) == 0


def test_payload_size_reflects_persisted_bytes(
    store: LocalFsEvidenceArtifactStore,
) -> None:
    payload = b"x" * 12345
    result = store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    assert result.size_bytes == 12345
    assert len(store.get(artifact_ref=result.artifact_ref) or b"") == 12345


@pytest.mark.skipif(sys.platform == "win32", reason="symlink semantics differ on Windows")
def test_get_refuses_to_follow_symlink_at_artifact_path(tmp_path: Path) -> None:
    """If the artifact file is replaced by a symlink pointing outside
    the root, ``get`` must refuse rather than read sensitive bytes
    via the link. lstat-based regular-file check rejects symlinks."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    payload = b'{"log":{}}'
    result = store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    # Verify normal read works first.
    assert store.get(artifact_ref=result.artifact_ref) == payload
    # Replace the file with a symlink to a sensitive sibling.
    target_files = list((tmp_path / "evidence").rglob("har-*.har.json"))
    assert len(target_files) == 1
    artifact_file = target_files[0]
    sensitive = tmp_path / "sensitive.txt"
    sensitive.write_bytes(b"DO NOT LEAK ME")
    artifact_file.unlink()
    artifact_file.symlink_to(sensitive)
    # ``get`` must refuse to follow the symlink.
    assert store.get(artifact_ref=result.artifact_ref) is None


@pytest.mark.skipif(sys.platform == "win32", reason="symlink semantics differ on Windows")
def test_get_refuses_symlinked_directory_ancestor(tmp_path: Path) -> None:
    """A compromised directory ancestor (the run-dir or attempt-dir
    replaced by a symlink) must also cause ``get`` to refuse."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    result = store.put(
        run_ref="run:dir-symlink",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    # Find the run dir and replace it with a symlink to a sibling
    # tree that contains a same-named file but with sensitive contents.
    run_dirs = [p for p in (tmp_path / "evidence").iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    # Build a parallel tree with a same-named artifact carrying
    # different bytes.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    # Mirror the inner structure: <elsewhere>/<attempt>/<file>
    attempt_dirs = list(run_dir.iterdir())
    assert len(attempt_dirs) == 1
    attempt_name = attempt_dirs[0].name
    artifact_files = list(attempt_dirs[0].iterdir())
    assert len(artifact_files) == 1
    artifact_name = artifact_files[0].name
    (elsewhere / attempt_name).mkdir()
    (elsewhere / attempt_name / artifact_name).write_bytes(b"SENSITIVE")
    # Swap run_dir to a symlink pointing at ``elsewhere``.
    import shutil

    shutil.rmtree(run_dir)
    run_dir.symlink_to(elsewhere)
    # ``get`` must refuse — any ancestor that is not a real directory
    # makes the read unsafe.
    assert store.get(artifact_ref=result.artifact_ref) is None


def test_disk_full_raises_evidence_artifact_store_error(
    monkeypatch: pytest.MonkeyPatch,
    store: LocalFsEvidenceArtifactStore,
) -> None:
    """Simulate ``os.write`` failure: must surface as a typed store
    error so callers can map it to a recovery / failure category
    instead of leaking ``OSError``."""

    from veracrawl.ports.evidence_artifact_store import EvidenceArtifactStoreError

    real_write = os.write

    def _failing_write(fd: int, data: bytes) -> int:
        # Close the fd then return a fake "no space left" error.
        try:
            real_write(fd, b"")  # touch fd to simulate work
        except OSError:
            pass
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "write", _failing_write)
    with pytest.raises(EvidenceArtifactStoreError):
        store.put(
            run_ref="run:r",
            attempt_ref="attempt:1",
            kind=ArtifactKind.HAR,
            payload=b'{"log":{}}',
            content_type="application/json",
            redaction_applied=True,
        )
    # No partial file left behind.
    leftovers = list(store._root.rglob("*.tmp"))  # noqa: SLF001
    assert leftovers == []
