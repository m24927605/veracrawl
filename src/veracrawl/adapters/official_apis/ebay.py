"""eBay Browse API adapter."""

from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request
from typing import cast

from veracrawl.adapters.official_apis.common import (
    HttpTransport,
    adapter_failure,
    credential_refs,
    env_present,
    missing_outcome,
    stdlib_transport,
)
from veracrawl.contracts.ecommerce_official_api import EcommerceOfficialApiTargetSpec
from veracrawl.ports.ecommerce_official_api import EcommerceOfficialApiFetchOutcome

_USER_AGENT = "VeraCrawl-ebay-browse-api/1"
_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_SCOPE = "https://api.ebay.com/oauth/api_scope"
_CLIENT_ID_ENV = "EBAY_CLIENT_ID"
_CLIENT_SECRET_ENV = "EBAY_CLIENT_SECRET"
_ACCESS_TOKEN_ENV = "EBAY_ACCESS_TOKEN"
_MARKETPLACE_ENV = "EBAY_MARKETPLACE_ID"


class EbayBrowseApiAdapter:
    def __init__(self, transport: HttpTransport | None = None) -> None:
        self._transport = transport or stdlib_transport

    def fetch_product(
        self,
        *,
        fixture_id: str,
        target: EcommerceOfficialApiTargetSpec,
    ) -> EcommerceOfficialApiFetchOutcome:
        access_token = os.environ.get(_ACCESS_TOKEN_ENV, "").strip()
        client_id = os.environ.get(_CLIENT_ID_ENV, "").strip()
        client_secret = os.environ.get(_CLIENT_SECRET_ENV, "").strip()
        if not access_token and not (client_id and client_secret):
            return missing_outcome(
                fixture_id=fixture_id,
                target=target,
                missing_env_vars=[f"{_ACCESS_TOKEN_ENV} or {_CLIENT_ID_ENV}+{_CLIENT_SECRET_ENV}"],
            )
        used_env = [_ACCESS_TOKEN_ENV] if access_token else [_CLIENT_ID_ENV, _CLIENT_SECRET_ENV]
        if not access_token:
            token_outcome = self._fetch_access_token(
                fixture_id=fixture_id,
                target=target,
                client_id=client_id,
                client_secret=client_secret,
            )
            if token_outcome.failure_type is not None:
                return token_outcome
            token_response = token_outcome.response
            if token_response is None:
                return adapter_failure(
                    fixture_id=fixture_id,
                    target=target,
                    failure_type="official_api_oauth_missing_response",
                    diagnostics=["eBay OAuth token response was missing"],
                )
            try:
                token_payload = json.loads(token_response.body.decode("utf-8", errors="replace"))
            except json.JSONDecodeError as exc:
                return adapter_failure(
                    fixture_id=fixture_id,
                    target=target,
                    failure_type="official_api_oauth_invalid_json",
                    diagnostics=[f"eBay OAuth token response was invalid JSON: {exc}"],
                )
            if not isinstance(token_payload, dict) or not isinstance(
                token_payload.get("access_token"), str
            ):
                return adapter_failure(
                    fixture_id=fixture_id,
                    target=target,
                    failure_type="official_api_oauth_missing_access_token",
                    diagnostics=["eBay OAuth token response did not include access_token"],
                )
            access_token = cast(str, token_payload["access_token"])

        query = _search_query(target)
        request_url = f"{_BROWSE_SEARCH_URL}?{query}"
        request = urllib.request.Request(
            request_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": _USER_AGENT,
                "X-EBAY-C-MARKETPLACE-ID": os.environ.get(_MARKETPLACE_ENV, "EBAY_US"),
            },
            method="GET",
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
                diagnostics=[f"eBay Browse API request failed: {exc}"],
            )
        return EcommerceOfficialApiFetchOutcome(
            credential_grant_ref=grant_ref,
            credential_audit_ref=audit_ref,
            response=response,
        )

    def _fetch_access_token(
        self,
        *,
        fixture_id: str,
        target: EcommerceOfficialApiTargetSpec,
        client_id: str,
        client_secret: str,
    ) -> EcommerceOfficialApiFetchOutcome:
        encoded = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")
        body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "scope": _SCOPE,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            _TOKEN_URL,
            data=body,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": _USER_AGENT,
            },
            method="POST",
        )
        grant_ref, audit_ref = credential_refs(
            fixture_id=fixture_id,
            target=target,
            env_names=[_CLIENT_ID_ENV, _CLIENT_SECRET_ENV],
        )
        try:
            response = self._transport(request, max(target.timeout_ms / 1000, 1))
        except OSError as exc:
            return adapter_failure(
                fixture_id=fixture_id,
                target=target,
                failure_type="official_api_oauth_network_error",
                diagnostics=[f"eBay OAuth token request failed: {exc}"],
            )
        if not 200 <= response.status_code < 300:
            return EcommerceOfficialApiFetchOutcome(
                credential_grant_ref=grant_ref,
                credential_audit_ref=audit_ref,
                response=response,
                failure_type="official_api_oauth_http_error",
                diagnostics=[f"eBay OAuth token endpoint returned HTTP {response.status_code}"],
            )
        return EcommerceOfficialApiFetchOutcome(
            credential_grant_ref=grant_ref,
            credential_audit_ref=audit_ref,
            response=response,
        )


def required_credentials_available() -> bool:
    return env_present(_ACCESS_TOKEN_ENV) or (
        env_present(_CLIENT_ID_ENV) and env_present(_CLIENT_SECRET_ENV)
    )


def _search_query(target: EcommerceOfficialApiTargetSpec) -> str:
    identifier_type = target.product_identifier_type.lower()
    if identifier_type == "gtin":
        params = {"gtin": target.product_identifier, "limit": "1"}
    elif identifier_type == "epid":
        params = {"epid": target.product_identifier, "limit": "1"}
    else:
        params = {"q": target.product_identifier, "limit": "1"}
    return urllib.parse.urlencode(params)
