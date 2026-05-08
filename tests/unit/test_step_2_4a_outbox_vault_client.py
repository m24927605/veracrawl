"""Unit tests for Phase 2 step 2.4a — ``OutboxVaultClient``.

Coverage:

1. Happy path — backend returns a value, get returns CredentialValue, audit row written.
2. Backend NOT_FOUND → None → CredentialNotFoundError + audit success=False.
3. Backend raises VaultBackendError → CredentialNotFoundError + audit
   success=False (no exception chain leak).
4. Empty / whitespace-only backend value → CredentialNotFoundError + audit success=False.
5. Invalid scope_ref / key shape → ValueError raised before backend call.
6. Audit row carries run_ref + tz-aware timestamp from injected clock.
7. CredentialValue redaction contract holds end-to-end.
8. Production gate: client itself has none (production-safe); InMemoryVaultBackend has the gate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from veracrawl.adapters.credential_vault.in_memory_vault_backend import (
    InMemoryVaultBackend,
)
from veracrawl.adapters.credential_vault.outbox_vault_client import (
    OutboxVaultClient,
)
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
)
from veracrawl.ports.vault_backend import (
    VaultBackendErrorKind,
)


class _RecordingAudit:
    """Minimal CredentialAccessAuditPort impl that records calls."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        scope_ref: str,
        key: str,
        success: bool,
        run_ref: str,
        timestamp: datetime,
    ) -> None:
        self.records.append(
            {
                "scope_ref": scope_ref,
                "key": key,
                "success": success,
                "run_ref": run_ref,
                "timestamp": timestamp,
            }
        )


_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


def _make_client(
    *,
    backend: InMemoryVaultBackend | None = None,
    audit: _RecordingAudit | None = None,
    run_ref: str = "run:test:1",
) -> tuple[OutboxVaultClient, _RecordingAudit]:
    audit = audit if audit is not None else _RecordingAudit()
    backend_arg = backend if backend is not None else InMemoryVaultBackend()
    client = OutboxVaultClient(
        backend=backend_arg,
        audit=audit,
        run_ref=run_ref,
        clock=lambda: _FROZEN_NOW,
    )
    return client, audit


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_get_returns_credential_value_for_present_credential() -> None:
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): "sk_live_abc123"}
    )
    client, audit = _make_client(backend=backend)
    result = client.get(scope_ref="EBAY_PROD", key="API_KEY")
    assert isinstance(result, CredentialValue)
    assert result.reveal() == "sk_live_abc123"
    assert result.scope_ref == "EBAY_PROD"
    assert len(audit.records) == 1
    assert audit.records[0]["success"] is True


def test_get_writes_audit_row_with_injected_clock_timestamp() -> None:
    backend = InMemoryVaultBackend(credentials={("X", "K"): "v"})
    client, audit = _make_client(backend=backend)
    client.get(scope_ref="X", key="K")
    record = audit.records[0]
    assert record["timestamp"] == _FROZEN_NOW
    assert record["timestamp"].tzinfo is not None
    assert record["run_ref"] == "run:test:1"
    assert record["scope_ref"] == "X"
    assert record["key"] == "K"


# ---------------------------------------------------------------------------
# Failure paths — all map to CredentialNotFoundError + audit success=False
# ---------------------------------------------------------------------------


def test_get_missing_credential_raises_not_found_with_audit() -> None:
    backend = InMemoryVaultBackend(credentials={})
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert len(audit.records) == 1
    assert audit.records[0]["success"] is False


@pytest.mark.parametrize(
    "kind",
    [
        VaultBackendErrorKind.BACKEND_UNREACHABLE,
        VaultBackendErrorKind.AUTH_FAILED,
        VaultBackendErrorKind.INTERNAL,
    ],
)
def test_backend_error_translates_to_not_found_and_audits_failure(
    kind: VaultBackendErrorKind,
) -> None:
    backend = InMemoryVaultBackend(fail_with_kind=kind)
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert len(audit.records) == 1
    assert audit.records[0]["success"] is False


def test_backend_error_does_not_leak_via_exception_chain() -> None:
    """Codex recurring concern (e): re-raise must not chain the
    underlying VaultBackendError because its public attributes
    could carry backend-specific identifiers a logging.exception
    pipeline would surface via __cause__/__context__ traversal.

    Walk the exception chain via __cause__/__context__ recursively
    and assert no reachable exception's args/dict carries the
    backend kind. Cannot rely on traceback string scanning alone
    because it would include source-code lines like
    ``except VaultBackendError:`` that legitimately contain the
    class name.
    """

    backend = InMemoryVaultBackend(fail_with_kind=VaultBackendErrorKind.AUTH_FAILED)
    client, _ = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError) as excinfo:
        client.get(scope_ref="X", key="K")
    err = excinfo.value
    assert err.__cause__ is None
    assert err.__context__ is None
    # Walk reachable exceptions; none should carry the backend kind.
    seen: set[int] = set()
    chain: list[BaseException] = [err]
    while chain:
        node = chain.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        for arg in node.args:
            if isinstance(arg, str):
                assert "AUTH_FAILED" not in arg
                assert "auth_failed" not in arg
        if node.__cause__ is not None:
            chain.append(node.__cause__)
        if node.__context__ is not None:
            chain.append(node.__context__)


