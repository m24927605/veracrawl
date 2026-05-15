"""Unit tests for ``InMemoryReplayConsumer`` (s11)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from veracrawl.adapters.replay.in_memory_replay_consumer import (
    InMemoryReplayConsumer,
)
from veracrawl.contracts.errors import (
    ReplayBundleLookupMissError,
    ReplayExhaustedError,
)
from veracrawl.contracts.replay_bundle import ReplayBundle
from veracrawl.ports.replay_consumer import ReplayConsumerPort


def _bundle() -> ReplayBundle:
    return ReplayBundle(
        id="bundle:run-1:1",
        run_ref="run:1",
        recorded_at=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
        clock_trace=[
            "2026-05-15T12:00:00+00:00",
            "2026-05-15T12:00:05+00:00",
        ],
        model_response_refs={"req:1": "raw:1"},
        seed_refs={"dispatch": 42},
        fetch_outcome_refs={"https://a.example/1": "fetch:1"},
    )


def test_consumer_implements_replay_consumer_port() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    assert isinstance(consumer, ReplayConsumerPort)


def test_next_utc_returns_canned_iso_datetimes_in_order() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    a = consumer.next_utc()
    b = consumer.next_utc()
    assert a < b
    assert a.tzinfo is UTC
    assert a == datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def test_next_utc_raises_replay_exhausted_on_overrun() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    consumer.next_utc()
    consumer.next_utc()
    with pytest.raises(ReplayExhaustedError):
        consumer.next_utc()


def test_lookup_model_response_returns_raw_response_ref() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    assert consumer.lookup_model_response("req:1") == "raw:1"


def test_lookup_model_response_raises_on_unknown_request_id() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    with pytest.raises(ReplayBundleLookupMissError) as exc:
        consumer.lookup_model_response("req:missing")
    assert exc.value.category == "model_response"


def test_next_seed_returns_canned_integer_by_name() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    assert consumer.next_seed("dispatch") == 42


def test_next_seed_raises_on_unknown_name() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    with pytest.raises(ReplayBundleLookupMissError) as exc:
        consumer.next_seed("missing")
    assert exc.value.category == "seed"


def test_lookup_fetch_outcome_returns_ref() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    assert consumer.lookup_fetch_outcome("https://a.example/1") == "fetch:1"


def test_lookup_fetch_outcome_raises_on_unknown_url() -> None:
    consumer = InMemoryReplayConsumer(bundle=_bundle())
    with pytest.raises(ReplayBundleLookupMissError) as exc:
        consumer.lookup_fetch_outcome("https://nope.example/")
    assert exc.value.category == "fetch_outcome"


def test_load_bundle_returns_injected_bundle() -> None:
    bundle = _bundle()
    consumer = InMemoryReplayConsumer(bundle=bundle)
    assert consumer.load_bundle("any-ref") is bundle
