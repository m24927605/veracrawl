"""Unit tests for ``InMemoryConditionalCache``.

design.md §4 Phase 1 step 1.5 production default for
``ConditionalCachePort``. Behaviors under test:

* round-trip put / get
* per-run isolation: same URL under run:a and run:b have distinct
  entries
* fragment / case normalization in URL keys
* eviction at ``max_entries`` (oldest first, LRU touch on get)
* clear_run drops all entries for a run
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.network.in_memory_conditional_cache import (
    InMemoryConditionalCache,
)
from veracrawl.ports.conditional_cache import CachedConditional


def _entry(body: bytes = b"<html>", *, etag: str | None = '"v1"') -> CachedConditional:
    return CachedConditional(
        etag=etag,
        last_modified=None,
        body_bytes=body,
        body_artifact_ref="artifact:t:cached:1",
        content_type="text/html",
        status_code=200,
    )


def test_round_trip_get_after_put() -> None:
    cache = InMemoryConditionalCache()
    cache.put(run_ref="run:r", url="https://example.test/p", entry=_entry())
    fetched = cache.get(run_ref="run:r", url="https://example.test/p")
    assert fetched is not None
    assert fetched.etag == '"v1"'
    assert fetched.body_bytes == b"<html>"


def test_per_run_isolation() -> None:
    cache = InMemoryConditionalCache()
    cache.put(run_ref="run:a", url="https://example.test/p", entry=_entry(b"a-body"))
    cache.put(run_ref="run:b", url="https://example.test/p", entry=_entry(b"b-body"))
    a = cache.get(run_ref="run:a", url="https://example.test/p")
    b = cache.get(run_ref="run:b", url="https://example.test/p")
    assert a is not None and a.body_bytes == b"a-body"
    assert b is not None and b.body_bytes == b"b-body"


def test_fragment_normalized() -> None:
    cache = InMemoryConditionalCache()
    cache.put(
        run_ref="run:r",
        url="https://example.test/p#section",
        entry=_entry(),
    )
    fetched = cache.get(run_ref="run:r", url="https://example.test/p#different")
    assert fetched is not None  # fragment-insensitive


def test_case_normalized_in_scheme_and_host() -> None:
    cache = InMemoryConditionalCache()
    cache.put(
        run_ref="run:r",
        url="HTTPS://Example.Test/p",
        entry=_entry(),
    )
    fetched = cache.get(run_ref="run:r", url="https://example.test/p")
    assert fetched is not None


def test_path_and_query_preserved_in_key() -> None:
    cache = InMemoryConditionalCache()
    cache.put(run_ref="run:r", url="https://example.test/a", entry=_entry(b"A"))
    cache.put(run_ref="run:r", url="https://example.test/b", entry=_entry(b"B"))
    a = cache.get(run_ref="run:r", url="https://example.test/a")
    b = cache.get(run_ref="run:r", url="https://example.test/b")
    assert a is not None and a.body_bytes == b"A"
    assert b is not None and b.body_bytes == b"B"


def test_query_string_keys_distinct() -> None:
    cache = InMemoryConditionalCache()
    cache.put(run_ref="run:r", url="https://example.test/p?x=1", entry=_entry(b"X1"))
    cache.put(run_ref="run:r", url="https://example.test/p?x=2", entry=_entry(b"X2"))
    a = cache.get(run_ref="run:r", url="https://example.test/p?x=1")
    b = cache.get(run_ref="run:r", url="https://example.test/p?x=2")
    assert a is not None and a.body_bytes == b"X1"
    assert b is not None and b.body_bytes == b"X2"


def test_lru_eviction_at_max_entries() -> None:
    cache = InMemoryConditionalCache(max_entries=2)
    cache.put(run_ref="run:r", url="https://example.test/a", entry=_entry(b"A"))
    cache.put(run_ref="run:r", url="https://example.test/b", entry=_entry(b"B"))
    # Touch /a so it stays warm.
    assert cache.get(run_ref="run:r", url="https://example.test/a") is not None
    # Putting /c evicts the LRU which is now /b.
    cache.put(run_ref="run:r", url="https://example.test/c", entry=_entry(b"C"))
    assert cache.get(run_ref="run:r", url="https://example.test/a") is not None
    assert cache.get(run_ref="run:r", url="https://example.test/b") is None
    assert cache.get(run_ref="run:r", url="https://example.test/c") is not None


def test_max_entries_must_be_positive() -> None:
    with pytest.raises(ValueError):
        InMemoryConditionalCache(max_entries=0)


def test_clear_run_drops_only_run_entries() -> None:
    cache = InMemoryConditionalCache()
    cache.put(run_ref="run:a", url="https://example.test/p", entry=_entry(b"a"))
    cache.put(run_ref="run:b", url="https://example.test/p", entry=_entry(b"b"))
    cache.clear_run(run_ref="run:a")
    assert cache.get(run_ref="run:a", url="https://example.test/p") is None
    assert cache.get(run_ref="run:b", url="https://example.test/p") is not None


def test_len_reflects_entry_count() -> None:
    cache = InMemoryConditionalCache()
    assert len(cache) == 0
    cache.put(run_ref="run:r", url="https://example.test/a", entry=_entry())
    cache.put(run_ref="run:r", url="https://example.test/b", entry=_entry())
    assert len(cache) == 2
