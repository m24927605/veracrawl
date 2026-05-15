"""``InMemoryReplayConsumer`` — deterministic ``ReplayConsumerPort`` adapter (s11).

Cursors through the bundle's ``clock_trace`` and serves
``lookup_*`` calls from the bundle's dict maps. Raises
``ReplayExhaustedError`` on clock overrun and
``ReplayBundleLookupMissError`` on unknown keys.

See ``docs/plans/general-purpose-crawler-agentification/
s11-replay-consumer-port.md``.
"""

from __future__ import annotations

from datetime import datetime

from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import (
    ReplayBundleLookupMissError,
    ReplayExhaustedError,
)
from veracrawl.contracts.replay_bundle import ReplayBundle


class InMemoryReplayConsumer:
    def __init__(self, *, bundle: ReplayBundle) -> None:
        self._bundle = bundle
        self._clock_cursor = 0

    def load_bundle(self, bundle_ref: Ref) -> ReplayBundle:  # noqa: ARG002
        return self._bundle

    def next_utc(self) -> datetime:
        if self._clock_cursor >= len(self._bundle.clock_trace):
            raise ReplayExhaustedError(
                category="clock_trace",
                recorded_length=len(self._bundle.clock_trace),
            )
        entry = self._bundle.clock_trace[self._clock_cursor]
        self._clock_cursor += 1
        return datetime.fromisoformat(entry)

    def lookup_model_response(self, request_id: str) -> Ref:
        try:
            return self._bundle.model_response_refs[request_id]
        except KeyError as exc:
            raise ReplayBundleLookupMissError(
                category="model_response", key=request_id,
            ) from exc

    def next_seed(self, name: str) -> int:
        try:
            return self._bundle.seed_refs[name]
        except KeyError as exc:
            raise ReplayBundleLookupMissError(
                category="seed", key=name,
            ) from exc

    def lookup_fetch_outcome(self, url: str) -> Ref:
        try:
            return self._bundle.fetch_outcome_refs[url]
        except KeyError as exc:
            raise ReplayBundleLookupMissError(
                category="fetch_outcome", key=url,
            ) from exc


__all__ = ["InMemoryReplayConsumer"]
