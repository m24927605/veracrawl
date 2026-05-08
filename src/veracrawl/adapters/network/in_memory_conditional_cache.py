"""``InMemoryConditionalCache`` — production default for
``ConditionalCachePort``.

Per-(run_ref, url) entry; thread-safe via a single coarse lock
(cooperative crawl is not contention-bound, so a finer-grained
scheme is over-engineered for Phase 1). Bounded by both
``max_entries`` (count) and ``max_total_bytes`` (sum of body
sizes); ``max_entry_bytes`` rejects oversized payloads at
``put`` time. Eviction is **LRU** — entries are touched on
``get`` and the least-recently-used entry is evicted first
when either cap is exceeded (codex iter-2 minor: docstring
previously claimed insertion-order eviction, which is wrong).
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Final
from urllib.parse import urlsplit, urlunsplit

from veracrawl.ports.conditional_cache import CachedConditional

_DEFAULT_MAX_ENTRIES: Final[int] = 4096
# Per-entry size cap: a body larger than this is not cached. Default
# 1 MiB matches the cooperative-crawler "small page" budget — large
# downloads belong on the evidence store, not in an in-memory short-
# circuit cache. Codex iter-1 important #4.
_DEFAULT_MAX_ENTRY_BYTES: Final[int] = 1 * 1024 * 1024
# Total budget across all entries. 64 MiB default keeps the cache
# usefully large without letting a long-lived crawl process retain
# unbounded memory under load. Eviction trims oldest entries first
# when the total exceeds this cap (LRU-style).
_DEFAULT_MAX_TOTAL_BYTES: Final[int] = 64 * 1024 * 1024


def _normalize_url(url: str) -> str:
    """Drop fragment + lowercase scheme/host. Path / query stay literal.

    Two URLs that differ only in fragment must hit the same cache
    entry (the fragment is client-side only and does not influence
    the response body / ETag). Casing of scheme + host is also
    canonicalized so ``HTTPS://Example.test/`` and
    ``https://example.test/`` share an entry.
    """

    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            parts.query,
            "",  # drop fragment
        )
    )


class InMemoryConditionalCache:
    """Thread-safe LRU-ish in-memory cache for ETag / Last-Modified.

    Bounded by both ``max_entries`` (count) and ``max_total_bytes``
    (sum of body sizes). Each entry is also subject to
    ``max_entry_bytes`` — bodies larger than this are silently
    skipped at ``put`` time (the next request will re-fetch
    without conditional headers, which is correct behavior).
    """

    def __init__(
        self,
        *,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        max_entry_bytes: int = _DEFAULT_MAX_ENTRY_BYTES,
        max_total_bytes: int = _DEFAULT_MAX_TOTAL_BYTES,
    ) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        if max_entry_bytes <= 0:
            raise ValueError("max_entry_bytes must be positive")
        if max_total_bytes <= 0:
            raise ValueError("max_total_bytes must be positive")
        if max_entry_bytes > max_total_bytes:
            raise ValueError("max_entry_bytes must be <= max_total_bytes")
        self._max_entries = max_entries
        self._max_entry_bytes = max_entry_bytes
        self._max_total_bytes = max_total_bytes
        self._lock = threading.Lock()
        # OrderedDict so we can evict oldest in O(1) when over cap.
        self._entries: OrderedDict[tuple[str, str], CachedConditional] = OrderedDict()
        self._total_bytes: int = 0

    def get(self, *, run_ref: str, url: str) -> CachedConditional | None:
        key = (run_ref, _normalize_url(url))
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                # Touch LRU order so a hot entry survives eviction.
                self._entries.move_to_end(key)
            return entry

    def put(
        self,
        *,
        run_ref: str,
        url: str,
        entry: CachedConditional,
    ) -> None:
        # Codex iter-1 important #4: refuse oversized bodies at the
        # cache layer. The next conditional fetch will re-fetch
        # without ``If-None-Match`` (correct), and the cache stays
        # usefully bounded.
        body_bytes = len(entry.body_bytes)
        if body_bytes > self._max_entry_bytes:
            return
        key = (run_ref, _normalize_url(url))
        with self._lock:
            existing = self._entries.get(key)
            if existing is not None:
                self._total_bytes -= len(existing.body_bytes)
            self._entries[key] = entry
            self._entries.move_to_end(key)
            self._total_bytes += body_bytes
            # Evict until both caps are satisfied (oldest first).
            while (
                len(self._entries) > self._max_entries or self._total_bytes > self._max_total_bytes
            ):
                _evicted_key, evicted_entry = self._entries.popitem(last=False)
                self._total_bytes -= len(evicted_entry.body_bytes)
            if self._total_bytes < 0:
                # Defence-in-depth: should never happen, but if
                # arithmetic drifted, snap to zero.
                self._total_bytes = 0

    def clear_run(self, *, run_ref: str) -> None:
        """Drop every entry for ``run_ref`` (test / lifecycle helper)."""

        with self._lock:
            keys_to_drop = [k for k in self._entries if k[0] == run_ref]
            for k in keys_to_drop:
                self._total_bytes -= len(self._entries[k].body_bytes)
                del self._entries[k]
            if self._total_bytes < 0:
                self._total_bytes = 0

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def total_bytes(self) -> int:
        """Return the current total body-bytes across all entries."""

        with self._lock:
            return self._total_bytes


__all__ = ["InMemoryConditionalCache"]
