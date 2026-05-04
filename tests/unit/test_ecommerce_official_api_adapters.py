from __future__ import annotations

import json
import urllib.request

from pytest import MonkeyPatch

from veracrawl.adapters.official_apis.amazon import AmazonCreatorsApiAdapter
from veracrawl.adapters.official_apis.ebay import EbayBrowseApiAdapter
from veracrawl.contracts.ecommerce_official_api import EcommerceOfficialApiTargetSpec
from veracrawl.ports.ecommerce_official_api import EcommerceOfficialApiResponse


def _amazon_target() -> EcommerceOfficialApiTargetSpec:
    return EcommerceOfficialApiTargetSpec(
        id="amazon",
        site_name="Amazon",
        platform="amazon",
        api_family="amazon_creators_api_credentialed",
        allowed_origin="https://affiliate-program.amazon.com",
        entry_point_url="https://affiliate-program.amazon.com/creatorsapi",
        product_identifier_type="asin",
        product_identifier="B09X7CRKRZ",
        required_identity_terms=["SanDisk"],
        credential_env_vars=[
            "AMAZON_CREATORS_API_ENDPOINT",
            "AMAZON_CREATORS_API_BEARER_TOKEN",
        ],
        required_evidence_types=["identity", "price", "availability"],
    )


def _ebay_target() -> EcommerceOfficialApiTargetSpec:
    return EcommerceOfficialApiTargetSpec(
        id="ebay",
        site_name="eBay",
        platform="ebay",
        api_family="ebay_browse_v1",
        allowed_origin="https://api.ebay.com",
        entry_point_url="https://api.ebay.com/buy/browse/v1/item_summary/search",
        product_identifier_type="query",
        product_identifier="SanDisk 256GB Extreme microSDXC",
        required_identity_terms=["SanDisk"],
        credential_env_vars=["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"],
        required_evidence_types=["identity", "price", "availability"],
    )


def test_amazon_adapter_requires_credentialed_creators_api_endpoint(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("AMAZON_CREATORS_API_ENDPOINT", raising=False)
    monkeypatch.delenv("AMAZON_CREATORS_API_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("AMAZON_CREATORS_API_KEY", raising=False)

    outcome = AmazonCreatorsApiAdapter().fetch_product(
        fixture_id="fixture",
        target=_amazon_target(),
    )

    assert outcome.failure_type == "official_api_credentials_unavailable"
    assert outcome.response is None


def test_amazon_adapter_posts_redacted_credentialed_request(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def transport(
        request: urllib.request.Request,
        timeout_seconds: float,
    ) -> EcommerceOfficialApiResponse:
        captured["url"] = request.full_url
        captured["timeout"] = timeout_seconds
        captured["auth"] = request.get_header("Authorization")
        captured["body"] = request.data
        return EcommerceOfficialApiResponse(
            status_code=200,
            request_url=str(request.full_url),
            final_url=str(request.full_url),
            headers={"Content-Type": "application/json"},
            body=b'{"items":[]}',
        )

    monkeypatch.setenv(
        "AMAZON_CREATORS_API_ENDPOINT",
        "https://affiliate-program.amazon.com/creatorsapi/product-data",
    )
    monkeypatch.setenv("AMAZON_CREATORS_API_BEARER_TOKEN", "secret-token")

    outcome = AmazonCreatorsApiAdapter(transport=transport).fetch_product(
        fixture_id="fixture",
        target=_amazon_target(),
    )

    assert outcome.failure_type is None
    assert captured["url"] == "https://affiliate-program.amazon.com/creatorsapi/product-data"
    assert captured["auth"] == "Bearer secret-token"
    body = captured["body"]
    assert isinstance(body, bytes)
    assert json.loads(body.decode())["itemIds"] == ["B09X7CRKRZ"]


def test_ebay_adapter_requires_access_token_or_oauth_credentials(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("EBAY_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    outcome = EbayBrowseApiAdapter().fetch_product(
        fixture_id="fixture",
        target=_ebay_target(),
    )

    assert outcome.failure_type == "official_api_credentials_unavailable"
    assert outcome.response is None


def test_ebay_adapter_uses_browse_search_with_bearer_token(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, str | None] = {}

    def transport(
        request: urllib.request.Request,
        timeout_seconds: float,
    ) -> EcommerceOfficialApiResponse:
        del timeout_seconds
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["marketplace"] = request.get_header("X-ebay-c-marketplace-id")
        return EcommerceOfficialApiResponse(
            status_code=200,
            request_url=str(request.full_url),
            final_url=str(request.full_url),
            headers={"Content-Type": "application/json"},
            body=b'{"itemSummaries":[]}',
        )

    monkeypatch.setenv("EBAY_ACCESS_TOKEN", "access-token")
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    outcome = EbayBrowseApiAdapter(transport=transport).fetch_product(
        fixture_id="fixture",
        target=_ebay_target(),
    )

    assert outcome.failure_type is None
    assert captured["auth"] == "Bearer access-token"
    assert "q=SanDisk+256GB+Extreme+microSDXC" in str(captured["url"])
    assert captured["marketplace"] == "EBAY_US"
