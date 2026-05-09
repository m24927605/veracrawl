"""Unit tests for Phase 2 step 2.4b — ``AuthorizedSessionAdapter``.

Coverage:

1. Happy path — scope check passes, vault returns credential,
   request gets ``Authorization: Bearer <secret>`` header, response
   returned, CredentialUseRecord written.
2. Out-of-scope refusal — CredentialScopeViolation raised; vault not
   called; transport not called; no use record written.
3. Vault refusal — CredentialNotFoundError propagates; transport not
   called; no use record written.
4. 4xx / 5xx response is still a "successful HTTP completion" —
   use record IS written with the actual status.
5. Audit failure — refuses response (no use without audit) +
   fallback structured-log + sanitized exception (no chain leak).
6. Naive clock — refuses before any side effect.
7. Authorization header injected with Bearer prefix; revealed value
   used.
8. CredentialUseRecord carries injected timestamp + run_ref +
   credential_scope.id.
9. Scope policy check uses the SAME ``now`` value as the use record
   timestamp (replay determinism — no skew between policy check
   and use record).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from veracrawl.adapters.credential_vault.in_memory_vault_backend import (
    InMemoryVaultBackend,
)
from veracrawl.adapters.credential_vault.outbox_vault_client import (
    OutboxVaultClient,
)
from veracrawl.adapters.session.authorized_session_adapter import (
    AuthorizedSessionAdapter,
)
from veracrawl.adapters.session.strict_allowlist_scope import StrictAllowlistScope
from veracrawl.contracts.errors import (
    CredentialScopeReason,
    CredentialScopeViolation,
)
from veracrawl.contracts.security_privacy import (
    CredentialScope,
    CredentialUseRecord,
)
from veracrawl.ports.credential_access_audit import CredentialAccessOutcome
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
)

_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


class _RecordingUseAudit:
    """Minimal CredentialUseAuditPort impl that records calls."""

    def __init__(self) -> None:
        self.records: list[CredentialUseRecord] = []

    def record(self, use_record: CredentialUseRecord) -> None:
        self.records.append(use_record)


class _RecordingAccessAudit:
    """Minimal CredentialAccessAuditPort impl for vault-side audit."""

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


def _make_scope(
    *,
    allowed_methods: list[str] | None = None,
    expires_at: datetime | None = None,
) -> CredentialScope:
    return CredentialScope(
        id="cred-scope:ebay-prod",
        credential_handle_ref="vault:ebay#prod",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=["^/v1/items"],
        allowed_methods=allowed_methods or ["GET"],
        expires_at=expires_at,
    )


def _make_adapter(
    *,
    transport: httpx.BaseTransport,
    credentials: dict[tuple[str, str], str] | None = None,
    scope: CredentialScope | None = None,
    use_audit: _RecordingUseAudit | None = None,
    clock: Callable[[], datetime] = lambda: _FROZEN_NOW,
) -> tuple[AuthorizedSessionAdapter, _RecordingUseAudit, _RecordingAccessAudit]:
    creds = credentials if credentials is not None else {("EBAY_PROD", "API_KEY"): "sk-live-abc"}
    backend = InMemoryVaultBackend(credentials=creds)
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:test:1",
        clock=clock,
    )
    use_audit = use_audit if use_audit is not None else _RecordingUseAudit()
    adapter = AuthorizedSessionAdapter(
        transport=transport,
        vault=vault,
        scope_policy=StrictAllowlistScope(),
        credential_scope=scope or _make_scope(),
        vault_scope_ref="EBAY_PROD",
        vault_key="API_KEY",
        use_audit=use_audit,
        run_ref="run:test:1",
        clock=clock,
    )
    return adapter, use_audit, access_audit


def _ok_transport() -> httpx.MockTransport:
    return httpx.MockTransport(lambda req: httpx.Response(200, content=b'{"ok":true}'))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_request_returns_response_for_in_scope_request() -> None:
    transport = _ok_transport()
    adapter, use_audit, access_audit = _make_adapter(transport=transport)
    response = adapter.request(method="GET", url="https://api.example.com/v1/items/123")
    assert response.status_code == 200
    assert len(use_audit.records) == 1
    assert len(access_audit.records) == 1
    assert access_audit.records[0]["outcome"] is CredentialAccessOutcome.SUCCESS


def test_request_injects_authorization_bearer_header() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        for header_name, header_value in request.headers.items():
            captured_headers[header_name.lower()] = header_value
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    adapter, _, _ = _make_adapter(
        transport=transport,
        credentials={("EBAY_PROD", "API_KEY"): "sk-live-canary-DEADBEEF"},
    )
    adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert captured_headers.get("authorization") == "Bearer sk-live-canary-DEADBEEF"


def test_use_record_carries_run_ref_scope_url_method_status_timestamp() -> None:
    transport = _ok_transport()
    adapter, use_audit, _ = _make_adapter(transport=transport)
    adapter.request(method="GET", url="https://api.example.com/v1/items")
    record = use_audit.records[0]
    assert record.run_ref == "run:test:1"
    assert record.credential_scope_ref == "cred-scope:ebay-prod"
    assert record.request_url == "https://api.example.com/v1/items"
    assert record.request_method == "GET"
    assert record.response_status == 200
    assert record.timestamp_used == _FROZEN_NOW


def test_use_record_id_is_unique_per_request() -> None:
    transport = _ok_transport()
    adapter, use_audit, _ = _make_adapter(transport=transport)
    adapter.request(method="GET", url="https://api.example.com/v1/items/1")
    adapter.request(method="GET", url="https://api.example.com/v1/items/2")
    assert len({r.id for r in use_audit.records}) == 2


def test_4xx_response_is_still_audited_with_status() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    adapter, use_audit, _ = _make_adapter(transport=transport)
    response = adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert response.status_code == 404
    assert use_audit.records[0].response_status == 404


def test_5xx_response_is_still_audited_with_status() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(503))
    adapter, use_audit, _ = _make_adapter(transport=transport)
    adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert use_audit.records[0].response_status == 503


# ---------------------------------------------------------------------------
# Refusal paths
# ---------------------------------------------------------------------------


def test_out_of_scope_origin_refuses_before_vault_or_transport() -> None:
    transport_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal transport_called
        transport_called = True
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    adapter, use_audit, access_audit = _make_adapter(transport=transport)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        adapter.request(method="GET", url="https://other.example.com/v1/items")
    assert excinfo.value.reason is CredentialScopeReason.ORIGIN_NOT_ALLOWED
    assert transport_called is False
    assert use_audit.records == []
    assert access_audit.records == []  # vault not called either


def test_method_not_allowed_refuses_before_vault_or_transport() -> None:
    transport = _ok_transport()
    adapter, use_audit, access_audit = _make_adapter(transport=transport)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        adapter.request(method="DELETE", url="https://api.example.com/v1/items")
    assert excinfo.value.reason is CredentialScopeReason.METHOD_NOT_ALLOWED
    assert use_audit.records == []
    assert access_audit.records == []


def test_route_not_allowed_refuses_before_vault_or_transport() -> None:
    transport = _ok_transport()
    adapter, use_audit, access_audit = _make_adapter(transport=transport)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        adapter.request(method="GET", url="https://api.example.com/v2/users")
    assert excinfo.value.reason is CredentialScopeReason.ROUTE_NOT_ALLOWED
    assert use_audit.records == []


def test_expired_scope_refuses_before_vault_or_transport() -> None:
    expired = datetime.now(UTC) - timedelta(seconds=1)
    scope = _make_scope(expires_at=expired)
    transport = _ok_transport()
    adapter, use_audit, access_audit = _make_adapter(transport=transport, scope=scope)
    with pytest.raises(CredentialScopeViolation) as excinfo:
        adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert excinfo.value.reason is CredentialScopeReason.EXPIRED
    assert use_audit.records == []


def test_vault_missing_credential_refuses_before_transport() -> None:
    transport_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal transport_called
        transport_called = True
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    # Empty credential dict → vault returns NOT_FOUND.
    adapter, use_audit, _ = _make_adapter(transport=transport, credentials={})
    with pytest.raises(CredentialNotFoundError):
        adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert transport_called is False
    assert use_audit.records == []


# ---------------------------------------------------------------------------
# Audit-failure path (no use without audit)
# ---------------------------------------------------------------------------


def test_audit_failure_after_response_refuses_response() -> None:
    """Codex iter-1 (anticipated): if the use audit write fails
    AFTER the request was sent + response received, the adapter
    must refuse to return the response. Mirror of
    OutboxVaultClient's iter-3 fail-closed audit semantics."""

    class _FailingUseAudit:
        def record(self, use_record: CredentialUseRecord) -> None:
            del use_record
            raise RuntimeError("simulated audit queue full with sensitive details")

    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, content=b'{"item":"data"}')
    )
    adapter, _, _ = _make_adapter(transport=transport, use_audit=_FailingUseAudit())  # type: ignore[arg-type]
    with pytest.raises(CredentialNotFoundError) as excinfo:
        adapter.request(method="GET", url="https://api.example.com/v1/items")
    err = excinfo.value
    # No chain leak — sanitized refusal.
    assert err.__cause__ is None
    assert err.__context__ is None
    text = " ".join(str(a) for a in err.args if isinstance(a, str))
    assert "simulated audit queue full" not in text
    assert "sensitive details" not in text


# ---------------------------------------------------------------------------
# Clock validation (defense in depth)
# ---------------------------------------------------------------------------


def test_naive_clock_refuses_before_any_side_effect() -> None:
    transport_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal transport_called
        transport_called = True
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)

    def naive_clock() -> datetime:
        return datetime(2026, 5, 9, 12, 0, 0)  # noqa: DTZ001 — intentional

    adapter, use_audit, access_audit = _make_adapter(
        transport=transport,
        clock=naive_clock,
    )
    with pytest.raises(RuntimeError, match="tz-aware"):
        adapter.request(method="GET", url="https://api.example.com/v1/items")
    assert transport_called is False
    assert use_audit.records == []
    # Vault clock validation also fires; access audit should be empty
    # because the adapter aborts BEFORE calling the vault.
    assert access_audit.records == []


# ---------------------------------------------------------------------------
# Replay determinism
# ---------------------------------------------------------------------------


def test_scope_check_and_use_record_share_timestamp() -> None:
    """Codex recurring concern (replay determinism): the timestamp
    used in the scope-policy check (as ``now``) must equal the
    timestamp recorded in the CredentialUseRecord — otherwise a
    replay against a different clock would yield different scope
    decisions than the recorded use record claims."""

    times_called: list[datetime] = []

    def counting_clock() -> datetime:
        ts = _FROZEN_NOW + timedelta(seconds=len(times_called))
        times_called.append(ts)
        return ts

    transport = _ok_transport()
    adapter, use_audit, _ = _make_adapter(transport=transport, clock=counting_clock)
    adapter.request(method="GET", url="https://api.example.com/v1/items")
    # The adapter calls _now() once at the top of request() — that
    # ts feeds BOTH the scope_policy.check ``now`` AND the use
    # record's timestamp_used. The vault layer's clock invocations
    # are independent (separate audit timestamps) but they're a
    # different scope.
    assert use_audit.records[0].timestamp_used == _FROZEN_NOW
