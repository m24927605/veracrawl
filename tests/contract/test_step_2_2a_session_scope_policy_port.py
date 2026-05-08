"""Contract tests for Phase 2 step 2.2a — ``SessionScopePolicy`` port.

The Protocol must be satisfied by a minimal in-memory test double
and the production :class:`StrictAllowlistScope`. Both must raise
:class:`CredentialScopeViolation` (a typed
:class:`PolicyViolation`) on refusal — never plain
:class:`ValueError` — because callers dispatch on the typed shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import cast

import pytest

from veracrawl.adapters.session.strict_allowlist_scope import StrictAllowlistScope
from veracrawl.contracts.errors import CredentialScopeViolation, PolicyViolation
from veracrawl.contracts.security_privacy import CredentialScope
from veracrawl.ports.session_scope_policy import SessionScopePolicy


def _scope() -> CredentialScope:
    return CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=["^/v1/items"],
        allowed_methods=["GET"],
    )


def test_strict_allowlist_scope_has_check_attribute() -> None:
    """Smoke test only — runtime-checkable ``Protocol``'s
    ``isinstance`` check verifies attribute presence, not signature
    or behavior. Behavioral coverage lives in the unit tests.
    Static type-checking is what enforces signature compatibility."""

    policy: SessionScopePolicy = StrictAllowlistScope()
    assert isinstance(policy, SessionScopePolicy)
    assert callable(policy.check)


def test_in_memory_test_double_has_check_attribute() -> None:
    """A minimal allow-everything double exposes the same surface —
    proves the port is small enough that test fixtures can fake
    it without inheriting from the production class. Same caveat
    as the test above: ``isinstance`` only checks attribute
    presence."""

    class _AlwaysAllow:
        def check(
            self,
            scope: CredentialScope,
            *,
            request_url: str,
            method: str,
            now: datetime | None = None,
        ) -> None:
            del scope, request_url, method, now
            return None

    policy: SessionScopePolicy = _AlwaysAllow()
    assert isinstance(policy, SessionScopePolicy)
    assert callable(policy.check)


def test_refusal_is_credential_scope_violation_not_value_error() -> None:
    """A scope refusal must be the typed exception — callers
    dispatch on ``except CredentialScopeViolation`` and would miss
    a plain ``ValueError``."""

    policy = StrictAllowlistScope()
    with pytest.raises(CredentialScopeViolation):
        policy.check(_scope(), request_url="https://other.example.com/v1/items", method="GET")


def test_refusal_inherits_policy_violation() -> None:
    """``except PolicyViolation`` must catch scope refusals so the
    common policy-handling path in the agent runtime works."""

    policy = StrictAllowlistScope()
    try:
        policy.check(_scope(), request_url="https://api.example.com/v1/items", method="DELETE")
    except PolicyViolation as exc:
        assert isinstance(exc, CredentialScopeViolation)
    else:
        pytest.fail("expected CredentialScopeViolation to be raised")


def test_refusal_carries_sanitized_attributes_not_raw_url() -> None:
    """The raised exception must carry redacted public attributes —
    a credentialed URL passed by the caller cannot leak through
    ``__dict__`` / ``vars(err)`` / ``logging.exception()``."""

    policy = StrictAllowlistScope()
    leaky_url = "https://user:secret@evil.example.com/v1/items?api_key=DEADBEEF"
    with pytest.raises(CredentialScopeViolation) as excinfo:
        policy.check(_scope(), request_url=leaky_url, method="GET")
    err = cast(CredentialScopeViolation, excinfo.value)
    text = f"{err!r} {err} {err.__dict__}"
    assert "secret@" not in text
    assert "DEADBEEF" not in text
    assert "api_key" not in text
