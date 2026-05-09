"""Phase 3 step 3.4 — eBay OAuth token cache contract tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from veracrawl.adapters.ebay.file_backed_token_cache import (
    FileBackedEbayTokenCache,
)
from veracrawl.ports.ebay_token_cache import EbayTokenCachePort

_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


def _build(tmp_path: Path) -> FileBackedEbayTokenCache:
    return FileBackedEbayTokenCache(
        cache_path=tmp_path / "cache" / "ebay-oauth-tokens.json"
    )


# --- Construction ----------------------------------------------------------


def test_construction_creates_parent_directory(tmp_path: Path) -> None:
    cache_dir = tmp_path / "deeper" / "cache"
    assert not cache_dir.exists()
    cache = FileBackedEbayTokenCache(
        cache_path=cache_dir / "ebay-tokens.json"
    )
    assert cache_dir.exists()
    # Cache file itself doesn't exist until first store.
    assert not cache.cache_path.exists()


def test_runtime_checkable(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    assert isinstance(cache, EbayTokenCachePort)


# --- Cache key validators --------------------------------------------------


@pytest.mark.parametrize(
    "bad_key", ["", "  ", "key with spaces", "key/with/slash", "../escape", "key\x00null"]
)
def test_fetch_rejects_invalid_cache_key(tmp_path: Path, bad_key: str) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="cache_key"):
        cache.fetch(cache_key=bad_key, now=_NOW)


@pytest.mark.parametrize(
    "bad_key", ["", "  ", "key with spaces", "key/with/slash", "../escape"]
)
def test_store_rejects_invalid_cache_key(tmp_path: Path, bad_key: str) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="cache_key"):
        cache.store(
            cache_key=bad_key,
            access_token="t",
            expires_at=_NOW + timedelta(hours=1),
            minted_at=_NOW,
        )


def test_fetch_rejects_naive_datetime(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="tz-aware"):
        cache.fetch(cache_key="ebay_v1", now=datetime(2026, 5, 9))


def test_store_rejects_naive_expires_at(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="tz-aware"):
        cache.store(
            cache_key="ebay_v1",
            access_token="t",
            expires_at=datetime(2026, 5, 9, 14),
            minted_at=_NOW,
        )


def test_store_rejects_blank_token(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="access_token"):
        cache.store(
            cache_key="ebay_v1",
            access_token="   ",
            expires_at=_NOW + timedelta(hours=1),
            minted_at=_NOW,
        )


def test_store_rejects_expires_before_minted(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="expires_at"):
        cache.store(
            cache_key="ebay_v1",
            access_token="t",
            expires_at=_NOW,
            minted_at=_NOW + timedelta(seconds=1),
        )


def test_fetch_rejects_negative_safety_margin(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    with pytest.raises(ValueError, match="safety_margin"):
        cache.fetch(cache_key="ebay_v1", now=_NOW, safety_margin_seconds=-1)


# --- Fetch / store round trip ---------------------------------------------


def test_fetch_returns_none_on_missing_cache(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) is None


def test_store_then_fetch_round_trip(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_v1",
        access_token="token-abc",
        expires_at=_NOW + timedelta(hours=2),
        minted_at=_NOW,
    )
    fetched = cache.fetch(cache_key="ebay_v1", now=_NOW)
    assert fetched == "token-abc"


def test_fetch_returns_none_for_expired_token(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_v1",
        access_token="token-abc",
        expires_at=_NOW + timedelta(seconds=30),
        minted_at=_NOW,
    )
    # Now is 31 seconds later; token expired.
    later = _NOW + timedelta(seconds=31)
    assert cache.fetch(cache_key="ebay_v1", now=later) is None


def test_fetch_returns_none_within_safety_margin(tmp_path: Path) -> None:
    """Default safety margin is 60s. A token that expires
    in 30s is treated as already-expired so the caller mints
    a fresh one."""

    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_v1",
        access_token="token-abc",
        expires_at=_NOW + timedelta(seconds=30),
        minted_at=_NOW,
    )
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) is None


def test_fetch_returns_token_outside_safety_margin(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_v1",
        access_token="token-abc",
        expires_at=_NOW + timedelta(seconds=120),
        minted_at=_NOW,
    )
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) == "token-abc"


def test_separate_cache_keys_isolated(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_browse_v1",
        access_token="token-browse",
        expires_at=_NOW + timedelta(hours=2),
        minted_at=_NOW,
    )
    cache.store(
        cache_key="ebay_finding_v1",
        access_token="token-finding",
        expires_at=_NOW + timedelta(hours=2),
        minted_at=_NOW,
    )
    assert cache.fetch(cache_key="ebay_browse_v1", now=_NOW) == "token-browse"
    assert cache.fetch(cache_key="ebay_finding_v1", now=_NOW) == "token-finding"


def test_overwriting_same_key_replaces_token(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.store(
        cache_key="ebay_v1",
        access_token="old-token",
        expires_at=_NOW + timedelta(hours=2),
        minted_at=_NOW,
    )
    cache.store(
        cache_key="ebay_v1",
        access_token="new-token",
        expires_at=_NOW + timedelta(hours=3),
        minted_at=_NOW + timedelta(seconds=1),
    )
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) == "new-token"


# --- Atomicity + corruption tolerance --------------------------------------


def test_corrupted_cache_file_returns_none_on_fetch(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache.cache_path.write_text("not valid json", encoding="utf-8")
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) is None


def test_non_dict_root_returns_none_on_fetch(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache.cache_path.write_text(json.dumps(["a", "b"]), encoding="utf-8")
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) is None


def test_malformed_entry_returns_none(tmp_path: Path) -> None:
    cache = _build(tmp_path)
    cache.cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Missing required ``expires_at`` field.
    cache.cache_path.write_text(
        json.dumps({"ebay_v1": {"access_token": "t"}}),
        encoding="utf-8",
    )
    assert cache.fetch(cache_key="ebay_v1", now=_NOW) is None
