"""Tool gateway.

Two operating modes:

- **Legacy** (``InMemoryToolGateway()`` with no ``policy`` argument): the
  original "always commit" behavior, preserved unchanged for fixture and
  contract tests that drive synthetic recommendations through a permissive
  gateway. No audit events are recorded.
- **Policy-aware** (``policy=ToolPolicy(...)``): enforces an allowlist of
  ``command_type`` values, a per-actor quota over both call count and a
  configurable cost-per-call (in tokens), and writes a structured audit
  event for every decision (committed and rejected). The audit log lists
  only command metadata (id / type / actor / decision); it never embeds
  payload bytes, since the project's RAW_RESPONSE_LEAK boundary forbids
  payload content from entering audit, log, or telemetry surfaces.

Any caller that hands an LLM-driven agent direct access to the gateway
should use the policy-aware mode. The legacy mode exists only because
the contract test suite predates the policy surface and would otherwise
need broad refactoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from veracrawl.agents.recommendations import recommendation_to_owner_command
from veracrawl.contracts.agent import AgentRecommendation
from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.enums import CommandResultStatus


class RejectionReason(StrEnum):
    """Stable wire-format enum so callers can dispatch on the rejection cause."""

    UNKNOWN_TOOL = "unknown_tool"
    QUOTA_EXCEEDED_CALLS = "quota_exceeded_calls"
    QUOTA_EXCEEDED_COST = "quota_exceeded_cost"
    POLICY_DENIED = "policy_denied"


@dataclass(frozen=True)
class ToolPolicy:
    """Enforcement policy for an :class:`InMemoryToolGateway` instance.

    The policy is immutable: a process running multiple agents with
    different policies should construct multiple gateways.
    """

    allowed_command_types: frozenset[str]
    max_calls_per_actor: int = 100
    max_cost_tokens_per_actor: int = 100_000
    cost_per_call: dict[str, int] = field(default_factory=dict)


class ToolGatewayAuditEvent(BaseModel):
    """One row of the gateway's audit log.

    Captures only what is needed to reconstruct *that the call happened*
    and *what category of decision was made*. Deliberately does NOT include
    payload bytes, prompt text, or response content.
    """

    command_id: str
    command_type: str
    actor_ref: str
    decision: str  # "COMMITTED" | "REJECTED"
    rejection_reason: RejectionReason | None = None
    detail: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class _ActorQuotaState:
    """Per-actor accumulators consulted before each policy-mode commit."""

    __slots__ = ("calls", "cost_tokens")

    def __init__(self) -> None:
        self.calls: int = 0
        self.cost_tokens: int = 0


class InMemoryToolGateway:
    """Minimal gateway that keeps mutations command/result backed.

    Historically permissive; pass ``policy=ToolPolicy(...)`` to enable
    allowlist + quota + audit enforcement.
    """

    def __init__(self, *, policy: ToolPolicy | None = None) -> None:
        self._policy = policy
        self._actor_state: dict[str, _ActorQuotaState] = {}
        self._audit: list[ToolGatewayAuditEvent] = []

    # Backwards-compat method retained for the contract / fixture suites.
    def command_for_recommendation(
        self, recommendation: AgentRecommendation
    ) -> CommandEnvelope:
        return recommendation_to_owner_command(recommendation)

    def execute_recommendation(
        self, recommendation: AgentRecommendation
    ) -> CommandResult:
        command = self.command_for_recommendation(recommendation)
        return self.execute(command)

    @property
    def audit_events(self) -> tuple[ToolGatewayAuditEvent, ...]:
        """Return an immutable snapshot of audit events recorded so far."""
        return tuple(self._audit)

    def execute(self, command: CommandEnvelope) -> CommandResult:
        if self._policy is None:
            # Legacy permissive mode (no audit, no enforcement).
            return self._build_committed(command)

        # Policy mode: allowlist first.
        if command.command_type not in self._policy.allowed_command_types:
            return self._reject(
                command,
                reason=RejectionReason.UNKNOWN_TOOL,
                detail=f"command_type {command.command_type!r} not in allowlist",
            )

        # Quota check (uses prospective totals so we never under-report).
        state = self._actor_state.setdefault(command.actor_ref, _ActorQuotaState())
        prospective_calls = state.calls + 1
        if prospective_calls > self._policy.max_calls_per_actor:
            return self._reject(
                command,
                reason=RejectionReason.QUOTA_EXCEEDED_CALLS,
                detail=(
                    f"actor {command.actor_ref!r} would reach "
                    f"{prospective_calls} calls (cap {self._policy.max_calls_per_actor})"
                ),
            )

        cost = int(self._policy.cost_per_call.get(command.command_type, 0))
        prospective_cost = state.cost_tokens + cost
        if prospective_cost > self._policy.max_cost_tokens_per_actor:
            return self._reject(
                command,
                reason=RejectionReason.QUOTA_EXCEEDED_COST,
                detail=(
                    f"actor {command.actor_ref!r} would reach "
                    f"{prospective_cost} cost tokens "
                    f"(cap {self._policy.max_cost_tokens_per_actor})"
                ),
            )

        # Commit.
        state.calls = prospective_calls
        state.cost_tokens = prospective_cost
        result = self._build_committed(command)
        self._audit.append(
            ToolGatewayAuditEvent(
                command_id=command.id,
                command_type=command.command_type,
                actor_ref=command.actor_ref,
                decision="COMMITTED",
            )
        )
        return result

    def _reject(
        self,
        command: CommandEnvelope,
        *,
        reason: RejectionReason,
        detail: str,
    ) -> CommandResult:
        result = CommandResult(
            id=f"result:{command.id}",
            command_id=command.id,
            result=CommandResultStatus.REJECTED,
            rejection_reasons=[f"{reason.value}: {detail}"],
        )
        self._audit.append(
            ToolGatewayAuditEvent(
                command_id=command.id,
                command_type=command.command_type,
                actor_ref=command.actor_ref,
                decision="REJECTED",
                rejection_reason=reason,
                detail=detail,
            )
        )
        return result

    def _build_committed(self, command: CommandEnvelope) -> CommandResult:
        return CommandResult(
            id=f"result:{command.id}",
            command_id=command.id,
            result=CommandResultStatus.COMMITTED,
            emitted_event_refs=[f"event:{command.id}:committed"],
            output_refs=[f"output:{command.id}"],
        )
