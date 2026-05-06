"""Tests for the policy-aware InMemoryToolGateway behavior.

The legacy ``InMemoryToolGateway()`` (no policy) is preserved for
fixture / contract test compatibility. The new policy-aware mode is
opt-in via the ``policy=`` keyword and enforces:

- allowlist of command_type values
- per-actor quota (max calls + max cost)
- audit log of every decision (committed and rejected)
"""

from __future__ import annotations

from veracrawl.agents.tool_gateway import (
    InMemoryToolGateway,
    RejectionReason,
    ToolGatewayAuditEvent,
    ToolPolicy,
)
from veracrawl.contracts.command import CommandEnvelope
from veracrawl.contracts.enums import CommandResultStatus, CommandStatus


def _envelope(
    *,
    command_type: str = "accept_agent_recommendation",
    actor_ref: str = "agent:test",
    command_id: str = "cmd:1",
) -> CommandEnvelope:
    return CommandEnvelope(
        id=command_id,
        command_type=command_type,
        target_aggregate_type="recommendation",
        target_aggregate_id="rec:1",
        idempotency_key=f"idem:{command_id}",
        actor_ref=actor_ref,
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=["policy:test:tool-call"],
        status=CommandStatus.PROPOSED,
    )


# Backwards compat: legacy mode (no policy) preserved.


def test_legacy_mode_no_policy_still_commits() -> None:
    gateway = InMemoryToolGateway()
    result = gateway.execute(_envelope())
    assert result.result == CommandResultStatus.COMMITTED


def test_legacy_mode_does_not_record_audit_events() -> None:
    gateway = InMemoryToolGateway()
    gateway.execute(_envelope())
    # In legacy mode the audit feed stays empty so existing fixture tests do
    # not have to assert against new state.
    assert gateway.audit_events == ()


# Policy mode: allowlist enforcement.


def test_policy_mode_rejects_unknown_command_type() -> None:
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    result = gateway.execute(_envelope(command_type="DELETE_ALL_USERS"))
    assert result.result == CommandResultStatus.REJECTED
    assert result.rejection_reasons
    assert RejectionReason.UNKNOWN_TOOL.value in result.rejection_reasons[0]


def test_policy_mode_allows_known_command_type() -> None:
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    result = gateway.execute(_envelope(command_type="accept_agent_recommendation"))
    assert result.result == CommandResultStatus.COMMITTED


def test_policy_with_empty_allowlist_rejects_everything() -> None:
    gateway = InMemoryToolGateway(policy=ToolPolicy(allowed_command_types=frozenset()))
    result = gateway.execute(_envelope())
    assert result.result == CommandResultStatus.REJECTED


# Policy mode: quota enforcement.


def test_quota_max_calls_per_actor_exceeded() -> None:
    policy = ToolPolicy(
        allowed_command_types=frozenset({"accept_agent_recommendation"}),
        max_calls_per_actor=2,
    )
    gateway = InMemoryToolGateway(policy=policy)

    r1 = gateway.execute(_envelope(command_id="cmd:a"))
    r2 = gateway.execute(_envelope(command_id="cmd:b"))
    r3 = gateway.execute(_envelope(command_id="cmd:c"))

    assert r1.result == CommandResultStatus.COMMITTED
    assert r2.result == CommandResultStatus.COMMITTED
    assert r3.result == CommandResultStatus.REJECTED
    assert RejectionReason.QUOTA_EXCEEDED_CALLS.value in r3.rejection_reasons[0]


def test_quota_max_cost_per_actor_exceeded() -> None:
    policy = ToolPolicy(
        allowed_command_types=frozenset({"accept_agent_recommendation"}),
        max_cost_tokens_per_actor=100,
        cost_per_call={"accept_agent_recommendation": 50},
    )
    gateway = InMemoryToolGateway(policy=policy)

    # 50 + 50 = 100 == cap (allowed), next would push to 150 (over).
    r1 = gateway.execute(_envelope(command_id="cmd:a"))
    r2 = gateway.execute(_envelope(command_id="cmd:b"))
    r3 = gateway.execute(_envelope(command_id="cmd:c"))

    assert r1.result == CommandResultStatus.COMMITTED
    assert r2.result == CommandResultStatus.COMMITTED
    assert r3.result == CommandResultStatus.REJECTED
    assert RejectionReason.QUOTA_EXCEEDED_COST.value in r3.rejection_reasons[0]


def test_quota_is_per_actor_independent() -> None:
    policy = ToolPolicy(
        allowed_command_types=frozenset({"accept_agent_recommendation"}),
        max_calls_per_actor=1,
    )
    gateway = InMemoryToolGateway(policy=policy)

    r_a1 = gateway.execute(_envelope(actor_ref="agent:a", command_id="cmd:a1"))
    r_a2 = gateway.execute(_envelope(actor_ref="agent:a", command_id="cmd:a2"))
    r_b1 = gateway.execute(_envelope(actor_ref="agent:b", command_id="cmd:b1"))

    assert r_a1.result == CommandResultStatus.COMMITTED
    assert r_a2.result == CommandResultStatus.REJECTED
    # Actor B not yet over quota.
    assert r_b1.result == CommandResultStatus.COMMITTED


