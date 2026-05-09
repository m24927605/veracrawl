"""Phase 3 step 3.6 — EbayBrowseAdapter integration tests (fixture-mode).

Live test against the real eBay Browse API requires eBay
developer credentials and lands at Phase 6 step 6.4
alongside the controlled-credential live regression suite.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from veracrawl.adapters.ebay.browse_adapter import (
    EbayBrowseAdapter,
    EbayBrowseError,
)
from veracrawl.adapters.ebay.file_backed_token_cache import (
    FileBackedEbayTokenCache,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
)

_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


def _build_adapter(
    tmp_path: Path,
    *,
    handler: Any,
    token_refresh_fn: Any = None,
) -> EbayBrowseAdapter:
    cache = FileBackedEbayTokenCache(
        cache_path=tmp_path / "cache" / "ebay-tokens.json"
    )
    if token_refresh_fn is None:
        def token_refresh_fn() -> tuple[str, datetime]:
            return ("token-fixture", _NOW + timedelta(hours=2))
    return EbayBrowseAdapter(
        token_cache=cache,
        token_refresh_fn=token_refresh_fn,
        transport=httpx.MockTransport(handler),
        clock=lambda: _NOW,
        runtime_mode=RuntimeMode.FIXTURE,
    )


def _ok_search_response(skus: list[str]) -> dict[str, Any]:
    return {
        "href": "https://api.ebay.com/buy/browse/v1/item_summary/search?q=widget",
        "limit": 50,
        "offset": 0,
        "total": len(skus),
        "itemSummaries": [
            {"itemId": f"v1|{sku}|0", "title": f"Widget {sku}", "sku": sku}
            for sku in skus
        ],
    }


# --- Construction gates ---------------------------------------------------


def test_production_mode_raises(tmp_path: Path) -> None:
    cache = FileBackedEbayTokenCache(
        cache_path=tmp_path / "cache" / "ebay.json"
    )
    with pytest.raises(ProductionRuntimeNotImplemented):
        EbayBrowseAdapter(
            token_cache=cache,
            token_refresh_fn=lambda: ("t", _NOW + timedelta(hours=1)),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
            runtime_mode=RuntimeMode.PRODUCTION,
        )


def test_fixture_mode_refuses_real_transport(tmp_path: Path) -> None:
    cache = FileBackedEbayTokenCache(
        cache_path=tmp_path / "cache" / "ebay.json"
    )
    with pytest.raises(ValueError, match="MockTransport"):
        EbayBrowseAdapter(
            token_cache=cache,
            token_refresh_fn=lambda: ("t", _NOW + timedelta(hours=1)),
            transport=httpx.HTTPTransport(),
            runtime_mode=RuntimeMode.FIXTURE,
        )


# --- Search input validators ---------------------------------------------


def test_search_rejects_blank_query(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, json={})
    )
    with pytest.raises(ValueError, match="query"):
        adapter.search(query="   ")


@pytest.mark.parametrize("bad_limit", [0, -1, 201, 1000])
def test_search_rejects_out_of_range_limit(tmp_path: Path, bad_limit: int) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, json={})
    )
    with pytest.raises(ValueError, match="limit"):
        adapter.search(query="widget", limit=bad_limit)


def test_search_rejects_negative_offset(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, json={})
    )
    with pytest.raises(ValueError, match="offset"):
        adapter.search(query="widget", offset=-1)


# --- Wire shape ----------------------------------------------------------


def test_search_sends_authorization_and_marketplace_headers(tmp_path: Path) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_ok_search_response(["A", "B"]))

    adapter = _build_adapter(tmp_path, handler=handler)
    items = adapter.search(query="widget pro")
    assert [i["sku"] for i in items] == ["A", "B"]
    request = captured[0]
    assert request.headers["authorization"] == "Bearer token-fixture"
    assert request.headers["x-ebay-c-marketplace-id"] == "EBAY_US"
    assert "q=widget+pro" in str(request.url)
    assert "limit=50" in str(request.url)
    assert "offset=0" in str(request.url)


def test_search_with_custom_limit_and_offset(tmp_path: Path) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_ok_search_response([]))

    adapter = _build_adapter(tmp_path, handler=handler)
    adapter.search(query="widget", limit=25, offset=50)
    assert "limit=25" in str(captured[0].url)
    assert "offset=50" in str(captured[0].url)


# --- Token caching --------------------------------------------------------


def test_token_refresh_called_only_once_when_cached(tmp_path: Path) -> None:
    refresh_count = 0

    def refresh() -> tuple[str, datetime]:
        nonlocal refresh_count
        refresh_count += 1
        return ("token-fresh", _NOW + timedelta(hours=2))

    adapter = _build_adapter(
        tmp_path,
        handler=lambda _: httpx.Response(200, json=_ok_search_response([])),
        token_refresh_fn=refresh,
    )
    for _ in range(3):
        adapter.search(query="widget")
    assert refresh_count == 1


def test_token_refresh_rejects_blank_access_token(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path,
        handler=lambda _: httpx.Response(200, json={}),
        token_refresh_fn=lambda: ("   ", _NOW + timedelta(hours=1)),
    )
    with pytest.raises(EbayBrowseError, match="blank access_token"):
        adapter.search(query="widget")


def test_token_refresh_rejects_past_expiry(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path,
        handler=lambda _: httpx.Response(200, json={}),
        token_refresh_fn=lambda: ("token", _NOW - timedelta(seconds=1)),
    )
    with pytest.raises(EbayBrowseError, match="non-future"):
        adapter.search(query="widget")


# --- Error paths ----------------------------------------------------------


def test_search_raises_on_non_200(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(500, json={})
    )
    with pytest.raises(EbayBrowseError, match="HTTP 500"):
        adapter.search(query="widget")


def test_search_raises_on_invalid_json(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, content=b"not json")
    )
    with pytest.raises(EbayBrowseError, match="not valid JSON"):
        adapter.search(query="widget")


def test_search_returns_empty_list_when_no_item_summaries(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, json={"total": 0})
    )
    items = adapter.search(query="widget")
    assert items == []


def test_search_walks_pagination_loop_until_short_page(tmp_path: Path) -> None:
    """Codex iter-1 important: the adapter must walk
    multi-page results, not silently truncate at one page.
    The loop terminates when a page returns fewer than
    ``limit`` items (canonical end-of-results signal)."""

    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Full page (limit=2 → 2 items)
            return httpx.Response(
                200,
                json={
                    "itemSummaries": [{"itemId": "1"}, {"itemId": "2"}],
                },
            )
        if call_count == 2:
            return httpx.Response(
                200,
                json={
                    "itemSummaries": [{"itemId": "3"}, {"itemId": "4"}],
                },
            )
        # Short page → end of results.
        return httpx.Response(
            200,
            json={"itemSummaries": [{"itemId": "5"}]},
        )

    adapter = _build_adapter(tmp_path, handler=handler)
    items = adapter.search(query="widget", limit=2)
    assert [i["itemId"] for i in items] == ["1", "2", "3", "4", "5"]
    assert call_count == 3


def test_search_pagination_respects_max_pages(tmp_path: Path) -> None:
    """If every page returns a full ``limit`` items (infinite
    cursor), the loop halts at ``max_pages``."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"itemSummaries": [{"itemId": "X"}, {"itemId": "Y"}]},
        )

    adapter = _build_adapter(tmp_path, handler=handler)
    items = adapter.search(query="widget", limit=2, max_pages=3)
    assert len(items) == 6  # 3 pages × 2 items


