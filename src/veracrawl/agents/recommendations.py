"""Framework-neutral agent recommendation intake."""

from __future__ import annotations

from veracrawl.contracts.agent import AgentRecommendation
from veracrawl.contracts.command import CommandEnvelope
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AgentRecommendationStatus, OwnerService
from veracrawl.control.runtime import create_runtime_command

FORBIDDEN_CONTEXT_MARKERS = (
    "raw_secret",
    "agent_visible_secret",
    "untainted_page_text",
    "policy-denied",
    "framework-native-state",
)


def recommendation_policy_errors(recommendation: AgentRecommendation) -> list[str]:
    errors: list[str] = []
    refs = [
        recommendation.context_bundle_trace_ref,
        recommendation.recommendation_payload_ref,
        recommendation.subject_ref,
    ]
    for ref in refs:
        normalized_ref = ref.lower().replace(":", "_").replace("-", "_")
        if any(marker in normalized_ref for marker in FORBIDDEN_CONTEXT_MARKERS):
            errors.append(f"forbidden recommendation context ref: {ref}")
    if not recommendation.policy_decision_refs:
        errors.append("agent recommendation requires policy decision refs")
    return errors


def recommendation_to_owner_command(
    recommendation: AgentRecommendation,
    *,
    command_id: str | None = None,
    actor_ref: Ref = "actor:agent-recommendation-intake",
) -> CommandEnvelope:
    if recommendation_policy_errors(recommendation):
        raise ValueError("rejected recommendations cannot become owner commands")
    return create_runtime_command(
        command_id=command_id or f"cmd:{recommendation.id}:owner-command",
        command_type="accept_agent_recommendation",
        target_aggregate_type=recommendation.subject_type.value,
        target_aggregate_id=recommendation.subject_ref,
        actor_ref=actor_ref,
        payload_ref=recommendation.recommendation_payload_ref,
        policy_decision_refs=recommendation.policy_decision_refs,
    )


def intake_agent_recommendation(
    recommendation: AgentRecommendation,
) -> tuple[AgentRecommendation, CommandEnvelope | None]:
    errors = recommendation_policy_errors(recommendation)
    if errors:
        return (
            recommendation.model_copy(
                update={
                    "status": AgentRecommendationStatus.REJECTED,
                    "rejection_reasons": errors,
                    "owner_command_ref": None,
                }
            ),
            None,
        )
    command = recommendation_to_owner_command(recommendation)
    return (
        recommendation.model_copy(
            update={
                "status": AgentRecommendationStatus.ACCEPTED,
                "owner_command_ref": command.id,
            }
        ),
        command,
    )


def recommendation_owner() -> OwnerService:
    return OwnerService.AGENTS
