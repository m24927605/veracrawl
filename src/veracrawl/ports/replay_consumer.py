"""``ReplayConsumerPort`` — replay-side reader of a ``ReplayBundle`` (s11).

The runner consults this port before reading any non-deterministic
external source. The fixture in-memory adapter is shipped in this
slice; production adapters (durable file/SQLite backends) land
later.

See ``docs/plans/general-purpose-crawler-agentification/
s11-replay-consumer-port.md``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.replay_bundle import ReplayBundle


@runtime_checkable
class ReplayConsumerPort(Protocol):
    def load_bundle(self, bundle_ref: Ref) -> ReplayBundle: ...

    def next_utc(self) -> datetime: ...

    def lookup_model_response(self, request_id: str) -> Ref: ...

    def next_seed(self, name: str) -> int: ...

    def lookup_fetch_outcome(self, url: str) -> Ref: ...


__all__ = ["ReplayConsumerPort"]