@pytest.mark.parametrize("blank_value", ["", "   ", "\t", "\n"])
def test_backend_returns_blank_value_treated_as_not_found(blank_value: str) -> None:
    backend = InMemoryVaultBackend(credentials={("X", "K"): blank_value})
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert audit.records[0]["success"] is False


# ---------------------------------------------------------------------------
# Identifier shape validation (defense in depth)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scope_ref",
    [
        "",  # empty
        "ebay",  # lowercase
        "EBAY-PROD",  # dash
        "EBAY.PROD",  # dot
        "EBAY/PROD",  # slash
        "EBAY PROD",  # space
        "EBAY\nPROD",  # control char
    ],
)
def test_invalid_scope_ref_raises_value_error_before_backend_call(
    scope_ref: str,
) -> None:
    backend = InMemoryVaultBackend()
    client, audit = _make_client(backend=backend)
    with pytest.raises(ValueError, match=r"^[A-Z0-9_]+|redacted"):
        client.get(scope_ref=scope_ref, key="API_KEY")
    # No audit row written — validation rejected before backend call.
    assert audit.records == []


@pytest.mark.parametrize(
    "key",
    [
        "",
        "api_key",
        "API-KEY",
        "API.KEY",
        "API/KEY",
    ],
)
def test_invalid_key_raises_value_error_before_backend_call(key: str) -> None:
    backend = InMemoryVaultBackend()
    client, audit = _make_client(backend=backend)
    with pytest.raises(ValueError):
        client.get(scope_ref="EBAY", key=key)
    assert audit.records == []


def test_invalid_identifier_error_does_not_echo_raw_value() -> None:
    """Codex recurring concern (f): caller-supplied identifier
    that fails shape validation must NOT echo the rejected value
    in the error text — it could carry a secret-shaped string."""

    backend = InMemoryVaultBackend()
    client, _ = _make_client(backend=backend)
    secret_shaped = "sk_live_canary"
    with pytest.raises(ValueError) as excinfo:
        client.get(scope_ref=secret_shaped, key="K")
    assert secret_shaped not in str(excinfo.value)
    assert "canary" not in str(excinfo.value)
    assert "redacted" in str(excinfo.value)


# ---------------------------------------------------------------------------
# CredentialValue redaction contract holds end-to-end
# ---------------------------------------------------------------------------


def test_returned_credential_value_redacts_in_repr_and_str() -> None:
    backend = InMemoryVaultBackend(
        credentials={("X", "K"): "secret-vault-token-DEADBEEF"}
    )
    client, _ = _make_client(backend=backend)
    cred = client.get(scope_ref="X", key="K")
    assert "secret-vault-token-DEADBEEF" not in repr(cred)
    assert "secret-vault-token-DEADBEEF" not in str(cred)
    assert "secret-vault-token-DEADBEEF" not in f"{cred}"


# ---------------------------------------------------------------------------
# Multiple gets — independent audit rows
# ---------------------------------------------------------------------------


def test_multiple_gets_emit_independent_audit_rows() -> None:
    backend = InMemoryVaultBackend(
        credentials={
            ("EBAY", "API_KEY"): "v1",
            ("AMAZON", "TOKEN"): "v2",
        }
    )
    client, audit = _make_client(backend=backend)
    client.get(scope_ref="EBAY", key="API_KEY")
    client.get(scope_ref="AMAZON", key="TOKEN")
    assert len(audit.records) == 2
    assert audit.records[0]["scope_ref"] == "EBAY"
    assert audit.records[1]["scope_ref"] == "AMAZON"


# ---------------------------------------------------------------------------
# Protocol satisfaction (smoke test only — Protocol just checks attrs)
# ---------------------------------------------------------------------------


def test_outbox_vault_client_satisfies_credential_vault_port() -> None:
    """OutboxVaultClient is the production CredentialVaultPort impl."""

    from veracrawl.ports.credential_vault import CredentialVaultPort

    backend = InMemoryVaultBackend()
    audit = _RecordingAudit()
    client: CredentialVaultPort = OutboxVaultClient(
        backend=backend, audit=audit, run_ref="r"
    )
    assert isinstance(client, CredentialVaultPort)
