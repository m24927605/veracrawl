"""Contract tests for Phase 2 step 2.2b — ``CredentialScopeReason``.

Phase 0 step 0.4 reservation pull-forward: replace the free-form
``reason: str`` field on :class:`CredentialScopeViolation` with a
structured :class:`CredentialScopeReason` enum so a producer cannot
leak arbitrary content (PII / OAuth tokens / session ids /
JWT-shaped strings) through the exception path even if a future
caller pipes raw user input into the field.

Acceptance criteria:

1. ``CredentialScopeReason`` enumerates the four refusal classes
   ``StrictAllowlistScope`` emits at runtime
   (``ORIGIN_NOT_ALLOWED`` / ``ROUTE_NOT_ALLOWED`` /
   ``METHOD_NOT_ALLOWED`` / ``EXPIRED``).
2. ``CredentialScopeReason`` is a :class:`StrEnum` so existing
   call sites that compare ``err.reason == "expired"`` keep
   working without an explicit ``.value`` access.
3. ``CredentialScopeViolation(reason=...)`` accepts an enum value,
   coerces a matching string, and raises :class:`ValueError` for
   anything else — closing the free-form leak path structurally.
4. The formatted exception message uses the enum's stable string
   value (e.g., ``"expired"``), not a free-form prose explanation.
"""

from __future__ import annotations

from enum import StrEnum

import pytest

from veracrawl.contracts.errors import (
    CredentialScopeReason,
    CredentialScopeViolation,
)


def test_credential_scope_reason_is_a_str_enum() -> None:
    """``StrEnum`` is what makes ``err.reason == 'expired'`` work
    without an explicit ``.value`` access — keeps existing call
    sites unchanged."""

    assert issubclass(CredentialScopeReason, StrEnum)


def test_credential_scope_reason_covers_all_four_refusal_classes() -> None:
    """The four classes ``StrictAllowlistScope`` (Phase 2 step 2.2a)
    emits at runtime. New refusal modes added later must extend
    the enum so the leak surface stays closed."""

    expected = {
        "ORIGIN_NOT_ALLOWED",
        "ROUTE_NOT_ALLOWED",
        "METHOD_NOT_ALLOWED",
        "EXPIRED",
    }
    actual = {member.name for member in CredentialScopeReason}
    assert expected.issubset(actual)


def test_credential_scope_reason_values_are_lower_snake_case() -> None:
    """Stable wire / log-line shape: lowercase snake_case."""

    expected_values = {
        "origin_not_allowed",
        "route_not_allowed",
        "method_not_allowed",
        "expired",
    }
    assert expected_values.issubset({member.value for member in CredentialScopeReason})


# ---------------------------------------------------------------------------
# Construction acceptance
# ---------------------------------------------------------------------------


def test_violation_accepts_enum_value() -> None:
    err = CredentialScopeViolation(
        scope_ref="cred-scope-1",
        requested_origin="https://api.example.com",
        requested_route="/v1/items",
        requested_method="GET",
        reason=CredentialScopeReason.EXPIRED,
    )
    assert err.reason is CredentialScopeReason.EXPIRED
    assert err.reason == "expired"
    assert "expired" in str(err)


def test_violation_accepts_matching_string_form() -> None:
    """A raw string matching one of the enum values still works —
    convenient for serialized / replay-loaded refusal events."""

    err = CredentialScopeViolation(
        scope_ref="cred-scope-1",
        requested_origin="https://api.example.com",
        requested_route="/v1/items",
        requested_method="GET",
        reason="route_not_allowed",
    )
    assert err.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED


@pytest.mark.parametrize(
    "bad_reason",
    [
        "ORIGIN_NOT_ALLOWED",  # uppercase form — not the enum value
        "expired ",  # trailing whitespace — strict equality
        "expired-route",  # combined unknown
        "",  # empty
        "this is a free-form prose reason",
        "header Authorization: Bearer eyJhbGc",  # leak vector
        "received password=hunter2",  # PII leak vector
        "code=oauth-grant-12345",  # OAuth leak vector
    ],
)
def test_violation_rejects_unknown_string_reason(bad_reason: str) -> None:
    """Anything outside the enum's value set raises before the
    exception even constructs — there is no free-form path to
    leak through."""

    with pytest.raises(ValueError, match="CredentialScopeReason"):
        CredentialScopeViolation(
            scope_ref="cred-scope-1",
            requested_origin="https://api.example.com",
            requested_route="/v1/items",
            requested_method="GET",
            reason=bad_reason,
        )


def test_violation_rejection_does_not_echo_bad_reason() -> None:
    """The ``ValueError`` raised on a bad reason must NOT echo the
    rejected text — the caller may have piped a credential-shaped
    value, and the exception text would otherwise carry it into
    logs / pytest output / telemetry."""

    secret_shaped = "Bearer eyJhbGciOiJIUzI1NiJ9.SECRET_PAYLOAD.SIG"
    with pytest.raises(ValueError) as excinfo:
        CredentialScopeViolation(
            scope_ref="cred-scope-1",
            requested_origin="https://api.example.com",
            requested_route="/v1/items",
            requested_method="GET",
            reason=secret_shaped,
        )
    assert secret_shaped not in str(excinfo.value)
    assert "SECRET_PAYLOAD" not in str(excinfo.value)
    assert "eyJhbGc" not in str(excinfo.value)


def test_violation_rejection_does_not_chain_raw_reason_through_cause() -> None:
    """Codex iter-1 important: ``raise ... from exc`` chained the
    ``CredentialScopeReason(reason)`` lookup exception, whose
    ``args`` carry the raw rejected value. A traceback log
    (``logging.exception``, ``traceback.format_exc()``) would have
    leaked the credential-shaped string even though
    ``str(excinfo.value)`` is sanitized. Verify the outer
    ``ValueError`` has no ``__cause__`` and no ``__context__`` that
    would surface the raw reason in a formatted traceback."""

    import traceback

    secret_shaped = "Bearer eyJhbGciOiJIUzI1NiJ9.SECRET_PAYLOAD.SIG"
    with pytest.raises(ValueError) as excinfo:
        CredentialScopeViolation(
            scope_ref="cred-scope-1",
            requested_origin="https://api.example.com",
            requested_route="/v1/items",
            requested_method="GET",
            reason=secret_shaped,
        )
    err = excinfo.value
    assert err.__cause__ is None
    formatted = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    assert secret_shaped not in formatted
    assert "SECRET_PAYLOAD" not in formatted


def test_violation_rejection_handles_non_string_reason() -> None:
    """A caller passing a non-string non-enum (e.g., an int from a
    deserialization bug) must also be rejected with the same typed
    error — never reach a ``TypeError`` on string operations
    inside the constructor."""

    with pytest.raises(ValueError, match="CredentialScopeReason"):
        CredentialScopeViolation(  # type: ignore[arg-type]
            scope_ref="cred-scope-1",
            requested_origin="https://api.example.com",
            requested_route="/v1/items",
            requested_method="GET",
            reason=42,
        )


# ---------------------------------------------------------------------------
# Formatted-message stability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reason", list(CredentialScopeReason))
def test_violation_message_emits_enum_value_for_every_refusal_class(
    reason: CredentialScopeReason,
) -> None:
    """``str(err)`` must contain the stable enum value, not some
    prose form. Operators / log-aggregation rely on the value being
    grepable across releases."""

    err = CredentialScopeViolation(
        scope_ref="cred-scope-1",
        requested_origin="https://api.example.com",
        requested_route="/v1/items",
        requested_method="GET",
        reason=reason,
    )
    assert reason.value in str(err)
