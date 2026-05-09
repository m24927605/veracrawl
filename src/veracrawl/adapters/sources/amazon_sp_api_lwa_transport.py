"""Phase 3 step 3.5b — Amazon SP-API LWA-only signing transport.

Wraps an inner ``httpx.BaseTransport`` and adds the
``x-amz-access-token`` header to outgoing requests, fetching
a fresh access_token via the LWA refresh-token grant when
the cached token has expired (with a safety margin).

Per Amazon's 2023-10-02 SP-API changelog
(https://developer-docs.amazon.com/sp-api/docs/sp-api-will-no-longer-require-aws-iam-or-aws-signature-version-4):
**no AWS SigV4 / IAM signing is required**. The only
authentication is the LWA bearer token in the
``x-amz-access-token`` header.

Wire shape — token refresh:

::

    POST https://api.amazon.com/auth/o2/token
    Content-Type: application/x-www-form-urlencoded

    grant_type=refresh_token
    &refresh_token=<long-lived refresh token>
    &client_id=<LWA client id>
    &client_secret=<LWA client secret>

    → 200 OK
      {"access_token": "...", "expires_in": 3600,
       "token_type": "bearer"}

Boundary invariants:

* All credentials (refresh_token / client_id / client_secret)
  arrive as opaque strings — the transport never logs them
  and never echoes them in exceptions.
* The token refresh endpoint is hard-coded (``api.amazon.com``)
  to prevent caller-supplied URL injection.
* The cache port is injected so multiple worktree runs share
  one access_token (process-cache by default;
  ``FileBackedEbayTokenCache`` is shape-compatible if the
  caller wants persistence — same JSON shape).
* PRODUCTION mode is gated behind ``ProductionRuntimeNotImplemented``
  until Phase 6 step 6.1 wires the production deployment.
* Live validation (step 6.4) requires SP-API developer-
  account approval and an LWA refresh token.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
_DEFAULT_SAFETY_MARGIN_SECONDS = 60
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)


@dataclass(frozen=True)
class LwaCredentialBundle:
    """Opaque credential bundle for the LWA refresh-token grant.

    Construction validates non-blank fields. ``__repr__`` /
    ``__str__`` redact the secret values so they don't surface
    in logs accidentally.
    """

    refresh_token: str
    client_id: str
    client_secret: str

    def __post_init__(self) -> None:
        for name in ("refresh_token", "client_id", "client_secret"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"LWA credential {name!r} must be non-blank")

    def __repr__(self) -> str:
        return (
            "LwaCredentialBundle(refresh_token=<redacted>, "
            "client_id=<redacted>, client_secret=<redacted>)"
        )

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class _CachedToken:
    access_token: str
    expires_at: datetime


class AmazonSpApiLwaTransport(httpx.BaseTransport):
    """LWA-only signing transport for SP-API.

    Construct with an inner ``httpx.BaseTransport`` (typically
    the Phase 1 cooperative HTTP transport in production, or
    ``httpx.MockTransport`` in fixture mode) plus an LWA
    credential bundle. Outgoing requests get the
    ``x-amz-access-token`` header injected; the transport
    refreshes the token on first call and whenever the cached
    token is within the safety-margin window.

    The token-refresh endpoint runs on its own
    ``httpx.Client`` so the inner transport (which may be
    pre-wrapped with the cooperative HTTP stack) doesn't see
    the refresh call as an SP-API request.
    """

    def __init__(
        self,
        *,
        inner: httpx.BaseTransport,
        credentials: LwaCredentialBundle,
        token_refresh_transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        safety_margin_seconds: int = _DEFAULT_SAFETY_MARGIN_SECONDS,
        runtime_mode: RuntimeMode | None = None,
    ) -> None:
        effective_mode = runtime_mode if runtime_mode is not None else current_mode()
        if effective_mode is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="amazon_sp_api_lwa_transport",
                gate="phase_3_step_3_5b_production_call",
            )
        if safety_margin_seconds < 0:
            raise ValueError("safety_margin_seconds must be non-negative")
        if token_refresh_transport is None:
            raise ValueError(
                "AmazonSpApiLwaTransport in FIXTURE mode requires an explicit "
                "token_refresh_transport (typically httpx.MockTransport). The "
                "PRODUCTION wiring is gated until Phase 6 step 6.1."
            )
        if not isinstance(token_refresh_transport, httpx.MockTransport):
            raise ValueError(
                "AmazonSpApiLwaTransport in FIXTURE mode only accepts "
                "httpx.MockTransport for the token-refresh transport."
            )
        self._inner = inner
        self._credentials = credentials
        self._safety_margin_seconds = safety_margin_seconds
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(UTC))
        self._refresh_client = httpx.Client(
            transport=token_refresh_transport, timeout=_DEFAULT_TIMEOUT
        )
        self._cached: _CachedToken | None = None
        self._lock = threading.Lock()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        token = self._fetch_or_refresh_token()
        # Mutate a copy of the headers so the original
        # request object isn't shared-state-modified.
        request.headers["x-amz-access-token"] = token
        return self._inner.handle_request(request)

    def _fetch_or_refresh_token(self) -> str:
        with self._lock:
            now = self._clock()
            cached = self._cached
            if (
                cached is not None
                and (cached.expires_at - now).total_seconds()
                > self._safety_margin_seconds
            ):
                return cached.access_token
            # Cache miss or near-expiry → refresh.
            access_token, expires_in = self._post_refresh()
            self._cached = _CachedToken(
                access_token=access_token,
                expires_at=now + timedelta(seconds=expires_in),
            )
            return access_token

    def _post_refresh(self) -> tuple[str, int]:
        body = {
            "grant_type": "refresh_token",
            "refresh_token": self._credentials.refresh_token,
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
        }
        try:
            response = self._refresh_client.post(
                _LWA_TOKEN_URL,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise LwaRefreshError("LWA refresh transport failure") from exc
        if response.status_code != 200:
            response.read()
            raise LwaRefreshError(
                f"LWA refresh failed with HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except Exception:
            raise LwaRefreshError("LWA refresh response was not valid JSON") from None
        if not isinstance(payload, dict):
            raise LwaRefreshError("LWA refresh response was not a JSON object")
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not isinstance(access_token, str) or not access_token.strip():
            raise LwaRefreshError(
                "LWA refresh response missing or blank 'access_token'"
            )
        if not isinstance(expires_in, int) or isinstance(expires_in, bool):
            raise LwaRefreshError(
                "LWA refresh response 'expires_in' must be a plain integer"
            )
        if expires_in <= 0:
            raise LwaRefreshError(
                "LWA refresh response 'expires_in' must be positive"
            )
        return access_token, expires_in


class LwaRefreshError(RuntimeError):
    """Raised when the LWA refresh-token grant fails. Sanitized
    — message never echoes the response body or the credentials."""


__all__ = [
    "AmazonSpApiLwaTransport",
    "LwaCredentialBundle",
    "LwaRefreshError",
]
