"""``HttpxCrawlFetcher`` — default :class:`CrawlHttpFetcherPort` implementation.

Built on :mod:`httpx`. Enforces:

* http(s) scheme only;
* a size budget on the response body (refuse rather than truncate);
* private-network denial unless ``allow_loopback`` is opted in (the
  same toggle the URL classifier uses);
* a configurable user agent header.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urlsplit

import httpx

from veracrawl.ports.crawl_http_fetcher import FetchError, FetchOutcome, RedirectHop

_SUPPORTED_SCHEMES = frozenset({"http", "https"})


def _is_private_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        try:
            resolved = socket.gethostbyname(host)
        except OSError:
            return False
        try:
            addr = ipaddress.ip_address(resolved)
        except ValueError:
            return False
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
    )


class HttpxCrawlFetcher:
    """Default :class:`CrawlHttpFetcherPort` impl backed by :mod:`httpx`.

    Uses a single persistent :class:`httpx.Client` so cookies set by
    earlier responses are sent on later requests to the same host
    (sites that gate listing pages behind a session cookie now work
    out-of-the-box). Connection pooling also reduces per-fetch
    handshake cost.
    """

    def __init__(
        self,
        *,
        user_agent: str,
        max_response_bytes: int,
        allow_loopback: bool = False,
        max_redirects: int = 10,
        default_timeout_seconds: float = 10.0,
    ) -> None:
        if not user_agent or not user_agent.strip():
            raise ValueError("user_agent must be non-empty")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if max_redirects < 0:
            raise ValueError("max_redirects must be non-negative")
        self._user_agent = user_agent
        self._max_response_bytes = max_response_bytes
        self._allow_loopback = allow_loopback
        self._max_redirects = max_redirects
        self._client = httpx.Client(
            follow_redirects=True,
            max_redirects=max_redirects,
            timeout=default_timeout_seconds,
            headers={"User-Agent": user_agent},
        )

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:
        parsed = urlsplit(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in _SUPPORTED_SCHEMES:
            raise FetchError(f"refusing unsupported scheme {scheme!r} for {url!r}")

        host = (parsed.hostname or "").lower()
        if not host:
            raise FetchError(f"url missing hostname: {url!r}")
        if not self._allow_loopback and _is_private_host(host):
            raise FetchError(
                f"refusing to fetch private-network host {host!r}; "
                "set allow_loopback=True only for local fixtures"
            )

        started = time.monotonic()
        try:
            response = self._client.get(url, timeout=timeout_seconds)
            body = response.content
        except httpx.HTTPError as exc:
            raise FetchError(f"transport error fetching {url!r}: {exc}") from exc

        if len(body) > self._max_response_bytes:
            raise FetchError(
                f"response body for {url!r} exceeds size budget "
                f"({len(body)} > {self._max_response_bytes} bytes)"
            )

        redirect_chain = [str(resp.url) for resp in response.history]
        redirect_history: list[RedirectHop] = []
        # Each entry in response.history is the 3xx response that
        # *caused* a redirect. The next-step URL is the requested
        # URL of the next history entry, falling back to the final
        # response URL for the last hop.
        for idx, hop_resp in enumerate(response.history):
            if idx + 1 < len(response.history):
                to_url = str(response.history[idx + 1].url)
            else:
                to_url = str(response.url)
            redirect_history.append(
                RedirectHop(
                    from_url=str(hop_resp.url),
                    to_url=to_url,
                    status_code=hop_resp.status_code,
                )
            )
        elapsed_ms = (time.monotonic() - started) * 1000.0
        return FetchOutcome(
            requested_url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items()},
            body=body,
            content_type=response.headers.get("content-type", ""),
            redirect_chain=redirect_chain,
            redirect_history=redirect_history,
            elapsed_ms=elapsed_ms,
        )

    def close(self) -> None:
        """Release the underlying httpx connection pool."""
        self._client.close()

    def __enter__(self) -> HttpxCrawlFetcher:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


__all__ = ["HttpxCrawlFetcher"]
