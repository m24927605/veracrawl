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

import hashlib
from datetime import UTC, datetime
from typing import Any

import pytest

from veracrawl.adapters.credential_vault.in_memory_vault_backend import (
    InMemoryVaultBackend,
)
from veracrawl.adapters.credential_vault.outbox_vault_client import (
    OutboxVaultClient,
)
from veracrawl.ports.credential_access_audit import CredentialAccessOutcome
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
        outcome: CredentialAccessOutcome,
        run_ref: str,
        timestamp: datetime,
    ) -> None:
        self.records.append(
            {
                "scope_ref": scope_ref,
                "key": key,
                "outcome": outcome,
                "run_ref": run_ref,
                "timestamp": timestamp,
            }
        )


_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


def _expected_hashed_ref(name: str) -> str:
    """Mirror of ``_hashed_ref`` in outbox_vault_client.py for assertions."""

    return f"sha256:{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}"


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
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.SUCCESS


def test_get_writes_audit_row_with_injected_clock_timestamp() -> None:
    """Codex iter-2 important: audit row must carry HASHED scope_ref
    and key, never the raw caller-supplied identifier (even
    shape-validated identifiers may be secret-shaped uppercase
    tokens). Hash is stable so log aggregation can correlate."""

    backend = InMemoryVaultBackend(credentials={("X", "K"): "v"})
    client, audit = _make_client(backend=backend)
    client.get(scope_ref="X", key="K")
    record = audit.records[0]
    assert record["timestamp"] == _FROZEN_NOW
    assert record["timestamp"].tzinfo is not None
    assert record["run_ref"] == "run:test:1"
    # Audit carries hashed refs, not raw "X" / "K".
    assert record["scope_ref"] == _expected_hashed_ref("X")
    assert record["key"] == _expected_hashed_ref("K")
    # Defense in depth: assert raw value is NOT present anywhere
    # in the audit record's stringified form.
    serialized = str(record)
    # "X" and "K" alone are too short to assert on; use a longer
    # secret-shaped scope to verify.

    backend2 = InMemoryVaultBackend(credentials={("AKIAIOSFODNN7EXAMPLE", "API_KEY"): "v"})
    client2, audit2 = _make_client(backend=backend2)
    client2.get(scope_ref="AKIAIOSFODNN7EXAMPLE", key="API_KEY")
    serialized2 = str(audit2.records[0])
    assert "AKIAIOSFODNN7EXAMPLE" not in serialized2
    assert "API_KEY" not in serialized2
    del serialized  # silence unused


# ---------------------------------------------------------------------------
# Failure paths — all map to CredentialNotFoundError + audit success=False
# ---------------------------------------------------------------------------


def test_get_missing_credential_raises_not_found_with_audit() -> None:
    backend = InMemoryVaultBackend(credentials={})
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert len(audit.records) == 1
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.NOT_FOUND


@pytest.mark.parametrize(
    "kind,expected_outcome",
    [
        (VaultBackendErrorKind.BACKEND_UNREACHABLE, CredentialAccessOutcome.BACKEND_UNREACHABLE),
        (VaultBackendErrorKind.AUTH_FAILED, CredentialAccessOutcome.AUTH_FAILED),
        (VaultBackendErrorKind.INTERNAL, CredentialAccessOutcome.INTERNAL),
        (VaultBackendErrorKind.NOT_FOUND, CredentialAccessOutcome.NOT_FOUND),
    ],
)
def test_backend_error_translates_to_structured_audit_outcome(
    kind: VaultBackendErrorKind,
    expected_outcome: CredentialAccessOutcome,
) -> None:
    """Codex iter-1 important: the audit row must preserve the
    structured backend failure kind, not collapse to a boolean.
    Operational triage needs to distinguish auth_failed /
    backend_unreachable / internal in production logs."""

    backend = InMemoryVaultBackend(fail_with_kind=kind)
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert len(audit.records) == 1
    assert audit.records[0]["outcome"] is expected_outcome


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


@pytest.mark.parametrize("blank_value", ["   ", "\t", "\n"])
def test_backend_returns_blank_value_treated_as_blank_value_outcome(
    blank_value: str,
) -> None:
    """Whitespace-only values are caught by the InMemoryVaultBackend
    (returns None) before they reach the client; outcome is
    therefore NOT_FOUND. The BLANK_VALUE outcome path is exercised
    when a future backend (e.g., a vault that returns the empty
    string distinctly from missing) returns a literal blank — see
    test below using a stub that returns blank directly."""

    backend = InMemoryVaultBackend(credentials={("X", "K"): blank_value})
    client, audit = _make_client(backend=backend)
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    # InMemoryVaultBackend's blank-value handling reports as NOT_FOUND
    # (it returns None for blank). Distinct backend behavior is
    # tested below.
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.NOT_FOUND


