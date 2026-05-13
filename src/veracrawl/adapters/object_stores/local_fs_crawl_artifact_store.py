"""``LocalFsCrawlArtifactStore`` — filesystem-backed external crawl store.

Implements :class:`veracrawl.ports.crawl_artifact_store.CrawlArtifactStorePort`
for the external (non-fixture) crawl runtime. One store instance owns
exactly one ``<root>/<run_id>/`` directory tree.

Layout::

    <root>/<run_id>/
      artifacts/
        raw-html/
        documents/
        normalized/
        screenshots/
        metadata/
      reports/
      events/
      outputs/

For each ``put_bytes`` call the store writes the payload at
``artifacts/<artifact_ref>`` plus a sidecar JSON at
``artifacts/<artifact_ref>.meta.json`` capturing the evidence-grade
fields (source_url, privacy_classification, replay_ref, content
digest, size, content type, created_at, freeform metadata).

Safety properties:
* ``artifact_ref`` is validated to forbid absolute paths and any
  ``..`` segment, so even a buggy caller cannot write outside the
  run's artifact tree.
* Writes are staged via ``tempfile.NamedTemporaryFile`` and finalised
  with :func:`os.replace` — readers never observe a partial file.
* A re-put with the same ``artifact_ref`` is allowed only when the
  content digest matches; differing bytes raise rather than silently
  overwriting prior evidence.
* :meth:`get_bytes` refuses symlinks anywhere on the route from
  run root to the artifact file, so a hostile workspace cannot
  trick the store into reading attacker-controlled bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Final

from veracrawl.ports.crawl_artifact_store import (
    REQUIRED_METADATA_KEYS,
    ArtifactWriteResult,
)

_ARTIFACT_DIRS: Final = ("raw-html", "documents", "normalized", "screenshots", "metadata")
_RUN_DIRS: Final = ("artifacts", "reports", "events", "outputs")
_SIDECAR_SUFFIX: Final = ".meta.json"


class CrawlArtifactStoreError(RuntimeError):
    """Raised when the filesystem store refuses an operation."""


class LocalFsCrawlArtifactStore:
    """Filesystem-backed :class:`CrawlArtifactStorePort` implementation."""

    def __init__(self, *, root: Path, run_id: str) -> None:
        if not run_id or any(c in run_id for c in "/\\") or run_id.startswith("."):
            raise CrawlArtifactStoreError(
                f"run_id must be a non-empty single path segment, got {run_id!r}"
            )
        self._root = Path(root).resolve()
        self._run_id = run_id
        self._run_root = (self._root / run_id).resolve()
        self._artifacts_root = self._run_root / "artifacts"
        self._ensure_layout()

    @property
    def run_root(self) -> Path:
        return self._run_root

    def _ensure_layout(self) -> None:
        for child in _RUN_DIRS:
            (self._run_root / child).mkdir(parents=True, exist_ok=True)
        for sub in _ARTIFACT_DIRS:
            (self._artifacts_root / sub).mkdir(parents=True, exist_ok=True)

    def _validate_ref(self, artifact_ref: str) -> PurePosixPath:
        if not artifact_ref or not artifact_ref.strip():
            raise CrawlArtifactStoreError("artifact_ref must be non-empty")
        # Reject absolute paths and Windows drive letters.
        if artifact_ref.startswith(("/", "\\")) or (
            len(artifact_ref) >= 2 and artifact_ref[1] == ":"
        ):
            raise CrawlArtifactStoreError(
                f"artifact_ref must be relative, got {artifact_ref!r}"
            )
        rel = PurePosixPath(artifact_ref)
        if rel.is_absolute():
            raise CrawlArtifactStoreError(
                f"artifact_ref must be relative, got {artifact_ref!r}"
            )
        for part in rel.parts:
            if part in ("..", ""):
                raise CrawlArtifactStoreError(
                    f"artifact_ref must not contain '..' segments, got {artifact_ref!r}"
                )
        # Reject paths that would land on a sidecar suffix.
        if rel.name.endswith(_SIDECAR_SUFFIX):
            raise CrawlArtifactStoreError(
                f"artifact_ref must not end with {_SIDECAR_SUFFIX}"
            )
        return rel

    def _resolve_artifact_path(self, artifact_ref: str) -> Path:
        rel = self._validate_ref(artifact_ref)
        return self._artifacts_root / Path(*rel.parts)

    def _validate_metadata(self, metadata: dict[str, str]) -> None:
        missing = REQUIRED_METADATA_KEYS - metadata.keys()
        if missing:
            key = sorted(missing)[0]
            raise CrawlArtifactStoreError(
                f"metadata missing required key {key!r}; "
                f"required keys are {sorted(REQUIRED_METADATA_KEYS)}"
            )

    def _atomic_write_bytes(self, target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(tmp_path, target)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise

    def put_bytes(
        self,
        artifact_ref: str,
        data: bytes,
        *,
        content_type: str,
        metadata: dict[str, str],
    ) -> ArtifactWriteResult:
        self._validate_metadata(metadata)
        if not content_type or not content_type.strip():
            raise CrawlArtifactStoreError("content_type must be non-empty")
        target = self._resolve_artifact_path(artifact_ref)
        digest = hashlib.sha256(data).hexdigest()

        if target.exists():
            # Idempotent re-write only if bytes identical.
            existing = target.read_bytes()
            if hashlib.sha256(existing).hexdigest() != digest:
                raise CrawlArtifactStoreError(
                    f"refusing to overwrite {artifact_ref!r}: digest mismatch"
                )

        self._atomic_write_bytes(target, data)

        created_at = datetime.now(tz=UTC)
        result = ArtifactWriteResult(
            artifact_ref=artifact_ref,
            content_digest=digest,
            size_bytes=len(data),
            content_type=content_type,
            metadata=dict(metadata),
            created_at=created_at,
        )
        self._write_sidecar(target, result)
        return result

    def put_text(
        self,
        artifact_ref: str,
        text: str,
        *,
        content_type: str,
        metadata: dict[str, str],
    ) -> ArtifactWriteResult:
        return self.put_bytes(
            artifact_ref,
            text.encode("utf-8"),
            content_type=content_type,
            metadata=metadata,
        )

    def get_bytes(self, artifact_ref: str) -> bytes:
        target = self._resolve_artifact_path(artifact_ref)
        if not target.exists():
            raise CrawlArtifactStoreError(f"artifact not found: {artifact_ref!r}")
        # Refuse to follow symlinks anywhere from the run root down to
        # the artifact file.
        cursor = self._run_root
        rel = Path(target).relative_to(self._run_root)
        for part in rel.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise CrawlArtifactStoreError(
                    f"refusing to read symlink on path to {artifact_ref!r}"
                )
        return target.read_bytes()

    def exists(self, artifact_ref: str) -> bool:
        try:
            target = self._resolve_artifact_path(artifact_ref)
        except CrawlArtifactStoreError:
            return False
        return target.is_file()

    def _write_sidecar(self, target: Path, result: ArtifactWriteResult) -> None:
        sidecar = target.with_name(target.name + _SIDECAR_SUFFIX)
        payload = result.model_dump(mode="json")
        self._atomic_write_bytes(
            sidecar,
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        )


__all__ = [
    "CrawlArtifactStoreError",
    "LocalFsCrawlArtifactStore",
]
