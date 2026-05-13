"""URL canonicalisation and the external-crawl admissibility filter.

Pure helpers with no I/O. Used by the frontier scheduler so it can
decide whether a candidate URL is admissible against the job spec.

The two responsibilities are deliberately separate:

* :func:`canonicalize_url` produces a stable, dedup-safe form of a URL
  (lowercase host, default ports stripped, fragment removed, query
  keys sorted). Two URLs that point to the same resource collapse to
  the same canonical form so the frontier's visited set works.
* :func:`classify_url` decides whether the URL is admitted by the job
  spec, returning a :class:`DomainFilterDecision` carrying both the
  canonical form and the rejection reason (if any).
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qsl, urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}
_SUPPORTED_SCHEMES = frozenset({"http", "https"})


class DomainFilterReason(StrEnum):
    OUTSIDE_ALLOWED_DOMAIN = "outside_allowed_domain"
    DENIED_DOMAIN = "denied_domain"
    UNSUPPORTED_SCHEME = "unsupported_scheme"
    PRIVATE_NETWORK_DENIED = "private_network_denied"


@dataclass(frozen=True, slots=True)
class DomainFilterDecision:
    admit: bool
    reason: DomainFilterReason | None
    canonical_url: str | None = None


def canonicalize_url(url: str) -> str:
    """Return a deterministic form of ``url`` for dedup + comparison.

    Idempotent: ``canonicalize_url(canonicalize_url(x)) == canonicalize_url(x)``.
    Raises :class:`ValueError` if the input is not a parseable URL.
    """
    if not url or not url.strip():
        raise ValueError("url must be non-empty")
    parsed = urlsplit(url.strip())
    if not parsed.scheme:
        raise ValueError(f"url missing scheme: {url!r}")

    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if not host and scheme in _SUPPORTED_SCHEMES:
        # Distinguish "no host" from "weird scheme" for the caller.
        raise ValueError(f"url missing hostname: {url!r}")

    port = parsed.port
    netloc = host
    if port is not None and port != _DEFAULT_PORTS.get(scheme):
        netloc = f"{host}:{port}"

    # Preserve userinfo only if it was present — almost never wanted
    # for crawls, but stripping it would change semantics for the
    # rare case it matters.
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo = f"{userinfo}:{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    path = parsed.path or "/"

    # Sort query keys but preserve duplicate-key values (parse_qsl
    # keeps order within the same key, which is stable under sort).
    if parsed.query:
        pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True))
        query = "&".join(f"{k}={v}" for k, v in pairs)
    else:
        query = ""

    return urlunsplit((scheme, netloc, path, query, ""))


def _is_private_network(host: str) -> bool:
    """Best-effort check: does ``host`` resolve into RFC1918/loopback/link-local space?

    We avoid network resolution for the common case of a literal IP
    or ``localhost`` since the frontier may be called many times per
    second. For DNS hostnames we fall back to ``socket.gethostbyname``
    once — callers can disable this by handing a bare-IP allowlist.
    """
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


def _host_matches_allowed(host: str, allowed_domains: frozenset[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in allowed_domains)


def _host_matches_denied(host: str, denied_domains: frozenset[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in denied_domains)


def classify_url(
    url: str,
    *,
    allowed_domains: frozenset[str],
    denied_domains: frozenset[str],
    allow_loopback: bool = False,
) -> DomainFilterDecision:
    """Classify ``url`` against the job spec's admissibility rules.

    ``allow_loopback`` should be ``True`` only for tests pointing at a
    locally-served fixture — production crawl jobs leave it ``False``
    so RFC1918 / loopback addresses are denied.
    """
    try:
        parsed = urlsplit(url.strip()) if url else urlsplit("")
    except ValueError:
        return DomainFilterDecision(
            admit=False, reason=DomainFilterReason.UNSUPPORTED_SCHEME
        )

    scheme = (parsed.scheme or "").lower()
    if scheme not in _SUPPORTED_SCHEMES:
        return DomainFilterDecision(
            admit=False, reason=DomainFilterReason.UNSUPPORTED_SCHEME
        )

    host = (parsed.hostname or "").lower()
    if not host:
        return DomainFilterDecision(
            admit=False, reason=DomainFilterReason.UNSUPPORTED_SCHEME
        )

    canonical = canonicalize_url(url)

    if _host_matches_denied(host, denied_domains):
        return DomainFilterDecision(
            admit=False,
            reason=DomainFilterReason.DENIED_DOMAIN,
            canonical_url=canonical,
        )

    if not _host_matches_allowed(host, allowed_domains):
        return DomainFilterDecision(
            admit=False,
            reason=DomainFilterReason.OUTSIDE_ALLOWED_DOMAIN,
            canonical_url=canonical,
        )

    if not allow_loopback and _is_private_network(host):
        return DomainFilterDecision(
            admit=False,
            reason=DomainFilterReason.PRIVATE_NETWORK_DENIED,
            canonical_url=canonical,
        )

    return DomainFilterDecision(admit=True, reason=None, canonical_url=canonical)


__all__ = [
    "DomainFilterDecision",
    "DomainFilterReason",
    "canonicalize_url",
    "classify_url",
]
