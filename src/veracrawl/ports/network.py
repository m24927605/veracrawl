"""Network acquisition port definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.network import NetworkRequest, NetworkResponse, RedirectHop
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult


@dataclass(frozen=True)
class NetworkClientResult:
    response: NetworkResponse
    redirect_hops: list[RedirectHop]
    body_text: str
    artifact_refs: list[Ref]


class NetworkClientPort(Protocol):
    def fetch(self, request: NetworkRequest) -> NetworkClientResult: ...


class NetworkSourceAdapterPort(Protocol):
    @property
    def last_result(self) -> NetworkClientResult | None: ...

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
