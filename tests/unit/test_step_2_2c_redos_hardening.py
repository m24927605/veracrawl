"""Unit tests for Phase 2 step 2.2c — runtime ReDoS hardening.

Phase 0 step 0.3 reservation pull-forward + Phase 2 step 2.2a
runtime-ReDoS reservation. Codex flagged across 4 of 5 step-2.2a
iterations that the credential-bearing route matcher relied solely
on a 4 KiB path-length cap + contract-time AST guard, leaving
contract-valid patterns with ambiguous alternations
(``(a|aa)+``) able to backtrack catastrophically on much shorter
hostile inputs.

Step 2.2c switches the matcher to the third-party ``regex``
package, which supports a per-match wall-clock ``timeout=`` kwarg.
A pattern that exceeds the budget raises :class:`TimeoutError`;
``StrictAllowlistScope`` translates that to a typed
``CredentialScopeViolation(ROUTE_NOT_ALLOWED)`` refusal.

These tests verify:

1. Happy-path matches still succeed without timeout.
2. A known catastrophic-backtracking pattern + adversarial input
   is bounded by the timeout (well under 1 s wall-clock).
3. The refusal is the typed scope event, not a raw
   :class:`TimeoutError` — callers that ``except
   CredentialScopeViolation`` keep working.
4. Timeout latency stays small enough for production load
   (< 200 ms regression budget).
"""

from __future__ import annotations

import time

import pytest
import regex

from veracrawl.adapters.session.strict_allowlist_scope import StrictAllowlistScope
from veracrawl.contracts.errors import (
    CredentialScopeReason,
    CredentialScopeViolation,
)
from veracrawl.contracts.security_privacy import CredentialScope


def _scope_with_pattern(pattern: str) -> CredentialScope:
    return CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=[pattern],
        allowed_methods=["GET"],
    )


def test_happy_path_match_completes_without_timeout() -> None:
    """A normal pattern + matching URL must succeed under the
    timeout (no false-positive timeout on benign inputs)."""

    StrictAllowlistScope().check(
        _scope_with_pattern("^/v1/items"),
        request_url="https://api.example.com/v1/items/123",
        method="GET",
    )


def test_happy_path_non_match_completes_without_timeout() -> None:
    """A normal pattern + non-matching URL must refuse with
    ``ROUTE_NOT_ALLOWED`` under the timeout — same behavior as the
    pre-2.2c matcher, just bounded by the timeout."""

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _scope_with_pattern("^/v1/items"),
            request_url="https://api.example.com/v2/users",
            method="GET",
        )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED


