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


def test_cumulative_budget_caps_total_matcher_work_per_request() -> None:
    """Codex iter-1 important: even with a 50 ms per-match timeout,
    a scope containing many patterns could spend
    ``N * 50 ms`` per credentialed request — a long-tail latency
    channel. The cumulative ``_TOTAL_BUDGET_SECONDS`` (100 ms)
    caps aggregate matcher work; a scope with multiple
    backtracking patterns must refuse under the whole-check
    budget, not the sum of per-match budgets."""

    backtracking_pattern = "^/(a|aa)+$"
    adversarial_path = "/" + ("a" * 60) + "!"

    # Five backtracking patterns + a final permissive matcher. With
    # only the per-match timeout, this would take ~5 × 50ms = 250 ms
    # before reaching the permissive pattern. The cumulative budget
    # forces a refusal under ~100 ms regardless of how many
    # patterns the scope carries.
    scope = CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=[
            backtracking_pattern,
            backtracking_pattern,
            backtracking_pattern,
            backtracking_pattern,
            backtracking_pattern,
            "/a",  # would otherwise match the adversarial path prefix
        ],
        allowed_methods=["GET"],
    )

    start = time.monotonic()
    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            scope,
            request_url=f"https://api.example.com{adversarial_path}",
            method="GET",
        )
    elapsed = time.monotonic() - start

    # Cumulative budget is 100 ms; the cap forces refusal under
    # 250 ms (5 * 50ms per-match would otherwise consume).
    assert elapsed < 0.25, (
        f"matcher took {elapsed:.3f}s — expected <0.25s under the "
        "cumulative whole-check budget"
    )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED


def test_timeout_path_does_not_break_other_patterns_in_same_scope() -> None:
    """If a scope has multiple ``allowed_route_patterns``, a timeout
    on one MUST refuse the whole request rather than fall through
    to the next pattern. Otherwise a hostile URL could ride a
    permissive secondary pattern and bypass the protection.

    Concretely: scope with ``[backtracking_pattern, "/v1/items"]``
    and an adversarial input that times out on the first pattern —
    the request must be refused, not allowed via the second."""

    backtracking_pattern = "^/(a|aa)+$"
    permissive_secondary = "/"  # would match anything, but contract
    # layer rejects bare "/" as catch-all. Use a near-permissive
    # pattern that the adversarial input also matches.
    adversarial_path = "/" + ("a" * 60) + "!"

    scope = CredentialScope(
        id="cred-scope-1",
        credential_handle_ref="vault:test#1",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=[backtracking_pattern, "/a"],
        allowed_methods=["GET"],
    )
    del permissive_secondary  # documented intent only

    with pytest.raises(CredentialScopeViolation) as excinfo:
        StrictAllowlistScope().check(
            scope,
            request_url=f"https://api.example.com{adversarial_path}",
            method="GET",
        )
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED
