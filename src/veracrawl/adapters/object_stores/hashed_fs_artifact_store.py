"""``HashedFsArtifactStore`` — content-addressed FS ``ArtifactStorePort`` (s15).

Production-track artifact store for s15. ``write(bytes)`` returns
``f"artifact:sha256:{hexdigest}"`` — same bytes always produce the
same ref so replay invariants stay byte-stable. ``read(ref)`` round-
trips the original bytes.

Layout: each blob lives at
``<root>/<aa>/<bb>/<digest>.bin`` where ``<aa>`` and ``<bb>`` are
the first two byte-pairs of the digest (fan-out for filesystems
that struggle with millions of siblings in one dir). Sidecar
metadata is JSON at the matching ``<digest>.json`` and is NOT
factored into the ref — per R2 reservation, ``created_at`` etc.
live in the sidecar, never in the content hash.

See ``docs/plans/general-purpose-crawler-agentification/
s15-hashed-fs-artifact-store-default.md``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from veracrawl.contracts.common import Ref

_REF_PREFIX = "artifact:sha256:"


class HashedFsArtifactStore:
    def __init__(self, *, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        content: bytes,
        metadata: dict[str, Any] | None = None,
    ) -> Ref:
        digest = hashlib.sha256(content).hexdigest()
        ref = f"{_REF_PREFIX}{digest}"
        blob_path = self._blob_path_for(digest)
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        # Re-writing the same bytes is a no-op; idempotent by design.
        if not blob_path.exists():
            blob_path.write_bytes(content)
        if metadata is not None:
            self._sidecar_path_for(digest).write_text(
                json.dumps(metadata, sort_keys=True),
                encoding="utf-8",
            )
        return ref

    def exists(self, ref: Ref) -> bool:
        digest = self._digest_from_ref(ref)
        if digest is None:
            return False
        return self._blob_path_for(digest).exists()

    def read(self, ref: Ref) -> bytes:
        digest = self._digest_from_ref(ref)
        if digest is None:
            raise KeyError(ref)
        path = self._blob_path_for(digest)
        if not path.exists():
            raise KeyError(ref)
        return path.read_bytes()

    def metadata_for(self, ref: Ref) -> dict[str, Any]:
        digest = self._digest_from_ref(ref)
        if digest is None or not self._blob_path_for(digest).exists():
            raise KeyError(ref)
        sidecar = self._sidecar_path_for(digest)
        if not sidecar.exists():
            return {}
        return json.loads(sidecar.read_text(encoding="utf-8"))

    def _blob_path_for(self, digest: str) -> Path:
        return self._root / digest[:2] / digest[2:4] / f"{digest}.bin"

    def _sidecar_path_for(self, digest: str) -> Path:
        return self._root / digest[:2] / digest[2:4] / f"{digest}.json"

    @staticmethod
    def _digest_from_ref(ref: Ref) -> str | None:
        if not ref.startswith(_REF_PREFIX):
            return None
        return ref[len(_REF_PREFIX):]


__all__ = ["HashedFsArtifactStore"]
