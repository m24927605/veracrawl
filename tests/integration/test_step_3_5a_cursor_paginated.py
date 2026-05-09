"""Phase 3 step 3.5a — CursorPaginatedAdapter integration tests."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from veracrawl.adapters.sources.cursor_paginated import (
    CursorPaginatedAdapter,
    CursorWalkResult,
)


def _build_pages(*pages: dict[str, Any]) -> list[httpx.Response]:
    return [httpx.Response(200, json=page) for page in pages]


def _make_handler(
    pages: list[dict[str, Any]],
) -> tuple[Any, list[httpx.Request]]:
    captured: list[httpx.Request] = []
    iterator = iter(pages)

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        try:
            payload = next(iterator)
        except StopIteration:
            return httpx.Response(200, json={"items": [], "nextToken": None})
        return httpx.Response(200, json=payload)

    return handler, captured


# --- Happy path -----------------------------------------------------------


def test_walk_collects_items_across_pages() -> None:
    pages: list[dict[str, Any]] = [
        {"items": [{"sku": "A"}, {"sku": "B"}], "nextToken": "cur1"},
        {"items": [{"sku": "C"}], "nextToken": "cur2"},
        {"items": [{"sku": "D"}], "nextToken": None},
    ]
    handler, captured = _make_handler(pages)
    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert [i["sku"] for i in result.items] == ["A", "B", "C", "D"]
    assert result.pages_fetched == 3
    assert result.halted_by is None
    # Cursor passed in subsequent requests.
    assert "nextToken" not in str(captured[0].url)
    assert "nextToken=cur1" in str(captured[1].url)
    assert "nextToken=cur2" in str(captured[2].url)


def test_walk_stops_on_empty_next_token() -> None:
    pages = [{"items": [{"sku": "A"}], "nextToken": None}]
    handler, _ = _make_handler(pages)
    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert result.pages_fetched == 1
    assert result.halted_by is None


def test_walk_with_initial_cursor() -> None:
    handler, captured = _make_handler(
        [{"items": [{"sku": "X"}], "nextToken": None}]
    )
    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    adapter.walk(initial_cursor="resumeFromHere")
    assert "nextToken=resumeFromHere" in str(captured[0].url)


# --- Auth refresh on 401 --------------------------------------------------


def test_walk_refreshes_auth_on_401_and_retries() -> None:
    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(401, json={"error": "auth"})
        return httpx.Response(
            200, json={"items": [{"sku": "A"}], "nextToken": None}
        )

    refresh_called = False

    def refresh() -> dict[str, str]:
        nonlocal refresh_called
        refresh_called = True
        return {"Authorization": "Bearer fresh-token"}

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
        refresh_auth_fn=refresh,
    )
    result = adapter.walk()
    assert refresh_called
    assert result.pages_fetched == 1
    assert [i["sku"] for i in result.items] == ["A"]


def test_walk_halts_on_401_without_refresh_callback() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={})

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert result.halted_by == "http_401"
    assert result.items == []


def test_walk_halts_on_refresh_callback_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={})

    def refresh_raises() -> dict[str, str]:
        raise RuntimeError("refresh failed")

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
        refresh_auth_fn=refresh_raises,
    )
    result = adapter.walk()
    assert result.halted_by == "auth_refresh_failed"
    assert isinstance(result.error, RuntimeError)


# --- Partial-batch on per-page exception ---------------------------------


def test_walk_returns_partial_result_on_mid_walk_failure() -> None:
    """First page succeeds; second page returns 500. Result
    carries the items from page 1 + ``halted_by``."""

    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(
                200,
                json={"items": [{"sku": "A"}, {"sku": "B"}], "nextToken": "cur1"},
            )
        return httpx.Response(500, json={})

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert [i["sku"] for i in result.items] == ["A", "B"]
    assert result.halted_by == "http_500"
    assert result.pages_fetched == 1


def test_walk_handles_invalid_json_gracefully() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not valid json")

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert result.halted_by == "json_decode"


def test_walk_handles_non_object_root() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["a", "b"])

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert result.halted_by == "non_object_root"


def test_walk_skips_non_dict_items_in_payload() -> None:
    """An item that's not a dict is skipped (defensive — the
    caller downstream-validates dict shapes)."""

    pages = [
        {
            "items": [{"sku": "A"}, "not-a-dict", {"sku": "B"}],
            "nextToken": None,
        }
    ]
    handler, _ = _make_handler(pages)
    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
    )
    result = adapter.walk()
    assert [i["sku"] for i in result.items] == ["A", "B"]


# --- Page budget ----------------------------------------------------------


def test_walk_halts_on_max_pages() -> None:
    """Cursor is infinite (every page returns nextToken). Walk
    halts after ``max_pages`` and reports ``halted_by``."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"items": [{"sku": "X"}], "nextToken": "endless"},
        )

    adapter = CursorPaginatedAdapter(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.com/v1/items",
        max_pages=3,
    )
    result = adapter.walk()
    assert result.pages_fetched == 3
    assert result.halted_by == "max_pages"
    assert len(result.items) == 3


# --- Construction validators --------------------------------------------


def test_construction_rejects_blank_base_url() -> None:
    with pytest.raises(ValueError, match="base_url"):
        CursorPaginatedAdapter(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
            base_url="   ",
        )


def test_construction_rejects_zero_max_pages() -> None:
    with pytest.raises(ValueError, match="max_pages"):
        CursorPaginatedAdapter(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
            base_url="https://api.example.com/v1/items",
            max_pages=0,
        )


def test_construction_rejects_blank_cursor_param() -> None:
    with pytest.raises(ValueError, match="cursor_query_param"):
        CursorPaginatedAdapter(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
            base_url="https://api.example.com/v1/items",
            cursor_query_param="   ",
        )


# --- CursorWalkResult shape -----------------------------------------------


def test_cursor_walk_result_default_shape() -> None:
    result = CursorWalkResult()
    assert result.items == []
    assert result.pages_fetched == 0
    assert result.final_cursor is None
    assert result.halted_by is None
    assert result.error is None
