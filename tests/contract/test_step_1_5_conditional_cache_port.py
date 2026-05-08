"""Contract tests for Phase 1 step 1.5 — ``ConditionalCachePort``.

design.md §4 Phase 1 step 1.5 deliverable: ETag / Last-Modified
conditional fetch via ``If-None-Match`` / ``If-Modified-Since``;
304 short-circuits to cached body. The port surface is two
methods: ``get(run_ref, url)`` and ``put(run_ref, url, entry)``.
The framework default :class:`NoopConditionalCache` is empty (every
get misses) so existing tests pass without configuration (Phase 1
boundary acceptance).
"""

from __future__ import annotations

from veracrawl.ports.conditional_cache import (
    CachedConditional,
    ConditionalCachePort,
    NoopConditionalCache,
)


def test_noop_satisfies_runtime_protocol() -> None:
    cache = NoopConditionalCache()
    assert isinstance(cache, ConditionalCachePort)


def test_noop_get_always_misses() -> None:
    cache = NoopConditionalCache()
    assert cache.get(run_ref="run:r", url="https://example.test/") is None


def test_noop_put_is_no_op() -> None:
    cache = NoopConditionalCache()
    entry = CachedConditional(
        etag='"v1"',
        last_modified=None,
        body_bytes=b"<html>",
        body_artifact_ref="artifact:test:cached:abc",
        content_type="text/html",
        status_code=200,
    )
    cache.put(run_ref="run:r", url="https://example.test/", entry=entry)
    # Even after a put, the noop's get returns None.
    assert cache.get(run_ref="run:r", url="https://example.test/") is None


def test_cached_conditional_is_immutable() -> None:
    from dataclasses import FrozenInstanceError

    entry = CachedConditional(
        etag='"v1"',
        last_modified="Wed, 21 Oct 2026 07:28:00 GMT",
        body_bytes=b"<html></html>",
        body_artifact_ref="artifact:t:cached:abc",
        content_type="text/html",
        status_code=200,
    )
    import pytest as _pytest

    with _pytest.raises(FrozenInstanceError):
        entry.etag = '"v2"'  # type: ignore[misc]


def test_cached_conditional_validator_rejects_no_etag_no_last_modified() -> None:
    """Iter-3 important: cache entry must carry at least one of the
    conditional-fetch hints — otherwise it cannot drive any 304."""

    import pytest as _pytest

    with _pytest.raises(ValueError):
        CachedConditional(
            etag=None,
            last_modified=None,
            body_bytes=b"x",
            body_artifact_ref="artifact:t:1",
            content_type="text/html",
            status_code=200,
        )


def test_cached_conditional_validator_rejects_non_2xx_status() -> None:
    import pytest as _pytest

    with _pytest.raises(ValueError):
        CachedConditional(
            etag='"v"',
            last_modified=None,
            body_bytes=b"x",
            body_artifact_ref="artifact:t:1",
            content_type="text/html",
            status_code=500,
        )


def test_cached_conditional_validator_rejects_empty_body_artifact_ref() -> None:
    import pytest as _pytest

    with _pytest.raises(ValueError):
        CachedConditional(
            etag='"v"',
            last_modified=None,
            body_bytes=b"x",
            body_artifact_ref="",
            content_type="text/html",
            status_code=200,
        )


def test_cached_conditional_validator_rejects_empty_content_type() -> None:
    import pytest as _pytest

    with _pytest.raises(ValueError):
        CachedConditional(
            etag='"v"',
            last_modified=None,
            body_bytes=b"x",
            body_artifact_ref="artifact:t:1",
            content_type="",
            status_code=200,
        )


def test_cached_conditional_carries_all_fields() -> None:
    entry = CachedConditional(
        etag='"v1"',
        last_modified="Wed, 21 Oct 2026 07:28:00 GMT",
        body_bytes=b"<html>x</html>",
        body_artifact_ref="artifact:r:cached:1",
        content_type="text/html",
        status_code=200,
    )
    assert entry.etag == '"v1"'
    assert entry.last_modified == "Wed, 21 Oct 2026 07:28:00 GMT"
    assert entry.body_bytes == b"<html>x</html>"
    assert entry.body_artifact_ref == "artifact:r:cached:1"
    assert entry.content_type == "text/html"
    assert entry.status_code == 200
