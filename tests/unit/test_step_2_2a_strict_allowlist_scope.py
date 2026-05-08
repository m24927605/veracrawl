"""Unit tests for ``StrictAllowlistScope`` (Phase 2 step 2.2a).

Behavioral expectations:

1. Allow when origin / route / method / expiry all match.
2. Refuse with ``origin_not_allowed`` when origin doesn't match
   (different host, different scheme, different port, malformed
   URL, non-http scheme).
3. Refuse with ``route_not_allowed`` when path doesn't match any
   pattern (path-anchored regex match).
4. Refuse with ``method_not_allowed`` when method isn't in the
   allowlist (case-insensitive normalize).
5. Refuse with ``expired`` when ``scope.expires_at`` has lapsed
   (injectable ``now``).
6. Stable behavior under (a) default port stripping, (b) host
   case-insensitivity, (c) trailing slashes, (d) query / fragment
   on the request URL not affecting route match.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from veracrawl.adapters.session.strict_allowlist_scope import StrictAllowlistScope
from veracrawl.contracts.errors import CredentialScopeViolation
from veracrawl.contracts.security_privacy import CredentialScope


def _make_scope(
    *,
    allowed_origins: list[str] | None = None,
    allowed_route_patterns: list[str] | None = None,
    allowed_methods: list[str] | None = None,
    expires_at: datetime | None = None,
) -> CredentialScope:
    return CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=allowed_origins or ["https://api.example.com"],
        allowed_route_patterns=allowed_route_patterns or ["^/v1/items"],
        allowed_methods=allowed_methods or ["GET"],
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_allows_request_within_scope() -> None:
    StrictAllowlistScope().check(
        _make_scope(),
        request_url="https://api.example.com/v1/items",
        method="GET",
    )


def test_allows_default_port_request_against_no_port_origin() -> None:
    """``https://host`` and ``https://host:443`` are the same origin
    per RFC 6454. The matcher normalizes default ports."""

    StrictAllowlistScope().check(
        _make_scope(),
        request_url="https://api.example.com:443/v1/items",
        method="GET",
    )


def test_allows_request_with_query_and_fragment_on_route_match() -> None:
    """Query / fragment on the request URL must not change which
    route the matcher tests; the route is the path component only."""

    StrictAllowlistScope().check(
        _make_scope(),
        request_url="https://api.example.com/v1/items?page=2#section",
        method="GET",
    )


def test_method_match_is_case_insensitive_against_allowlist() -> None:
    """The allowlist is upper-case (CredentialScope contract enforces
    that). The runtime accepts a lower-case caller method by
    upper-casing before comparison."""

    StrictAllowlistScope().check(
        _make_scope(allowed_methods=["GET", "POST"]),
        request_url="https://api.example.com/v1/items",
        method="get",
    )


def test_host_match_is_case_insensitive() -> None:
    """``API.Example.COM`` and ``api.example.com`` are the same host
    per RFC 3986."""

    StrictAllowlistScope().check(
        _make_scope(allowed_origins=["https://API.Example.COM"]),
        request_url="https://api.example.com/v1/items",
        method="GET",
    )


def test_allows_when_expiry_in_future() -> None:
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    StrictAllowlistScope().check(
        _make_scope(expires_at=expires_at),
        request_url="https://api.example.com/v1/items",
        method="GET",
    )


def test_allows_when_expiry_unset() -> None:
    """``expires_at=None`` means the scope never expires at the
    runtime layer."""

    StrictAllowlistScope().check(
        _make_scope(expires_at=None),
        request_url="https://api.example.com/v1/items",
        method="GET",
    )


def test_route_pattern_match_is_anchored_via_caret() -> None:
    """``^/v1/items`` matches ``/v1/items/123`` (search semantics +
    explicit caret) but not ``/items``."""

    policy = StrictAllowlistScope()
    policy.check(
        _make_scope(allowed_route_patterns=["^/v1/items"]),
        request_url="https://api.example.com/v1/items/123",
        method="GET",
    )
    with pytest.raises(CredentialScopeViolation) as excinfo:
        policy.check(
            _make_scope(allowed_route_patterns=["^/v1/items"]),
            request_url="https://api.example.com/items",
            method="GET",
        )
    assert excinfo.value.reason == "route_not_allowed"


# ---------------------------------------------------------------------------
# Refusal paths
# ---------------------------------------------------------------------------


def test_refuses_unknown_origin_with_origin_not_allowed_reason() -> None:
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(),
            request_url="https://other.example.com/v1/items",
            method="GET",
        )
    assert excinfo.value.reason == "origin_not_allowed"


def test_refuses_scheme_downgrade_with_origin_not_allowed_reason() -> None:
    """``https://api.example.com`` and ``http://api.example.com`` are
    different origins (the scheme is part of the origin tuple per
    RFC 6454). A scope allowing one must not admit the other."""

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(),
            request_url="http://api.example.com/v1/items",
            method="GET",
        )
    assert excinfo.value.reason == "origin_not_allowed"


def test_refuses_non_default_port_with_origin_not_allowed_reason() -> None:
    """``https://api.example.com`` (default 443) is not the same as
    ``https://api.example.com:8443``."""

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(),
            request_url="https://api.example.com:8443/v1/items",
            method="GET",
        )
    assert excinfo.value.reason == "origin_not_allowed"


