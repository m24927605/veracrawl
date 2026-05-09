"""Phase 2 step 2.5b — credential lifecycle end-to-end integration test.

design.md §4 Phase 2 acceptance: "an authorized session against a
test API succeeds with vault audit, credential redaction, and
replay event present." We don't yet have a controlled test API
(Phase 6 step 6.4 ships that infra). This test runs as a
non-live integration test (no `@pytest.mark.live` marker — that
marker is reserved for tests that hit real external services).
The "live test against controlled API" is therefore a Phase 6
step 6.4 reservation; this step ships the structural integration
test instead.

Components exercised:

* :class:`InMemoryVaultBackend` (test vault)
* :class:`OutboxVaultClient` (production vault client + access audit)
* :class:`StrictAllowlistScope` (production scope policy)
* :class:`AuthorizedSessionAdapter` (production credential injection +
  lifecycle counter auto-wiring)
* :class:`AgentCredentialLifecycle` (production lifecycle wrapper)
* :class:`OutboxCredentialUseAuditWriter` (production durable use
  audit — test injects in-memory persister + outbox repo)

The integration test asserts the durable replay-event contract:
each credential use produces one ``CredentialUseRecord`` AND one
outbox row on the ``"credential-use"`` topic, ready for a
downstream replay tool to consume.
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
from veracrawl.adapters.credential_vault.outbox_credential_use_audit import (
    OutboxCredentialUseAuditWriter,
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
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.security_privacy import (
    CredentialScope,
    CredentialUseRecord,
)
from veracrawl.ports.credential_access_audit import CredentialAccessOutcome

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


class _InMemoryOutboxRepo:
    def __init__(self) -> None:
        self.appended: list[OutboxRecord] = []

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.appended.append(record)
        return f"outbox-ref:{record.id}"

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        del run_ref
        return list(self.appended)

    def mark_outbox_dispatched(
        self, outbox_ref: Ref, *, dispatched_at_ref: Ref
    ) -> OutboxRecord:
        del outbox_ref, dispatched_at_ref
        raise NotImplementedError

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        del outbox_ref, error_ref
        raise NotImplementedError


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
        id="agent-run-request:int-2-5b",
        run_id="run:int-2-5b:1",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="runtime-spec:int-2-5b",
        objective_ref="objective:int-2-5b",
        context_bundle_id="context-bundle:int-2-5b",
        required_output_schema_ref="output-schema:int-2-5b",
        loop_budget_ref="loop-budget:int-2-5b",
        policy_decision_refs=["policy-decision:int-2-5b"],
        credential_scope_refs=[scope_ref],
    )


def _echo_authorization_transport() -> tuple[httpx.MockTransport, list[str]]:
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("authorization")
        if auth is not None:
            captured.append(auth)
        return httpx.Response(200, content=b'{"echoed":"ok"}')

    return httpx.MockTransport(handler), captured


def _build_stack(
    *, persisted_records: list[CredentialUseRecord]
) -> tuple[
    AuthorizedSessionAdapter,
    AgentCredentialLifecycle,
    _RecordingAccessAudit,
    list[str],
    _InMemoryOutboxRepo,
]:
    """Construct the full Phase 2 production stack with auto-wired
    lifecycle counter (codex iter-1 important — adapter owns the
    accounting, not the test). Returns the components the test
    asserts on."""

    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:int-2-5b:1",
        clock=lambda: _FROZEN_NOW,
    )
    transport, captured_auth = _echo_authorization_transport()
    outbox_repo = _InMemoryOutboxRepo()

    def persister(record: CredentialUseRecord) -> Ref:
        persisted_records.append(record)
        return f"payload:{record.id}"

    use_audit = OutboxCredentialUseAuditWriter(
        record_persister=persister,
        outbox_repo=outbox_repo,
        command_result_ref="cmd-result:int-2-5b",
        event_ref="event:int-2-5b",
    )
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")

    lifecycle = AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:int-2-5b:1",
        clock=lambda: _FROZEN_NOW,
    )
    lifecycle.__enter__()
    adapter = AuthorizedSessionAdapter(
        transport=transport,
        vault=vault,
        scope_policy=StrictAllowlistScope(),
        credential_scope=lifecycle.scope_for("cred-scope:ebay-prod"),
        vault_scope_ref="EBAY_PROD",
        vault_key="API_KEY",
        use_audit=use_audit,
        run_ref="run:int-2-5b:1",
        clock=lambda: _FROZEN_NOW,
        lifecycle=lifecycle,
    )
    return adapter, lifecycle, access_audit, captured_auth, outbox_repo


def test_three_request_flow_records_one_use_record_and_outbox_row_per_request() -> None:
    """End-to-end: 3 requests → 3 CredentialUseRecord rows in the
    durable persister + 3 outbox rows on the ``credential-use``
    topic + lifecycle counter == 3 (auto-wired)."""

    persisted: list[CredentialUseRecord] = []
    adapter, lifecycle, access_audit, captured_auth, outbox_repo = _build_stack(
        persisted_records=persisted
    )

    try:
        for path in ("/v1/items/1", "/v1/items/2", "/v1/items/3"):
            response = adapter.request(
                method="GET",
                url=f"https://api.example.com{path}",
            )
            assert response.status_code == 200
        assert lifecycle.credential_use_count == 3
    finally:
        lifecycle.__exit__(None, None, None)

    assert len(access_audit.records) == 3
    assert all(
        rec["outcome"] is CredentialAccessOutcome.SUCCESS
        for rec in access_audit.records
    )
    assert len(persisted) == 3
    assert all(rec.response_status == 200 for rec in persisted)
    assert len(outbox_repo.appended) == 3
    for outbox_row in outbox_repo.appended:
        assert outbox_row.dispatch_topic == "credential-use"
        assert outbox_row.run_ref == "run:int-2-5b:1"
    assert len(captured_auth) == 3


def test_credential_redaction_holds_through_durable_audit_chain() -> None:
    """Canary secret never appears in:
    - access audit records
    - durable persisted CredentialUseRecord
    - outbox rows
    - structured-log events"""

    persisted: list[CredentialUseRecord] = []
    with structlog.testing.capture_logs() as captured_logs:
        adapter, lifecycle, access_audit, _, outbox_repo = _build_stack(
            persisted_records=persisted
        )
        try:
            adapter.request(method="GET", url="https://api.example.com/v1/items")
        finally:
            lifecycle.__exit__(None, None, None)

    for record in access_audit.records:
        assert _CANARY_SECRET not in str(record)
    for record in persisted:
        assert _CANARY_SECRET not in str(record.__dict__)
    for outbox_row in outbox_repo.appended:
        assert _CANARY_SECRET not in str(outbox_row.__dict__)
    for event in captured_logs:
        assert _CANARY_SECRET not in str(event)


def test_replay_event_present_via_outbox_row_payload_ref() -> None:
    """Each credential use produces one durable outbox row with a
    payload_ref pointing at the persisted CredentialUseRecord —
    replay tooling consumes the outbox topic + dereferences the
    payload."""

    persisted: list[CredentialUseRecord] = []
    adapter, lifecycle, _, _, outbox_repo = _build_stack(
        persisted_records=persisted
    )
    try:
        adapter.request(method="GET", url="https://api.example.com/v1/items")
    finally:
        lifecycle.__exit__(None, None, None)

    assert len(outbox_repo.appended) == 1
    outbox_row = outbox_repo.appended[0]
    assert outbox_row.dispatch_topic == "credential-use"
    assert outbox_row.idempotency_key == persisted[0].id
    assert outbox_row.payload_ref == f"payload:{persisted[0].id}"


def test_lifecycle_counter_matches_use_record_count_via_auto_wiring() -> None:
    """Lifecycle counter and use-record count agree by construction
    — the adapter owns the accounting (codex iter-1 important)."""

    persisted: list[CredentialUseRecord] = []
    adapter, lifecycle, _, _, outbox_repo = _build_stack(
        persisted_records=persisted
    )
    try:
        for _ in range(5):
            adapter.request(method="GET", url="https://api.example.com/v1/items")
    finally:
        lifecycle.__exit__(None, None, None)

    assert lifecycle.credential_use_count == 5
    assert len(persisted) == 5
    assert len(outbox_repo.appended) == 5


def test_transport_failure_increments_lifecycle_counter() -> None:
    """Codex iter-2 important: a persisted CredentialUseRecord on
    the transport-failure path IS a credential use; lifecycle
    counter must reflect it so durable count and lifecycle count
    agree by construction."""

    persisted: list[CredentialUseRecord] = []
    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:int-2-5b:tx-fail",
        clock=lambda: _FROZEN_NOW,
    )

    class _RaisingTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            del request
            raise RuntimeError("simulated transport failure")

    outbox_repo = _InMemoryOutboxRepo()

    def persister(record: CredentialUseRecord) -> Ref:
        persisted.append(record)
        return f"payload:{record.id}"

    use_audit = OutboxCredentialUseAuditWriter(
        record_persister=persister,
        outbox_repo=outbox_repo,
        command_result_ref="cmd-result:tx-fail",
        event_ref="event:tx-fail",
    )
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")
    lifecycle = AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:int-2-5b:tx-fail",
        clock=lambda: _FROZEN_NOW,
    )
    lifecycle.__enter__()
    adapter = AuthorizedSessionAdapter(
        transport=_RaisingTransport(),
        vault=vault,
        scope_policy=StrictAllowlistScope(),
        credential_scope=lifecycle.scope_for("cred-scope:ebay-prod"),
        vault_scope_ref="EBAY_PROD",
        vault_key="API_KEY",
        use_audit=use_audit,
        run_ref="run:int-2-5b:tx-fail",
        clock=lambda: _FROZEN_NOW,
        lifecycle=lifecycle,
    )
    try:
        with pytest.raises(RuntimeError, match="simulated transport failure"):
            adapter.request(method="GET", url="https://api.example.com/v1/items")
        # Persisted use record + matching lifecycle counter.
        assert len(persisted) == 1
        assert persisted[0].response_status is None
        assert lifecycle.credential_use_count == 1
    finally:
        lifecycle.__exit__(None, None, None)


def test_stale_lifecycle_record_use_logs_audit_gap_not_raises() -> None:
    """Codex iter-2 important: a stale lifecycle (never entered)
    would cause record_use to raise. Adapter must wrap and log
    the accounting gap rather than propagate after the credential
    was already used + durably audited."""

    persisted: list[CredentialUseRecord] = []
    scope = _make_credential_scope()
    backend = InMemoryVaultBackend(
        credentials={("EBAY_PROD", "API_KEY"): _CANARY_SECRET}
    )
    access_audit = _RecordingAccessAudit()
    vault = OutboxVaultClient(
        backend=backend,
        audit=access_audit,
        run_ref="run:int-2-5b:stale",
        clock=lambda: _FROZEN_NOW,
    )
    transport, _ = _echo_authorization_transport()
    outbox_repo = _InMemoryOutboxRepo()

    def persister(record: CredentialUseRecord) -> Ref:
        persisted.append(record)
        return f"payload:{record.id}"

    use_audit = OutboxCredentialUseAuditWriter(
        record_persister=persister,
        outbox_repo=outbox_repo,
        command_result_ref="cmd-result:stale",
        event_ref="event:stale",
    )
    registry = _StubScopeRegistry({"cred-scope:ebay-prod": scope})
    request = _make_run_request("cred-scope:ebay-prod")
    # Lifecycle constructed but NOT entered — record_use will raise.
    stale_lifecycle = AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:int-2-5b:stale",
        clock=lambda: _FROZEN_NOW,
    )
    adapter = AuthorizedSessionAdapter(
        transport=transport,
        vault=vault,
        scope_policy=StrictAllowlistScope(),
        credential_scope=scope,
        vault_scope_ref="EBAY_PROD",
        vault_key="API_KEY",
        use_audit=use_audit,
        run_ref="run:int-2-5b:stale",
        clock=lambda: _FROZEN_NOW,
        lifecycle=stale_lifecycle,
    )
    with structlog.testing.capture_logs() as captured_logs:
        # Adapter must NOT raise even though stale_lifecycle.record_use
        # would. The credential is already audited; gap is logged.
        response = adapter.request(
            method="GET", url="https://api.example.com/v1/items"
        )
    assert response.status_code == 200
    assert len(persisted) == 1
    failures = [
        e
        for e in captured_logs
        if e.get("event") == "credential_use_lifecycle_record_failed"
    ]
    assert len(failures) == 1
    assert failures[0]["phase"] == "completion"


def test_lifecycle_not_incremented_when_request_is_refused() -> None:
    """Out-of-scope refusal must NOT increment the lifecycle
    counter (no successful credential use)."""

    from veracrawl.contracts.errors import CredentialScopeViolation

    persisted: list[CredentialUseRecord] = []
    adapter, lifecycle, _, _, _ = _build_stack(persisted_records=persisted)
    try:
        with pytest.raises(CredentialScopeViolation):
            adapter.request(
                method="GET",
                url="https://other.example.com/v1/items",
            )
        assert lifecycle.credential_use_count == 0
    finally:
        lifecycle.__exit__(None, None, None)
