"""Shared helpers for persisting + reading back provider response bytes.

s2.1 producer (`persist_provider_response`) + same-slice consumer
(`read_persisted_provider_response`) for OpenAI/Anthropic v2
adapters. Stdlib + ArtifactStorePort only — no SDK / no adapter
imports.
"""

from __future__ import annotations

from datetime import UTC, datetime

from veracrawl.contracts.common import Ref
from veracrawl.ports.stores import ArtifactStorePort


def persist_provider_response(
    *,
    artifact_store: ArtifactStorePort,
    raw_bytes: bytes,
    provider_name: str,
    request_id: str,
    upstream_id: str,
    captured_at: datetime,
) -> Ref:
    """Persist raw provider response bytes; return the artifact ref.

    Metadata schema is fixed: provider, request_id, upstream_id,
    captured_at (ISO 8601 UTC), bytes_len. Caller writes this ref
    into ``ProviderResponse.raw_response_ref``.
    """

    if not request_id or not request_id.strip():
        raise ValueError("request_id must be non-blank")
    if not upstream_id or not upstream_id.strip():
        raise ValueError("upstream_id must be non-blank")
    if not provider_name or not provider_name.strip():
        raise ValueError("provider_name must be non-blank")
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("captured_at must be UTC")
    if captured_at.utcoffset() != UTC.utcoffset(captured_at):
        raise ValueError("captured_at must be UTC")
    metadata: dict[str, object] = {
        "provider": provider_name,
        "request_id": request_id,
        "upstream_id": upstream_id,
        "captured_at": captured_at.isoformat(),
        "bytes_len": len(raw_bytes),
    }
    return artifact_store.write(raw_bytes, metadata=metadata)


def read_persisted_provider_response(
    *, artifact_store: ArtifactStorePort, raw_response_ref: Ref,
) -> bytes:
    """Read back persisted bytes by ``raw_response_ref``.

    Raises ``KeyError`` when the ref is not present in the store.
    Used by replay paths (and the s2.1 round-trip test) to prove
    persisted refs survive the store round-trip byte-equal.
    """

    if not raw_response_ref or not raw_response_ref.strip():
        raise ValueError("raw_response_ref must be non-blank")
    return artifact_store.read(raw_response_ref)