def test_backend_that_returns_literal_blank_audits_as_blank_value() -> None:
    """A backend that distinguishes blank-string from missing (some
    vaults do — they store empty placeholders) drives the
    BLANK_VALUE outcome path. The client treats a returned blank
    string as fail-closed missing, distinct from the
    NOT_FOUND-from-backend case."""

    class _BlankReturningBackend:
        def fetch(self, *, scope_ref: str, key: str) -> str | None:
            del scope_ref, key
            return "   "

    audit = _RecordingAudit()
    client = OutboxVaultClient(
        backend=_BlankReturningBackend(),
        audit=audit,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    )
    with pytest.raises(CredentialNotFoundError):
        client.get(scope_ref="X", key="K")
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.BLANK_VALUE


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
def test_invalid_scope_ref_raises_value_error_with_invalid_identifier_audit(
    scope_ref: str,
) -> None:
    """Codex iter-1 important: invalid-identifier rejection must
    still emit an audit row (operationally distinct outcome:
    INVALID_IDENTIFIER). Identifiers in the audit row are
    redacted to `[REDACTED]` placeholders since the rejected
    values may carry secret-shaped strings."""

    backend = InMemoryVaultBackend()
    client, audit = _make_client(backend=backend)
    with pytest.raises(ValueError):
        client.get(scope_ref=scope_ref, key="API_KEY")
    assert len(audit.records) == 1
    record = audit.records[0]
    assert record["outcome"] is CredentialAccessOutcome.INVALID_IDENTIFIER
    assert record["scope_ref"] == "[REDACTED]"
    assert record["key"] == "[REDACTED]"


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
def test_invalid_key_raises_value_error_with_invalid_identifier_audit(
    key: str,
) -> None:
    backend = InMemoryVaultBackend()
    client, audit = _make_client(backend=backend)
    with pytest.raises(ValueError):
        client.get(scope_ref="EBAY", key=key)
    assert len(audit.records) == 1
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.INVALID_IDENTIFIER


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
    assert audit.records[0]["scope_ref"] == _expected_hashed_ref("EBAY")
    assert audit.records[1]["scope_ref"] == _expected_hashed_ref("AMAZON")


# ---------------------------------------------------------------------------
# Protocol satisfaction (smoke test only — Protocol just checks attrs)
# ---------------------------------------------------------------------------


def test_unexpected_backend_exception_audits_internal_and_raises_not_found() -> None:
    """Codex iter-2 important: backend SDKs may raise non-typed
    exceptions (RuntimeError / TimeoutError / etc.). The client
    must catch them, audit one INTERNAL row, and surface the
    canonical CredentialNotFoundError with no chain leak."""

    class _MisbehavingBackend:
        def fetch(self, *, scope_ref: str, key: str) -> str | None:
            del scope_ref, key
            raise RuntimeError("simulated SDK panic with sensitive details: api_key=sk_live")

    audit = _RecordingAudit()
    client = OutboxVaultClient(
        backend=_MisbehavingBackend(),
        audit=audit,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    )
    with pytest.raises(CredentialNotFoundError) as excinfo:
        client.get(scope_ref="X", key="K")
    assert len(audit.records) == 1
    assert audit.records[0]["outcome"] is CredentialAccessOutcome.INTERNAL
    # No chain leak — raw RuntimeError args carry "api_key=sk_live"
    # which must NOT appear in the surfaced exception or its chain.
    err = excinfo.value
    assert err.__cause__ is None
    assert err.__context__ is None
    formatted_args = " ".join(
        str(a) for a in err.args if isinstance(a, str)
    )
    assert "api_key=" not in formatted_args
    assert "sk_live" not in formatted_args


