"""``PersistedRuntimeArtifactStore`` — runtime-style artifact store backed by ``ArtifactStorePort``.

Closes carry-forward gap #3 (s15 default-swap reconciliation). Two
artifact-store abstractions exist in the codebase:

1. ``veracrawl.artifact_lifecycle.runtime.InMemoryArtifactStore`` — the
   runtime-spine fixture store with a rich API
   (``write(*, artifact_id, artifact_type, producer_service,
   source_ref, content: str, privacy_classification) ->
   RuntimeArtifactRef``) used by fetch / normalize / extract /
   evidence runtime paths.
2. ``veracrawl.ports.stores.ArtifactStorePort`` — the low-level
   bytes port (``write(content: bytes, metadata) -> Ref``) that
   s15's ``HashedFsArtifactStore`` implements.

This adapter bridges them: it presents the rich runtime API while
persisting content bytes through an injected ``ArtifactStorePort``.
That makes ``HashedFsArtifactStore`` usable as the durable backend
without rewriting every fetch/normalize/extract call site.

Metadata (lifecycle state, retention policy, producer service,
privacy classification) lives in an in-memory index — that's a
non-content layer that doesn't need durable storage for the
fixture-runtime use case. A future slice can persist the metadata
to SQLite alongside the event store if needed.

Trade-offs:
* Bytes round-trip through the port: ``write`` calls
  ``content.encode("utf-8")`` then port.write; ``read`` does
  ``port.read(...).decode("utf-8")``. Adds one copy each direction.
* ``list_refs()`` / ``get_ref()`` are still in-memory dict reads
  (the runtime emits per-run reports; cross-run discovery isn't
  needed).
"""

from __future__ import annotations

from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import ArtifactType, OwnerService, PrivacyClassification
from veracrawl.ports.stores import ArtifactStorePort


class PersistedRuntimeArtifactStore:
    """Runtime-style artifact store backed by a low-level bytes port."""

    def __init__(self, *, byte_store: ArtifactStorePort) -> None:
        self._byte_store = byte_store
        self._refs: dict[str, RuntimeArtifactRef] = {}
        # Maps the runtime artifact_id → the byte-store ref so read()
        # can retrieve content. The two namespaces are deliberately
        # different: runtime ids are caller-supplied (descriptive,
        # often namespaced like "artifact:{run}:{stage}:raw"), byte-
        # store refs are content-addressed sha256 strings.
        self._content_refs: dict[str, Ref] = {}

    def write(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        producer_service: OwnerService,
        source_ref: Ref,
        content: str,
        privacy_classification: PrivacyClassification = PrivacyClassification.INTERNAL,
    ) -> RuntimeArtifactRef:
        # Persist bytes through the injected port.
        body = content.encode("utf-8")
        backing_ref = self._byte_store.write(body)
        # Build the rich-metadata ref the runtime expects.
        artifact_ref = RuntimeArtifactRef(
            id=artifact_id,
            artifact_type=artifact_type,
            producer_service=producer_service,
            source_ref=source_ref,
            content_digest=stable_hash(content),
            size_bytes=len(body),
            privacy_classification=privacy_classification,
            lifecycle_state_ref=f"lifecycle:{artifact_id}:active",
            retention_policy_ref="retention:runtime-persisted",
        )
        self._refs[artifact_id] = artifact_ref
        self._content_refs[artifact_id] = backing_ref
        return artifact_ref

    def read(self, artifact_ref: Ref) -> str | None:
        backing = self._content_refs.get(artifact_ref)
        if backing is None:
            return None
        return self._byte_store.read(backing).decode("utf-8")

    def get_ref(self, artifact_ref: Ref) -> RuntimeArtifactRef | None:
        return self._refs.get(artifact_ref)

    def list_refs(self) -> list[RuntimeArtifactRef]:
        return list(self._refs.values())


__all__ = ["PersistedRuntimeArtifactStore"]