@pytest.mark.parametrize(
    "malformed_url",
    [
        "ftp://api.example.com/v1/items",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "not-a-url",
        "",
        "//missing-scheme.example.com/v1/items",
    ],
)
def test_refuses_non_http_or_malformed_url_as_origin_not_allowed(malformed_url: str) -> None:
    """Malformed / non-http URLs become ``origin_not_allowed`` —
    never plain ``ValueError`` — because the caller dispatches on
    typed scope events."""

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(),
            request_url=malformed_url,
            method="GET",
        )
    assert excinfo.value.reason == "origin_not_allowed"


def test_refuses_unknown_method_with_method_not_allowed_reason() -> None:
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(allowed_methods=["GET"]),
            request_url="https://api.example.com/v1/items",
            method="DELETE",
        )
    assert excinfo.value.reason == "method_not_allowed"


def test_refuses_route_not_in_patterns_with_route_not_allowed_reason() -> None:
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(allowed_route_patterns=["^/v1/items"]),
            request_url="https://api.example.com/v2/users",
            method="GET",
        )
    assert excinfo.value.reason == "route_not_allowed"


def test_refuses_when_expires_at_in_past_with_expired_reason() -> None:
    expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(expires_at=expires_at),
            request_url="https://api.example.com/v1/items",
            method="GET",
        )
    assert excinfo.value.reason == "expired"


def test_refuses_when_now_equals_expires_at_with_expired_reason() -> None:
    """Expiry is a strict-greater comparison: ``now == expires_at``
    is treated as expired."""

    expires_at = datetime(2026, 5, 8, 12, 0, 0, tzinfo=UTC)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(expires_at=expires_at),
            request_url="https://api.example.com/v1/items",
            method="GET",
            now=expires_at,
        )
    assert excinfo.value.reason == "expired"


def test_expiry_check_uses_injected_now() -> None:
    """A frozen ``now`` in the future relative to ``expires_at`` is
    expired regardless of wall clock — proves replay determinism."""

    expires_at = datetime(2026, 1, 1, tzinfo=UTC)
    later = datetime(2026, 6, 1, tzinfo=UTC)
    with pytest.raises(CredentialScopeViolation):
        StrictAllowlistScope().check(
            _make_scope(expires_at=expires_at),
            request_url="https://api.example.com/v1/items",
            method="GET",
            now=later,
        )


def test_expiry_check_refuses_naive_now() -> None:
    """A tz-naive ``now`` is rejected with ``ValueError`` (not a
    scope refusal): the contract requires tz-aware times for replay
    determinism, and silently assuming UTC would mask wiring bugs."""

    expires_at = datetime.now(UTC) + timedelta(hours=1)
    naive_now = datetime(2026, 5, 8, 12, 0, 0)  # noqa: DTZ001 — intentional
    with pytest.raises(ValueError, match="timezone"):
        StrictAllowlistScope().check(
            _make_scope(expires_at=expires_at),
            request_url="https://api.example.com/v1/items",
            method="GET",
            now=naive_now,
        )


# ---------------------------------------------------------------------------
# Refusal precedence — first-match-wins keeps the runtime path
# deterministic for replay
# ---------------------------------------------------------------------------


def test_expired_takes_precedence_over_other_refusals() -> None:
    """If the scope is already expired, the refusal must surface as
    ``expired`` regardless of whether the request would also fail
    other checks. Operators triaging a refusal should see the
    primary cause (the credential is no longer valid), not a
    secondary one."""

    expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(expires_at=expires_at),
            request_url="https://other.example.com/wrong",
            method="DELETE",
            now=datetime.now(UTC),
        )
    assert excinfo.value.reason == "expired"


# ---------------------------------------------------------------------------
# Refusal payload privacy
# ---------------------------------------------------------------------------


def test_refusal_does_not_leak_credentialed_url() -> None:
    """The raised exception's stringification and ``__dict__`` must
    not echo userinfo / query parameters on the request URL."""

    leaky_url = "https://u:p@api.example.com/v1/items?api_key=ABCD&session=XYZ#code=Q"
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _make_scope(allowed_methods=["POST"]),  # forces method_not_allowed
            request_url=leaky_url,
            method="GET",
        )
    err = excinfo.value
    text = f"{err!r} {err} {err.__dict__}"
    assert "u:p@" not in text
    assert "ABCD" not in text
    assert "XYZ" not in text
    assert "api_key" not in text
