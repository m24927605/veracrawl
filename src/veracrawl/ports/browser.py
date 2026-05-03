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
    dom_text: str = ""
    dom_content_hash: Ref | None = None
    screenshot_byte_count: int = 0
    network_request_count: int = 1
    blocked_request_count: int = 0
    console_log_count: int = 0
    wall_time_ms: int = 1


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
