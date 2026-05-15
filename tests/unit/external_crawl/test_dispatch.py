"""Unit tests for ``_choose_fetcher`` (s3.2 tests 1-9)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from veracrawl.contracts.crawl_planner import AdapterPrior
from veracrawl.contracts.enums import AdapterType
from veracrawl.external_crawl.dispatch import _choose_fetcher
from veracrawl.external_crawl.frontier import FrontierItem


def _item(url: str = "https://a.example/p", depth: int = 0) -> FrontierItem:
    return FrontierItem(
        canonical_url=url, depth=depth, parent_canonical_url=None,
        discovered_at=datetime(2026, 5, 16, 0, 0, tzinfo=UTC),
    )


def _prior(t: AdapterType, w: float, rationale: str = "r:1") -> AdapterPrior:
    return AdapterPrior(adapter_type=t, weight=w, rationale_ref=rationale)


_FAKE_FETCHER = object()


def _map_with(*types: AdapterType) -> Mapping[AdapterType, object]:
    return {t: _FAKE_FETCHER for t in types}


_ALL_ADAPTERS = [AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT]


# Test 1
def test_choose_fetcher_picks_only_available_type() -> None:
    chosen = _choose_fetcher(
        item=_item(),
        priors=[_prior(AdapterType.HTTP, 0.5, "r:http"),
                _prior(AdapterType.BROWSER_SNAPSHOT, 0.5, "r:browser")],
        fetcher_map=_map_with(AdapterType.HTTP),
        replay_seed_ref="seed:test:1",
        source_adapters=_ALL_ADAPTERS,
    )
    assert chosen is AdapterType.HTTP


# Test 2
def test_choose_fetcher_renormalizes_weights_after_filter() -> None:
    # priors say HTTP=0.3, BROWSER_SNAPSHOT=0.7; only HTTP is available
    # in the fetcher_map — HTTP must still be chosen even though its
    # raw weight is lower.
    chosen = _choose_fetcher(
        item=_item(),
        priors=[_prior(AdapterType.HTTP, 0.3, "r:http"),
                _prior(AdapterType.BROWSER_SNAPSHOT, 0.7, "r:browser")],
        fetcher_map=_map_with(AdapterType.HTTP),
        replay_seed_ref="seed:test:2",
        source_adapters=_ALL_ADAPTERS,
    )
    assert chosen is AdapterType.HTTP


# Test 3
def test_choose_fetcher_deterministic_for_same_url_and_seed() -> None:
    kwargs = {
        "item": _item(),
        "priors": [_prior(AdapterType.HTTP, 0.5, "r:http"),
                   _prior(AdapterType.BROWSER_SNAPSHOT, 0.5, "r:browser")],
        "fetcher_map": _map_with(*_ALL_ADAPTERS),
        "replay_seed_ref": "seed:test:3",
        "source_adapters": _ALL_ADAPTERS,
    }
    choices = {_choose_fetcher(**kwargs) for _ in range(100)}  # type: ignore[arg-type]
    assert len(choices) == 1


# Test 4
def test_choose_fetcher_distributes_across_priors_for_pinned_corpus() -> None:
    # Pinned URL corpus + 50/50 weights → deterministic choices per URL.
    # Both adapters must appear at least once over 10 URLs.
    urls = [f"https://a.example/{i}" for i in range(10)]
    chosen = [
        _choose_fetcher(
            item=_item(u),
            priors=[_prior(AdapterType.HTTP, 0.5, "r:http"),
                    _prior(AdapterType.BROWSER_SNAPSHOT, 0.5, "r:browser")],
            fetcher_map=_map_with(*_ALL_ADAPTERS),
            replay_seed_ref="seed:test:corpus",
            source_adapters=_ALL_ADAPTERS,
        )
        for u in urls
    ]
    assert AdapterType.HTTP in chosen
    assert AdapterType.BROWSER_SNAPSHOT in chosen


# Test 5
def test_choose_fetcher_pure_function_no_global_state() -> None:
    a_args = {
        "item": _item("https://a.example/1"),
        "priors": [_prior(AdapterType.HTTP, 0.5, "r:http"),
                   _prior(AdapterType.BROWSER_SNAPSHOT, 0.5, "r:browser")],
        "fetcher_map": _map_with(*_ALL_ADAPTERS),
        "replay_seed_ref": "seed:test:pure",
        "source_adapters": _ALL_ADAPTERS,
    }
    b_args = {**a_args, "item": _item("https://a.example/2")}
    first = _choose_fetcher(**a_args)  # type: ignore[arg-type]
    _ = _choose_fetcher(**b_args)  # type: ignore[arg-type]
    again = _choose_fetcher(**a_args)  # type: ignore[arg-type]
    assert first == again


# Test 6
def test_choose_fetcher_rejects_empty_priors() -> None:
    with pytest.raises(ValueError, match="priors"):
        _choose_fetcher(
            item=_item(),
            priors=[],
            fetcher_map=_map_with(AdapterType.HTTP),
            replay_seed_ref="seed:x",
            source_adapters=_ALL_ADAPTERS,
        )


# Test 7
def test_choose_fetcher_rejects_empty_fetcher_map() -> None:
    with pytest.raises(ValueError, match="fetcher_map"):
        _choose_fetcher(
            item=_item(),
            priors=[_prior(AdapterType.HTTP, 1.0)],
            fetcher_map={},
            replay_seed_ref="seed:x",
            source_adapters=_ALL_ADAPTERS,
        )


# Test 8
def test_choose_fetcher_rejects_blank_replay_seed_ref() -> None:
    with pytest.raises(ValueError, match="replay_seed_ref"):
        _choose_fetcher(
            item=_item(),
            priors=[_prior(AdapterType.HTTP, 1.0)],
            fetcher_map=_map_with(AdapterType.HTTP),
            replay_seed_ref=" ",
            source_adapters=_ALL_ADAPTERS,
        )


# Test 9
def test_choose_fetcher_handles_no_matching_priors() -> None:
    # priors only have BROWSER_SNAPSHOT, fetcher_map only has HTTP.
    with pytest.raises(ValueError, match="eligible"):
        _choose_fetcher(
            item=_item(),
            priors=[_prior(AdapterType.BROWSER_SNAPSHOT, 1.0)],
            fetcher_map=_map_with(AdapterType.HTTP),
            replay_seed_ref="seed:x",
            source_adapters=_ALL_ADAPTERS,
        )


# Reservation R2 (s3.2 plan iter-5): zero-effective-weight after filtering.
def test_choose_fetcher_rejects_zero_effective_weight_after_filtering() -> None:
    # AdapterPrior validates weight >= 0; build a zero-weight prior to
    # confirm the helper rejects it post-filter.
    zero = AdapterPrior(
        adapter_type=AdapterType.HTTP, weight=0.0, rationale_ref="r:zero",
    )
    with pytest.raises(ValueError, match="eligible"):
        _choose_fetcher(
            item=_item(),
            priors=[zero],
            fetcher_map=_map_with(AdapterType.HTTP),
            replay_seed_ref="seed:x",
            source_adapters=_ALL_ADAPTERS,
        )
