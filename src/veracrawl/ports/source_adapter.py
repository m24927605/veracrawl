"""Source adapter port definitions."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult


class SourceAdapterPort(Protocol):
    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
