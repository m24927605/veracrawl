"""Network acquisition port definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.network import (
    NetworkAttemptEvidence,
    NetworkRequest,
    NetworkResponse,
    RedirectHop,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult


@dataclass(frozen=True)
class NetworkClientResult:
    response: NetworkResponse
    redirect_hops: list[RedirectHop]
    body_text: str
    artifact_refs: list[Ref]
    # Phase 1 step 1.5: per-attempt evidence sidecar populated by the
    # cooperative HTTP / browser paths. One entry per HTTP attempt
    # (initial URL plus every redirect hop plus retries within
    # ``_send_with_retry`` in the stdlib_http adapter). Defaults to
    # ``[]`` so existing call sites that don't populate it stay valid.
    attempt_evidences: list[NetworkAttemptEvidence] = field(default_factory=list)


class NetworkClientPort(Protocol):
    def fetch(self, request: NetworkRequest) -> NetworkClientResult: ...


class NetworkSourceAdapterPort(Protocol):
    @property
    def last_result(self) -> NetworkClientResult | None: ...

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
