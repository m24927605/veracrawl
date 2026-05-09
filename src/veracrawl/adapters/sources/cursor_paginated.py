"""Phase 3 step 3.5a — generic cursor-paginated source adapter.

Walks a JSON-API cursor (``nextToken`` style) over an
injectable ``httpx.BaseTransport``. Handles:

* cursor-loop termination on empty body / missing token /
  caller-supplied max page count;
* 401-refresh hook so a stale auth token mid-walk can be
  refreshed without re-running the whole cursor;
* partial-batch result on per-page exception so the caller
  gets the items already collected up to the failure plus
  a typed cause record;
* per-walk page budget so an infinite-cursor bug stops
  bounded.

Provider-neutral on purpose: any JSON API with the same
shape (``items`` array + ``nextToken`` field) plugs in.
Phase 3 step 3.5b composes this with
``AmazonSpApiLwaTransport`` to talk to the SP-API. The
paginator itself has no Amazon-specific code — eBay Inventory
or a future provider can reuse the same shape.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

_DEFAULT_MAX_PAGES = 50
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)


@dataclass
class CursorWalkResult:
    """Result of one cursor walk.

    ``items`` is the flattened list of records collected
    across all pages successfully fetched. ``error`` is
    populated when the walk halted partway (per-page
    exception, 401 + refresh failure, or page-budget
    exhaustion); ``items`` still carries everything collected
    before the halt — the caller decides whether to keep the
    partial result or treat the walk as failed.
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    pages_fetched: int = 0
    final_cursor: str | None = None
    halted_by: str | None = None  # "max_pages" / "auth_refresh_failed" / "transport" / None
    error: BaseException | None = None


class CursorPaginatedAdapter:
    """Generic cursor walker.

    The caller supplies:

    * ``transport`` — an ``httpx.BaseTransport`` (typically the
      Phase 1 cooperative HTTP transport or a provider-specific
      auth-wrapping transport).
    * ``base_url`` — the cursor endpoint.
    * ``cursor_query_param`` — query key the API uses for the
      cursor (e.g., ``"nextToken"`` for SP-API).
    * ``items_key`` — top-level JSON key holding the items
      array (e.g., ``"items"``).
    * ``next_cursor_key`` — top-level JSON key holding the next
      cursor (e.g., ``"nextToken"``).
    * ``refresh_auth_fn`` — optional callable returning fresh
      ``Authorization`` header value on a 401; ``None``
      disables refresh and 401 halts the walk.
    """

    def __init__(
        self,
        *,
        transport: httpx.BaseTransport,
        base_url: str,
        cursor_query_param: str = "nextToken",
        items_key: str = "items",
        next_cursor_key: str = "nextToken",
        max_pages: int = _DEFAULT_MAX_PAGES,
        refresh_auth_fn: Callable[[], dict[str, str]] | None = None,
        initial_headers: dict[str, str] | None = None,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("base_url must be non-blank")
        if max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        for name, key in (
            ("cursor_query_param", cursor_query_param),
            ("items_key", items_key),
            ("next_cursor_key", next_cursor_key),
        ):
            if not key or not key.strip():
                raise ValueError(f"{name} must be non-blank")
        self._transport = transport
        self._base_url = base_url
        self._cursor_query_param = cursor_query_param
        self._items_key = items_key
        self._next_cursor_key = next_cursor_key
        self._max_pages = max_pages
        self._refresh_auth_fn = refresh_auth_fn
        self._initial_headers: dict[str, str] = dict(initial_headers or {})
        self._client = httpx.Client(
            transport=transport, timeout=_DEFAULT_TIMEOUT
        )

    def walk(self, *, initial_cursor: str | None = None) -> CursorWalkResult:
        result = CursorWalkResult()
        cursor: str | None = initial_cursor
        headers = dict(self._initial_headers)
        for page_index in range(self._max_pages):
            del page_index  # readability
            params: dict[str, str] = {}
            if cursor is not None:
                params[self._cursor_query_param] = cursor
            try:
                response = self._client.get(
                    self._base_url, headers=headers, params=params
                )
            except httpx.HTTPError as exc:
                result.halted_by = "transport"
                result.error = exc
                return result
            if response.status_code == 401 and self._refresh_auth_fn is not None:
                try:
                    refreshed_headers = self._refresh_auth_fn()
                except Exception as exc:
                    result.halted_by = "auth_refresh_failed"
                    result.error = exc
                    return result
                headers.update(refreshed_headers)
                # Drain + retry the SAME page once.
                response.read()
                try:
                    response = self._client.get(
                        self._base_url, headers=headers, params=params
                    )
                except httpx.HTTPError as exc:
                    result.halted_by = "transport"
                    result.error = exc
                    return result
            if not response.is_success:
                result.halted_by = f"http_{response.status_code}"
                response.read()
                # Don't echo the body into the error; the
                # caller can inspect ``result.halted_by`` for
                # the status code.
                return result
            try:
                payload = response.json()
            except Exception as exc:
                result.halted_by = "json_decode"
                result.error = exc
                return result
            if not isinstance(payload, dict):
                result.halted_by = "non_object_root"
                return result
            items = payload.get(self._items_key, [])
            if isinstance(items, list):
                # Defensive: only append dict items so the
                # caller can downstream-validate cleanly.
                for item in items:
                    if isinstance(item, dict):
                        result.items.append(item)
            result.pages_fetched += 1
            next_cursor = payload.get(self._next_cursor_key)
            if not isinstance(next_cursor, str) or not next_cursor:
                # End of cursor.
                return result
            cursor = next_cursor
            result.final_cursor = cursor
        # Loop exhausted ``max_pages`` without termination.
        result.halted_by = "max_pages"
        return result


__all__ = ["CursorPaginatedAdapter", "CursorWalkResult"]
