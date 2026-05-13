"""Unit tests for URL canonicalisation + domain filtering helpers.

Pure helpers, no I/O. They underpin the Phase 2 frontier scheduler:
canonicalisation drives dedup, and the filter decides whether a
candidate URL is admissible against the job spec's allowlist /
denylist / scheme / private-network policy.
"""

from __future__ import annotations

import pytest

from veracrawl.external_crawl.url import (
    DomainFilterReason,
    canonicalize_url,
    classify_url,
)


def test_canonicalize_lowercases_host_and_scheme() -> None:
    assert (
        canonicalize_url("HTTPS://Example.COM/Path")
        == "https://example.com/Path"
    )


def test_canonicalize_strips_fragment() -> None:
    assert canonicalize_url("https://example.com/page#section") == "https://example.com/page"


def test_canonicalize_empty_path_becomes_slash() -> None:
    assert canonicalize_url("https://example.com") == "https://example.com/"


def test_canonicalize_strips_default_ports() -> None:
    assert canonicalize_url("http://example.com:80/a") == "http://example.com/a"
    assert canonicalize_url("https://example.com:443/a") == "https://example.com/a"


def test_canonicalize_preserves_non_default_port() -> None:
    assert (
        canonicalize_url("http://example.com:8080/a")
        == "http://example.com:8080/a"
    )


def test_canonicalize_sorts_query_keys() -> None:
    # Sorting only the keys preserves duplicate parameter semantics.
    assert (
        canonicalize_url("https://example.com/p?b=2&a=1")
        == "https://example.com/p?a=1&b=2"
    )


def test_canonicalize_idempotent() -> None:
    once = canonicalize_url("HTTPS://Example.COM:443/Path?b=2&a=1#frag")
    twice = canonicalize_url(once)
    assert once == twice


def test_classify_allowed_domain_admits() -> None:
    decision = classify_url(
        "https://example.com/a",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit is True
    assert decision.reason is None
    assert decision.canonical_url == "https://example.com/a"


def test_classify_subdomain_of_allowed_domain_admits() -> None:
    decision = classify_url(
        "https://shop.example.com/a",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit
    assert decision.reason is None


def test_classify_unrelated_domain_rejected() -> None:
    decision = classify_url(
        "https://other.test/",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.OUTSIDE_ALLOWED_DOMAIN


def test_classify_denied_domain_rejected_even_if_allowed() -> None:
    decision = classify_url(
        "https://shop.example.com/a",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset({"shop.example.com"}),
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.DENIED_DOMAIN


def test_classify_non_http_scheme_rejected() -> None:
    decision = classify_url(
        "ftp://example.com/file",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.UNSUPPORTED_SCHEME


def test_classify_javascript_url_rejected() -> None:
    decision = classify_url(
        "javascript:alert(1)",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.UNSUPPORTED_SCHEME


def test_classify_loopback_host_marked_private_network() -> None:
    decision = classify_url(
        "http://127.0.0.1/",
        allowed_domains=frozenset({"127.0.0.1"}),
        denied_domains=frozenset(),
        allow_loopback=False,
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.PRIVATE_NETWORK_DENIED


def test_classify_loopback_allowed_when_opted_in() -> None:
    decision = classify_url(
        "http://127.0.0.1/",
        allowed_domains=frozenset({"127.0.0.1"}),
        denied_domains=frozenset(),
        allow_loopback=True,
    )
    assert decision.admit is True
    assert decision.reason is None


def test_classify_private_network_rfc1918_rejected() -> None:
    for host in ("10.0.0.5", "192.168.1.1", "172.16.5.5"):
        decision = classify_url(
            f"http://{host}/",
            allowed_domains=frozenset({host}),
            denied_domains=frozenset(),
            allow_loopback=False,
        )
        assert decision.admit is False, host
        assert decision.reason == DomainFilterReason.PRIVATE_NETWORK_DENIED, host


def test_classify_missing_hostname_rejected() -> None:
    decision = classify_url(
        "http:///page",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.admit is False
    assert decision.reason == DomainFilterReason.UNSUPPORTED_SCHEME


def test_classify_returns_canonical_url() -> None:
    decision = classify_url(
        "HTTPS://Example.COM/A?b=2&a=1#frag",
        allowed_domains=frozenset({"example.com"}),
        denied_domains=frozenset(),
    )
    assert decision.canonical_url == "https://example.com/A?a=1&b=2"


def test_classify_invalid_url_raises_value_error() -> None:
    # A genuinely unparseable URL is a programming error upstream;
    # we surface it rather than silently rejecting.
    with pytest.raises(ValueError):
        canonicalize_url("not a url at all")
