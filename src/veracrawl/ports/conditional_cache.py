"""``ConditionalCachePort`` — ETag / Last-Modified short-circuit cache.

Phase 1 step 1.5 deliverable (design.md §4 Phase 1):

    ETag / Last-Modified conditional fetch via ``If-None-Match`` /
    ``If-Modified-Since``; 304 short-circuits to cached body.

Surface:

* :meth:`ConditionalCachePort.get` returns the cached
  :class:`CachedConditional` for the ``(run_ref, url)`` pair, or
  ``None`` when there is no cached entry. The caller adds
  ``If-None-Match`` / ``If-Modified-Since`` headers from this entry
  before issuing the next request.
* :meth:`ConditionalCachePort.put` stores ``etag`` / ``last_modified``
  + the cached body bytes + the artifact ref the caller already
  associated with the body. The body bytes are kept inline so a
  subsequent ``304`` short-circuits without depending on the
  evidence store layer.

Scope is **per run**: a cache entry from ``run:a`` must not affect
``run:b``. Implementations are responsible for isolating run state;
the framework default :class:`NoopConditionalCache` is per-design
empty (every ``get`` returns ``None``) so existing tests pass
without configuration (Phase 1 boundary acceptance).

URL key normalization (codex iter-3 minor): implementations should
treat URLs that differ only in fragment or in scheme / host casing
as the same key. Path + query / case-sensitive characters are
preserved verbatim. The framework default no-op does no
normalization (no entries persist anyway); the production
:class:`InMemoryConditionalCache` lowercases scheme + netloc and
drops the fragment.

Thread safety: callers can issue concurrent ``get`` / ``put`` for
distinct runs and URLs. Production impls use a lock; the no-op is
trivially safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class CachedConditional:
    """Cached conditional-fetch state for one ``(run_ref, url)`` pair.

    Invariants enforced by ``__post_init__`` (codex iter-3
    important): a cached entry must carry at least one of
    ``etag`` / ``last_modified`` (otherwise it cannot drive any
    conditional fetch); ``body_artifact_ref`` must be a non-empty
    string (replay traceability); ``content_type`` must be
    non-empty; ``status_code`` must be a 2xx (we don't cache
    redirects / errors).

    Attributes:
        etag: Server-supplied ``ETag`` value (opaque to us; stored
            verbatim and echoed back as ``If-None-Match``). ``None``
            when the response did not include the header.
        last_modified: Server-supplied ``Last-Modified`` HTTP-date
            string. ``None`` when absent. Echoed back as
            ``If-Modified-Since`` when ``etag`` is not available.
        body_bytes: The cached response body. Kept inline so a 304
            short-circuit doesn't depend on the evidence store
            being reachable.
        body_artifact_ref: The artifact ref the caller associated
            with the body when it was first cached. On a 304
            short-circuit the caller re-uses this ref so replay
            traceability points back at the original artifact.
        content_type: Cached ``Content-Type`` header value (without
            parameters).
        status_code: HTTP status of the original cached response
            (always 2xx — we don't cache redirects or errors).
    """

    etag: str | None
    last_modified: str | None
    body_bytes: bytes
    body_artifact_ref: str
    content_type: str
    status_code: int

    def __post_init__(self) -> None:
        if self.etag is None and self.last_modified is None:
            raise ValueError("CachedConditional requires at least one of etag / last_modified")
        if not self.body_artifact_ref:
            raise ValueError("CachedConditional.body_artifact_ref must be non-empty")
        if not self.content_type:
            raise ValueError("CachedConditional.content_type must be non-empty")
        if not (200 <= self.status_code < 300):
            raise ValueError(f"CachedConditional.status_code must be 2xx, got {self.status_code}")


@runtime_checkable
class ConditionalCachePort(Protocol):
    """Hexagonal port for ETag / Last-Modified short-circuit caching."""

    def get(self, *, run_ref: str, url: str) -> CachedConditional | None:
        """Return the cached entry for ``(run_ref, url)``, or ``None``."""

    def put(
        self,
        *,
        run_ref: str,
        url: str,
        entry: CachedConditional,
    ) -> None:
        """Store ``entry`` for ``(run_ref, url)``.

        Implementations may evict older entries to bound memory; the
        contract guarantees only that a freshly stored entry is
        available to the very next ``get`` for the same key.
        """


class NoopConditionalCache:
    """Permissive default — every ``get`` misses, every ``put`` is dropped.

    Used when no conditional cache is configured (Phase 1 boundary
    acceptance: existing tests pass without configuration). Production
    callers inject a real impl; leaving the no-op in production just
    means conditional-fetch is disabled (correct, just less efficient
    — not a security gate).
    """

    def get(self, *, run_ref: str, url: str) -> CachedConditional | None:
        del run_ref, url
        return None

    def put(
        self,
        *,
        run_ref: str,
        url: str,
        entry: CachedConditional,
    ) -> None:
        del run_ref, url, entry


__all__ = [
    "CachedConditional",
    "ConditionalCachePort",
    "NoopConditionalCache",
]
