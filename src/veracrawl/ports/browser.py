"""Browser observation port definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from veracrawl.contracts.browser import BrowserInteractionStep, BrowserSandboxPolicy
from veracrawl.contracts.common import Ref
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult


@dataclass(frozen=True)
class BrowserObservationResult:
    step: BrowserInteractionStep
    artifact_refs: list[Ref]


class BrowserObservationPort(Protocol):
    def observe(
        self,
        *,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult: ...


class BrowserSourceAdapterPort(BrowserObservationPort, Protocol):
    @property
    def last_result(self) -> BrowserObservationResult | None: ...

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