def test_unknown_command_type_does_not_consume_quota() -> None:
    policy = ToolPolicy(
        allowed_command_types=frozenset({"accept_agent_recommendation"}),
        max_calls_per_actor=2,
    )
    gateway = InMemoryToolGateway(policy=policy)

    # Two rejected calls do not eat the actor's quota.
    gateway.execute(_envelope(command_type="DELETE_USERS", command_id="cmd:r1"))
    gateway.execute(_envelope(command_type="DELETE_USERS", command_id="cmd:r2"))

    # Then two legitimate calls should still both succeed.
    r1 = gateway.execute(_envelope(command_id="cmd:ok1"))
    r2 = gateway.execute(_envelope(command_id="cmd:ok2"))
    assert r1.result == CommandResultStatus.COMMITTED
    assert r2.result == CommandResultStatus.COMMITTED


# Policy mode: audit events.


def test_audit_event_recorded_on_commit() -> None:
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    gateway.execute(_envelope(command_id="cmd:audit-ok"))

    events = gateway.audit_events
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, ToolGatewayAuditEvent)
    assert event.command_id == "cmd:audit-ok"
    assert event.command_type == "accept_agent_recommendation"
    assert event.actor_ref == "agent:test"
    assert event.decision == "COMMITTED"
    assert event.rejection_reason is None


def test_audit_event_recorded_on_rejection() -> None:
    policy = ToolPolicy(allowed_command_types=frozenset({"only_this_one"}))
    gateway = InMemoryToolGateway(policy=policy)
    gateway.execute(_envelope(command_type="DENIED_TYPE", command_id="cmd:audit-no"))

    events = gateway.audit_events
    assert len(events) == 1
    event = events[0]
    assert event.command_id == "cmd:audit-no"
    assert event.command_type == "DENIED_TYPE"
    assert event.decision == "REJECTED"
    assert event.rejection_reason == RejectionReason.UNKNOWN_TOOL


def test_audit_events_returned_as_immutable_snapshot() -> None:
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    gateway.execute(_envelope(command_id="cmd:1"))
    snapshot = gateway.audit_events
    gateway.execute(_envelope(command_id="cmd:2"))
    # Snapshot taken before second call must still show only 1.
    assert len(snapshot) == 1


def test_audit_event_does_not_carry_payload_data() -> None:
    """Audit must reference the command by id/type/actor only — never embed
    raw payload bytes that could leak prompts or other sensitive content."""
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    gateway.execute(_envelope(command_id="cmd:no-payload"))

    event = gateway.audit_events[0]
    # Audit fields enumerate exactly what is captured.
    captured = event.model_dump()
    # No "payload", "args", "body", "prompt", etc. keys.
    forbidden = {"payload", "args", "body", "prompt", "context", "raw"}
    assert not (forbidden & set(captured.keys()))


# Existing CommandResult validators still hold.


def test_rejected_result_carries_rejection_reasons_per_contract() -> None:
    """CommandResult model_validator requires rejection_reasons on REJECTED.
    The gateway must satisfy this so the result is constructible at all."""
    gateway = InMemoryToolGateway(policy=ToolPolicy(allowed_command_types=frozenset()))
    result = gateway.execute(_envelope())
    assert result.result == CommandResultStatus.REJECTED
    assert len(result.rejection_reasons) >= 1


def test_committed_result_carries_emitted_event_refs_per_contract() -> None:
    """CommandResult validator requires emitted_event_refs on COMMITTED."""
    policy = ToolPolicy(allowed_command_types=frozenset({"accept_agent_recommendation"}))
    gateway = InMemoryToolGateway(policy=policy)
    result = gateway.execute(_envelope())
    assert result.result == CommandResultStatus.COMMITTED
    assert len(result.emitted_event_refs) >= 1


def test_rejection_reason_enum_values_are_stable_strings() -> None:
    """Callers may switch on the enum value; verify the wire format is stable."""
    assert RejectionReason.UNKNOWN_TOOL.value == "unknown_tool"
    assert RejectionReason.QUOTA_EXCEEDED_CALLS.value == "quota_exceeded_calls"
    assert RejectionReason.QUOTA_EXCEEDED_COST.value == "quota_exceeded_cost"


# pytest discovery sanity for empty-policy edge case.


def test_default_policy_kwargs_have_safe_defaults() -> None:
    """ToolPolicy with only allowlist should still produce well-defined behavior."""
    policy = ToolPolicy(allowed_command_types=frozenset({"a"}))
    assert policy.max_calls_per_actor > 0
    assert policy.max_cost_tokens_per_actor >= 0
    assert isinstance(policy.cost_per_call, dict)
