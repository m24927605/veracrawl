"""Phase 3 step 3.5b — AmazonSpApiLwaTransport integration tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from veracrawl.adapters.sources.amazon_sp_api_lwa_transport import (
    AmazonSpApiLwaTransport,
    LwaCredentialBundle,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
)

_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
_REFRESH_TOKEN_CANARY = "CANARY-LWA-REFRESH-TOKEN-must-not-leak"
_CLIENT_SECRET_CANARY = "CANARY-LWA-CLIENT-SECRET-must-not-leak"


def _credentials() -> LwaCredentialBundle:
    return LwaCredentialBundle(
        refresh_token=_REFRESH_TOKEN_CANARY,
        client_id="amzn1.application-oa2-client.canary",
        client_secret=_CLIENT_SECRET_CANARY,
    )


def _ok_token_response(
    *, access_token: str = "Atza|access-token-fixture", expires_in: int = 3600
) -> dict[str, Any]:
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "token_type": "bearer",
    }


def _build_transport(
    *,
    inner_handler: Callable[[httpx.Request], httpx.Response],
    refresh_handler: Callable[[httpx.Request], httpx.Response],
    clock: Callable[[], datetime] | None = None,
) -> AmazonSpApiLwaTransport:
    return AmazonSpApiLwaTransport(
        inner=httpx.MockTransport(inner_handler),
        credentials=_credentials(),
        token_refresh_transport=httpx.MockTransport(refresh_handler),
        clock=clock or (lambda: _NOW),
        runtime_mode=RuntimeMode.FIXTURE,
    )


# --- LwaCredentialBundle ---------------------------------------------------


def test_credential_bundle_rejects_blank_refresh_token() -> None:
    with pytest.raises(ValueError, match="refresh_token"):
        LwaCredentialBundle(
            refresh_token="   ",
            client_id="x",
            client_secret="y",
        )


def test_credential_bundle_rejects_blank_client_id() -> None:
    with pytest.raises(ValueError, match="client_id"):
        LwaCredentialBundle(
            refresh_token="r",
            client_id="",
            client_secret="y",
        )


def test_credential_bundle_redacts_repr() -> None:
    creds = _credentials()
    assert _REFRESH_TOKEN_CANARY not in repr(creds)
    assert _CLIENT_SECRET_CANARY not in repr(creds)
    assert "<redacted>" in repr(creds)


def test_credential_bundle_redacts_str() -> None:
    creds = _credentials()
    assert _REFRESH_TOKEN_CANARY not in str(creds)
    assert _CLIENT_SECRET_CANARY not in str(creds)


# --- Construction gates ----------------------------------------------------


def test_production_mode_raises() -> None:
    with pytest.raises(ProductionRuntimeNotImplemented):
        AmazonSpApiLwaTransport(
            inner=httpx.MockTransport(lambda _: httpx.Response(200)),
            credentials=_credentials(),
            token_refresh_transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=_ok_token_response())
            ),
            runtime_mode=RuntimeMode.PRODUCTION,
        )


def test_fixture_mode_requires_token_refresh_transport() -> None:
    with pytest.raises(ValueError, match="token_refresh_transport"):
        AmazonSpApiLwaTransport(
            inner=httpx.MockTransport(lambda _: httpx.Response(200)),
            credentials=_credentials(),
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_fixture_mode_refuses_real_token_refresh_transport() -> None:
    with pytest.raises(ValueError, match="MockTransport"):
        AmazonSpApiLwaTransport(
            inner=httpx.MockTransport(lambda _: httpx.Response(200)),
            credentials=_credentials(),
            token_refresh_transport=httpx.HTTPTransport(),
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_construction_consults_current_mode_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    with pytest.raises(ProductionRuntimeNotImplemented):
        AmazonSpApiLwaTransport(
            inner=httpx.MockTransport(lambda _: httpx.Response(200)),
            credentials=_credentials(),
            token_refresh_transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=_ok_token_response())
            ),
        )


# --- Wire shape ------------------------------------------------------------


def test_outgoing_request_carries_x_amz_access_token() -> None:
    inner_calls: list[httpx.Request] = []

    def inner(request: httpx.Request) -> httpx.Response:
        inner_calls.append(request)
        return httpx.Response(200, json={"items": []})

    refresh_calls: list[httpx.Request] = []

    def refresh(request: httpx.Request) -> httpx.Response:
        refresh_calls.append(request)
        return httpx.Response(
            200, json=_ok_token_response(access_token="Atza|fresh")
        )

    transport = _build_transport(inner_handler=inner, refresh_handler=refresh)
    client = httpx.Client(transport=transport)
    client.get("https://sellingpartnerapi-na.amazon.com/listings/items")
    assert inner_calls[0].headers["x-amz-access-token"] == "Atza|fresh"
    assert len(refresh_calls) == 1
    # Refresh request hits the LWA endpoint.
    assert "api.amazon.com/auth/o2/token" in str(refresh_calls[0].url)
    # Body is form-encoded with the credentials.
    body = refresh_calls[0].content.decode("utf-8")
    assert "grant_type=refresh_token" in body
    assert f"refresh_token={_REFRESH_TOKEN_CANARY}" in body


def test_token_cached_across_calls() -> None:
    refresh_call_count = 0

    def refresh(_: httpx.Request) -> httpx.Response:
        nonlocal refresh_call_count
        refresh_call_count += 1
        return httpx.Response(200, json=_ok_token_response())

    transport = _build_transport(
        inner_handler=lambda _: httpx.Response(200, json={}),
        refresh_handler=refresh,
    )
    client = httpx.Client(transport=transport)
    for _ in range(5):
        client.get("https://sellingpartnerapi-na.amazon.com/listings/items")
    assert refresh_call_count == 1  # cached after first


def test_token_refreshed_when_within_safety_margin() -> None:
    refresh_call_count = 0
    current_time = _NOW

    def refresh(_: httpx.Request) -> httpx.Response:
        nonlocal refresh_call_count
        refresh_call_count += 1
        return httpx.Response(200, json=_ok_token_response(expires_in=120))

    def clock() -> datetime:
        return current_time

    transport = AmazonSpApiLwaTransport(
        inner=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        credentials=_credentials(),
        token_refresh_transport=httpx.MockTransport(refresh),
        clock=clock,
        runtime_mode=RuntimeMode.FIXTURE,
    )
    client = httpx.Client(transport=transport)
    client.get("https://sellingpartnerapi-na.amazon.com/listings/items")
    assert refresh_call_count == 1
    # Advance time past the safety margin.
    current_time = _NOW + timedelta(seconds=80)
    client.get("https://sellingpartnerapi-na.amazon.com/listings/items")
    assert refresh_call_count == 2  # refreshed