def test_timeout_error_translates_to_typed_refusal_via_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex iter-2 important: deterministically verify the
    timeout-translation path. Patch ``regex.match`` to raise
    :class:`TimeoutError` unconditionally; the matcher must
    translate that to ``CredentialScopeViolation(ROUTE_NOT_ALLOWED)``,
    not let the raw ``TimeoutError`` escape the policy boundary.
    Real-engine timing tests below are supplemental — the
    ``regex`` package's optimizer can converge quickly on patterns
    that would have hung stdlib ``re``, so a wall-clock assertion
    is not a reliable test of the translation path.
    """

    def _always_timeout(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TimeoutError("simulated regex.match timeout")

    monkeypatch.setattr(
        "veracrawl.adapters.session.strict_allowlist_scope.regex.match",
        _always_timeout,
    )

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _scope_with_pattern("^/v1/items"),
            request_url="https://api.example.com/v1/items",
            method="GET",
        )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED


def test_known_backtracking_pattern_does_not_hang_the_worker() -> None:
    """Sanity check (supplemental to the deterministic monkeypatch
    test above): a known ReDoS-shaped pattern + adversarial input
    must complete in bounded time, regardless of whether the
    ``regex`` engine optimizes the match away (returning ``None``)
    or actually hits the timeout. Either outcome is acceptable —
    the contract is that the worker is not wedged."""

    # ``regex.compile("/(a|aa)+")`` is contract-valid (no
    # structurally nested quantifiers); ``regex`` may optimize
    # this and return ``None`` faster than the timeout fires.
    # We don't care which path runs — only that the credential
    # gate doesn't hang on this kind of input.
    backtracking_pattern = "^/(a|aa)+$"
    adversarial_path = "/" + ("a" * 60) + "!"

    start = time.monotonic()
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            _scope_with_pattern(backtracking_pattern),
            request_url=f"https://api.example.com{adversarial_path}",
            method="GET",
        )
    elapsed = time.monotonic() - start

    # 200 ms regression budget — generous over the 50 ms internal
    # timeout for test-runner overhead. A truly hung matcher would
    # blow this budget.
    assert elapsed < 0.2, (
        f"matcher took {elapsed:.3f}s on a backtracking-shaped "
        "pattern — expected <0.2s either by optimization or timeout"
    )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED


def test_timeout_does_not_escape_as_raw_timeout_error() -> None:
    """A caller that ``except CredentialScopeViolation`` must catch
    the timeout-induced refusal — never see a bare
    :class:`TimeoutError` escape from the policy boundary."""

    backtracking_pattern = "^/(a|aa)+$"
    adversarial_path = "/" + ("a" * 60) + "!"
    try:
        StrictAllowlistScope().check(
            _scope_with_pattern(backtracking_pattern),
            request_url=f"https://api.example.com{adversarial_path}",
            method="GET",
        )
    except CredentialScopeViolation:
        pass  # Expected typed refusal.
    except TimeoutError:
        pytest.fail("raw TimeoutError escaped the policy boundary")


def test_cumulative_budget_refuses_after_deadline_via_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex iter-3 important: deterministic verification that the
    cumulative-deadline refusal fires. Patch ``regex.match`` to
    sleep almost exactly the per-match budget on every call, then
    advance through the pattern list — once the cumulative wall
    clock crosses ``_TOTAL_BUDGET_SECONDS`` the matcher must
    refuse rather than continue iterating, regardless of whether
    a later pattern would have matched."""

    from veracrawl.adapters.session import strict_allowlist_scope as sas

    call_log: list[float] = []
    fake_now = [0.0]

    def fake_monotonic() -> float:
        return fake_now[0]

    def fake_match(*args: object, **kwargs: object) -> None:
        # Simulate ~per_match_timeout of work by advancing the
        # fake clock. ``timeout=`` kwarg is the budget the matcher
        # passed in; consume it fully and return None (no match).
        timeout = kwargs.get("timeout", sas._MATCH_TIMEOUT_SECONDS)
        assert isinstance(timeout, float)
        call_log.append(timeout)
        fake_now[0] += timeout
        return None

    monkeypatch.setattr(sas, "regex", type("R", (), {"match": staticmethod(fake_match)}))
    monkeypatch.setattr(sas.time, "monotonic", fake_monotonic)

    scope = CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=[
            "^/v1/items",
            "^/v2/items",
            "^/v3/items",
            "^/v4/items",
            "^/v5/items",  # would otherwise be the 5th attempt
        ],
        allowed_methods=["GET"],
    )

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            scope,
            request_url="https://api.example.com/never-matches",
            method="GET",
        )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED

    # Cumulative budget is 100 ms; per-match is 50 ms. After two
    # full per-match consumptions (100 ms), the third iteration
    # finds ``remaining <= 0`` and refuses without invoking
    # ``regex.match`` again. Verify the call log and budget shrink.
    assert len(call_log) == 2, (
        f"expected matcher to bail after 2 full per-match consumptions; "
        f"got {len(call_log)} calls: {call_log}"
    )
    # The two timeouts passed in are bounded by the per-match cap
    # AND the remaining cumulative budget at the time of each call.
    assert call_log[0] == pytest.approx(0.05, abs=1e-6)
    assert call_log[1] == pytest.approx(0.05, abs=1e-6)


