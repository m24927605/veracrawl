"""In-memory ``ArtifactStorePort`` implementation for bytes content.

Used by s2.1 tests and any caller wanting an in-memory bytes store.
Content-addressed: write(bytes) returns a deterministic ref derived
from the SHA-256 of the bytes. Same bytes → same ref (no clock or
RNG); read(ref) round-trips byte-equal.
"""

from __future__ import annotations

import hashlib

from veracrawl.contracts.common import Ref


class InMemoryBytesArtifactStore:
    def __init__(self) -> None:
        self._content: dict[Ref, bytes] = {}
        self._metadata: dict[Ref, dict[str, object]] = {}

    def write(self, content: bytes, metadata: dict[str, object] | None = None) -> Ref:
        digest = hashlib.sha256(content).hexdigest()
        ref: Ref = f"artifact:sha256:{digest}"
        self._content[ref] = content
        if metadata is not None:
            self._metadata[ref] = dict(metadata)
        return ref

    def exists(self, ref: Ref) -> bool:
        return ref in self._content

    def read(self, ref: Ref) -> bytes:
        if ref not in self._content:
            raise KeyError(ref)
        return self._content[ref]

    def metadata_for(self, ref: Ref) -> dict[str, object]:
        """Test helper — not part of ArtifactStorePort."""
        return dict(self._metadata.get(ref, {}))