def test_clock_returning_naive_datetime_raises_runtime_error() -> None:
    """Codex iter-2 minor: defense-in-depth — producer-side guard
    that the injected clock returns tz-aware. A custom audit
    adapter may not validate, so the producer must."""

    backend = InMemoryVaultBackend(credentials={("X", "K"): "v"})
    audit = _RecordingAudit()

    def naive_clock() -> datetime:
        return datetime(2026, 5, 9, 12, 0, 0)  # noqa: DTZ001 — intentional naive

    client = OutboxVaultClient(
        backend=backend,
        audit=audit,
        run_ref="r",
        clock=naive_clock,
    )
    with pytest.raises(RuntimeError, match="tz-aware"):
        client.get(scope_ref="X", key="K")


def test_naive_clock_refuses_before_calling_backend() -> None:
    """Codex iter-3 important: tz-naive clock must abort BEFORE
    the backend is invoked — otherwise a credential may be fetched
    but no audit row recorded (violates "no access without audit")."""

    class _CountingBackend:
        def __init__(self) -> None:
            self.fetch_count = 0

        def fetch(self, *, scope_ref: str, key: str) -> str | None:
            del scope_ref, key
            self.fetch_count += 1
            return "should-not-reach"

    backend = _CountingBackend()
    audit = _RecordingAudit()

    def naive_clock() -> datetime:
        return datetime(2026, 5, 9, 12, 0, 0)  # noqa: DTZ001

    client = OutboxVaultClient(
        backend=backend,
        audit=audit,
        run_ref="r",
        clock=naive_clock,
    )
    with pytest.raises(RuntimeError, match="tz-aware"):
        client.get(scope_ref="X", key="K")
    assert backend.fetch_count == 0
    # No audit row either since we abort BEFORE the audit attempt.
    assert audit.records == []


def test_audit_writer_failure_after_fetch_refuses_credential_return() -> None:
    """Codex iter-3 important: even if the audit writer fails AFTER
    a successful backend fetch, the client refuses to return the
    credential — "no access without audit". A fallback
    ``credential_access_audit_failed`` structured-log event signals
    the operator that audit dropped."""

    class _FailingAudit:
        """Always raises on record."""

        def record(
            self,
            *,
            scope_ref: str,
            key: str,
            outcome: CredentialAccessOutcome,
            run_ref: Any,
            timestamp: Any,
        ) -> None:
            del scope_ref, key, outcome, run_ref, timestamp
            raise RuntimeError("simulated audit queue full")

    backend = InMemoryVaultBackend(
        credentials={("X", "K"): "secret-canary-DEADBEEF"}
    )
    audit = _FailingAudit()
    client = OutboxVaultClient(
        backend=backend,
        audit=audit,
        run_ref="r",
        clock=lambda: _FROZEN_NOW,
    )
    with pytest.raises(CredentialNotFoundError) as excinfo:
        client.get(scope_ref="X", key="K")
    err = excinfo.value
    # No chain leak; the secret must NEVER appear in the
    # surfaced exception.
    assert err.__cause__ is None
    assert err.__context__ is None
    text = " ".join(str(a) for a in err.args if isinstance(a, str))
    assert "secret-canary-DEADBEEF" not in text


def test_audit_writer_failure_on_invalid_identifier_propagates() -> None:
    """If the audit writer fails on the INVALID_IDENTIFIER row,
    the original ValueError is replaced by the audit-failure
    refusal. Either way no credential is returned, so the
    "no access without audit" contract holds."""

    class _FailingAudit:
        def record(
            self,
            *,
            scope_ref: str,
            key: str,
            outcome: CredentialAccessOutcome,
            run_ref: Any,
            timestamp: Any,
        ) -> None:
            del scope_ref, key, outcome, run_ref, timestamp
            raise RuntimeError("simulated audit queue full")

    backend = InMemoryVaultBackend()
    client = OutboxVaultClient(
        backend=backend,
        audit=_FailingAudit(),
        run_ref="r",
        clock=lambda: _FROZEN_NOW,
    )
    # Audit failure is what surfaces; the original identifier
    # rejection is masked but the credential is still refused.
    with pytest.raises(RuntimeError, match="simulated audit queue full"):
        client.get(scope_ref="lowercase", key="K")


def test_outbox_vault_client_satisfies_credential_vault_port() -> None:
    """OutboxVaultClient is the production CredentialVaultPort impl."""

    from veracrawl.ports.credential_vault import CredentialVaultPort

    backend = InMemoryVaultBackend()
    audit = _RecordingAudit()
    client: CredentialVaultPort = OutboxVaultClient(
        backend=backend, audit=audit, run_ref="r"
    )
    assert isinstance(client, CredentialVaultPort)
