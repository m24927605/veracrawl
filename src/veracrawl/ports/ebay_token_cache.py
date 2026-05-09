"""Phase 3 step 3.4 — eBay OAuth token cache port.

eBay's Browse API requires an application-level OAuth
access token (client-credentials grant). Tokens are valid
for ~2 hours; minting a new one for every request burns
the rate budget. The cache port lets adapters fetch a
still-valid token from disk and only mint a new one when
the cached token has expired (with a safety margin).

The on-disk shape is JSON:

.. code-block:: json

    {
      "ebay_browse_v1": {
        "access_token": "<opaque>",
        "expires_at": "2026-05-09T14:30:00+00:00",
        "minted_at": "2026-05-09T12:30:00+00:00"
      }
    }

The cache stores the raw token because that's what the
adapter needs to send. An attacker with read access to the
cache file can use the token until it expires; deployments
that need stronger isolation should swap the FileBacked
implementation for a Vault-sidecar or OS-keychain backend
(both Phase 6 deployment work).

The cache key is opaque (e.g., ``"ebay_browse_v1"``) so
different adapter scopes can hold their own tokens without
clobbering each other.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class EbayTokenCachePort(Protocol):
    """OAuth token cache for eBay Browse API."""

    def fetch(
        self,
        *,
        cache_key: str,
        now: datetime,
        safety_margin_seconds: int = 60,
    ) -> str | None:
        """Return the cached access_token if it's still valid
        (``expires_at - now > safety_margin_seconds``).
        Otherwise return ``None`` and let the caller mint a
        fresh token via :meth:`store`.
        """

        ...

    def store(
        self,
        *,
        cache_key: str,
        access_token: str,
        expires_at: datetime,
        minted_at: datetime,
    ) -> None:
        """Persist a freshly minted token. Atomic write."""

        ...


__all__ = ["EbayTokenCachePort"]
