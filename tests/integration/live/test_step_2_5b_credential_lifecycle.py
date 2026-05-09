"""Live integration test #4 — Phase 2 credential lifecycle end-to-end.

design.md §4 Phase 2 acceptance: "an authorized session against a
test API (controlled by us, not third-party) succeeds with vault
audit, credential redaction, and replay event present."

We do not yet have a controlled test API (Phase 6 step 6.4 ships
that infrastructure). Following Phase 1 step 1.6 / Phase 3 step
3.6 precedent, this test runs under fixture mode against an
``httpx.MockTransport`` that echoes the Authorization header
back. The "liveness" is the end-to-end integration of every
Phase 2 component:

* :class:`InMemoryVaultBackend` (test vault)
* :class:`OutboxVaultClient` (production vault client + access audit)
* :class:`StrictAllowlistScope` (production scope policy)
* :class:`AuthorizedSessionAdapter` (production credential injection)
* :class:`AgentCredentialLifecycle` (production lifecycle wrapper)
* Logging audit writers for both access + use audit ports

Phase 6 step 6.4 will replace the MockTransport with a controlled
test API + real network round trip; the assertions stay identical
because the contract surface is the same.

Marker ``@pytest.mark.live`` for runtime separation from unit
tests; this test runs in fixture mode but exercises the
production code paths end-to-end.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
import structlog

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
from veracrawl.agents.credential_lifecycle import AgentCredentialLifecycle
from veracrawl.contracts.agent import AgentRole, AgentRunRequest
from veracrawl.contracts.common import Ref
from veracrawl.contracts.security_privacy import (
    CredentialScope,
    CredentialUseRecord,
)
from veracrawl.ports.credential_access_audit import CredentialAccessOutcome

pytestmark = pytest.mark.live

_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
_CANARY_SECRET = "sk-live-canary-DEADBEEF-must-not-leak"


class _RecordingAccessAudit:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        scope_ref: str,
        key: str,
        outcome: CredentialAccessOutcome,
        run_ref: Ref,
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


class _RecordingUseAudit:
    def __init__(self) -> None:
        self.records: list[CredentialUseRecord] = []

    def record(self, use_record: CredentialUseRecord) -> None:
        self.records.append(use_record)


class _StubScopeRegistry:
    def __init__(self, scopes: dict[Ref, CredentialScope]) -> None:
        self._scopes = scopes

    def resolve(self, scope_ref: Ref) -> CredentialScope:
        return self._scopes[scope_ref]


def _make_credential_scope() -> CredentialScope:
    return CredentialScope(
        id="cred-scope:ebay-prod",
        credential_handle_ref="vault:ebay#prod",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=["^/v1/items"],
        allowed_methods=["GET"],
    )


def _make_run_request(scope_ref: Ref) -> AgentRunRequest:
    return AgentRunRequest(
        id="agent-run-request:live-2-5b",
        run_id="run:live-2-5b:1",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="runtime-spec:live-2-5b",
        objective_ref="objective:live-2-5b",
        context_bundle_id="context-bundle:live-2-5b",
        required_output_schema_ref="output-schema:live-2-5b",
        loop_budget_ref="loop-budget:live-2-5b",
        policy_decision_refs=["policy-decision:live-2-5b"],
        credential_scope_refs=[scope_ref],
    )


def _echo_authorization_transport() -> tuple[httpx.MockTransport, list[str]]:
    """MockTransport that records every Authorization header it
    sees. Returns (transport, captured_authorization_values)."""

    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("authorization")
        if auth is not None:
            captured.append(auth)
        return httpx.Response(200, content=b'{"echoed":"ok"}')

    return httpx.MockTransport(handler), captured


def test_phase2_credential_lifecycle_end_to_end_three_requests() -> None:
    """Construct the full Phase 2 production stack and drive 3
    credential-bearing requests through it. Assert vault audit
    records 3 access events, use audit records 3 use events,
    lifecycle counts 3 uses, no credential value leaks anywhere
    in the audit trail."""

    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:live-2-5b:1",
        clock=lambda: _FROZEN_NOW,
    )
    transport, captured_auth = _echo_authorization_transport()
    use_audit = _RecordingUseAudit()
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")

    with structlog.testing.capture_logs() as captured_logs:
        with AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:live-2-5b:1",
            clock=lambda: _FROZEN_NOW,
        ) as session:
            adapter = AuthorizedSessionAdapter(
                transport=transport,
                vault=vault,
                scope_policy=StrictAllowlistScope(),
                credential_scope=session.scope_for("cred-scope:ebay-prod"),
                vault_scope_ref="EBAY_PROD",
                vault_key="API_KEY",
                use_audit=use_audit,
                run_ref="run:live-2-5b:1",
                clock=lambda: _FROZEN_NOW,
            )
            for path in ("/v1/items/1", "/v1/items/2", "/v1/items/3"):
                response = adapter.request(
                    method="GET",
                    url=f"https://api.example.com{path}",
                )
                assert response.status_code == 200
                session.record_use()

    # 3 access audit records (vault-side).
    assert len(access_audit.records) == 3
    assert all(
        rec["outcome"] is CredentialAccessOutcome.SUCCESS for rec in access_audit.records
    )

    # 3 use audit records (adapter-side).
    assert len(use_audit.records) == 3
    assert all(rec.response_status == 200 for rec in use_audit.records)

    # 3 Authorization headers landed on the wire.
    assert len(captured_auth) == 3
    for auth_value in captured_auth:
        assert auth_value == f"Bearer {_CANARY_SECRET}"

    # End event reports credential_use_count == 3, cleanup succeeded.
    end_events = [
        e for e in captured_logs if e.get("event") == "agent_credential_session_ended"
    ]
    assert len(end_events) == 1
    assert end_events[0]["credential_use_count"] == 3
    assert end_events[0]["cleanup_succeeded"] is True
    assert end_events[0]["ended_with_exception"] is False


def test_phase2_credential_redaction_holds_through_audit_chain() -> None:
    """The canary secret must NOT appear anywhere in the audit
    chain: vault access records, use records, structured-log
    events. Defense in depth — every layer redacts."""

    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:live-2-5b:redact",
        clock=lambda: _FROZEN_NOW,
    )
    transport, _captured_auth = _echo_authorization_transport()
    use_audit = _RecordingUseAudit()
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")

    with structlog.testing.capture_logs() as captured_logs:
        with AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:live-2-5b:redact",
            clock=lambda: _FROZEN_NOW,
        ) as session:
            adapter = AuthorizedSessionAdapter(
                transport=transport,
                vault=vault,
                scope_policy=StrictAllowlistScope(),
                credential_scope=session.scope_for("cred-scope:ebay-prod"),
                vault_scope_ref="EBAY_PROD",
                vault_key="API_KEY",
                use_audit=use_audit,
                run_ref="run:live-2-5b:redact",
                clock=lambda: _FROZEN_NOW,
            )
            adapter.request(method="GET", url="https://api.example.com/v1/items")
            session.record_use()

    # Canary not in vault access audit row stringification.
    for record in access_audit.records:
        assert _CANARY_SECRET not in str(record)

    # Canary not on use record.
    for record in use_audit.records:
        assert _CANARY_SECRET not in str(record.__dict__)

    # Canary not in any structured-log event.
    for event in captured_logs:
        assert _CANARY_SECRET not in str(event)


def test_phase2_replay_event_present_in_audit_chain() -> None:
    """design.md acceptance: "replay event present". The Phase 2
    audit chain produces an ``agent_credential_session_ended``
    event with all the fields needed for replay (run_ref,
    scope_id_hashes, credential_use_count, cleanup_succeeded,
    timestamp_iso). This test asserts the replay-readiness
    contract — Phase 6 step 6.4 wires real replay tooling."""

    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:live-2-5b:replay",
        clock=lambda: _FROZEN_NOW,
    )
    transport, _ = _echo_authorization_transport()
    use_audit = _RecordingUseAudit()
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")

    with structlog.testing.capture_logs() as captured_logs:
        with AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:live-2-5b:replay",
            clock=lambda: _FROZEN_NOW,
        ) as session:
            adapter = AuthorizedSessionAdapter(
                transport=transport,
                vault=vault,
                scope_policy=StrictAllowlistScope(),
                credential_scope=session.scope_for("cred-scope:ebay-prod"),
                vault_scope_ref="EBAY_PROD",
                vault_key="API_KEY",
                use_audit=use_audit,
                run_ref="run:live-2-5b:replay",
                clock=lambda: _FROZEN_NOW,
            )
            adapter.request(method="GET", url="https://api.example.com/v1/items")
            session.record_use()

    end = next(
        e for e in captured_logs if e.get("event") == "agent_credential_session_ended"
    )
    assert end["run_ref"] == "run:live-2-5b:replay"
    assert end["credential_use_count"] == 1
    assert end["cleanup_succeeded"] is True
    assert end["timestamp_iso"] == "2026-05-09T12:00:00+00:00"
    assert "scope_count" in end
