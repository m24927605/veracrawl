"""Unit tests for Phase 2 step 2.5a — ``AgentCredentialLifecycle``."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

import pytest
import structlog

from veracrawl.agents.credential_lifecycle import AgentCredentialLifecycle
from veracrawl.contracts.agent import AgentRole, AgentRunRequest
from veracrawl.contracts.common import Ref
from veracrawl.contracts.security_privacy import CredentialScope
from veracrawl.ports.credential_scope_registry import (
    CredentialScopeRegistryError,
    CredentialScopeRegistryPort,
)

_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


def _make_scope(*, id: str = "cred-scope:ebay-prod") -> CredentialScope:
    return CredentialScope(
        id=id,
        credential_handle_ref=f"vault:{id}",
        allowed_origins=["https://api.example.com"],
        allowed_route_patterns=["^/v1/items"],
        allowed_methods=["GET"],
    )


def _make_request(*, scope_refs: list[Ref] | None = None) -> AgentRunRequest:
    return AgentRunRequest(
        id="agent-run-request:1",
        run_id="run:test:1",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="runtime-spec:test",
        objective_ref="objective:test",
        context_bundle_id="context-bundle:test",
        required_output_schema_ref="output-schema:test",
        loop_budget_ref="loop-budget:test",
        policy_decision_refs=["policy-decision:test"],
        credential_scope_refs=scope_refs or [],
    )


class _StubRegistry:
    def __init__(self, *, scopes: dict[Ref, CredentialScope] | None = None) -> None:
        self._scopes = scopes or {}

    def resolve(self, scope_ref: Ref) -> CredentialScope:
        if scope_ref not in self._scopes:
            raise CredentialScopeRegistryError(scope_ref_length=len(scope_ref))
        return self._scopes[scope_ref]


def test_lifecycle_resolves_all_scope_refs_at_enter() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    with AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    ) as session:
        assert len(session.scopes) == 1
        assert session.scopes[0] is scope
        assert session.scope_for("cred-scope:ebay-prod") is scope


def test_lifecycle_with_no_credential_refs_resolves_to_empty() -> None:
    registry = _StubRegistry()
    request = _make_request(scope_refs=[])
    with AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    ) as session:
        assert session.scopes == ()


def test_lifecycle_emits_start_and_end_events() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    with structlog.testing.capture_logs() as captured:
        with AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:test:1",
            clock=lambda: _FROZEN_NOW,
        ):
            pass
    starts = [e for e in captured if e.get("event") == "agent_credential_session_started"]
    ends = [e for e in captured if e.get("event") == "agent_credential_session_ended"]
    assert len(starts) == 1
    assert len(ends) == 1
    assert starts[0]["scope_count"] == 1
    assert starts[0]["scope_ids"] == ("cred-scope:ebay-prod",)
    assert ends[0]["scope_count"] == 1
    assert ends[0]["ended_with_exception"] is False


def test_lifecycle_invokes_on_session_end_callback() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    invocations: list[tuple[CredentialScope, ...]] = []

    def callback(scopes: Iterable[CredentialScope]) -> None:
        invocations.append(tuple(scopes))

    with AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:test:1",
        on_session_end=callback,
        clock=lambda: _FROZEN_NOW,
    ):
        pass
    assert len(invocations) == 1
    assert invocations[0] == (scope,)


def test_unknown_scope_ref_raises_at_enter() -> None:
    registry = _StubRegistry()
    request = _make_request(scope_refs=["cred-scope:unknown"])
    lifecycle = AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    )
    with pytest.raises(CredentialScopeRegistryError) as excinfo:
        lifecycle.__enter__()
    # Length-only redacted error text.
    assert "cred-scope:unknown" not in str(excinfo.value)
    assert "redacted" in str(excinfo.value)


def test_lifecycle_marks_exit_with_exception_when_body_raises() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    with structlog.testing.capture_logs() as captured:
        with pytest.raises(RuntimeError):
            with AgentCredentialLifecycle(
                request=request,
                registry=registry,
                run_ref="run:test:1",
                clock=lambda: _FROZEN_NOW,
            ):
                raise RuntimeError("simulated agent failure")
    ends = [e for e in captured if e.get("event") == "agent_credential_session_ended"]
    assert len(ends) == 1
    assert ends[0]["ended_with_exception"] is True


def test_lifecycle_callback_failure_does_not_mask_exit() -> None:
    """If the on_session_end callback raises, lifecycle still exits
    cleanly (logs the failure). Don't mask the original __exit__
    semantics — agent runtime should not break because a vault
    cache-invalidation hook misbehaved."""

    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])

    def failing_callback(scopes: Iterable[CredentialScope]) -> None:
        del scopes
        raise RuntimeError("simulated cache invalidation failure")

    with structlog.testing.capture_logs() as captured:
        with AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:test:1",
            on_session_end=failing_callback,
            clock=lambda: _FROZEN_NOW,
        ):
            pass
    failures = [
        e
        for e in captured
        if e.get("event") == "agent_credential_session_end_callback_failed"
    ]
    assert len(failures) == 1


def test_scope_for_unknown_ref_raises_keyerror() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    with AgentCredentialLifecycle(
        request=request,
        registry=registry,
        run_ref="run:test:1",
        clock=lambda: _FROZEN_NOW,
    ) as session:
        with pytest.raises(KeyError):
            session.scope_for("cred-scope:unresolved")


def test_session_id_is_unique_per_lifecycle() -> None:
    scope = _make_scope()
    registry = _StubRegistry(scopes={"cred-scope:ebay-prod": scope})
    request = _make_request(scope_refs=["cred-scope:ebay-prod"])
    ids: set[str] = set()
    for _ in range(3):
        lifecycle = AgentCredentialLifecycle(
            request=request,
            registry=registry,
            run_ref="run:test:1",
            clock=lambda: _FROZEN_NOW,
        )
        ids.add(lifecycle.session_id)
    assert len(ids) == 3


def test_registry_satisfies_protocol() -> None:
    """Smoke test: the stub satisfies the Protocol surface."""

    registry: CredentialScopeRegistryPort = _StubRegistry()
    assert isinstance(registry, CredentialScopeRegistryPort)


def test_credential_scope_refs_default_empty_on_request() -> None:
    """Backward compat: AgentRunRequest without explicit
    credential_scope_refs defaults to empty (existing call sites
    keep working)."""

    request = AgentRunRequest(
        id="r:1",
        run_id="run:1",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="rts:1",
        objective_ref="obj:1",
        context_bundle_id="ctx:1",
        required_output_schema_ref="out:1",
        loop_budget_ref="lb:1",
        policy_decision_refs=["pol:1"],
    )
    assert request.credential_scope_refs == []
