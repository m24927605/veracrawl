"""Contract tests for ``CrawlArtifactStorePort`` and ``ArtifactWriteResult``.

The port is the unified bytes+text artifact persistence surface used by
the external crawl runtime. Existing ``ArtifactStorePort`` definitions
in ``ports/artifact_store.py`` (text-only) and ``ports/stores.py``
(bytes, sparse metadata) remain untouched for backward compat.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from veracrawl.ports.crawl_artifact_store import (
    REQUIRED_METADATA_KEYS,
    ArtifactWriteResult,
    CrawlArtifactStorePort,
)


def test_artifact_write_result_minimal_construction() -> None:
    result = ArtifactWriteResult(
        artifact_ref="run:demo/raw-html/abc",
        content_digest="0" * 64,
        size_bytes=12,
        content_type="text/html",
        metadata={
            "source_url": "https://demo.example/",
            "privacy_classification": "internal",
            "replay_ref": "replay:abc",
        },
        created_at=datetime(2026, 5, 13, tzinfo=UTC),
    )
    assert result.size_bytes == 12
    assert result.metadata["source_url"] == "https://demo.example/"


def test_artifact_write_result_requires_64_char_content_digest() -> None:
    with pytest.raises(ValidationError, match="content_digest"):
        ArtifactWriteResult(
            artifact_ref="ref",
            content_digest="too-short",
            size_bytes=1,
            content_type="text/plain",
            metadata={
                "source_url": "https://demo.example/",
                "privacy_classification": "internal",
                "replay_ref": "replay:x",
            },
            created_at=datetime(2026, 5, 13, tzinfo=UTC),
        )


def test_artifact_write_result_requires_non_negative_size() -> None:
    with pytest.raises(ValidationError, match="size_bytes"):
        ArtifactWriteResult(
            artifact_ref="ref",
            content_digest="a" * 64,
            size_bytes=-1,
            content_type="text/plain",
            metadata={
                "source_url": "https://demo.example/",
                "privacy_classification": "internal",
                "replay_ref": "replay:x",
            },
            created_at=datetime(2026, 5, 13, tzinfo=UTC),
        )


def test_artifact_write_result_requires_utc_timestamp() -> None:
    with pytest.raises(ValidationError, match="timestamp"):
        ArtifactWriteResult(
            artifact_ref="ref",
            content_digest="a" * 64,
            size_bytes=1,
            content_type="text/plain",
            metadata={
                "source_url": "https://demo.example/",
                "privacy_classification": "internal",
                "replay_ref": "replay:x",
            },
            created_at=datetime(2026, 5, 13),  # naive
        )


def test_artifact_write_result_requires_evidence_metadata_keys() -> None:
    # source_url, privacy_classification, and replay_ref are the
    # evidence-grade keys every external-crawl artifact must carry so
    # the run_report can reconstruct lineage. Missing any key is a
    # validation error at construction time.
    for missing in REQUIRED_METADATA_KEYS:
        metadata = {key: "value" for key in REQUIRED_METADATA_KEYS}
        metadata.pop(missing)
        with pytest.raises(ValidationError, match=missing):
            ArtifactWriteResult(
                artifact_ref="ref",
                content_digest="a" * 64,
                size_bytes=1,
                content_type="text/plain",
                metadata=metadata,
                created_at=datetime(2026, 5, 13, tzinfo=UTC),
            )


def test_required_metadata_keys_are_stable() -> None:
    # The set is a contract; if it changes, callers must change too.
    assert REQUIRED_METADATA_KEYS == frozenset(
        {"source_url", "privacy_classification", "replay_ref"}
    )


def test_protocol_runtime_check_accepts_minimal_implementation() -> None:
    # CrawlArtifactStorePort is a structural Protocol — any object
    # exposing the four methods is a valid implementation.
    class _Store:
        def put_bytes(
            self,
            artifact_ref: str,
            data: bytes,
            *,
            content_type: str,
            metadata: dict[str, str],
        ) -> ArtifactWriteResult:
            return ArtifactWriteResult(
                artifact_ref=artifact_ref,
                content_digest=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
                content_type=content_type,
                metadata=metadata,
                created_at=datetime(2026, 5, 13, tzinfo=UTC),
            )

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
            return b""

        def exists(self, artifact_ref: str) -> bool:
            return False

    store: CrawlArtifactStorePort = _Store()
    result = store.put_text(
        "ref:1",
        "hello",
        content_type="text/plain",
        metadata={
            "source_url": "https://demo.example/",
            "privacy_classification": "internal",
            "replay_ref": "replay:1",
        },
    )
    assert result.size_bytes == len(b"hello")
