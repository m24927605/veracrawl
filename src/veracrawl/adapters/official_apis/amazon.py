"""Amazon official product API adapter.

Amazon's public PA-API v5 documentation now points new integrations to
Creators API. Detailed Creators API endpoints are credentialed/account gated, so
this adapter uses an operator-provided Creators API endpoint and credentials
while keeping all native state outside VeraCrawl core.
"""

from __future__ import annotations

import json
import os
import urllib.request

from veracrawl.adapters.official_apis.common import (
    HttpTransport,
    adapter_failure,
    credential_refs,
    env_present,
    missing_outcome,
    require_origin,
    stdlib_transport,
)
from veracrawl.contracts.ecommerce_official_api import EcommerceOfficialApiTargetSpec
from veracrawl.ports.ecommerce_official_api import EcommerceOfficialApiFetchOutcome

_USER_AGENT = "VeraCrawl-amazon-creators-api/1"
_ENDPOINT_ENV = "AMAZON_CREATORS_API_ENDPOINT"
_TOKEN_ENV = "AMAZON_CREATORS_API_BEARER_TOKEN"
_API_KEY_ENV = "AMAZON_CREATORS_API_KEY"


class AmazonCreatorsApiAdapter:
    def __init__(self, transport: HttpTransport | None = None) -> None:
        self._transport = transport or stdlib_transport

    def fetch_product(
        self,
        *,
        fixture_id: str,
        target: EcommerceOfficialApiTargetSpec,
    ) -> EcommerceOfficialApiFetchOutcome:
        endpoint = os.environ.get(_ENDPOINT_ENV, "").strip()
        bearer_token = os.environ.get(_TOKEN_ENV, "").strip()
        api_key = os.environ.get(_API_KEY_ENV, "").strip()
        missing = [_ENDPOINT_ENV] if not endpoint else []
        if not (bearer_token or api_key):
            missing.append(f"{_TOKEN_ENV} or {_API_KEY_ENV}")
        if missing:
            return missing_outcome(
                fixture_id=fixture_id,
                target=target,
                missing_env_vars=missing,
            )
        if not require_origin(endpoint, target.allowed_origin):
            return adapter_failure(
                fixture_id=fixture_id,
                target=target,
                failure_type="official_api_endpoint_scope_violation",
                diagnostics=[
                    f"Amazon Creators API endpoint {endpoint} is outside {target.allowed_origin}"
                ],
            )

        payload = {
            "itemIds": [target.product_identifier],
            "itemIdType": target.product_identifier_type.upper(),
            "marketplace": os.environ.get("AMAZON_CREATORS_API_MARKETPLACE", "www.amazon.com"),
            "resources": [
                "ItemInfo.Title",
                "OffersV2.Listings.Price",
                "OffersV2.Listings.Availability",
                "Offers.Listings.Price",
                "Offers.Listings.Availability",
            ],
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        }
        used_env = [_ENDPOINT_ENV]
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
            used_env.append(_TOKEN_ENV)
        if api_key:
            headers["x-api-key"] = api_key
            used_env.append(_API_KEY_ENV)
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        grant_ref, audit_ref = credential_refs(
            fixture_id=fixture_id,
            target=target,
            env_names=used_env,
        )
        try:
            response = self._transport(request, max(target.timeout_ms / 1000, 1))
        except OSError as exc:
            return adapter_failure(
                fixture_id=fixture_id,
                target=target,
                failure_type="official_api_network_error",
                diagnostics=[f"Amazon Creators API request failed: {exc}"],
            )
        return EcommerceOfficialApiFetchOutcome(
            credential_grant_ref=grant_ref,
            credential_audit_ref=audit_ref,
            response=response,
        )


def required_credentials_available() -> bool:
    return env_present(_ENDPOINT_ENV) and (env_present(_TOKEN_ENV) or env_present(_API_KEY_ENV))

