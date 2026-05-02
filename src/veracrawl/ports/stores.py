"""Infrastructure store ports. Core code must depend on these, not concrete clients."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.command import CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.event import CrawlRunEvent


class EventStorePort(Protocol):
    def append(self, event: CrawlRunEvent) -> Ref: ...

    def stream(self, run_id: str) -> list[CrawlRunEvent]: ...


class ArtifactStorePort(Protocol):
    def write(self, content: bytes, metadata: dict[str, object] | None = None) -> Ref: ...

    def exists(self, ref: Ref) -> bool: ...


class CommandResultRepositoryPort(Protocol):
    def save(self, result: CommandResult) -> Ref: ...

    def get(self, ref: Ref) -> CommandResult | None: ...