def test_per_match_timeout_shrinks_with_remaining_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex iter-3 important: per-match timeouts must be the
    minimum of the per-match cap and the remaining cumulative
    budget. Patch ``regex.match`` to consume a partial budget
    on each call, then assert the next call receives a smaller
    timeout that reflects the remaining deadline."""

    from veracrawl.adapters.session import strict_allowlist_scope as sas

    timeouts_seen: list[float] = []
    fake_now = [0.0]

    def fake_monotonic() -> float:
        return fake_now[0]

    def fake_match(*args: object, **kwargs: object) -> None:
        timeout = kwargs.get("timeout", sas._MATCH_TIMEOUT_SECONDS)
        assert isinstance(timeout, float)
        timeouts_seen.append(timeout)
        # Consume 80% of the budget on each call so the next
        # iteration sees a strictly smaller remaining budget.
        fake_now[0] += timeout * 0.8
        return None

    monkeypatch.setattr(sas, "regex", type("R", (), {"match": staticmethod(fake_match)}))
    monkeypatch.setattr(sas.time, "monotonic", fake_monotonic)

    scope = CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=[
            "^/v1/items",
            "^/v2/items",
            "^/v3/items",
            "^/v4/items",
        ],
        allowed_methods=["GET"],
    )

    with pytest.raises(CredentialScopeViolation):
        StrictAllowlistScope().check(
            scope,
            request_url="https://api.example.com/no-match",
            method="GET",
        )

    # Each timeout must not exceed the per-match cap, AND must
    # decrease as the cumulative deadline approaches. Once the
    # remaining budget drops below the per-match cap, the
    # ``min(per_match, remaining)`` rule kicks in.
    assert all(t <= 0.05 + 1e-9 for t in timeouts_seen), timeouts_seen
    # First call sees full per-match budget (cumulative budget
    # 100 ms is well above per-match 50 ms).
    assert timeouts_seen[0] == pytest.approx(0.05, abs=1e-6)
    # Eventually a call sees a budget strictly less than the
    # per-match cap because the cumulative deadline kicked in.
    assert any(t < 0.05 - 1e-6 for t in timeouts_seen[1:]), (
        f"expected at least one shrunk timeout after the cumulative "
        f"deadline kicked in; got {timeouts_seen}"
    )


def test_timeout_on_first_pattern_refuses_via_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex iter-3 important: a timeout on one pattern must NOT
    fall through to a permissive secondary pattern. Patch
    ``regex.match`` to raise ``TimeoutError`` on the first call
    and assert refusal — never give the request a chance to ride
    a later pattern."""

    from veracrawl.adapters.session import strict_allowlist_scope as sas

    calls = [0]

    def fake_match(*args: object, **kwargs: object) -> object:
        del args, kwargs
        calls[0] += 1
        if calls[0] == 1:
            raise TimeoutError("simulated timeout on first pattern")
        # The next call would match — but the matcher must have
        # refused before reaching here.
        return object()  # truthy; would match if reached

    monkeypatch.setattr(sas, "regex", type("R", (), {"match": staticmethod(fake_match)}))

    scope = CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=["^/never-times-out", "/a"],
        allowed_methods=["GET"],
    )

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            scope,
            request_url="https://api.example.com/anything",
            method="GET",
        )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED
    assert calls[0] == 1, (
        f"matcher must refuse after first-pattern timeout; instead "
        f"made {calls[0]} regex.match calls"
    )


def test_contract_validated_patterns_compile_under_regex() -> None:
    """Codex iter-3 minor: the contract validator
    (``_validate_route_pattern``) uses stdlib ``re.compile`` /
    ``re._parser`` to check pattern syntax + structural shape; the
    runtime executes via the third-party ``regex`` package. Verify
    the boundary: every pattern shape the contract layer accepts
    must also compile under ``regex`` so no contract-valid scope
    fails at runtime with a compile error.

    ``regex`` is documented as a strict superset of stdlib ``re``
    syntax for the constructs the contract layer permits
    (``^``-anchored, alternation, character classes, basic
    quantifiers); the test locks that compatibility as a regression
    boundary."""

    contract_valid_patterns = [
        "^/v1/items",
        "/v1/items",
        "^/v1/items$",
        "/v1/(items|users)",
        "/v1/items/[a-z]+",
        "/v1/items/[0-9]{1,10}",
        "/api/v1/.+",
        "^/oauth/token$",
    ]
    for pattern in contract_valid_patterns:
        compiled = regex.compile(pattern)
        # Compilation succeeded; verify a basic match against a
        # representative input doesn't error either.
        compiled.match("/v1/items/123")
