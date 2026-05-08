"""Contract tests for Phase 2 step 2.4a — ``VaultBackendPort``,
``VaultBackendError``, ``VaultBackendErrorKind``.

The Protocol must be satisfied by both the
:class:`InMemoryVaultBackend` fixture and an arbitrary in-memory
test double — proves the port surface is small enough for
production adapters (HashiCorp Vault / AWS Secrets Manager) to
plug in without inheriting from any concrete class.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.credential_vault.in_memory_vault_backend import (
    InMemoryVaultBackend,
)
from veracrawl.contracts.errors import VeraCrawlError
from veracrawl.ports.vault_backend import (
    VaultBackendError,
    VaultBackendErrorKind,
    VaultBackendPort,
)


def test_in_memory_backend_satisfies_port() -> None:
    backend: VaultBackendPort = InMemoryVaultBackend()
    assert isinstance(backend, VaultBackendPort)
    assert callable(backend.fetch)


def test_minimal_test_double_satisfies_port() -> None:
    class _AlwaysReturnsValue:
        def fetch(self, *, scope_ref: str, key: str) -> str | None:
            del scope_ref, key
            return "value"

    backend: VaultBackendPort = _AlwaysReturnsValue()
    assert isinstance(backend, VaultBackendPort)


# ---------------------------------------------------------------------------
# VaultBackendError contract
# ---------------------------------------------------------------------------


def test_error_is_veracrawl_error() -> None:
    err = VaultBackendError(kind=VaultBackendErrorKind.AUTH_FAILED)
    assert isinstance(err, VeraCrawlError)


def test_error_carries_structured_kind_attribute() -> None:
    err = VaultBackendError(kind=VaultBackendErrorKind.BACKEND_UNREACHABLE)
    assert err.kind is VaultBackendErrorKind.BACKEND_UNREACHABLE


def test_error_accepts_string_form_of_kind() -> None:
    err = VaultBackendError(kind="auth_failed")
    assert err.kind is VaultBackendErrorKind.AUTH_FAILED


@pytest.mark.parametrize(
    "bad_kind",
    [
        "AUTH_FAILED",  # uppercase form — not enum value
        "unknown_reason",
        "",
        "free-form text reason",
    ],
)
def test_error_rejects_unknown_kind_string(bad_kind: str) -> None:
    with pytest.raises(ValueError, match="VaultBackendErrorKind"):
        VaultBackendError(kind=bad_kind)


def test_error_rejection_does_not_chain_raw_kind_through_cause() -> None:
    """Codex recurring concern (e): sanitized rejection must not
    leave the rejected kind reachable via ``__cause__`` /
    ``__context__``."""

    secret_shaped = "Bearer eyJhbGciOiJIUzI1NiJ9.SECRET.SIG"
    with pytest.raises(ValueError) as excinfo:
        VaultBackendError(kind=secret_shaped)
    err = excinfo.value
    assert err.__cause__ is None
    assert err.__context__ is None
    assert secret_shaped not in str(err)
    assert "SECRET" not in str(err)


def test_error_message_does_not_carry_scope_ref_or_key() -> None:
    """``VaultBackendError`` does not accept scope_ref / key
    parameters — those would land on ``__dict__`` and be a
    leakage path. The orchestrator already has the keys in scope
    for triage."""

    err = VaultBackendError(kind=VaultBackendErrorKind.NOT_FOUND)
    # Public attrs should be limited to the structured kind.
    assert "kind" in err.__dict__
    # No scope_ref / key fields.
    assert "scope_ref" not in err.__dict__
    assert "key" not in err.__dict__


def test_error_kind_enum_values_are_lower_snake_case() -> None:
    expected_values = {"not_found", "backend_unreachable", "auth_failed", "internal"}
    actual = {member.value for member in VaultBackendErrorKind}
    assert expected_values.issubset(actual)
