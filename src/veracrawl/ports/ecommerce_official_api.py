"""Official ecommerce API adapter port definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.ecommerce_official_api import EcommerceOfficialApiTargetSpec


@dataclass(frozen=True)
class EcommerceOfficialApiResponse:
    status_code: int
    request_url: str
    final_url: str
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True)
class EcommerceOfficialApiFetchOutcome:
    credential_grant_ref: Ref
    credential_audit_ref: Ref
    response: EcommerceOfficialApiResponse | None = None
    failure_type: str | None = None
    diagnostics: list[str] = field(default_factory=list)


class EcommerceOfficialApiAdapterPort(Protocol):
    def fetch_product(
        self,
        *,
        fixture_id: str,
        target: EcommerceOfficialApiTargetSpec,
    ) -> EcommerceOfficialApiFetchOutcome: ...

