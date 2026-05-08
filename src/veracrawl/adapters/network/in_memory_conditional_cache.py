"""``InMemoryConditionalCache`` — production default for
``ConditionalCachePort``.

Per-(run_ref, url) entry; thread-safe via a single coarse lock
(cooperative crawl is not contention-bound, so a finer-grained
scheme is over-engineered for Phase 1). Bounded by ``max_entries``
to prevent unbounded growth — entries past the cap are evicted in
insertion order (oldest first).
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Final
from urllib.parse import urlsplit, urlunsplit

from veracrawl.ports.conditional_cache import CachedConditional

_DEFAULT_MAX_ENTRIES: Final[int] = 4096


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
    """Thread-safe LRU-ish in-memory cache for ETag / Last-Modified."""

    def __init__(self, *, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._lock = threading.Lock()
        # OrderedDict so we can evict oldest in O(1) when over cap.
        self._entries: OrderedDict[tuple[str, str], CachedConditional] = OrderedDict()

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
        key = (run_ref, _normalize_url(url))
        with self._lock:
            self._entries[key] = entry
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear_run(self, *, run_ref: str) -> None:
        """Drop every entry for ``run_ref`` (test / lifecycle helper)."""

        with self._lock:
            keys_to_drop = [k for k in self._entries if k[0] == run_ref]
            for k in keys_to_drop:
                del self._entries[k]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


__all__ = ["InMemoryConditionalCache"]