def test_search_pagination_passes_correct_offsets(tmp_path: Path) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        # Return short page on third call to halt loop.
        if len(captured) >= 3:
            return httpx.Response(200, json={"itemSummaries": [{"itemId": "Z"}]})
        return httpx.Response(
            200,
            json={"itemSummaries": [{"itemId": "X"}, {"itemId": "Y"}]},
        )

    adapter = _build_adapter(tmp_path, handler=handler)
    adapter.search(query="widget", limit=2, offset=10)
    # Three calls at offsets 10, 12, 14.
    assert "offset=10" in str(captured[0].url)
    assert "offset=12" in str(captured[1].url)
    assert "offset=14" in str(captured[2].url)


def test_search_401_refreshes_token_and_retries_once(tmp_path: Path) -> None:
    """Codex iter-1 important: 401 must invalidate the
    cached token, refresh once, and retry — NOT crash."""

    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(401, json={"errors": [{"message": "stale"}]})
        return httpx.Response(
            200,
            json={"itemSummaries": [{"itemId": "RECOVERED"}]},
        )

    refresh_count = 0

    def refresh() -> tuple[str, datetime]:
        nonlocal refresh_count
        refresh_count += 1
        return (f"token-fresh-{refresh_count}", _NOW + timedelta(hours=2))

    adapter = _build_adapter(
        tmp_path,
        handler=handler,
        token_refresh_fn=refresh,
    )
    items = adapter.search(query="widget", limit=2)
    assert [i["itemId"] for i in items] == ["RECOVERED"]
    # Two refreshes: initial cache miss + after 401 invalidation.
    assert refresh_count == 2
    assert call_count == 2


def test_search_rejects_zero_max_pages(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path, handler=lambda _: httpx.Response(200, json={})
    )
    with pytest.raises(ValueError, match="max_pages"):
        adapter.search(query="widget", max_pages=0)


def test_search_skips_non_dict_items(tmp_path: Path) -> None:
    adapter = _build_adapter(
        tmp_path,
        handler=lambda _: httpx.Response(
            200,
            json={
                "itemSummaries": [
                    {"itemId": "1"},
                    "not-a-dict",
                    {"itemId": "2"},
                ],
            },
        ),
    )
    items = adapter.search(query="widget")
    assert [i["itemId"] for i in items] == ["1", "2"]
