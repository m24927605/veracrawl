"""``LlmCrawlPlanner`` — s2 step 4 real LLM-driven crawl planner.

See ``docs/plans/general-purpose-crawler-agentification/
s2-llm-crawl-planner-adapter.md``. Composes
``ModelProviderPortV2`` + ``PromptRegistryPort`` + ``TokenBudgetPort``
to triage a caller's ``PlanRequest.seed_urls`` into a typed s1
``PlanDecision``. Replay-strict: requires
``ProviderResponse.raw_response_ref`` non-blank.
"""

from __future__ import annotations

from pydantic import ValidationError

from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    FrontierPriorityHint,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import (
    MessageRole,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import (
    ProviderTraceMissingError,
    StructuredOutputViolation,
)
from veracrawl.contracts.llm_crawl_planner import LlmPlanProposal
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.ports.crawl_planner import CrawlPlannerPort
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort


def _struct_violation() -> StructuredOutputViolation:
    return StructuredOutputViolation(
        status_code=200, error_code="STRUCTURED_OUTPUT_VIOLATION", request_id=None,
    )


class LlmCrawlPlanner(CrawlPlannerPort):
    """Real LLM-driven ``CrawlPlannerPort`` implementation (s2)."""

    def __init__(
        self,
        *,
        model_provider: ModelProviderPortV2,
        prompt_registry: PromptRegistryPort,
        token_budget: TokenBudgetPort,
        prompt_template_ref: str,
        model_name: str,
        max_output_tokens: int,
        temperature: float = 0.0,
        adapter_ref: str = "adapter:llm-crawl-planner:v1",
    ) -> None:
        self._model_provider = model_provider
        self._prompt_registry = prompt_registry
        self._token_budget = token_budget
        self._prompt_template_ref = prompt_template_ref
        self._model_name = model_name
        self._max_output_tokens = max_output_tokens
        self._temperature = temperature
        self._adapter_ref = adapter_ref

    def plan(self, request: PlanRequest) -> PlanDecision:
        rendered = self._prompt_registry.render(
            self._prompt_template_ref,
            {
                "objective_ref": request.objective_ref,
                "seed_urls": list(request.seed_urls),
                "budget_ref": request.budget_ref,
                "policy_snapshot_ref": request.policy_snapshot_ref,
                "run_ref": request.run_ref,
            },
        )
        provider_request = ProviderRequest(
            id=f"provider-request:{request.id}",
            run_ref=request.run_ref,
            model_name=self._model_name,
            messages=[Message(role=MessageRole.USER, content=rendered)],
            response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
            max_output_tokens=self._max_output_tokens,
            temperature=self._temperature,
        )
        self._token_budget.estimate_charge(provider_request)
        response = self._model_provider.complete(provider_request)
        # Charge BEFORE structured-output validation so malformed-output
        # calls still account for the tokens the provider billed.
        self._token_budget.charge(response.usage, request_ref=provider_request.id)
        if response.raw_response_ref is None or not response.raw_response_ref.strip():
            raise ProviderTraceMissingError(provider_request_id=provider_request.id)
        if response.parsed_output is None:
            raise _struct_violation()
        try:
            proposal = LlmPlanProposal.model_validate(response.parsed_output)
        except ValidationError as exc:
            del exc
            raise _struct_violation() from None
        return self._project(request, proposal, response.id, response.raw_response_ref)

    def _project(
        self, request: PlanRequest, proposal: LlmPlanProposal,
        response_id: str, raw_response_ref: str,
    ) -> PlanDecision:
        seeds = [
            PlannedSeed(
                canonical_url=s.canonical_url,
                priority_score=s.priority_score,
                adapter_hint=s.adapter_hint,
                rationale_ref=(
                    f"rationale:{self._adapter_ref}:{self._prompt_template_ref}:seed-{i}"
                ),
            )
            for i, s in enumerate(proposal.planned_seeds)
        ]
        priors = [
            AdapterPrior(
                adapter_type=p.adapter_type,
                weight=p.weight,
                rationale_ref=(
                    f"rationale:{self._adapter_ref}:{self._prompt_template_ref}"
                    f":prior-{p.adapter_type.value}"
                ),
            )
            for p in proposal.adapter_priors
        ]
        hints = [
            FrontierPriorityHint(
                match_kind=h.match_kind,
                match_value=h.match_value,
                priority_delta=h.priority_delta,
                rationale_ref=(
                    f"rationale:{self._adapter_ref}:{self._prompt_template_ref}"
                    f":hint-{h.match_kind.value}"
                ),
            )
            for h in proposal.frontier_priority_hints
        ]
        return PlanDecision(
            id=f"plan-decision:{request.id}",
            request_ref=request.id,
            planner_adapter_ref=self._adapter_ref,
            planned_seeds=seeds,
            adapter_priors=priors,
            frontier_priority_hints=hints,
            extraction_strategy_refs=list(proposal.extraction_strategy_refs),
            replay_refs=[
                request.id, self._adapter_ref, request.replay_config_ref,
                request.objective_ref, self._prompt_template_ref,
                response_id, raw_response_ref,
            ],
            policy_decision_refs=list(request.policy_decision_refs),
        )
