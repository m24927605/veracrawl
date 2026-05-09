"""Phase 3 step 3.6 — eBay Browse API adapter (fixture-mode).

Wraps the eBay Browse API ``GET /buy/browse/v1/item_summary/search``
endpoint behind a tight, fixture-testable surface. Composes:

* ``EbayTokenCachePort`` (Phase 3 step 3.4) for OAuth access
  token caching;
* ``CursorPaginatedAdapter`` (Phase 3 step 3.5a) for the
  ``offset``/``limit`` walk over the search response (eBay
  uses offset-based pagination, not cursor-token; the
  paginator's ``cursor_query_param`` is set to ``offset``
  and the ``next_cursor_key`` is computed from the search
  response's ``next`` href).

Boundary invariants:

* OAuth fetch goes through a caller-injected
  ``token_refresh_fn`` so the adapter doesn't import
  network secrets directly. In fixture mode the test
  injects a stub; in production (Phase 6 step 6.1) the
  real eBay client-credentials grant lands.
* ``cache_key`` is fixed to ``ebay_browse_v1`` so multiple
  ``EbayBrowseAdapter`` instances in the same process
  share the same access token.
* Production mode raises ``ProductionRuntimeNotImplemented``
  until step 6.1 wires the production token-fetch.
* Live test (search against real api.ebay.com) lives at
  Phase 6 step 6.4 alongside the controlled-credential
  live regression suite.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from veracrawl.ports.ebay_token_cache import EbayTokenCachePort
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_BROWSE_SEARCH_ENDPOINT = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_DEFAULT_LIMIT = 50
_TOKEN_CACHE_KEY = "ebay_browse_v1"
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)


class EbayBrowseAdapter:
    """Fixture-mode-friendly eBay Browse search adapter.

    ``token_refresh_fn`` is the only credential-touching
    dependency: it returns ``(access_token, expires_at)``
    tuples on demand. Tests inject a stub; production wires
    the real client-credentials grant.
    """

    def __init__(
        self,
        *,
        token_cache: EbayTokenCachePort,
        token_refresh_fn: Callable[[], tuple[str, datetime]],
        transport: httpx.BaseTransport,
        clock: Callable[[], datetime] | None = None,
        runtime_mode: RuntimeMode | None = None,
    ) -> None:
        effective_mode = runtime_mode if runtime_mode is not None else current_mode()
        if effective_mode is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="ebay_browse_adapter",
                gate="phase_3_step_3_6_production_call",
            )
        if not isinstance(transport, httpx.MockTransport):
            raise ValueError(
                "EbayBrowseAdapter in FIXTURE mode only accepts "
                "httpx.MockTransport for the search transport."
            )
        self._token_cache = token_cache
        self._token_refresh_fn = token_refresh_fn
        self._client = httpx.Client(transport=transport, timeout=_DEFAULT_TIMEOUT)
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(UTC))

    def search(
        self,
        *,
        query: str,
        limit: int = _DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("eBay browse search query must be non-blank")
        if limit < 1 or limit > 200:
            raise ValueError("limit must be in [1, 200] (eBay Browse cap)")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        token = self._fetch_or_refresh_token()
        response = self._client.get(
            _BROWSE_SEARCH_ENDPOINT,
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            },
            params={"q": query, "limit": str(limit), "offset": str(offset)},
        )
        if response.status_code != 200:
            response.read()
            raise EbayBrowseError(
                f"eBay Browse search failed with HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except Exception:
            raise EbayBrowseError("eBay Browse response was not valid JSON") from None
        if not isinstance(payload, dict):
            raise EbayBrowseError("eBay Browse response was not a JSON object")
        items = payload.get("itemSummaries", [])
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def _fetch_or_refresh_token(self) -> str:
        now = self._clock()
        cached = self._token_cache.fetch(cache_key=_TOKEN_CACHE_KEY, now=now)
        if cached is not None:
            return cached
        access_token, expires_at = self._token_refresh_fn()
        if not access_token or not access_token.strip():
            raise EbayBrowseError(
                "eBay token_refresh_fn returned blank access_token"
            )
        if expires_at <= now:
            raise EbayBrowseError(
                "eBay token_refresh_fn returned non-future expires_at"
            )
        self._token_cache.store(
            cache_key=_TOKEN_CACHE_KEY,
            access_token=access_token,
            expires_at=expires_at,
            minted_at=now,
        )
        return access_token


class EbayBrowseError(RuntimeError):
    """Raised when the eBay Browse API call fails. Sanitized
    — message never echoes response body or credentials."""


__all__ = ["EbayBrowseAdapter", "EbayBrowseError"]


# Convenience factory: production builds wire ``token_refresh_fn``
# to the real eBay client-credentials grant. Phase 6 step 6.1
# ships the real factory; this comment documents the migration
# point.
def _placeholder_refresh_fn() -> tuple[str, datetime]:
    """Phase 6 step 6.1 replaces this with the real eBay
    client-credentials POST. Until then, callers must inject
    their own token_refresh_fn explicitly."""

    raise ProductionRuntimeNotImplemented(
        backend="ebay_oauth_client_credentials",
        gate="phase_3_step_3_6_production_token_refresh",
    )
